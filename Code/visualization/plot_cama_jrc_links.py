"""Plot direct CaMa downstream-link JRC classifications without HydroRIVERS."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

import matplotlib
import rasterio
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from PIL import Image


matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
DEFAULT_DB = ROOT / "Output" / "CamaJRCDownstreamLinks" / RUN_LABEL / "cama_2019_jrc_links_corridor_5km.sqlite"
DEFAULT_OUTPUT = ROOT / "Output" / "CamaJRCDownstreamLinks" / RUN_LABEL / "cama_2019_jrc_links_corridor_5km_map.png"
DEFAULT_JRC_TIF = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.tif"
DEFAULT_JRC_PNG = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.png"
COLORS = {2: "#168552", 1: "#d53232", None: "#7d8585"}
LABELS = {2: "Perennial", 1: "Non-perennial", None: "Unresolved"}


def plot_links(db_path, jrc_tif, jrc_png, output_path, dpi):
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT longitude, latitude, downstream_longitude, downstream_latitude, jrc_status "
            "FROM catchment_links ORDER BY catchment_id"
        ).fetchall()
    with rasterio.open(jrc_tif) as source:
        extent = [source.bounds.left, source.bounds.right, source.bounds.bottom, source.bounds.top]
    with Image.open(jrc_png) as source:
        background = source.convert("RGBA")

    fig, ax = plt.subplots(figsize=(15, 10.6), dpi=dpi)
    ax.set_facecolor("#f7f9fa")
    ax.imshow(background, extent=extent, origin="upper", alpha=0.50, zorder=0)
    for zorder, status in enumerate((None, 1, 2), start=1):
        group = [row for row in rows if row[4] == status]
        segments = [
            [(row[0], row[1]), (row[2], row[3])]
            for row in group if row[2] is not None and row[3] is not None
        ]
        ax.add_collection(LineCollection(
            segments, colors=COLORS[status], linewidths=0.7,
            alpha=0.78, zorder=zorder, rasterized=True,
        ))
        ax.scatter(
            [row[0] for row in group], [row[1] for row in group],
            s=3.2, c=COLORS[status], edgecolors="none", alpha=0.85,
            zorder=zorder + 3, rasterized=True,
        )
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("CaMa downstream links classified by JRC blue-cell connectivity\n10 km-wide corridor | CaMa 2019 flow | JRC long-term status")
    counts = {status: sum(row[4] == status for row in rows) for status in COLORS}
    handles = [
        Line2D([], [], color=COLORS[status], linewidth=2, label=f"{LABELS[status]} ({counts[status]:,})")
        for status in (2, 1, None)
    ]
    ax.legend(handles=handles, loc="lower left", facecolor="white", framealpha=0.95)
    ax.grid(color="#dce2e4", linewidth=0.4, alpha=0.6, zorder=0)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return {LABELS[status]: counts[status] for status in (2, 1, None)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--jrc-tif", type=Path, default=DEFAULT_JRC_TIF)
    parser.add_argument("--jrc-png", type=Path, default=DEFAULT_JRC_PNG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()
    print(plot_links(args.database, args.jrc_tif, args.jrc_png, args.output, args.dpi))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
