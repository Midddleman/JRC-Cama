from collections import deque
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window


SOURCE_DIR = Path("../Data/JRC_seasonality_global")
OUTPUT_DIR = Path("../Output/ChinaFlowStatusTiles")

FACTOR = 33
WATER_RATIO_THRESHOLD = 0.3
PERENNIAL_MONTH_THRESHOLD = 10
PERENNIAL_RATIO_THRESHOLD = 0.5
NODATA = 255


def has_water_path_across(block):
    """Return True if a connected water component touches two different borders."""
    water_mask = block.astype(bool)
    if not np.any(water_mask):
        return False

    height, width = water_mask.shape
    visited = np.zeros_like(water_mask, dtype=bool)

    for row in range(height):
        for col in range(width):
            if not water_mask[row, col] or visited[row, col]:
                continue

            queue = deque([(row, col)])
            visited[row, col] = True
            touches = set()

            while queue:
                r, c = queue.popleft()
                if r == 0:
                    touches.add("top")
                if r == height - 1:
                    touches.add("bottom")
                if c == 0:
                    touches.add("left")
                if c == width - 1:
                    touches.add("right")

                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < height and 0 <= nc < width:
                            if water_mask[nr, nc] and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))

            if len(touches) >= 2:
                return True

    return False


def china_tile_paths(source_dir):
    # JRC names latitudes by the northern edge. These tiles cover about
    # 70-140E and 10-60N, which contains China.
    for lon in range(70, 140, 10):
        for lat_north in range(20, 70, 10):
            yield source_dir / f"seasonality_{lon}E_{lat_north}Nv1_4_2021.tif"


def aggregate_seasonality_file(
    input_path,
    output_path,
    factor=FACTOR,
    water_ratio_threshold=WATER_RATIO_THRESHOLD,
    perennial_month_threshold=PERENNIAL_MONTH_THRESHOLD,
    perennial_ratio_threshold=PERENNIAL_RATIO_THRESHOLD,
    stripe_output_rows=64,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(input_path) as src:
        out_height = int(np.ceil(src.height / factor))
        out_width = int(np.ceil(src.width / factor))
        out_transform = src.transform * Affine.scale(factor, factor)

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=out_height,
            width=out_width,
            count=1,
            dtype="uint8",
            transform=out_transform,
            nodata=NODATA,
            compress="lzw",
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            for out_row_start in range(0, out_height, stripe_output_rows):
                out_rows = min(stripe_output_rows, out_height - out_row_start)
                src_row_start = out_row_start * factor
                src_rows = min(out_rows * factor, src.height - src_row_start)

                window = Window(0, src_row_start, src.width, src_rows)
                data = src.read(1, window=window)

                padded_height = out_rows * factor
                padded_width = out_width * factor
                padded = np.full((padded_height, padded_width), NODATA, dtype=np.uint8)
                padded[:src_rows, :src.width] = data

                valid = padded != NODATA
                water = (padded > 0) & valid
                perennial = (padded >= perennial_month_threshold) & valid

                valid_blocks = valid.reshape(out_rows, factor, out_width, factor)
                water_blocks = water.reshape(out_rows, factor, out_width, factor)
                perennial_blocks = perennial.reshape(out_rows, factor, out_width, factor)

                valid_count = valid_blocks.sum(axis=(1, 3))
                water_count = water_blocks.sum(axis=(1, 3))
                perennial_count = perennial_blocks.sum(axis=(1, 3))

                water_ratio = np.divide(
                    water_count,
                    valid_count,
                    out=np.zeros_like(water_count, dtype=np.float32),
                    where=valid_count > 0,
                )
                perennial_ratio = np.divide(
                    perennial_count,
                    water_count,
                    out=np.zeros_like(perennial_count, dtype=np.float32),
                    where=water_count > 0,
                )

                status = np.full((out_rows, out_width), NODATA, dtype=np.uint8)
                has_valid = valid_count > 0
                water_connected = np.zeros((out_rows, out_width), dtype=bool)
                for out_row in range(out_rows):
                    for out_col in range(out_width):
                        block = water_blocks[out_row, :, out_col, :]
                        water_connected[out_row, out_col] = has_water_path_across(block)

                water_agg = ((water_ratio > water_ratio_threshold) | water_connected) & has_valid
                status[has_valid] = 0
                status[water_agg] = 1
                status[water_agg & (perennial_ratio > perennial_ratio_threshold)] = 2

                dst.write(status, 1, window=Window(0, out_row_start, out_width, out_rows))

            dst.update_tags(
                1,
                value_0="non-water",
                value_1="intermittent",
                value_2="perennial",
                value_255="nodata",
            )

    return output_path


def main():
    tile_paths = list(china_tile_paths(SOURCE_DIR))
    missing = [path for path in tile_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing input tiles:\n" + "\n".join(str(path) for path in missing))

    print(f"Processing {len(tile_paths)} China-covering JRC seasonality tiles")
    for index, input_path in enumerate(tile_paths, start=1):
        output_path = OUTPUT_DIR / input_path.name.replace("seasonality_", "flow_status_")
        if output_path.exists():
            print(f"[{index}/{len(tile_paths)}] Exists, skipping: {output_path}")
            continue

        print(f"[{index}/{len(tile_paths)}] Processing: {input_path.name}")
        aggregate_seasonality_file(input_path, output_path)
        print(f"[{index}/{len(tile_paths)}] Saved: {output_path}")


if __name__ == "__main__":
    main()
