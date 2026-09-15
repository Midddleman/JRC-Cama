"""Plot CaMa-Flood catchment points and downstream links on the flow-status map."""

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from PIL import Image
from scipy import ndimage


matplotlib.use("Agg")
import matplotlib.pyplot as plt


RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"
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
DEFAULT_FLOW_STATUS_PNG = (
    PROJECT_ROOT
    / "Output"
    / "ChinaFlowStatusMosaic"
    / RUN_LABEL
    / f"china_flow_status_factor33_{RUN_LABEL}.png"
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


def rowcol_arrays(transform, lon, lat):
    inv = ~transform
    col_f, row_f = inv * (lon, lat)
    return np.floor(row_f).astype(np.int64), np.floor(col_f).astype(np.int64)


def pixel_centers(transform, rows, cols):
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    return np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64)


def load_cama(path, bounds, min_upstream_area_km2):
    with xr.open_dataset(path) as ds:
        frame = pd.DataFrame(
            {
                "catchment_id": ds["catchment_id"].values.astype(np.int64),
                "downstream_id": ds["downstream_id"].values.astype(np.int64),
                "basin_id": ds["catchment_basin_id"].values.astype(np.int64),
                "longitude": ds["longitude"].values.astype(np.float64),
                "latitude": ds["latitude"].values.astype(np.float64),
                "upstream_area_km2": ds["upstream_area"].values.astype(np.float64) / 1_000_000.0,
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
        frame = frame.loc[frame["upstream_area_km2"] >= float(min_upstream_area_km2)].copy()
    return frame.reset_index(drop=True)


def add_match_columns(cama, flow_status, transform):
    water_mask = (flow_status == 1) | (flow_status == 2)
    _, nearest_indices = ndimage.distance_transform_edt(
        ~water_mask,
        return_indices=True,
    )

    rows, cols = rowcol_arrays(transform, cama["longitude"].to_numpy(), cama["latitude"].to_numpy())
    valid = (rows >= 0) & (rows < flow_status.shape[0]) & (cols >= 0) & (cols < flow_status.shape[1])
    rows_clipped = rows.clip(0, flow_status.shape[0] - 1)
    cols_clipped = cols.clip(0, flow_status.shape[1] - 1)

    nearest_rows = nearest_indices[0, rows_clipped, cols_clipped]
    nearest_cols = nearest_indices[1, rows_clipped, cols_clipped]
    nearest_lon, nearest_lat = pixel_centers(transform, nearest_rows, nearest_cols)
    nearest_distance_km = haversine_km(
        cama["longitude"].to_numpy(),
        cama["latitude"].to_numpy(),
        nearest_lon,
        nearest_lat,
    )

    point_status = np.full(len(cama), 255, dtype=np.uint8)
    point_status[valid] = flow_status[rows[valid], cols[valid]]

    cama = cama.copy()
    cama["flow_status_row"] = rows
    cama["flow_status_col"] = cols
    cama["point_flow_status"] = point_status
    cama["nearest_water_distance_km"] = nearest_distance_km
    cama["match_class"] = np.where(
        point_status == 2,
        "on perennial",
        np.where(point_status == 1, "on intermittent", np.where(nearest_distance_km <= 5.0, "near water", "far from water")),
    )
    return cama


def build_downstream_segments(cama):
    id_to_xy = {
        int(row.catchment_id): (float(row.longitude), float(row.latitude))
        for row in cama.itertuples(index=False)
    }
    segments = []
    for row in cama.itertuples(index=False):
        downstream_xy = id_to_xy.get(int(row.downstream_id))
        if downstream_xy is None:
            continue
        xy = (float(row.longitude), float(row.latitude))
        if xy == downstream_xy:
            continue
        segments.append([xy, downstream_xy])
    return segments


def build_downstream_vectors(cama):
    id_to_xy = {
        int(row.catchment_id): (float(row.longitude), float(row.latitude))
        for row in cama.itertuples(index=False)
    }
    xs = []
    ys = []
    us = []
    vs = []
    for row in cama.itertuples(index=False):
        downstream_xy = id_to_xy.get(int(row.downstream_id))
        if downstream_xy is None:
            continue
        x = float(row.longitude)
        y = float(row.latitude)
        dx = downstream_xy[0] - x
        dy = downstream_xy[1] - y
        if dx == 0.0 and dy == 0.0:
            continue
        xs.append(x)
        ys.append(y)
        us.append(dx)
        vs.append(dy)
    return np.asarray(xs), np.asarray(ys), np.asarray(us), np.asarray(vs)


def plot_map(
    flow_status_path,
    flow_status_png_path,
    cama,
    output_path,
    title,
    draw_boxes,
    draw_links,
    draw_arrows,
    line_alpha,
    point_scale,
    native_resolution,
    dpi,
):
    with rasterio.open(flow_status_path) as src:
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        raster_width = src.width
        raster_height = src.height

    background = Image.open(flow_status_png_path).convert("RGBA")
    if native_resolution:
        figsize = (raster_width / dpi, raster_height / dpi)
    else:
        figsize = (15, 11)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.imshow(background, extent=extent, origin="upper")

    if draw_links:
        segments = build_downstream_segments(cama)
        if segments:
            ax.add_collection(LineCollection(segments, colors="#111111", linewidths=0.22, alpha=line_alpha, zorder=2))

    if draw_arrows:
        xs, ys, us, vs = build_downstream_vectors(cama)
        if len(xs):
            ax.quiver(
                xs,
                ys,
                us,
                vs,
                angles="xy",
                scale_units="xy",
                scale=1,
                color="#111111",
                width=0.00055,
                headwidth=4.0,
                headlength=5.0,
                headaxislength=4.5,
                alpha=min(0.95, line_alpha + 0.25),
                zorder=4,
            )

    if draw_boxes:
        half = 0.05
        for row in cama.itertuples(index=False):
            ax.add_patch(
                plt.Rectangle(
                    (float(row.longitude) - half, float(row.latitude) - half),
                    0.1,
                    0.1,
                    fill=False,
                    edgecolor="#5f5f5f",
                    linewidth=0.15,
                    alpha=0.15,
                    zorder=1,
                )
            )

    styles = {
        "on perennial": {"color": "#005ce6", "s": 5.0 * point_scale, "alpha": 0.95, "label": "CaMa point on perennial cell"},
        "on intermittent": {"color": "#ff7f00", "s": 5.0 * point_scale, "alpha": 0.95, "label": "CaMa point on intermittent cell"},
        "near water": {"color": "#25a35a", "s": 4.5 * point_scale, "alpha": 0.75, "label": "CaMa point within 5 km of water"},
        "far from water": {"color": "#c1272d", "s": 5.0 * point_scale, "alpha": 0.75, "label": "CaMa point farther than 5 km"},
    }
    for match_class, style in styles.items():
        subset = cama[cama["match_class"] == match_class]
        if subset.empty:
            continue
        ax.scatter(
            subset["longitude"],
            subset["latitude"],
            s=style["s"],
            color=style["color"],
            alpha=style["alpha"],
            linewidths=0,
            zorder=3,
        )

    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    handles = []
    if draw_arrows:
        handles.append(Line2D([0], [0], color="#111111", linewidth=1.0, label="CaMa downstream direction"))
    elif draw_links:
        handles.append(Line2D([0], [0], color="#111111", linewidth=0.8, label="CaMa downstream link"))
    handles.extend(
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=style["color"],
            markeredgecolor="none",
            markersize=5,
            label=style["label"],
        )
        for style in styles.values()
    )
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=True)
    if native_resolution:
        fig.subplots_adjust(left=0.05, right=0.995, bottom=0.06, top=0.94)
    else:
        fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot CaMa-Flood catchments over the aggregated flow-status map.")
    parser.add_argument("--flow-status", type=Path, default=DEFAULT_FLOW_STATUS)
    parser.add_argument("--flow-status-png", type=Path, default=DEFAULT_FLOW_STATUS_PNG)
    parser.add_argument("--cama-parameters", type=Path, default=DEFAULT_CAMA_PARAMETERS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-upstream-area-km2", type=float, default=10000.0)
    parser.add_argument("--all-catchments", action="store_true")
    parser.add_argument("--draw-boxes", action="store_true")
    parser.add_argument("--no-links", action="store_true")
    parser.add_argument("--draw-arrows", action="store_true")
    parser.add_argument("--line-alpha", type=float, default=0.35)
    parser.add_argument("--point-scale", type=float, default=1.0)
    parser.add_argument("--native-resolution", action="store_true")
    parser.add_argument("--dpi", type=int, default=220)
    args = parser.parse_args()

    with rasterio.open(args.flow_status) as src:
        flow_status = src.read(1)
        transform = src.transform
        bounds = src.bounds

    print("Loading CaMa catchments")
    min_upstream_area_km2 = None if args.all_catchments else args.min_upstream_area_km2
    cama = load_cama(args.cama_parameters, bounds, min_upstream_area_km2)
    cama = add_match_columns(cama, flow_status, transform)

    suffix = "all" if min_upstream_area_km2 is None else f"uparea_{min_upstream_area_km2:g}km2"
    if args.draw_boxes:
        suffix += "_boxes"
    if args.no_links:
        suffix += "_points"
    if args.draw_arrows:
        suffix += "_arrows"
    if args.native_resolution:
        suffix += "_native"
    output_path = args.out_dir / f"cama_on_flow_status_{suffix}.png"
    filter_text = "all CaMa catchments" if min_upstream_area_km2 is None else f"upstream area >= {min_upstream_area_km2:g} km2"
    title = (
        "CaMa-Flood catchments projected on the 1 km flow-status map\n"
        f"{filter_text}, catchments = {len(cama):,}"
    )
    plot_map(
        args.flow_status,
        args.flow_status_png,
        cama,
        output_path,
        title,
        draw_boxes=args.draw_boxes,
        draw_links=not args.no_links,
        draw_arrows=args.draw_arrows,
        line_alpha=args.line_alpha,
        point_scale=args.point_scale,
        native_resolution=args.native_resolution,
        dpi=args.dpi,
    )

    summary_path = args.out_dir / f"cama_on_flow_status_{suffix}_summary.csv"
    cama.drop(columns=[]).to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(cama["match_class"].value_counts())
    print(f"Saved plot: {output_path}")
    print(f"Saved point summary: {summary_path}")


if __name__ == "__main__":
    main()
