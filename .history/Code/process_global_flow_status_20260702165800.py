import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window
from scipy import ndimage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "Data" / "JRC_seasonality_global"
OUTPUT_ROOT = PROJECT_ROOT / "Output" / "GlobalFlowStatusRuns"
PLOT_SCRIPT = PROJECT_ROOT / "Code" / "plot_global_flow_status.py"

FACTOR = 33
WATER_RATIO_THRESHOLD = 0.4
USE_CONNECTIVITY = True
MIN_CONNECTED_WATER_CELLS = 50
PERENNIAL_MONTH_THRESHOLD = 10
PERENNIAL_RATIO_THRESHOLD = 0.5
NODATA = 255
NUM_WORKERS = max(1, min(4, (os.cpu_count() or 1)))


def has_water_path_across(block, min_connected_water_cells=MIN_CONNECTED_WATER_CELLS):
    """Return True if a connected water component is large enough and touches two borders."""
    water_mask = block.astype(bool)
    if not np.any(water_mask):
        return False

    labeled, num_features = ndimage.label(
        water_mask,
        structure=np.ones((3, 3), dtype=np.uint8),
    )
    if num_features == 0:
        return False

    height, width = water_mask.shape
    for label_id in range(1, num_features + 1):
        component = labeled == label_id
        component_size = int(component.sum())
        if component_size < min_connected_water_cells:
            continue

        touches = set()
        if np.any(component[0, :]):
            touches.add("top")
        if np.any(component[-1, :]):
            touches.add("bottom")
        if np.any(component[:, 0]):
            touches.add("left")
        if np.any(component[:, -1]):
            touches.add("right")

        if len(touches) >= 2:
            return True

    return False


def global_tile_paths(source_dir):
    return sorted(source_dir.glob("seasonality_*v1_4_2021.tif"))


def run_label(water_ratio_threshold, use_connectivity, min_connected_water_cells, perennial_month_threshold, perennial_ratio_threshold):
    connectivity_label = "na" if not use_connectivity else f"{min_connected_water_cells}"
    return (
        f"water_ratio_{water_ratio_threshold:.2f}_"
        f"min_conn_{connectivity_label}_"
        f"perennial_{perennial_month_threshold}_"
        f"perennial_ratio_{perennial_ratio_threshold:.2f}"
    )


def resolve_num_workers(requested=None):
    if requested is not None:
        return max(1, int(requested))
    return NUM_WORKERS


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}h {minutes:d}m {secs:d}s"
    if minutes:
        return f"{minutes:d}m {secs:d}s"
    return f"{secs:d}s"


def print_progress(current, total, start_time):
    if total <= 0:
        return
    elapsed = time.time() - start_time
    percent = current / total * 100.0
    eta = elapsed * (total - current) / max(current, 1)
    bar_width = 30
    filled = int(bar_width * current / total)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(
        f"\r[{bar}] {current}/{total} ({percent:5.1f}%) | elapsed: {format_duration(elapsed)} | eta: {format_duration(eta)}",
        end="",
        flush=True,
    )


def build_tile_tasks(
    tile_paths,
    tile_output_dir,
    water_ratio_threshold=WATER_RATIO_THRESHOLD,
    use_connectivity=USE_CONNECTIVITY,
    min_connected_water_cells=MIN_CONNECTED_WATER_CELLS,
    perennial_month_threshold=PERENNIAL_MONTH_THRESHOLD,
    perennial_ratio_threshold=PERENNIAL_RATIO_THRESHOLD,
):
    tasks = []
    for input_path in tile_paths:
        output_path = tile_output_dir / input_path.name.replace("seasonality_", "flow_status_")
        tasks.append(
            (
                input_path,
                output_path,
                water_ratio_threshold,
                use_connectivity,
                min_connected_water_cells,
                perennial_month_threshold,
                perennial_ratio_threshold,
            )
        )
    return tasks


