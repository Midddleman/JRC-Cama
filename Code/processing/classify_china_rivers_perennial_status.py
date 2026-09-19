"""Classify HydroRIVERS segments using aggregated JRC flow-status cells.

The default segment rule uses perennial connectivity between the river start
and end neighborhoods. An optional stricter rule additionally requires the
perennial-cell ratio to meet a threshold.
"""

import argparse
import json
import sqlite3
from pathlib import Path

import fiona
import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from scipy.ndimage import label
from shapely.geometry import box
from PIL import Image


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
NODATA = 255


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
DEFAULT_FLOW_STATUS_PNG = (
    PROJECT_ROOT
    / "Output"
    / "ChinaFlowStatusMosaic"
    / RUN_LABEL
    / f"china_flow_status_factor33_{RUN_LABEL}.png"
)
DEFAULT_HYDRORIVERS = (
    PROJECT_ROOT
    / "Data"
    / "Google Earth Engine"
    / "HydroRIVERS_v10_as.gdb"
    / "HydroRIVERS_v10_as.gdb"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "ChinaRiverPerennialStatus" / RUN_LABEL


def load_hydrorivers(gdb_path, layer=None):
    layers = fiona.listlayers(gdb_path)
    selected_layer = layers[0] if layer is None else layer
    rivers = gpd.read_file(gdb_path, layer=selected_layer)
    return rivers, selected_layer


def get_main_linestring(geom):
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type == "LineString":
        return geom
    if geom.geom_type == "MultiLineString":
        lines = list(geom.geoms)
        return max(lines, key=lambda line: line.length) if lines else None
    return None


def endpoint_neighborhood_mask(point_xy, shape, transform, radius_cells):
    height, width = shape
    x, y = point_xy

    try:
        r, c = rasterio.transform.rowcol(transform, x, y)
    except Exception:
        return np.zeros(shape, dtype=bool)

    mask = np.zeros(shape, dtype=bool)
    r0 = max(0, r - radius_cells)
    r1 = min(height, r + radius_cells + 1)
    c0 = max(0, c - radius_cells)
    c1 = min(width, c + radius_cells + 1)
    mask[r0:r1, c0:c1] = True
    return mask


def has_perennial_connection_from_start_to_end(
    geom,
    flow_status_window,
    buffer_mask,
    window_transform,
    endpoint_radius_cells,
    min_component_cells=2,
):
    line = get_main_linestring(geom)
    if line is None:
        return False

    coords = list(line.coords)
    if len(coords) < 2:
        return False

    perennial_mask = (flow_status_window == 2) & buffer_mask
    if perennial_mask.sum() < min_component_cells:
        return False

    labeled, num_features = label(perennial_mask, structure=np.ones((3, 3), dtype=int))
    if num_features == 0:
        return False

    start_mask = endpoint_neighborhood_mask(coords[0], flow_status_window.shape, window_transform, endpoint_radius_cells)
    end_mask = endpoint_neighborhood_mask(coords[-1], flow_status_window.shape, window_transform, endpoint_radius_cells)

    for component_id in range(1, num_features + 1):
        component = labeled == component_id
        if component.sum() < min_component_cells:
            continue
        if np.any(component & start_mask) and np.any(component & end_mask):
            return True

    return False


def prepare_rivers(rivers, raster_bounds, discharge_threshold_cms):
    if rivers.crs is None:
        raise ValueError("HydroRIVERS data has no CRS.")

    rivers_lonlat = rivers.to_crs("EPSG:4326") if rivers.crs.to_string() != "EPSG:4326" else rivers.copy()
    if "DIS_AV_CMS" not in rivers_lonlat.columns:
        raise KeyError("HydroRIVERS input does not contain DIS_AV_CMS.")

    large_rivers = rivers_lonlat[rivers_lonlat["DIS_AV_CMS"] > discharge_threshold_cms].copy()
    region_geometry = box(*raster_bounds)
    region = gpd.GeoDataFrame(geometry=[region_geometry], crs="EPSG:4326")

    # Select by the raster extent without clipping the original river geometry.
    return large_rivers[large_rivers.intersects(region_geometry)].copy(), region


def classify_rivers(
    rivers_region,
    flow_status_path,
    buffer_m,
    endpoint_radius_cells,
    perennial_ratio_threshold,
    require_perennial_ratio,
    metric_crs,
    min_component_cells,
):
    rivers_classified = rivers_region.copy().reset_index(drop=True)
    if len(rivers_classified) == 0:
        return rivers_classified.assign(
            intermittent_count=[],
            perennial_count=[],
            water_count=[],
            perennial_ratio=[],
            connected_perennial=[],
            ratio_rule_passed=[],
            segment_status=[],
            segment_label=[],
        )

    buffers_lonlat = gpd.GeoSeries(
        rivers_classified.to_crs(metric_crs).geometry.buffer(buffer_m),
        crs=metric_crs,
    ).to_crs("EPSG:4326")

    rows = []
    with rasterio.open(flow_status_path) as src:
        raster_box = box(*src.bounds)
        for index, (geom, buffer_geom) in enumerate(zip(rivers_classified.geometry, buffers_lonlat), start=1):
            clipped_buffer = buffer_geom.intersection(raster_box)
            if clipped_buffer.is_empty:
                rows.append(empty_result("Non-perennial_outside_raster"))
                continue

            window = from_bounds(*clipped_buffer.bounds, transform=src.transform)
            window = window.round_offsets().round_lengths()
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if window.width <= 0 or window.height <= 0:
                rows.append(empty_result("Non-perennial_outside_raster"))
                continue

            flow_status = src.read(1, window=window)
            window_transform = src.window_transform(window)
            buffer_mask = geometry_mask(
                [clipped_buffer],
                out_shape=flow_status.shape,
                transform=window_transform,
                invert=True,
                all_touched=True,
            )

            intermittent_count = int(np.sum((flow_status == 1) & buffer_mask))
            perennial_count = int(np.sum((flow_status == 2) & buffer_mask))
            water_count = intermittent_count + perennial_count

            if water_count == 0:
                rows.append(
                    {
                        "intermittent_count": intermittent_count,
                        "perennial_count": perennial_count,
                        "water_count": water_count,
                        "perennial_ratio": np.nan,
                        "connected_perennial": False,
                        "ratio_rule_passed": False,
                        "segment_status": 1,
                        "segment_label": "Non-perennial_no_water",
                    }
                )
                continue

            perennial_ratio = perennial_count / water_count
            connected_perennial = has_perennial_connection_from_start_to_end(
                geom=geom,
                flow_status_window=flow_status,
                buffer_mask=buffer_mask,
                window_transform=window_transform,
                endpoint_radius_cells=endpoint_radius_cells,
                min_component_cells=min_component_cells,
            )
            ratio_rule_passed = perennial_ratio >= perennial_ratio_threshold

            is_perennial = connected_perennial and (
                ratio_rule_passed if require_perennial_ratio else True
            )
            if is_perennial:
                segment_status = 2
                segment_label = (
                    "Perennial_connected_and_ratio"
                    if require_perennial_ratio
                    else "Perennial_connected"
                )
            elif require_perennial_ratio and connected_perennial:
                segment_status = 1
                segment_label = "Non-perennial_ratio_below_threshold"
            else:
                segment_status = 1
                segment_label = "Non-perennial_no_connected_path"

            rows.append(
                {
                    "intermittent_count": intermittent_count,
                    "perennial_count": perennial_count,
                    "water_count": water_count,
                    "perennial_ratio": perennial_ratio,
                    "connected_perennial": connected_perennial,
                    "ratio_rule_passed": ratio_rule_passed,
                    "segment_status": segment_status,
                    "segment_label": segment_label,
                }
            )

            if index % 500 == 0:
                print(f"Classified {index}/{len(rivers_classified)} river segments")

    attrs = pd.DataFrame(rows)
    return rivers_classified.join(attrs)


def empty_result(label_text):
    return {
        "intermittent_count": 0,
        "perennial_count": 0,
        "water_count": 0,
        "perennial_ratio": np.nan,
        "connected_perennial": False,
        "ratio_rule_passed": False,
        "segment_status": 1,
        "segment_label": label_text,
    }


def summarize(classified, settings):
    counts = classified["segment_label"].value_counts(dropna=False).to_dict()
    total = int(len(classified))
    perennial = int(np.sum(classified["segment_status"] == 2))
    non_perennial = int(np.sum(classified["segment_status"] == 1))
    no_water = int(np.sum(classified["water_count"] == 0))
    return {
        "settings": settings,
        "total_segments": total,
        "perennial_segments": perennial,
        "non_perennial_segments": non_perennial,
        "no_water_segments": no_water,
        "perennial_segment_ratio": float(perennial / total) if total else 0.0,
        "label_counts": {str(key): int(value) for key, value in counts.items()},
    }


def _sqlite_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, bool):
        return int(value)
    return value


