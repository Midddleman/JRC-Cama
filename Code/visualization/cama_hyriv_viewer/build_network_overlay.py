"""Build the full-discharge-screened HydroRIVERS map layer for the viewer."""

import argparse
import gzip
import json
import os
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
DEFAULT_GDB = ROOT / "Data" / "Google Earth Engine" / "HydroRIVERS_v10_as.gdb" / "HydroRIVERS_v10_as.gdb"
DEFAULT_OUTPUT = ROOT / "Output" / "CamaHydroRIVERSIntegrated" / RUN_LABEL / "hydrorivers_as_dis_gt_20_map.json.gz"


def geometry_lines(geometry):
    if geometry.geom_type == "LineString":
        return [[list(xy) for xy in geometry.coords]]
    if geometry.geom_type == "MultiLineString":
        return [[list(xy) for xy in line.coords] for line in geometry.geoms]
    raise ValueError(f"Unexpected HydroRIVERS geometry: {geometry.geom_type}")


def build_overlay(gdb_path, output_path, threshold_cms, overwrite=False):
    if threshold_cms < 0:
        raise ValueError("Discharge threshold must be non-negative.")
    if output_path.exists() and not overwrite:
        raise FileExistsError(output_path)
    rivers = gpd.read_file(
        gdb_path,
        columns=["HYRIV_ID", "DIS_AV_CMS", "NEXT_DOWN"],
        where=f"DIS_AV_CMS > {threshold_cms:g}",
    )
    if rivers.crs is None or rivers.empty:
        raise ValueError("Filtered HydroRIVERS layer has no lines or CRS.")
    if rivers["HYRIV_ID"].duplicated().any() or not (rivers["DIS_AV_CMS"] > threshold_cms).all():
        raise ValueError("Filtered HydroRIVERS IDs or discharge values are invalid.")
    rivers = rivers.to_crs(4326)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="hydrorivers_viewer_", suffix=".json.gz", dir=output_path.parent, delete=False
    ) as handle:
        temp_path = Path(handle.name)
    try:
        with gzip.open(temp_path, "wt", encoding="utf-8", compresslevel=6) as output:
            output.write('{"threshold_cms":')
            output.write(json.dumps(threshold_cms))
            output.write(',"bounds":')
            output.write(json.dumps(rivers.total_bounds.tolist(), separators=(",", ":")))
            output.write(',"reaches":[')
            for index, row in enumerate(rivers.itertuples(index=False)):
                if index:
                    output.write(",")
                output.write(json.dumps(
                    [
                        int(row.HYRIV_ID), float(row.DIS_AV_CMS),
                        0 if pd.isna(row.NEXT_DOWN) else int(row.NEXT_DOWN),
                        geometry_lines(row.geometry),
                    ],
                    separators=(",", ":"),
                ))
            output.write("]}")
        if output_path.exists() and not overwrite:
            raise FileExistsError(output_path)
        os.replace(temp_path, output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return len(rivers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdb", type=Path, default=DEFAULT_GDB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--threshold-cms", type=float, default=20.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    count = build_overlay(args.gdb, args.output, args.threshold_cms, args.overwrite)
    print(f"Saved {count:,} reaches with DIS_AV_CMS > {args.threshold_cms:g} to {args.output}", flush=True)


if __name__ == "__main__":
    main()
