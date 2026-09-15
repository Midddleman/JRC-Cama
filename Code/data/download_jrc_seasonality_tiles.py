import argparse
from pathlib import Path
import urllib.error
import urllib.request


"""Download JRC Global Surface Water seasonality GeoTIFF tiles."""


DATASET_NAME = "seasonality"
BASE_URL = "https://storage.googleapis.com/global-surface-water/downloads2021"


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())


def global_tile_names():
    longs = [f"{w}W" for w in range(180, 0, -10)]
    longs.extend([f"{e}E" for e in range(0, 180, 10)])

    lats = [f"{s}S" for s in range(50, 0, -10)]
    lats.extend([f"{n}N" for n in range(0, 90, 10)])

    for lon in longs:
        for lat in lats:
            yield f"{DATASET_NAME}_{lon}_{lat}v1_4_2021.tif"


def download_file(url, output_path):
    try:
        urllib.request.urlretrieve(url, output_path)
        return True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"Not found: {url}")
            return False
        raise
    except urllib.error.URLError as exc:
        print(f"Failed: {url} ({exc})")
        return False


def download_global_seasonality(destination_folder):
    destination_folder = Path(destination_folder)
    destination_folder.mkdir(parents=True, exist_ok=True)

    filenames = list(global_tile_names())
    total = len(filenames)

    downloaded = 0
    skipped = 0
    failed = 0

    for index, filename in enumerate(filenames, start=1):
        output_path = destination_folder / filename
        if output_path.exists():
            print(f"[{index}/{total}] Exists, skipping: {output_path}")
            skipped += 1
            continue

        url = f"{BASE_URL}/{DATASET_NAME}/{filename}"
        print(f"[{index}/{total}] Downloading: {url}")
        if download_file(url, output_path):
            downloaded += 1
        else:
            failed += 1

    print("Done")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(
        description="Download global JRC Global Surface Water seasonality GeoTIFF tiles."
    )
    parser.add_argument(
        "destination_folder",
        nargs="?",
        default=PROJECT_ROOT / "Data" / "JRC_seasonality_global",
        help="Folder to save seasonality tiles.",
    )
    args = parser.parse_args()
    download_global_seasonality(args.destination_folder)


if __name__ == "__main__":
    main()
