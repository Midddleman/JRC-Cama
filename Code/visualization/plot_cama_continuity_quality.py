"""Plot CaMa downstream-link continuity quality over the flow-status map."""

import argparse
from pathlib import Path

import matplotlib
import pandas as pd
import rasterio
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from PIL import Image


matplotlib.use("Agg")
import matplotlib.pyplot as plt


RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"


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
DEFAULT_EDGE_CSV = (
    PROJECT_ROOT
    / "Output"
    / "CamaFlowStatusMatch"
    / RUN_LABEL
    / "cama_flow_status_uparea_10000km2_edge_continuity.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "CamaFlowStatusMatch" / RUN_LABEL


def build_segments(edges):
    return [
        [(float(row.src_lon), float(row.src_lat)), (float(row.dst_lon), float(row.dst_lat))]
        for row in edges.itertuples(index=False)
    ]


def plot_quality(flow_status_path, flow_status_png_path, edge_csv, output_path, native_resolution, dpi, basin_id):
    edges = pd.read_csv(edge_csv)
    if basin_id is not None:
        edges = edges.loc[edges["basin_id"] == basin_id].copy()
        if edges.empty:
            raise ValueError(f"No edges found for basin_id={basin_id}")

    with rasterio.open(flow_status_path) as src:
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        raster_width = src.width
        raster_height = src.height

    background = Image.open(flow_status_png_path).convert("RGBA")
    figsize = (raster_width / dpi, raster_height / dpi) if native_resolution else (15, 11)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.imshow(background, extent=extent, origin="upper")

    styles = {
        "good": {"color": "#00843d", "linewidth": 3.0, "alpha": 1.0, "label": "good continuity"},
        "uncertain": {"color": "#ffb000", "linewidth": 4.0, "alpha": 1.0, "label": "uncertain continuity"},
        "poor": {"color": "#d7191c", "linewidth": 5.2, "alpha": 1.0, "label": "poor continuity"},
    }
    for quality in ["good", "uncertain", "poor"]:
        subset = edges.loc[edges["edge_quality"] == quality]
        if subset.empty:
            continue
        segments = build_segments(subset)
        ax.add_collection(
            LineCollection(
                segments,
                colors="#ffffff",
                linewidths=styles[quality]["linewidth"] + 1.8,
                alpha=0.82,
                zorder={"good": 2, "uncertain": 3, "poor": 4}[quality],
            )
        )
        ax.add_collection(
            LineCollection(
                segments,
                colors=styles[quality]["color"],
                linewidths=styles[quality]["linewidth"],
                alpha=styles[quality]["alpha"],
                zorder={"good": 5, "uncertain": 6, "poor": 7}[quality],
            )
        )

    if basin_id is not None:
        pad = 1.5
        ax.set_xlim(edges[["src_lon", "dst_lon"]].min().min() - pad, edges[["src_lon", "dst_lon"]].max().max() + pad)
        ax.set_ylim(edges[["src_lat", "dst_lat"]].min().min() - pad, edges[["src_lat", "dst_lat"]].max().max() + pad)
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

    title_filter = f"basin_id = {basin_id}" if basin_id is not None else "all basins"
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"CaMa downstream-link continuity on the 1 km flow-status map\n{title_filter}, edges = {len(edges):,}")
    handles = [
        Line2D([0], [0], color=style["color"], linewidth=5.0, label=style["label"])
        for style in styles.values()
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=True)

    if native_resolution and basin_id is None:
        fig.subplots_adjust(left=0.05, right=0.995, bottom=0.06, top=0.94)
    else:
        fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot CaMa downstream-link continuity quality.")
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--flow-status-png", type=Path, default=DEFAULT_FLOW_STATUS_PNG)
    parser.add_argument("--edge-csv", type=Path, default=DEFAULT_EDGE_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--basin-id", type=int, default=None)
    parser.add_argument("--native-resolution", action="store_true")
    parser.add_argument("--dpi", type=int, default=100)
    args = parser.parse_args()

    suffix = "uparea_10000km2_edge_quality"
    if args.basin_id is not None:
        suffix += f"_basin_{args.basin_id}"
    if args.native_resolution and args.basin_id is None:
        suffix += "_native"
    output_path = args.out_dir / f"cama_flow_status_{suffix}.png"

    plot_quality(
        args.flow_status,
        args.flow_status_png,
        args.edge_csv,
        output_path,
        native_resolution=args.native_resolution,
        dpi=args.dpi,
        basin_id=args.basin_id,
    )
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    main()
