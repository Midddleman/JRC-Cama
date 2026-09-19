"""Map nearest-reach CaMa catchments colored by their reach's JRC status."""

import argparse
import sqlite3
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd
import rasterio
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from PIL import Image


matplotlib.use("Agg")
import matplotlib.pyplot as plt


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


ROOT = find_project_root(Path(__file__).resolve())
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
MATCH_STEM = "cama_2019_catchment_to_hyriv_as_coverage_5km_all_reaches_nearest"
MATCH_DIR = ROOT / "Output" / "CamaHydroRIVERSCatchmentMatch" / RUN_LABEL
DEFAULT_MATCH_DB = MATCH_DIR / f"{MATCH_STEM}.sqlite"
DEFAULT_INTEGRATED_DB = ROOT / "Output" / "CamaHydroRIVERSIntegrated" / RUN_LABEL / "cama_2019_hyriv_jrc_integrated_nearest_endpoint_7x7.sqlite"
DEFAULT_RIVERS = MATCH_DIR / f"{MATCH_STEM}_matched_reaches.geojson"
DEFAULT_OUTPUT = MATCH_DIR / f"{MATCH_STEM}_endpoint_7x7_map.png"
DEFAULT_JRC_OUTPUT = MATCH_DIR / f"{MATCH_STEM}_endpoint_7x7_jrc_map.png"
DEFAULT_JRC_TIF = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.tif"
DEFAULT_JRC_PNG = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.png"


def river_lines(geometries):
    for geometry in geometries:
        if geometry is None or geometry.is_empty:
            continue
        if geometry.geom_type == "LineString":
            yield list(geometry.coords)
        elif geometry.geom_type == "MultiLineString":
            for line in geometry.geoms:
                if not line.is_empty:
                    yield list(line.coords)


def plot_matches(match_db, integrated_db, river_geojson, output_path, dpi, jrc_tif=None, jrc_png=None):
    with sqlite3.connect(integrated_db) as connection:
        points = pd.read_sql_query(
            "SELECT c.catchment_id, c.longitude, c.latitude, c.match_status, "
            "r.jrc_status, r.jrc_evidence FROM catchments c "
            "JOIN river_segments r ON r.hyriv_id = c.hyriv_id ORDER BY c.catchment_id",
            connection,
        )
    with sqlite3.connect(match_db) as connection:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'search_km'"
        ).fetchone()
        coverage_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'coverage_km'"
        ).fetchone()
    if row is None:
        raise ValueError("Match database is missing the search_km metadata.")
    search_km = float(row[0])
    coverage_label = f"as coverage <= {float(coverage_row[0]):g} km | " if coverage_row else ""
    if points.empty:
        raise ValueError("Integrated database has no matched catchments.")

    rivers = gpd.read_file(river_geojson, columns=["geometry"])
    if rivers.crs is None:
        raise ValueError("HydroRIVERS geometry has no CRS.")
    if rivers.crs.to_epsg() != 4326:
        rivers = rivers.to_crs(4326)

    groups = {
        "Perennial catchment": points[points["jrc_status"] == 2],
        "Non-perennial catchment": points[(points["jrc_status"] == 1) & (points["jrc_evidence"] != "outside_raster")],
        "Outside JRC": points[points["jrc_evidence"] == "outside_raster"],
    }
    colors = {
        "Perennial catchment": "#168552",
        "Non-perennial catchment": "#d53232",
        "Outside JRC": "#8f9293",
    }
    sizes = {name: 9 for name in groups}

    fig, ax = plt.subplots(figsize=(15, 10.6), dpi=dpi)
    ax.set_facecolor("#f7f9fa")
    if jrc_tif is not None:
        if jrc_png is None:
            raise ValueError("JRC PNG must be provided with the JRC GeoTIFF.")
        with rasterio.open(jrc_tif) as source:
            extent = [
                source.bounds.left, source.bounds.right,
                source.bounds.bottom, source.bounds.top,
            ]
        with Image.open(jrc_png) as source:
            background = source.convert("RGBA")
        ax.imshow(background, extent=extent, origin="upper", alpha=0.50, zorder=0)
    ax.add_collection(
        LineCollection(
            list(river_lines(rivers.geometry)),
            colors="#879397" if jrc_tif is not None else "#acb8bc",
            linewidths=0.25,
            alpha=0.35 if jrc_tif is not None else 0.5,
            zorder=1,
            rasterized=True,
        )
    )
    for zorder, (name, group) in enumerate(groups.items(), start=2):
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=sizes[name] + (4 if jrc_tif is not None else 0),
            c=colors[name],
            edgecolors="white" if jrc_tif is not None else "none",
            linewidths=0.35 if jrc_tif is not None else 0,
            alpha=0.94 if jrc_tif is not None else 0.83,
            label=f"{name} ({len(group):,})",
            zorder=zorder,
            rasterized=True,
        )

    ax.set_xlim(70, 140.01)
    ax.set_ylim(9.99, 60.0 if jrc_tif is not None else 56.1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        ("CaMa catchment matches over JRC flow status\n" if jrc_tif is not None
         else "CaMa catchments by matched HydroRIVERS JRC status\n")
        + f"{coverage_label}nearest as reach within {search_km:g} km | {len(points):,} catchments"
    )
    handles = [
        Line2D(
            [], [], linestyle="none", marker="o", markersize=7,
            color=colors[name], label=f"{name} ({len(group):,})",
        )
        for name, group in groups.items()
    ]
    ax.legend(handles=handles, loc="lower left", frameon=True, facecolor="white", framealpha=0.95)
    ax.grid(color="#dce2e4", linewidth=0.4, alpha=0.6, zorder=0)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return {name: len(group) for name, group in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-db", type=Path, default=DEFAULT_MATCH_DB)
    parser.add_argument("--integrated-db", type=Path, default=DEFAULT_INTEGRATED_DB)
    parser.add_argument("--river-geojson", type=Path, default=DEFAULT_RIVERS)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--jrc-background", action="store_true")
    parser.add_argument("--jrc-tif", type=Path, default=DEFAULT_JRC_TIF)
    parser.add_argument("--jrc-png", type=Path, default=DEFAULT_JRC_PNG)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    output = args.output or (DEFAULT_JRC_OUTPUT if args.jrc_background else DEFAULT_OUTPUT)
    counts = plot_matches(
        args.match_db, args.integrated_db, args.river_geojson, output, args.dpi,
        jrc_tif=args.jrc_tif if args.jrc_background else None,
        jrc_png=args.jrc_png if args.jrc_background else None,
    )
    print(counts)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
