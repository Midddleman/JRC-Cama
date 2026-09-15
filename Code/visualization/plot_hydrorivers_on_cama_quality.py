"""Overlay HydroRIVERS on the CaMa continuity-quality map."""

import argparse
from pathlib import Path

import fiona
import geopandas as gpd
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
DEFAULT_HYDRORIVERS = (
    PROJECT_ROOT
    / "Data"
    / "Google Earth Engine"
    / "HydroRIVERS_v10_as.gdb"
    / "HydroRIVERS_v10_as.gdb"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output" / "CamaFlowStatusMatch" / RUN_LABEL


def lines_from_geometry(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [list(geom.coords)]
    if geom.geom_type == "MultiLineString":
        return [list(line.coords) for line in geom.geoms if not line.is_empty]
    return []


def cama_segments(edges):
    return [
        [(float(row.src_lon), float(row.src_lat)), (float(row.dst_lon), float(row.dst_lat))]
        for row in edges.itertuples(index=False)
    ]


def load_hydrorivers(path, bbox, min_discharge_cms, layer=None):
    selected_layer = fiona.listlayers(path)[0] if layer is None else layer
    rivers = gpd.read_file(
        path,
        layer=selected_layer,
        bbox=bbox,
        columns=["HYRIV_ID", "MAIN_RIV", "DIS_AV_CMS", "ORD_FLOW", "geometry"],
    )
    if rivers.crs is not None and rivers.crs.to_string() != "EPSG:4326":
        rivers = rivers.to_crs("EPSG:4326")
    rivers = rivers.loc[rivers["DIS_AV_CMS"] >= min_discharge_cms].copy()
    rivers = rivers.loc[rivers.geometry.notna() & ~rivers.geometry.is_empty].copy()
    return rivers.reset_index(drop=True), selected_layer


def plot_overlay(
    flow_status_path,
    flow_status_png_path,
    edge_csv,
    hydrorivers_path,
    output_path,
    min_discharge_cms,
    native_resolution,
    dpi,
):
    with rasterio.open(flow_status_path) as src:
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        bbox = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
        raster_width = src.width
        raster_height = src.height

    print("Loading HydroRIVERS")
    rivers, layer = load_hydrorivers(hydrorivers_path, bbox, min_discharge_cms)
    hydro_segments = []
    for geom in rivers.geometry:
        hydro_segments.extend(lines_from_geometry(geom))

    print("Loading CaMa edge quality")
    edges = pd.read_csv(edge_csv)
    background = Image.open(flow_status_png_path).convert("RGBA")
    figsize = (raster_width / dpi, raster_height / dpi) if native_resolution else (15, 11)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.imshow(background, extent=extent, origin="upper")

    styles = {
        "good": {"color": "#00843d", "linewidth": 2.5, "label": "CaMa good"},
        "uncertain": {"color": "#ffb000", "linewidth": 3.2, "label": "CaMa uncertain"},
        "poor": {"color": "#d7191c", "linewidth": 4.2, "label": "CaMa poor"},
    }
    for quality in ["good", "uncertain", "poor"]:
        subset = edges.loc[edges["edge_quality"] == quality]
        if subset.empty:
            continue
        segments = cama_segments(subset)
        ax.add_collection(
            LineCollection(
                segments,
                colors="#ffffff",
                linewidths=styles[quality]["linewidth"] + 1.6,
                alpha=0.70,
                zorder={"good": 2, "uncertain": 3, "poor": 4}[quality],
            )
        )
        ax.add_collection(
            LineCollection(
                segments,
                colors=styles[quality]["color"],
                linewidths=styles[quality]["linewidth"],
                alpha=0.96,
                zorder={"good": 5, "uncertain": 6, "poor": 7}[quality],
            )
        )

    if hydro_segments:
        ax.add_collection(
            LineCollection(
                hydro_segments,
                colors="#06283d",
                linewidths=2.25,
                alpha=0.95,
                zorder=10,
            )
        )
        ax.add_collection(
            LineCollection(
                hydro_segments,
                colors="#00e5ff",
                linewidths=1.25,
                alpha=0.98,
                zorder=11,
            )
        )

    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        "HydroRIVERS over CaMa downstream-link quality on the 1 km flow-status map\n"
        f"HydroRIVERS DIS_AV_CMS >= {min_discharge_cms:g}, segments = {len(rivers):,}; "
        f"CaMa edges = {len(edges):,}"
    )
    handles = [
        Line2D([0], [0], color="#00e5ff", linewidth=3.0, label="HydroRIVERS"),
        Line2D([0], [0], color=styles["good"]["color"], linewidth=4.0, label="CaMa good"),
        Line2D([0], [0], color=styles["uncertain"]["color"], linewidth=4.0, label="CaMa uncertain"),
        Line2D([0], [0], color=styles["poor"]["color"], linewidth=4.0, label="CaMa poor"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=True)

    if native_resolution:
        fig.subplots_adjust(left=0.05, right=0.995, bottom=0.06, top=0.94)
    else:
        fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"HydroRIVERS layer: {layer}")
    print(f"HydroRIVERS selected segments: {len(rivers)}")
    print(f"Saved plot: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Overlay HydroRIVERS on CaMa continuity quality.")
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--flow-status-png", type=Path, default=DEFAULT_FLOW_STATUS_PNG)
    parser.add_argument("--edge-csv", type=Path, default=DEFAULT_EDGE_CSV)
    parser.add_argument("--hydrorivers", type=Path, default=DEFAULT_HYDRORIVERS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-discharge-cms", type=float, default=500.0)
    parser.add_argument("--native-resolution", action="store_true")
    parser.add_argument("--dpi", type=int, default=100)
    args = parser.parse_args()

    suffix = f"uparea_10000km2_edge_quality_hydrorivers_dis_{args.min_discharge_cms:g}"
    if args.native_resolution:
        suffix += "_native"
    output_path = args.out_dir / f"cama_flow_status_{suffix}.png"
    plot_overlay(
        args.flow_status,
        args.flow_status_png,
        args.edge_csv,
        args.hydrorivers,
        output_path,
        min_discharge_cms=args.min_discharge_cms,
        native_resolution=args.native_resolution,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