def process_tile_task(task):
    (
        input_path,
        output_path,
        water_ratio_threshold,
        use_connectivity,
        min_connected_water_cells,
        perennial_month_threshold,
        perennial_ratio_threshold,
    ) = task
    return aggregate_seasonality_file(
        input_path,
        output_path,
        water_ratio_threshold=water_ratio_threshold,
        use_connectivity=use_connectivity,
        min_connected_water_cells=min_connected_water_cells,
        perennial_month_threshold=perennial_month_threshold,
        perennial_ratio_threshold=perennial_ratio_threshold,
    )


def aggregate_seasonality_file(
    input_path,
    output_path,
    factor=FACTOR,
    water_ratio_threshold=WATER_RATIO_THRESHOLD,
    use_connectivity=USE_CONNECTIVITY,
    min_connected_water_cells=MIN_CONNECTED_WATER_CELLS,
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
                        if water_ratio[out_row, out_col] > water_ratio_threshold:
                            water_connected[out_row, out_col] = True
                            continue

                        if not use_connectivity:
                            continue

                        if water_count[out_row, out_col] < min_connected_water_cells:
                            continue
                        block = water_blocks[out_row, :, out_col, :]
                        water_connected[out_row, out_col] = has_water_path_across(
                            block,
                            min_connected_water_cells=min_connected_water_cells,
                        )

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
    tile_paths = list(global_tile_paths(SOURCE_DIR))
    if not tile_paths:
        raise FileNotFoundError(f"No seasonality tiles found in {SOURCE_DIR}")

    run_dir = OUTPUT_ROOT / run_label(
        WATER_RATIO_THRESHOLD,
        USE_CONNECTIVITY,
        MIN_CONNECTED_WATER_CELLS,
        PERENNIAL_MONTH_THRESHOLD,
        PERENNIAL_RATIO_THRESHOLD,
    )
    if run_dir.exists():
        print(f"Run already exists, skipping: {run_dir}")
        return run_dir

    run_dir.mkdir(parents=True, exist_ok=True)
    tile_output_dir = run_dir / "tiles"
    tile_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing {len(tile_paths)} global JRC seasonality tiles")
    print(f"Run directory: {run_dir}")
    tasks = build_tile_tasks(
        tile_paths,
        tile_output_dir,
        water_ratio_threshold=WATER_RATIO_THRESHOLD,
        use_connectivity=USE_CONNECTIVITY,
        min_connected_water_cells=MIN_CONNECTED_WATER_CELLS,
        perennial_month_threshold=PERENNIAL_MONTH_THRESHOLD,
        perennial_ratio_threshold=PERENNIAL_RATIO_THRESHOLD,
    )
    pending_tasks = [task for task in tasks if not task[1].exists()]
    if not pending_tasks:
        print("All tiles already exist, nothing to process")
    else:
        num_workers = resolve_num_workers()
        print(f"Processing {len(pending_tasks)} tile(s) with {num_workers} worker(s)")
        start_time = time.time()
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_task = {executor.submit(process_tile_task, task): task for task in pending_tasks}
            for completed, future in enumerate(as_completed(future_to_task), start=1):
                task = future_to_task[future]
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"\nTile failed: {task[0].name}: {exc}")
                    raise
                print_progress(completed, len(pending_tasks), start_time)
                print(f"\n[{completed}/{len(pending_tasks)}] Saved: {result}")
        print()

    mosaic_dir = PROJECT_ROOT / "Output" / "GlobalFlowStatusMosaic" / run_dir.name
    mosaic_tif = mosaic_dir / f"global_flow_status_factor33_{run_dir.name}.tif"
    mosaic_png = mosaic_dir / f"global_flow_status_factor33_{run_dir.name}.png"
    if mosaic_tif.exists() and mosaic_png.exists():
        print(f"Plot outputs already exist, skipping plotting: {mosaic_dir}")
    else:
        print(f"Generating plot outputs for run: {run_dir.name}")
        subprocess.run([sys.executable, str(PLOT_SCRIPT), "--run-dir", str(run_dir)], check=True)


if __name__ == "__main__":
    main()
