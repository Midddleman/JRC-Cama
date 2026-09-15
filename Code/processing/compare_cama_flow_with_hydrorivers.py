"""Compare matched CaMa-Flood discharge with HydroRIVERS segments.

This script uses the CaMa downstream-edge continuity table, computes annual or
multi-year mean CaMa outflow for the selected catchments, matches each CaMa
edge to a nearby HydroRIVERS segment, and summarizes discharge agreement by
HYRIV_ID.
"""

import argparse
import json
from pathlib import Path

import fiona
import geopandas as gpd
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from shapely.geometry import LineString


RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
DEFAULT_EDGE_CSV = (
    PROJECT_ROOT
    / "Output"
    / "CamaFlowStatusMatch"
    / RUN_LABEL
    / "cama_flow_status_uparea_10000km2_edge_continuity.csv"
)
DEFAULT_FLOW_STATUS = (
    PROJECT_ROOT
    / "Output"
    / "ChinaFlowStatusMosaic"
    / RUN_LABEL
    / f"china_flow_status_factor33_{RUN_LABEL}.tif"
)
DEFAULT_CAMA_FLOW_DIR = PROJECT_ROOT / "Data" / "Cama-Flood output" / "glb_06min_VICBC_daily"
DEFAULT_CAMA_PARAMETERS = PROJECT_ROOT / "Data" / "Cama-Flood output" / "parameters_glb06.nc"
DEFAULT_HYDRORIVERS = (
    PROJECT_ROOT
    / "Data"
    / "Google Earth Engine"
    / "HydroRIVERS_v10_as.gdb"
    / "HydroRIVERS_v10_as.gdb"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "CamaHydroRIVERSFlowCheck" / RUN_LABEL


def load_hydrorivers(path, bbox, min_discharge_cms, layer=None):
    selected_layer = fiona.listlayers(path)[0] if layer is None else layer
    rivers = gpd.read_file(
        path,
        layer=selected_layer,
        bbox=bbox,
        columns=[
            "HYRIV_ID",
            "NEXT_DOWN",
            "MAIN_RIV",
            "LENGTH_KM",
            "UPLAND_SKM",
            "DIS_AV_CMS",
            "ORD_FLOW",
            "geometry",
        ],
    )
    rivers = rivers.to_crs("EPSG:4326") if rivers.crs is not None and rivers.crs.to_string() != "EPSG:4326" else rivers
    rivers = rivers.loc[rivers["DIS_AV_CMS"] >= min_discharge_cms].copy()
    rivers = rivers.loc[~rivers.geometry.is_empty & rivers.geometry.notna()].copy()
    return rivers.reset_index(drop=True), selected_layer


def cama_saved_point_positions(parameters_path, catchment_ids):
    catchment_ids = np.asarray(sorted(set(int(v) for v in catchment_ids)), dtype=np.int64)
    with xr.open_dataset(parameters_path) as ds:
        parameter_ids = ds["catchment_id"].values.astype(np.int64)
    positions = pd.Series(np.arange(len(parameter_ids), dtype=np.int64), index=parameter_ids).reindex(catchment_ids)
    keep = ~positions.isna()
    return catchment_ids[keep.to_numpy()], positions.loc[keep].to_numpy(dtype=np.int64)


def compute_cama_mean_outflow(flow_dir, parameters_path, catchment_ids, start_year, end_year, chunk_size):
    catchment_ids = np.asarray(sorted(set(int(v) for v in catchment_ids)), dtype=np.int64)
    catchment_ids, positions = cama_saved_point_positions(parameters_path, catchment_ids)
    sums = np.zeros(len(catchment_ids), dtype=np.float64)
    counts = np.zeros(len(catchment_ids), dtype=np.float64)
    order = np.argsort(positions)
    positions = positions[order]
    catchment_ids = catchment_ids[order]

    used_years = []
    for year in range(start_year, end_year + 1):
        path = flow_dir / f"river_outflow_mean_rank0_{year}.nc"
        if not path.exists():
            print(f"Missing CaMa flow file, skipping: {path}")
            continue

        with Dataset(path) as ds:
            flow = ds.variables["river_outflow_mean"]
            for start in range(0, len(positions), chunk_size):
                stop = min(start + chunk_size, len(positions))
                batch_positions = positions[start:stop]
                values = np.asarray(flow[:, batch_positions], dtype=np.float64)
                year_mean = np.nanmean(values, axis=0)
                valid = np.isfinite(year_mean)
                output_indices = np.arange(start, stop, dtype=np.int64)[valid]
                sums[output_indices] += year_mean[valid]
                counts[output_indices] += 1.0
        used_years.append(year)
        print(f"Computed CaMa mean outflow for {year}")

    means = np.divide(sums, counts, out=np.full_like(sums, np.nan), where=counts > 0)
    return pd.DataFrame({"catchment_id": catchment_ids, "cama_mean_outflow_cms": means, "cama_flow_year_count": counts.astype(int)}), used_years


def build_edge_geometries(edges):
    geometries = [
        LineString([(float(row.src_lon), float(row.src_lat)), (float(row.dst_lon), float(row.dst_lat))])
        for row in edges.itertuples(index=False)
    ]
    return gpd.GeoDataFrame(edges.copy(), geometry=geometries, crs="EPSG:4326")


def match_edges_to_hydrorivers(edges_gdf, rivers_gdf, max_distance_m):
    edges_metric = edges_gdf.to_crs("EPSG:3857")
    # A line-to-line nearest join can be slow for this data volume. The CaMa
    # edge midpoint is enough for assigning the modeled link to a HydroRIVERS
    # segment, while the continuity table still preserves the original edge.
    edges_metric = edges_metric.copy()
    edges_metric["edge_geometry"] = edges_metric.geometry
    edges_metric.geometry = edges_metric.geometry.interpolate(0.5, normalized=True)
    rivers_metric = rivers_gdf.to_crs("EPSG:3857")
    matched = gpd.sjoin_nearest(
        edges_metric,
        rivers_metric[
            [
                "HYRIV_ID",
                "NEXT_DOWN",
                "MAIN_RIV",
                "LENGTH_KM",
                "UPLAND_SKM",
                "DIS_AV_CMS",
                "ORD_FLOW",
                "geometry",
            ]
        ],
        how="left",
        max_distance=max_distance_m,
        distance_col="hydrorivers_distance_m",
    )
    matched = matched.drop(columns=["index_right"], errors="ignore")
    matched.geometry = matched["edge_geometry"]
    matched = matched.drop(columns=["edge_geometry"], errors="ignore")
    return matched.to_crs("EPSG:4326")


def add_flow_columns(edges, node_flow):
    flow_by_id = node_flow.set_index("catchment_id")["cama_mean_outflow_cms"]
    edges = edges.copy()
    edges["src_cama_outflow_cms"] = edges["catchment_id"].map(flow_by_id)
    edges["dst_cama_outflow_cms"] = edges["downstream_id"].map(flow_by_id)
    edges["edge_cama_outflow_mean_cms"] = edges[["src_cama_outflow_cms", "dst_cama_outflow_cms"]].mean(axis=1)
    edges["edge_cama_outflow_max_cms"] = edges[["src_cama_outflow_cms", "dst_cama_outflow_cms"]].max(axis=1)
    edges["cama_downstream_minus_source_cms"] = edges["dst_cama_outflow_cms"] - edges["src_cama_outflow_cms"]
    return edges


def summarize_hyriv(matched):
    table = matched.dropna(subset=["HYRIV_ID"]).copy()
    if table.empty:
        return pd.DataFrame()
    summary = table.groupby("HYRIV_ID").agg(
        cama_edge_count=("catchment_id", "count"),
        basin_ids=("basin_id", lambda s: ";".join(str(int(v)) for v in sorted(set(s))[:10])),
        hydrorivers_dis_av_cms=("DIS_AV_CMS", "first"),
        hydrorivers_upland_skm=("UPLAND_SKM", "first"),
        hydrorivers_main_riv=("MAIN_RIV", "first"),
        hydrorivers_ord_flow=("ORD_FLOW", "first"),
        mean_hydrorivers_distance_m=("hydrorivers_distance_m", "mean"),
        mean_cama_outflow_cms=("edge_cama_outflow_mean_cms", "mean"),
        median_cama_outflow_cms=("edge_cama_outflow_mean_cms", "median"),
        max_cama_outflow_cms=("edge_cama_outflow_max_cms", "max"),
        good_edge_ratio=("edge_quality", lambda s: float(np.mean(s == "good"))),
        mean_segment_water_ratio=("segment_water_ratio", "mean"),
    ).reset_index()
    summary["cama_to_hydrorivers_dis_ratio"] = summary["mean_cama_outflow_cms"] / summary["hydrorivers_dis_av_cms"]
    summary["abs_log10_discharge_ratio"] = np.abs(np.log10(summary["cama_to_hydrorivers_dis_ratio"]))
    return summary.sort_values(["cama_edge_count", "hydrorivers_dis_av_cms"], ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Compare CaMa-Flood outflow with matched HydroRIVERS segments.")
    parser.add_argument("--edge-csv", type=Path, default=DEFAULT_EDGE_CSV)
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--cama-flow-dir", type=Path, default=DEFAULT_CAMA_FLOW_DIR)
    parser.add_argument("--cama-parameters", type=Path, default=DEFAULT_CAMA_PARAMETERS)
    parser.add_argument("--hydrorivers", type=Path, default=DEFAULT_HYDRORIVERS)
    parser.add_argument("--hydrorivers-layer", default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--min-hydrorivers-discharge-cms", type=float, default=500.0)
    parser.add_argument("--max-hydrorivers-distance-m", type=float, default=15000.0)
    parser.add_argument("--only-good-edges", action="store_true")
    parser.add_argument("--flow-chunk-size", type=int, default=512)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    edges = pd.read_csv(args.edge_csv)
    if args.only_good_edges:
        edges = edges.loc[edges["edge_quality"] == "good"].copy()

    catchment_ids = pd.unique(pd.concat([edges["catchment_id"], edges["downstream_id"]], ignore_index=True))
    node_flow, used_years = compute_cama_mean_outflow(
        args.cama_flow_dir,
        args.cama_parameters,
        catchment_ids,
        args.start_year,
        args.end_year,
        args.flow_chunk_size,
    )
    edges = add_flow_columns(edges, node_flow)

    with rasterio.open(args.flow_status) as src:
        bbox = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
    rivers, layer = load_hydrorivers(
        args.hydrorivers,
        bbox=bbox,
        min_discharge_cms=args.min_hydrorivers_discharge_cms,
        layer=args.hydrorivers_layer,
    )
    print(f"HydroRIVERS layer: {layer}")
    print(f"HydroRIVERS selected segments: {len(rivers)}")

    edges_gdf = build_edge_geometries(edges)
    matched = match_edges_to_hydrorivers(edges_gdf, rivers, args.max_hydrorivers_distance_m)
    hyriv_summary = summarize_hyriv(matched)

    year_label = f"{args.start_year}" if args.start_year == args.end_year else f"{args.start_year}_{args.end_year}"
    quality_label = "good_edges" if args.only_good_edges else "all_edges"
    suffix = (
        f"uparea_10000km2_{quality_label}_cama_{year_label}_"
        f"hydro_dis_{args.min_hydrorivers_discharge_cms:g}_dist_{args.max_hydrorivers_distance_m:g}m"
    )
    edge_path = args.out_dir / f"cama_hydrorivers_edge_flow_compare_{suffix}.csv"
    hyriv_path = args.out_dir / f"cama_hydrorivers_segment_flow_summary_{suffix}.csv"
    node_path = args.out_dir / f"cama_node_outflow_{year_label}.csv"
    json_path = args.out_dir / f"cama_hydrorivers_flow_compare_{suffix}_summary.json"

    matched.drop(columns="geometry").to_csv(edge_path, index=False, encoding="utf-8-sig")
    hyriv_summary.to_csv(hyriv_path, index=False, encoding="utf-8-sig")
    node_flow.to_csv(node_path, index=False, encoding="utf-8-sig")

    valid = hyriv_summary.dropna(subset=["mean_cama_outflow_cms", "hydrorivers_dis_av_cms"])
    summary = {
        "used_years": used_years,
        "edge_count": int(len(edges)),
        "matched_edge_count": int(matched["HYRIV_ID"].notna().sum()),
        "matched_edge_ratio": float(matched["HYRIV_ID"].notna().mean()) if len(matched) else 0.0,
        "hydrorivers_segments_with_cama": int(len(hyriv_summary)),
        "hydrorivers_layer": layer,
        "min_hydrorivers_discharge_cms": args.min_hydrorivers_discharge_cms,
        "max_hydrorivers_distance_m": args.max_hydrorivers_distance_m,
        "only_good_edges": args.only_good_edges,
        "pearson_log10_discharge": float(
            np.corrcoef(
                np.log10(valid["mean_cama_outflow_cms"].clip(lower=1e-6)),
                np.log10(valid["hydrorivers_dis_av_cms"].clip(lower=1e-6)),
            )[0, 1]
        )
        if len(valid) >= 2
        else None,
        "median_cama_to_hydrorivers_dis_ratio": float(valid["cama_to_hydrorivers_dis_ratio"].median()) if len(valid) else None,
        "within_factor_2_ratio": float(np.mean(valid["abs_log10_discharge_ratio"] <= np.log10(2))) if len(valid) else None,
        "within_factor_5_ratio": float(np.mean(valid["abs_log10_discharge_ratio"] <= np.log10(5))) if len(valid) else None,
    }
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved edge comparison: {edge_path}")
    print(f"Saved HydroRIVERS segment summary: {hyriv_path}")
    print(f"Saved CaMa node flow: {node_path}")
    print(f"Saved summary: {json_path}")


if __name__ == "__main__":
    main()
