"""Store 2019 monthly CaMa-Flood flow statistics for selected catchments."""

import argparse
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
RUN_LABEL = "water_ratio_0.40_min_conn_50_perennial_10_perennial_ratio_0.50"
DEFAULT_SELECTION = (
    PROJECT_ROOT
    / "Output"
    / "CamaFlowStatusMatch"
    / RUN_LABEL
    / "cama_flow_status_match_uparea_10000km2.csv"
)
DEFAULT_PARAMETERS = PROJECT_ROOT / "Data" / "Cama-Flood output" / "parameters_glb06.nc"
DEFAULT_FLOW = (
    PROJECT_ROOT
    / "Data"
    / "Cama-Flood output"
    / "glb_06min_VICBC_daily"
    / "river_outflow_mean_rank0_2019.nc"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "Output" / "CamaMonthlyFlow" / "cama_2019_monthly_uparea_gt_10000km2.sqlite"


def monthly_statistics(values):
    valid = np.asarray(values, dtype=np.float64)
    valid = valid[np.isfinite(valid)]
    if len(valid) == 0:
        return (0, None, None, None, None, None, None, None, 0)

    q25, median, q75 = np.quantile(valid, [0.25, 0.5, 0.75])
    rounded_daily = np.round(valid, 3)
    unique, counts = np.unique(rounded_daily, return_counts=True)
    top_count = int(counts.max())
    modes = unique[counts == top_count]
    mode = float(modes[0]) if top_count > 1 and len(modes) == 1 else None
    return (
        len(valid),
        float(np.round(np.min(valid), 3)),
        float(np.round(q25, 3)),
        float(np.round(median, 3)),
        float(np.round(np.mean(valid), 3)),
        float(np.round(q75, 3)),
        float(np.round(np.max(valid), 3)),
        mode,
        top_count,
    )


def load_selection(selection_path, parameters_path, flow_ids, min_upstream_area_km2, max_points):
    columns = ["catchment_id", "downstream_id", "basin_id", "longitude", "latitude", "upstream_area"]
    selected = pd.read_csv(selection_path, usecols=columns)
    if selected["catchment_id"].duplicated().any():
        raise ValueError("Selection CSV contains duplicate catchment_id values.")

    with Dataset(parameters_path) as parameters:
        parameter_ids = np.asarray(parameters.variables["catchment_id"][:], dtype=np.int64)
        parameter_positions = pd.Index(parameter_ids).get_indexer(selected["catchment_id"])
        if np.any(parameter_positions < 0):
            raise ValueError("Some selected catchments are missing from the parameter file.")
        parameter_areas = np.asarray(parameters.variables["upstream_area"][:], dtype=np.float64)
        selected = selected.loc[
            parameter_areas[parameter_positions] > min_upstream_area_km2 * 1_000_000.0
        ].copy()

    if max_points is not None:
        selected = selected.head(max_points).copy()
    if selected.empty:
        raise ValueError("No catchments remain after the upstream-area filter.")

    selected["upstream_area_km2"] = selected["upstream_area"] / 1_000_000.0
    flow_positions = pd.Index(flow_ids).get_indexer(selected["catchment_id"])
    if np.any(flow_positions < 0):
        raise ValueError("Some selected catchments are missing from the flow file.")
    selected["flow_position"] = flow_positions
    return selected.sort_values("flow_position").reset_index(drop=True)


def create_schema(connection):
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE catchments (
            catchment_id INTEGER PRIMARY KEY,
            downstream_id INTEGER NOT NULL,
            basin_id INTEGER NOT NULL,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL,
            upstream_area_km2 REAL NOT NULL
        );
        CREATE TABLE monthly_flow_stats (
            catchment_id INTEGER NOT NULL REFERENCES catchments(catchment_id),
            year INTEGER NOT NULL,
            month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
            days_in_month INTEGER NOT NULL,
            valid_days INTEGER NOT NULL,
            min_flow_cms REAL,
            q25_flow_cms REAL,
            median_flow_cms REAL,
            mean_flow_cms REAL,
            q75_flow_cms REAL,
            max_flow_cms REAL,
            mode_flow_cms REAL,
            mode_frequency INTEGER NOT NULL,
            PRIMARY KEY (catchment_id, year, month)
        );
        CREATE INDEX monthly_flow_stats_year_month ON monthly_flow_stats(year, month);
        """
    )


def build_database(flow_path, parameters_path, selection_path, output_path, min_upstream_area_km2, batch_size, max_points):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")
    if output_path.exists():
        raise FileExistsError(f"Output already exists: {output_path}")

    with Dataset(flow_path) as source:
        flow = source.variables["river_outflow_mean"]
        flow_ids = np.asarray(source.variables["catchment_save_id"][:], dtype=np.int64)
        time = source.variables["time"]
        dates = num2date(time[:], units=time.units, calendar=getattr(time, "calendar", "standard"))
        if len(dates) != 365 or any(date.year != 2019 for date in dates):
            raise ValueError("Expected 365 daily observations from 2019.")
        if len({(date.year, date.month, date.day) for date in dates}) != 365:
            raise ValueError("2019 time axis contains duplicate dates.")
        month_indices = {month: np.flatnonzero([date.month == month for date in dates]) for month in range(1, 13)}
        selected = load_selection(selection_path, parameters_path, flow_ids, min_upstream_area_km2, max_points)
        positions = selected["flow_position"].to_numpy(dtype=np.int64)

        # The NC variable is chunked one full day per block, so scan days once.
        selected_daily_flow = np.empty((len(dates), len(selected)), dtype=np.float32)
        for day in range(len(dates)):
            daily_flow = np.ma.filled(flow[day, :], np.nan)
            selected_daily_flow[day, :] = daily_flow[positions]
            if (day + 1) % 60 == 0 or day + 1 == len(dates):
                print(f"Read {day + 1}/{len(dates)} daily records", flush=True)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="cama_monthly_", suffix=".sqlite", dir=output_path.parent, delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            with closing(sqlite3.connect(temp_path)) as connection, connection:
                create_schema(connection)
                connection.executemany(
                    "INSERT INTO metadata VALUES (?, ?)",
                    [
                        ("flow_file", str(flow_path.resolve())),
                        ("selection_file", str(selection_path.resolve())),
                        ("parameters_file", str(parameters_path.resolve())),
                        ("flow_variable", "river_outflow_mean"),
                        ("flow_units", "m3/s (from variable description)"),
                        ("year", "2019"),
                        ("min_upstream_area_km2_exclusive", str(min_upstream_area_km2)),
                        ("statistic_rounding", "Monthly statistics computed from raw daily flow, then rounded to 3 decimals"),
                        ("mode_rule", "Daily flow rounded to 3 decimals first; unique most-frequent value repeated at least twice, otherwise NULL"),
                    ],
                )
                connection.executemany(
                    "INSERT INTO catchments VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        (
                            int(row.catchment_id),
                            int(row.downstream_id),
                            int(row.basin_id),
                            float(row.longitude),
                            float(row.latitude),
                            float(row.upstream_area_km2),
                        )
                        for row in selected.itertuples(index=False)
                    ),
                )

                for start in range(0, len(selected), batch_size):
                    batch = selected.iloc[start : start + batch_size]
                    values = selected_daily_flow[:, start : start + len(batch)]
                    rows = []
                    for column, catchment_id in enumerate(batch["catchment_id"]):
                        for month, indices in month_indices.items():
                            stats = monthly_statistics(values[indices, column])
                            rows.append((int(catchment_id), 2019, month, len(indices), *stats))
                    connection.executemany(
                        "INSERT INTO monthly_flow_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        rows,
                    )
                    print(f"Processed {min(start + batch_size, len(selected)):,}/{len(selected):,} catchments", flush=True)

            if output_path.exists():
                raise FileExistsError(f"Output appeared while building: {output_path}")
            os.replace(temp_path, output_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    return len(selected)


def main():
    parser = argparse.ArgumentParser(description="Build a SQLite database of 2019 monthly CaMa-Flood flow statistics.")
    parser.add_argument("--flow", type=Path, default=DEFAULT_FLOW)
    parser.add_argument("--parameters", type=Path, default=DEFAULT_PARAMETERS)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-upstream-area-km2", type=float, default=10000.0)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--max-points", type=int, default=None)
    args = parser.parse_args()

    count = build_database(
        args.flow, args.parameters, args.selection, args.output,
        args.min_upstream_area_km2, args.batch_size, args.max_points,
    )
    print(f"Saved {count:,} catchments and {count * 12:,} monthly rows to {args.output}")


if __name__ == "__main__":
    main()
