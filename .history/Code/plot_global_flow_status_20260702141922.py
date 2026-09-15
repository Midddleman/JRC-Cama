from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.merge import merge


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "Output" / "GlobalFlowStatusRuns"
OUTPUT_DIR = PROJECT_ROOT / "Output" / "GlobalFlowStatusMap"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NODATA = 255


def save_classified_png(data, output_path):
    """Save classification raster as a full-resolution paletted PNG."""
    Image.MAX_IMAGE_PIXELS = None

    palette = [255, 255, 255] * 256
    palette[0:3] = [211, 211, 211]  # non-water
    palette[3:6] = [255, 165, 0]  # intermittent
    palette[6:9] = [0, 0, 255]  # perennial
    palette[255 * 3 : 255 * 3 + 3] = [255, 255, 255]  # nodata

    image = Image.fromarray(data.astype(np.uint8), mode="P")
    image.putpalette(palette)
    image.save(output_path)


def main():
    run_dirs = sorted([path for path in OUTPUT_ROOT.glob("*") if path.is_dir()])
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {OUTPUT_ROOT}")

    latest_run = run_dirs[-1]
    tile_dir = latest_run / "tiles"
    tile_paths = sorted(tile_dir.glob("flow_status_*.tif"))
    if not tile_paths:
        raise FileNotFoundError(f"No flow_status tiles found in {tile_dir}")

    mosaic_dir = OUTPUT_DIR / latest_run.name
    mosaic_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_TIF = mosaic_dir / f"global_flow_status_factor33_{latest_run.name}.tif"
    OUTPUT_PNG = mosaic_dir / f"global_flow_status_factor33_{latest_run.name}.png"

    print(f"Merging {len(tile_paths)} global flow_status tiles at full resolution from {latest_run.name}")
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

        with rasterio.open(OUTPUT_TIF, "w", **profile) as dst:
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
    total_non_water = int(np.sum(flow_status == 0))
    total_intermittent = int(np.sum(flow_status == 1))
    total_perennial = int(np.sum(flow_status == 2))

    save_classified_png(flow_status, OUTPUT_PNG)

    print("Non-water:", total_non_water)
    print("Intermittent:", total_intermittent)
    print("Perennial:", total_perennial)
    print(f"Saved global mosaic GeoTIFF: {OUTPUT_TIF}")
    print(f"Saved full-resolution PNG: {OUTPUT_PNG}")
    print("PNG size:", f"{flow_status.shape[1]} x {flow_status.shape[0]} pixels")


if __name__ == "__main__":
    main()
