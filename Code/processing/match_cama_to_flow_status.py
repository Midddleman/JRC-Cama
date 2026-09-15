"""Match CaMa-Flood catchment units to the aggregated flow-status raster.

The 1 km / 0.01 degree flow-status raster is kept as the reference grid.
CaMa-Flood catchments are projected onto it as points, and downstream_id is
used to sample a simple CaMa river segment from each point to its downstream
point.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from scipy import ndimage


RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"
NODATA = 255
EARTH_RADIUS_KM = 6371.0088


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
DEFAULT_FLOW_STATUS = (
    PROJECT_ROOT
    / "Output"
    / "ChinaFlowStatusMosaic"
    / RUN_LABEL
    / f"china_flow_status_factor33_{RUN_LABEL}.tif"
)
DEFAULT_CAMA_PARAMETERS = PROJECT_ROOT / "Data" / "Cama-Flood output" / "parameters_glb06.nc"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "CamaFlowStatusMatch" / RUN_LABEL


def haversine_km(lon1, lat1, lon2, lat2):
    lon1 = np.deg2rad(lon1)
    lat1 = np.deg2rad(lat1)
    lon2 = np.deg2rad(lon2)
    lat2 = np.deg2rad(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def load_cama_parameters(path, bounds, min_upstream_area_km2=None):
    with xr.open_dataset(path) as ds:
        frame = pd.DataFrame(
            {
                "catchment_id": ds["catchment_id"].values.astype(np.int64),
                "downstream_id": ds["downstream_id"].values.astype(np.int64),
                "basin_id": ds["catchment_basin_id"].values.astype(np.int64),
                "longitude": ds["longitude"].values.astype(np.float64),
                "latitude": ds["latitude"].values.astype(np.float64),
                "river_width": ds["river_width"].values.astype(np.float32),
                "river_depth": ds["river_depth"].values.astype(np.float32),
                "river_length": ds["river_length"].values.astype(np.float32),
                "catchment_area": ds["catchment_area"].values.astype(np.float64),
                "upstream_area": ds["upstream_area"].values.astype(np.float64),
                "is_river_mouth": ds["is_river_mouth"].values.astype(np.int8),
            }
        )

    inside = (
        (frame["longitude"] >= bounds.left)
        & (frame["longitude"] <= bounds.right)
        & (frame["latitude"] >= bounds.bottom)
        & (frame["latitude"] <= bounds.top)
    )
    frame = frame.loc[inside].copy()

    if min_upstream_area_km2 is not None:
        # CaMa parameter files commonly store area-like variables in m2.
        frame = frame.loc[frame["upstream_area"] >= float(min_upstream_area_km2) * 1_000_000.0].copy()

    return frame.reset_index(drop=True)


def rowcol_arrays(transform, lon, lat):
    inv = ~transform
    col_f, row_f = inv * (lon, lat)
    return np.floor(row_f).astype(np.int64), np.floor(col_f).astype(np.int64)


def pixel_centers(transform, rows, cols):
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    return np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64)


def label_flow_status(flow_status):
    water_mask = (flow_status == 1) | (flow_status == 2)
    component_labels, _ = ndimage.label(water_mask, structure=np.ones((3, 3), dtype=np.uint8))
    nearest_distance_deg, nearest_indices = ndimage.distance_transform_edt(
        ~water_mask,
        sampling=(1.0, 1.0),
        return_indices=True,
    )
    return water_mask, component_labels.astype(np.int32, copy=False), nearest_distance_deg, nearest_indices


def sample_segment(rows, cols, src_row, src_col, dst_row, dst_col, radius_cells):
    if src_row < 0 or src_col < 0 or dst_row < 0 or dst_col < 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)

    steps = int(max(abs(dst_row - src_row), abs(dst_col - src_col))) + 1
    if steps <= 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)

    line_rows = np.rint(np.linspace(src_row, dst_row, steps)).astype(np.int64)
    line_cols = np.rint(np.linspace(src_col, dst_col, steps)).astype(np.int64)

    if radius_cells <= 0:
        rr, cc = line_rows, line_cols
    else:
        offsets = np.arange(-radius_cells, radius_cells + 1, dtype=np.int64)
        dr, dc = np.meshgrid(offsets, offsets, indexing="ij")
        rr = (line_rows[:, None, None] + dr[None, :, :]).ravel()
        cc = (line_cols[:, None, None] + dc[None, :, :]).ravel()

    valid = (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
    if not np.any(valid):
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)

    unique = np.unique(np.stack([rr[valid], cc[valid]], axis=1), axis=0)
    return unique[:, 0], unique[:, 1]


def summarize_segment(flow_status, component_labels, src_row, src_col, dst_row, dst_col, radius_cells):
    rr, cc = sample_segment(
        flow_status.shape[0],
        flow_status.shape[1],
        src_row,
        src_col,
        dst_row,
        dst_col,
        radius_cells,
    )
    if len(rr) == 0:
        return {
            "segment_sample_cells": 0,
            "segment_water_cells": 0,
            "segment_perennial_cells": 0,
            "segment_water_ratio": np.nan,
            "segment_dominant_component_id": 0,
            "segment_component_ids": "",
        }

    status_values = flow_status[rr, cc]
    water = (status_values == 1) | (status_values == 2)
    component_values = component_labels[rr[water], cc[water]]
    component_values = component_values[component_values > 0]
    component_ids = np.unique(component_values)

    dominant_component_id = 0
    if len(component_values):
        values, counts = np.unique(component_values, return_counts=True)
        dominant_component_id = int(values[np.argmax(counts)])

    return {
        "segment_sample_cells": int(len(rr)),
        "segment_water_cells": int(np.sum(water)),
        "segment_perennial_cells": int(np.sum(status_values == 2)),
        "segment_water_ratio": float(np.sum(water) / len(rr)),
        "segment_dominant_component_id": dominant_component_id,
        "segment_component_ids": ";".join(str(int(v)) for v in component_ids[:20]),
    }


def confidence_label(nearest_distance_km, segment_water_ratio):
    if nearest_distance_km <= 2.0 and segment_water_ratio >= 0.20:
        return "high"
    if nearest_distance_km <= 5.0 or segment_water_ratio >= 0.10:
        return "medium"
    return "low"


def match_cama_to_flow_status(
    flow_status_path,
    cama_parameters_path,
    out_dir,
    min_upstream_area_km2,
    segment_radius_cells,
    max_catchments,
    write_geojson,
):
    out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(flow_status_path) as src:
        if src.crs is None or src.crs.to_string() != "EPSG:4326":
            raise ValueError("Flow-status raster must be in EPSG:4326 to match CaMa longitude/latitude directly.")
        flow_status = src.read(1)
        transform = src.transform
        bounds = src.bounds

    print("Labeling connected water components and nearest water cells")
    water_mask, component_labels, nearest_distance_cells, nearest_indices = label_flow_status(flow_status)

    cama = load_cama_parameters(cama_parameters_path, bounds, min_upstream_area_km2=min_upstream_area_km2)
    if max_catchments is not None:
        cama = cama.head(max_catchments).copy()
    print(f"CaMa catchments inside raster/filter: {len(cama)}")

    id_to_row = {int(cid): row for row, cid in enumerate(cama["catchment_id"].to_numpy())}
    src_rows, src_cols = rowcol_arrays(transform, cama["longitude"].to_numpy(), cama["latitude"].to_numpy())

    valid_cell = (
        (src_rows >= 0)
        & (src_rows < flow_status.shape[0])
        & (src_cols >= 0)
        & (src_cols < flow_status.shape[1])
    )

    nearest_rows = nearest_indices[0, src_rows.clip(0, flow_status.shape[0] - 1), src_cols.clip(0, flow_status.shape[1] - 1)]
    nearest_cols = nearest_indices[1, src_rows.clip(0, flow_status.shape[0] - 1), src_cols.clip(0, flow_status.shape[1] - 1)]
    nearest_lon, nearest_lat = pixel_centers(transform, nearest_rows, nearest_cols)
    nearest_distance_km = haversine_km(
        cama["longitude"].to_numpy(),
        cama["latitude"].to_numpy(),
        nearest_lon,
        nearest_lat,
    )

    point_status = np.full(len(cama), NODATA, dtype=np.uint8)
    point_component_id = np.zeros(len(cama), dtype=np.int32)
    point_status[valid_cell] = flow_status[src_rows[valid_cell], src_cols[valid_cell]]
    point_component_id[valid_cell] = component_labels[src_rows[valid_cell], src_cols[valid_cell]]

    segment_rows = []
    for i, item in cama.iterrows():
        downstream_index = id_to_row.get(int(item["downstream_id"]))
        if downstream_index is None:
            segment_rows.append(
                {
                    "downstream_in_raster": False,
                    "segment_sample_cells": 0,
                    "segment_water_cells": 0,
                    "segment_perennial_cells": 0,
                    "segment_water_ratio": np.nan,
                    "segment_dominant_component_id": 0,
                    "segment_component_ids": "",
                }
            )
            continue

        summary = summarize_segment(
            flow_status,
            component_labels,
            int(src_rows[i]),
            int(src_cols[i]),
            int(src_rows[downstream_index]),
            int(src_cols[downstream_index]),
            segment_radius_cells,
        )
        summary["downstream_in_raster"] = True
        segment_rows.append(summary)

        if (i + 1) % 10000 == 0:
            print(f"Matched {i + 1}/{len(cama)} catchments")

    segment_frame = pd.DataFrame(segment_rows)
    result = cama.join(segment_frame)
    result["flow_status_row"] = src_rows
    result["flow_status_col"] = src_cols
    result["point_flow_status"] = point_status
    result["point_component_id"] = point_component_id
    result["nearest_water_row"] = nearest_rows
    result["nearest_water_col"] = nearest_cols
    result["nearest_water_lon"] = nearest_lon
    result["nearest_water_lat"] = nearest_lat
    result["nearest_water_component_id"] = component_labels[nearest_rows, nearest_cols]
    result["nearest_water_status"] = flow_status[nearest_rows, nearest_cols]
    result["nearest_water_distance_km"] = nearest_distance_km
    result["match_confidence"] = [
        confidence_label(distance, ratio if np.isfinite(ratio) else 0.0)
        for distance, ratio in zip(result["nearest_water_distance_km"], result["segment_water_ratio"])
    ]

    suffix_parts = ["all" if min_upstream_area_km2 is None else f"uparea_{min_upstream_area_km2:g}km2"]
    if max_catchments is not None:
        suffix_parts.append(f"first_{max_catchments}")
    suffix = "_".join(suffix_parts)
    csv_path = out_dir / f"cama_flow_status_match_{suffix}.csv"
    json_path = out_dir / f"cama_flow_status_match_{suffix}_summary.json"

    result.to_csv(csv_path, index=False, encoding="utf-8-sig")
    summary = {
        "flow_status": str(flow_status_path),
        "cama_parameters": str(cama_parameters_path),
        "min_upstream_area_km2": min_upstream_area_km2,
        "segment_radius_cells": segment_radius_cells,
        "catchments": int(len(result)),
        "water_components": int(component_labels.max()),
        "confidence_counts": {str(k): int(v) for k, v in result["match_confidence"].value_counts().to_dict().items()},
        "point_status_counts": {str(k): int(v) for k, v in result["point_flow_status"].value_counts().to_dict().items()},
    }
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    geojson_path = None
    if write_geojson:
        geojson_path = out_dir / f"cama_flow_status_match_{suffix}.geojson"
        features = []
        for _, row in result.iterrows():
            props = row.drop(labels=["longitude", "latitude"]).to_dict()
            for key, value in list(props.items()):
                if pd.isna(value):
                    props[key] = None
                elif isinstance(value, np.generic):
                    props[key] = value.item()
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(row["longitude"]), float(row["latitude"])]},
                    "properties": props,
                }
            )
        geojson_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"Saved CSV: {csv_path}")
    print(f"Saved summary: {json_path}")
    if geojson_path is not None:
        print(f"Saved GeoJSON: {geojson_path}")


def main():
    parser = argparse.ArgumentParser(description="Match CaMa-Flood units to the aggregated 1 km flow-status raster.")
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--cama-parameters", type=Path, default=DEFAULT_CAMA_PARAMETERS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-upstream-area-km2", type=float, default=1000.0)
    parser.add_argument("--segment-radius-cells", type=int, default=2)
    parser.add_argument("--max-catchments", type=int, default=None)
    parser.add_argument("--write-geojson", action="store_true")
    args = parser.parse_args()

    match_cama_to_flow_status(
        flow_status_path=args.flow_status,
        cama_parameters_path=args.cama_parameters,
        out_dir=args.out_dir,
        min_upstream_area_km2=args.min_upstream_area_km2,
        segment_radius_cells=args.segment_radius_cells,
        max_catchments=args.max_catchments,
        write_geojson=args.write_geojson,
    )


if __name__ == "__main__":
    main()