def write_sqlite_database(classified, settings, output_path):
    columns = [
        "HYRIV_ID",
        "NEXT_DOWN",
        "MAIN_RIV",
        "LENGTH_KM",
        "DIST_DN_KM",
        "DIST_UP_KM",
        "CATCH_SKM",
        "UPLAND_SKM",
        "ENDORHEIC",
        "DIS_AV_CMS",
        "ORD_STRA",
        "ORD_CLAS",
        "ORD_FLOW",
        "HYBAS_L12",
        "Shape_Length",
        "intermittent_count",
        "perennial_count",
        "water_count",
        "perennial_ratio",
        "connected_perennial",
        "ratio_rule_passed",
        "segment_status",
        "segment_label",
    ]
    missing = [column for column in columns if column not in classified.columns]
    if missing:
        raise KeyError(f"Cannot build SQLite database; missing columns: {missing}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.unlink(missing_ok=True)

    connection = sqlite3.connect(temporary_path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE river_segments (
                hyriv_id INTEGER PRIMARY KEY,
                next_down INTEGER,
                main_riv INTEGER,
                length_km REAL,
                dist_dn_km REAL,
                dist_up_km REAL,
                catch_skm REAL,
                upland_skm REAL,
                endorheic INTEGER,
                dis_av_cms REAL NOT NULL,
                ord_stra INTEGER,
                ord_clas INTEGER,
                ord_flow INTEGER,
                hybas_l12 INTEGER,
                shape_length REAL,
                intermittent_count INTEGER NOT NULL,
                perennial_count INTEGER NOT NULL,
                water_count INTEGER NOT NULL,
                perennial_ratio REAL,
                connected_perennial INTEGER NOT NULL CHECK (connected_perennial IN (0, 1)),
                ratio_rule_passed INTEGER NOT NULL CHECK (ratio_rule_passed IN (0, 1)),
                segment_status INTEGER NOT NULL CHECK (segment_status IN (1, 2)),
                segment_label TEXT NOT NULL
            );
            CREATE TABLE analysis_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE INDEX idx_river_segments_status ON river_segments(segment_status);
            CREATE INDEX idx_river_segments_discharge ON river_segments(dis_av_cms);
            CREATE INDEX idx_river_segments_main_riv ON river_segments(main_riv);
            """
        )
        placeholders = ", ".join("?" for _ in columns)
        rows = (
            tuple(_sqlite_value(value) for value in row)
            for row in classified[columns].itertuples(index=False, name=None)
        )
        connection.executemany(
            f"INSERT INTO river_segments VALUES ({placeholders})",
            rows,
        )
        metadata = {
            "schema_version": "1",
            "status_codes": json.dumps(
                {"1": "non-perennial", "2": "perennial"}, ensure_ascii=False
            ),
            **{key: json.dumps(value, ensure_ascii=False) for key, value in settings.items()},
        }
        connection.executemany(
            "INSERT INTO analysis_metadata(key, value) VALUES (?, ?)",
            metadata.items(),
        )
        connection.commit()

        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        row_count = connection.execute("SELECT COUNT(*) FROM river_segments").fetchone()[0]
        if integrity != "ok" or row_count != len(classified):
            raise RuntimeError(
                f"SQLite verification failed: integrity={integrity}, rows={row_count}"
            )
    finally:
        connection.close()

    output_path.unlink(missing_ok=True)
    temporary_path.replace(output_path)


def plot_classified_rivers(flow_status_path, flow_status_png_path, region_gdf, rivers_classified, output_path, settings):
    with rasterio.open(flow_status_path) as src:
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    fig, ax = plt.subplots(figsize=(12, 9), dpi=180)
    background = Image.open(flow_status_png_path).convert("RGBA")
    ax.imshow(background, extent=extent, origin="upper")

    region_gdf.boundary.plot(ax=ax, color="black", linewidth=1.0)
    rivers_classified[rivers_classified["segment_status"] == 1].plot(ax=ax, color="red", linewidth=0.7, alpha=0.8)
    rivers_classified[rivers_classified["segment_status"] == 2].plot(ax=ax, color="green", linewidth=0.8, alpha=0.85)

    ax.legend(
        handles=[
            Line2D([0], [0], color="red", linewidth=1.0, label="Non-perennial river segment"),
            Line2D([0], [0], color="green", linewidth=1.0, label="Perennial river segment"),
        ],
        loc="lower left",
        title="River segment status",
    )
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_title(
        "HydroRIVERS segment perennial status\n"
        f"DIS_AV_CMS > {settings['discharge_threshold_cms']}, buffer = {settings['buffer_m'] / 1000:g} km"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Classify HydroRIVERS segments using perennial connectivity on an aggregated JRC flow-status map."
    )
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--flow-status-png", type=Path, default=DEFAULT_FLOW_STATUS_PNG)
    parser.add_argument("--hydrorivers", type=Path, default=DEFAULT_HYDRORIVERS)
    parser.add_argument("--layer", default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--discharge-threshold-cms", type=float, default=50.0)
    parser.add_argument("--buffer-m", type=float, default=5000.0)
    parser.add_argument("--endpoint-radius-cells", type=int, default=3)
    parser.add_argument("--perennial-ratio-threshold", type=float, default=0.5)
    parser.add_argument(
        "--require-perennial-ratio",
        action="store_true",
        help="Require both perennial connectivity and the perennial-ratio threshold.",
    )
    parser.add_argument("--metric-crs", default="EPSG:3857")
    parser.add_argument("--min-component-cells", type=int, default=2)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(args.flow_status) as src:
        raster_bounds = tuple(src.bounds)

    print(f"Flow-status raster: {args.flow_status}")
    print(f"HydroRIVERS source: {args.hydrorivers}")
    print(f"Discharge filter: DIS_AV_CMS > {args.discharge_threshold_cms} cms")

    rivers, layer = load_hydrorivers(args.hydrorivers, args.layer)
    rivers_region, region_gdf = prepare_rivers(
        rivers,
        raster_bounds=raster_bounds,
        discharge_threshold_cms=args.discharge_threshold_cms,
    )
    print(f"HydroRIVERS layer: {layer}")
    print(f"Selected river segments: {len(rivers_region)}")

    classified = classify_rivers(
        rivers_region=rivers_region,
        flow_status_path=args.flow_status,
        buffer_m=args.buffer_m,
        endpoint_radius_cells=args.endpoint_radius_cells,
        perennial_ratio_threshold=args.perennial_ratio_threshold,
        require_perennial_ratio=args.require_perennial_ratio,
        metric_crs=args.metric_crs,
        min_component_cells=args.min_component_cells,
    )

    settings = {
        "flow_status": str(args.flow_status),
        "flow_status_png": str(args.flow_status_png),
        "hydrorivers": str(args.hydrorivers),
        "hydrorivers_layer": layer,
        "discharge_threshold_cms": args.discharge_threshold_cms,
        "buffer_m": args.buffer_m,
        "endpoint_radius_cells": args.endpoint_radius_cells,
        "discharge_filter_operator": ">",
        "perennial_ratio_threshold": args.perennial_ratio_threshold,
        "require_perennial_ratio": args.require_perennial_ratio,
        "metric_crs": args.metric_crs,
        "min_component_cells": args.min_component_cells,
        "raster_bounds": list(raster_bounds),
        "selected_segment_count": int(len(rivers_region)),
    }
    summary = summarize(classified, settings)

    rule_label = "connectivity_and_ratio" if args.require_perennial_ratio else "connectivity_only"
    output_stem = f"china_river_perennial_status_discharge_gt_{args.discharge_threshold_cms:g}_{rule_label}"
    output_stem += f"_endpoint_{2 * args.endpoint_radius_cells + 1}x{2 * args.endpoint_radius_cells + 1}"
    geojson_path = args.out_dir / f"{output_stem}.geojson"
    csv_path = args.out_dir / f"{output_stem}.csv"
    json_path = args.out_dir / f"{output_stem}_summary.json"
    png_path = args.out_dir / f"{output_stem}.png"
    sqlite_path = args.out_dir / f"{output_stem}.sqlite"

    geojson_path.write_text(classified.to_json(drop_id=True), encoding="utf-8")
    classified.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_sqlite_database(classified, settings, sqlite_path)
    plot_classified_rivers(args.flow_status, args.flow_status_png, region_gdf, classified, png_path, settings)

    print("Segment labels:")
    print(classified["segment_label"].value_counts(dropna=False))
    print(f"Saved GeoJSON: {geojson_path}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved summary: {json_path}")
    print(f"Saved SQLite database: {sqlite_path}")
    print(f"Saved plot: {png_path}")


if __name__ == "__main__":
    main()
