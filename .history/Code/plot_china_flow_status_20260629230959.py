from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from rasterio.merge import merge


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TILE_DIR = PROJECT_ROOT / "Output" / "ChinaFlowStatusTiles"
OUTPUT_DIR = PROJECT_ROOT / "Output" / "ChinaFlowStatusMosaic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOSAIC_TIF = OUTPUT_DIR / "china_flow_status_factor33.tif"
MOSAIC_PNG = OUTPUT_DIR / "china_flow_status_factor33.png"
NODATA = 255


def main():
    tile_paths = sorted(TILE_DIR.glob("flow_status_*.tif"))
    if not tile_paths:
        raise FileNotFoundError(f"No flow_status tiles found in {TILE_DIR}")

    print(f"Merging {len(tile_paths)} tiles")
    datasets = [rasterio.open(path) for path in tile_paths]
    try:
        mosaic, transform = merge(datasets, nodata=NODATA)
        profile = datasets[0].profile.copy()
        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=transform,
            nodata=NODATA,
            compress="lzw",
        )

        with rasterio.open(MOSAIC_TIF, "w", **profile) as dst:
            dst.write(mosaic)
            dst.update_tags(
                1,
                value_0="non-water",
                value_1="intermittent",
                value_2="perennial",
                value_255="nodata",
            )
    finally:
        for dataset in datasets:
            dataset.close()

    flow_status = mosaic[0]
    print("Mosaic shape:", flow_status.shape)
    print("Unique values:", np.unique(flow_status))
    print("Non-water:", int(np.sum(flow_status == 0)))
    print("Intermittent:", int(np.sum(flow_status == 1)))
    print("Perennial:", int(np.sum(flow_status == 2)))

    west = transform.c
    north = transform.f
    east = west + transform.a * flow_status.shape[1]
    south = north + transform.e * flow_status.shape[0]
    extent = [west, east, south, north]

    masked = np.ma.masked_equal(flow_status, NODATA)
    cmap = ListedColormap(["lightgray", "orange", "blue"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)

    fig, ax = plt.subplots(figsize=(13, 10))
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    ax.legend(
        handles=[
            mpatches.Patch(color="lightgray", label="Non-water"),
            mpatches.Patch(color="orange", label="Intermittent"),
            mpatches.Patch(color="blue", label="Perennial"),
        ],
        loc="upper right",
        title="Flow status",
    )
    ax.set_xlim(70, 140)
    ax.set_ylim(10, 60)
    ax.set_aspect("equal")
    ax.set_title("China-Covering JRC Flow Status Mosaic, factor=33")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.tight_layout()
    fig.savefig(MOSAIC_PNG, dpi=600)

    print(f"Saved mosaic GeoTIFF: {MOSAIC_TIF}")
    print(f"Saved preview PNG: {MOSAIC_PNG}")


if __name__ == "__main__":
    main()
