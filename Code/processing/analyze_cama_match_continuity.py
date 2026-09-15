"""Analyze whether CaMa-Flood matches form continuous river paths."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
DEFAULT_MATCH_CSV = (
    PROJECT_ROOT
    / "Output"
    / "CamaFlowStatusMatch"
    / RUN_LABEL
    / "cama_flow_status_match_uparea_10000km2.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "CamaFlowStatusMatch" / RUN_LABEL


def parse_component_ids(value):
    if pd.isna(value) or value == "":
        return set()
    return {int(item) for item in str(value).split(";") if item}


def edge_quality(row):
    src_distance = float(row["src_nearest_water_distance_km"])
    dst_distance = float(row["dst_nearest_water_distance_km"])
    segment_ratio = float(row["segment_water_ratio"]) if np.isfinite(row["segment_water_ratio"]) else 0.0

    distance_ok = src_distance <= 5.0 and dst_distance <= 5.0
    distance_strong = src_distance <= 2.0 and dst_distance <= 2.0
    segment_ok = segment_ratio >= 0.20
    segment_strong = segment_ratio >= 0.35
    component_ok = bool(row["same_nearest_component"] or row["src_or_dst_component_on_segment"])

    score = 0
    score += 2 if distance_strong else (1 if distance_ok else 0)
    score += 2 if segment_strong else (1 if segment_ok else 0)
    score += 1 if component_ok else 0

    if score >= 4:
        return "good"
    if score >= 2:
        return "uncertain"
    return "poor"


def build_edge_table(nodes):
    node_by_id = nodes.set_index("catchment_id", drop=False)
    rows = []

    for src in nodes.itertuples(index=False):
        downstream_id = int(src.downstream_id)
        catchment_id = int(src.catchment_id)
        if downstream_id == catchment_id or downstream_id not in node_by_id.index:
            continue

        dst = node_by_id.loc[downstream_id]
        segment_components = parse_component_ids(src.segment_component_ids)
        src_component = int(src.nearest_water_component_id)
        dst_component = int(dst.nearest_water_component_id)

        rows.append(
            {
                "catchment_id": catchment_id,
                "downstream_id": downstream_id,
                "basin_id": int(src.basin_id),
                "src_lon": float(src.longitude),
                "src_lat": float(src.latitude),
                "dst_lon": float(dst.longitude),
                "dst_lat": float(dst.latitude),
                "src_upstream_area_km2": float(src.upstream_area) / 1_000_000.0,
                "dst_upstream_area_km2": float(dst.upstream_area) / 1_000_000.0,
                "src_nearest_water_distance_km": float(src.nearest_water_distance_km),
                "dst_nearest_water_distance_km": float(dst.nearest_water_distance_km),
                "src_point_flow_status": int(src.point_flow_status),
                "dst_point_flow_status": int(dst.point_flow_status),
                "src_nearest_component_id": src_component,
                "dst_nearest_component_id": dst_component,
                "segment_water_ratio": float(src.segment_water_ratio) if pd.notna(src.segment_water_ratio) else np.nan,
                "segment_water_cells": int(src.segment_water_cells),
                "segment_perennial_cells": int(src.segment_perennial_cells),
                "segment_dominant_component_id": int(src.segment_dominant_component_id),
                "same_nearest_component": src_component == dst_component and src_component > 0,
                "src_or_dst_component_on_segment": (
                    src_component in segment_components
                    or dst_component in segment_components
                    or int(src.segment_dominant_component_id) in {src_component, dst_component}
                ),
            }
        )

    edges = pd.DataFrame(rows)
    if len(edges):
        edges["edge_quality"] = edges.apply(edge_quality, axis=1)
    return edges


def summarize_by_basin(edges):
    grouped = edges.groupby("basin_id", dropna=False)
    summary = grouped.agg(
        edge_count=("catchment_id", "count"),
        good_edges=("edge_quality", lambda s: int(np.sum(s == "good"))),
        uncertain_edges=("edge_quality", lambda s: int(np.sum(s == "uncertain"))),
        poor_edges=("edge_quality", lambda s: int(np.sum(s == "poor"))),
        mean_segment_water_ratio=("segment_water_ratio", "mean"),
        median_src_distance_km=("src_nearest_water_distance_km", "median"),
        median_dst_distance_km=("dst_nearest_water_distance_km", "median"),
        same_component_edges=("same_nearest_component", "sum"),
        component_on_segment_edges=("src_or_dst_component_on_segment", "sum"),
        max_upstream_area_km2=("dst_upstream_area_km2", "max"),
    ).reset_index()
    summary["good_edge_ratio"] = summary["good_edges"] / summary["edge_count"]
    summary["poor_edge_ratio"] = summary["poor_edges"] / summary["edge_count"]
    summary["same_component_ratio"] = summary["same_component_edges"] / summary["edge_count"]
    summary["component_on_segment_ratio"] = summary["component_on_segment_edges"] / summary["edge_count"]
    return summary.sort_values(["edge_count", "max_upstream_area_km2"], ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Check CaMa-to-flow-status continuity along downstream links.")
    parser.add_argument("--match-csv", type=Path, default=DEFAULT_MATCH_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    nodes = pd.read_csv(args.match_csv)
    edges = build_edge_table(nodes)
    basin_summary = summarize_by_basin(edges)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    edge_path = args.out_dir / "cama_flow_status_uparea_10000km2_edge_continuity.csv"
    basin_path = args.out_dir / "cama_flow_status_uparea_10000km2_basin_continuity.csv"
    json_path = args.out_dir / "cama_flow_status_uparea_10000km2_continuity_summary.json"

    edges.to_csv(edge_path, index=False, encoding="utf-8-sig")
    basin_summary.to_csv(basin_path, index=False, encoding="utf-8-sig")

    total_edges = len(edges)
    summary = {
        "match_csv": str(args.match_csv),
        "nodes": int(len(nodes)),
        "downstream_edges_inside_filter": int(total_edges),
        "edge_quality_counts": {str(k): int(v) for k, v in edges["edge_quality"].value_counts().to_dict().items()},
        "edge_quality_ratios": {
            str(k): float(v / total_edges) for k, v in edges["edge_quality"].value_counts().to_dict().items()
        }
        if total_edges
        else {},
        "median_src_nearest_water_distance_km": float(edges["src_nearest_water_distance_km"].median()),
        "median_dst_nearest_water_distance_km": float(edges["dst_nearest_water_distance_km"].median()),
        "mean_segment_water_ratio": float(edges["segment_water_ratio"].mean()),
        "same_nearest_component_edges": int(edges["same_nearest_component"].sum()),
        "same_nearest_component_ratio": float(edges["same_nearest_component"].mean()),
        "src_or_dst_component_on_segment_ratio": float(edges["src_or_dst_component_on_segment"].mean()),
        "basins_with_at_least_20_edges": int(np.sum(basin_summary["edge_count"] >= 20)),
    }
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved edge continuity: {edge_path}")
    print(f"Saved basin continuity: {basin_path}")
    print(f"Saved summary: {json_path}")


if __name__ == "__main__":
    main()
