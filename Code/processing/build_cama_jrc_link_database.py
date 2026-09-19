"""Classify CaMa downstream links directly against the aggregated JRC raster."""

import argparse
import json
import math
import os
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio
from netCDF4 import Dataset
from pyproj import Transformer
from rasterio.windows import from_bounds
from scipy.ndimage import label


ROOT = Path(__file__).resolve().parents[2]
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
DEFAULT_CAMA_DB = ROOT / "Output" / "CamaMonthlyFlow" / "cama_2019_monthly_uparea_gt_10000km2.sqlite"
DEFAULT_PARAMETERS = ROOT / "Data" / "Cama-Flood output" / "parameters_glb06.nc"
DEFAULT_JRC_RASTER = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.tif"
DEFAULT_OUTPUT = ROOT / "Output" / "CamaJRCDownstreamLinks" / RUN_LABEL / "cama_2019_jrc_links_corridor_5km.sqlite"
EIGHT_CONNECTED = np.ones((3, 3), dtype=np.uint8)


@lru_cache(maxsize=60)
def local_transformers(zone):
    metric_crs = f"EPSG:{32600 + zone}"
    return (
        Transformer.from_crs(4326, metric_crs, always_xy=True),
        Transformer.from_crs(metric_crs, 4326, always_xy=True),
    )


def load_catchments(cama_db):
    with closing(sqlite3.connect(cama_db)) as connection:
        connection.row_factory = sqlite3.Row
        points = [dict(row) for row in connection.execute(
            "SELECT catchment_id, downstream_id, basin_id, longitude, latitude, "
            "upstream_area_km2 FROM catchments ORDER BY catchment_id"
        )]
    if len({row["catchment_id"] for row in points}) != len(points):
        raise ValueError("Duplicate CaMa catchment IDs.")
    return points


def downstream_locations(points, parameter_path):
    locations = {row["catchment_id"]: (row["longitude"], row["latitude"]) for row in points}
    missing = sorted({row["downstream_id"] for row in points if row["downstream_id"] not in locations})
    if not missing:
        return locations
    with Dataset(parameter_path) as source:
        ids = np.asarray(source.variables["catchment_id"][:], dtype=np.int64)
        order = np.argsort(ids)
        sorted_ids = ids[order]
        positions = np.searchsorted(sorted_ids, missing)
        valid = positions < len(sorted_ids)
        valid[valid] &= sorted_ids[positions[valid]] == np.asarray(missing)[valid]
        longitude = np.asarray(source.variables["longitude"][:], dtype=float)
        latitude = np.asarray(source.variables["latitude"][:], dtype=float)
        for downstream_id, position, found in zip(missing, positions, valid):
            if found:
                index = order[position]
                locations[downstream_id] = (float(longitude[index]), float(latitude[index]))
    return locations


def populate_channel_geometry(connection, parameter_path, catchment_ids):
    """Copy per-catchment channel parameters without changing JRC classifications."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS channel_geometry (
            catchment_id INTEGER PRIMARY KEY REFERENCES catchment_links(catchment_id),
            river_width_m REAL,
            river_height_m REAL,
            river_length_m REAL
        )
    """)
    wanted = np.asarray(sorted(catchment_ids), dtype=np.int64)
    with Dataset(parameter_path) as source:
        ids = np.asarray(source.variables["catchment_id"][:], dtype=np.int64)
        order = np.argsort(ids)
        positions = np.searchsorted(ids[order], wanted)
        if np.any(positions >= len(ids)) or np.any(ids[order[positions]] != wanted):
            raise ValueError("Some selected catchments are missing from the CaMa parameter file.")
        indices = order[positions]
        arrays = {}
        for name in ("river_width", "river_height", "river_length"):
            arrays[name] = np.asarray(np.ma.filled(source.variables[name][:], np.nan), dtype=float)[indices]

    def positive_or_none(value):
        return float(value) if np.isfinite(value) and value > 0 else None

    connection.executemany(
        "INSERT OR REPLACE INTO channel_geometry VALUES (?, ?, ?, ?)",
        ((int(catchment_id), *(positive_or_none(arrays[name][index]) for name in
          ("river_width", "river_height", "river_length")))
         for index, catchment_id in enumerate(wanted)),
    )
    return len(wanted)


def classify_link(start, end, raster, transform, bounds, half_width_m):
    lon0, lat0 = start
    lon1, lat1 = end
    if not all(np.isfinite(value) for value in (lon0, lat0, lon1, lat1)):
        return {"label": "unresolved_invalid_coordinates", "status": None, "corridor": None}

    zone = max(1, min(60, int((0.5 * (lon0 + lon1) + 180) // 6) + 1))
    to_metric, to_lonlat = local_transformers(zone)
    x0, y0 = to_metric.transform(lon0, lat0)
    x1, y1 = to_metric.transform(lon1, lat1)
    length_m = math.hypot(x1 - x0, y1 - y0)
    if length_m == 0:
        return {"label": "unresolved_zero_length", "status": None, "length_m": 0.0, "corridor": None}
    ux, uy = (x1 - x0) / length_m, (y1 - y0) / length_m
    px, py = -uy, ux
    corners_xy = [
        (x0 + px * half_width_m, y0 + py * half_width_m),
        (x1 + px * half_width_m, y1 + py * half_width_m),
        (x1 - px * half_width_m, y1 - py * half_width_m),
        (x0 - px * half_width_m, y0 - py * half_width_m),
    ]
    corridor = [list(to_lonlat.transform(x, y)) for x, y in corners_xy]
    result = {"length_m": length_m, "corridor": corridor, "status": None}

    res_lon = abs(transform.a)
    res_lat = abs(transform.e)
    xa, ya = to_metric.transform(0.5 * (lon0 + lon1) - res_lon / 2, 0.5 * (lat0 + lat1) - res_lat / 2)
    xb, yb = to_metric.transform(0.5 * (lon0 + lon1) + res_lon / 2, 0.5 * (lat0 + lat1) + res_lat / 2)
    cell_diagonal_m = math.hypot(xb - xa, yb - ya)
    result["endpoint_band_m"] = cell_diagonal_m
    if length_m <= 2 * cell_diagonal_m:
        return {**result, "label": "unresolved_below_raster_resolution"}

    if any(not (bounds.left <= lon < bounds.right and bounds.bottom < lat <= bounds.top)
           for lon, lat in [start, end, *corridor]):
        return {**result, "label": "unresolved_outside_raster"}

    lons, lats = zip(*corridor)
    window = from_bounds(min(lons), min(lats), max(lons), max(lats), transform=transform)
    col0 = max(0, math.floor(window.col_off) - 1)
    row0 = max(0, math.floor(window.row_off) - 1)
    col1 = min(raster.shape[1], math.ceil(window.col_off + window.width) + 1)
    row1 = min(raster.shape[0], math.ceil(window.row_off + window.height) + 1)
    if col1 <= col0 or row1 <= row0:
        return {**result, "label": "unresolved_no_sampled_cells"}

    rows, cols = np.mgrid[row0:row1, col0:col1]
    pixel_lon = transform.c + (cols + 0.5) * transform.a
    pixel_lat = transform.f + (rows + 0.5) * transform.e
    pixel_x, pixel_y = to_metric.transform(pixel_lon, pixel_lat)
    along = (pixel_x - x0) * ux + (pixel_y - y0) * uy
    across = -(pixel_x - x0) * uy + (pixel_y - y0) * ux
    in_corridor = (along >= 0) & (along <= length_m) & (np.abs(across) <= half_width_m)
    values = raster[row0:row1, col0:col1]
    valid = in_corridor & (values != 255)
    if not valid.any():
        return {**result, "label": "unresolved_no_valid_cells"}

    perennial = (values == 2) & in_corridor
    intermittent_count = int(np.count_nonzero((values == 1) & in_corridor))
    perennial_count = int(np.count_nonzero(perennial))
    start_band = in_corridor & (along <= cell_diagonal_m)
    end_band = in_corridor & (along >= length_m - cell_diagonal_m)
    if not start_band.any() or not end_band.any():
        return {**result, "label": "unresolved_no_endpoint_cells"}

    component, _ = label(perennial, structure=EIGHT_CONNECTED)
    start_ids = set(np.unique(component[start_band])) - {0}
    end_ids = set(np.unique(component[end_band])) - {0}
    connecting_ids = start_ids & end_ids
    connected = bool(connecting_ids)
    path_cells = max((int(np.count_nonzero(component == component_id)) for component_id in connecting_ids), default=0)
    return {
        **result,
        "status": 2 if connected else 1,
        "label": "perennial_connected" if connected else "nonperennial_no_water" if not (perennial_count + intermittent_count) else "nonperennial_no_connected_path",
        "sampled_cell_count": int(np.count_nonzero(in_corridor)),
        "valid_cell_count": int(np.count_nonzero(valid)),
        "perennial_count": perennial_count,
        "intermittent_count": intermittent_count,
        "connected_path_cells": path_cells,
    }


def build_database(cama_db, parameters, jrc_raster, output, half_width_m):
    if output.exists():
        raise FileExistsError(output)
    points = load_catchments(cama_db)
    locations = downstream_locations(points, parameters)
    selected_ids = {row["catchment_id"] for row in points}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="cama_jrc_links_", suffix=".sqlite", dir=output.parent, delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with rasterio.open(jrc_raster) as source:
            if source.crs.to_epsg() != 4326 or source.count != 1 or source.transform.b or source.transform.d:
                raise ValueError("Expected a north-up single-band EPSG:4326 JRC raster.")
            raster = source.read(1)
            transform = source.transform
            bounds = source.bounds
        with closing(sqlite3.connect(temp_path)) as connection:
            connection.execute("ATTACH DATABASE ? AS cama", (str(cama_db.resolve()),))
            connection.executescript("""
                PRAGMA foreign_keys = ON;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE catchment_links (
                    catchment_id INTEGER PRIMARY KEY,
                    downstream_id INTEGER NOT NULL,
                    basin_id INTEGER NOT NULL,
                    longitude REAL NOT NULL,
                    latitude REAL NOT NULL,
                    downstream_longitude REAL,
                    downstream_latitude REAL,
                    downstream_in_selection INTEGER NOT NULL,
                    upstream_area_km2 REAL NOT NULL,
                    link_length_m REAL,
                    corridor_json TEXT,
                    endpoint_band_m REAL,
                    jrc_status INTEGER CHECK (jrc_status IN (1, 2) OR jrc_status IS NULL),
                    jrc_label TEXT NOT NULL,
                    sampled_cell_count INTEGER,
                    valid_cell_count INTEGER,
                    perennial_count INTEGER,
                    intermittent_count INTEGER,
                    connected_path_cells INTEGER
                );
                CREATE TABLE monthly_flow_stats (
                    catchment_id INTEGER NOT NULL REFERENCES catchment_links(catchment_id),
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
                CREATE INDEX idx_links_status ON catchment_links(jrc_status);
                CREATE INDEX idx_links_downstream ON catchment_links(downstream_id);
                CREATE VIEW catchment_link_monthly_flow AS
                    SELECT l.*, f.year, f.month, f.days_in_month, f.valid_days,
                           f.min_flow_cms, f.q25_flow_cms, f.median_flow_cms,
                           f.mean_flow_cms, f.q75_flow_cms, f.max_flow_cms,
                           f.mode_flow_cms, f.mode_frequency
                    FROM catchment_links l JOIN monthly_flow_stats f USING(catchment_id);
            """)
            metadata = {
                "cama_db": str(cama_db.resolve()),
                "parameters_nc": str(parameters.resolve()),
                "jrc_raster": str(jrc_raster.resolve()),
                "corridor_half_width_m": half_width_m,
                "corridor_geometry": "flat-ended UTM rectangle between CaMa catchment and immediate downstream coordinates",
                "raster_rule": "pixel center inside corridor; eight-connected JRC perennial cells touch nonoverlapping one-pixel-diagonal endpoint bands",
                "unresolved_rule": "links too short for separate endpoint bands, outside raster, or without valid endpoint cells remain unknown",
                "temporal_note": "JRC 1984-2021 long-term seasonality compared with CaMa 2019 monthly flow",
                "channel_geometry_source": str(parameters.resolve()),
                "channel_geometry_note": "CaMa static river_width, river_height, and river_length; rectangle schematic is not a surveyed cross-section or daily water level",
            }
            connection.executemany("INSERT INTO metadata VALUES (?, ?)", ((key, json.dumps(value)) for key, value in metadata.items()))
            counts = Counter()
            rows = []
            for index, point in enumerate(points, start=1):
                target = locations.get(point["downstream_id"])
                if target is None:
                    result = {"label": "unresolved_missing_downstream", "status": None, "corridor": None}
                else:
                    result = classify_link(
                        (point["longitude"], point["latitude"]), target,
                        raster, transform, bounds, half_width_m,
                    )
                counts[result["label"]] += 1
                rows.append((
                    point["catchment_id"], point["downstream_id"], point["basin_id"],
                    point["longitude"], point["latitude"],
                    None if target is None else target[0], None if target is None else target[1],
                    int(point["downstream_id"] in selected_ids), point["upstream_area_km2"],
                    result.get("length_m"), json.dumps(result["corridor"]) if result.get("corridor") else None,
                    result.get("endpoint_band_m"), result["status"], result["label"],
                    result.get("sampled_cell_count"), result.get("valid_cell_count"),
                    result.get("perennial_count"), result.get("intermittent_count"),
                    result.get("connected_path_cells"),
                ))
                if len(rows) >= 1000:
                    connection.executemany("INSERT INTO catchment_links VALUES (" + ",".join("?" * 19) + ")", rows)
                    rows.clear()
                if index % 2000 == 0:
                    print(f"Classified {index:,}/{len(points):,} CaMa downstream links", flush=True)
            if rows:
                connection.executemany("INSERT INTO catchment_links VALUES (" + ",".join("?" * 19) + ")", rows)
            populate_channel_geometry(connection, parameters, selected_ids)
            connection.execute("INSERT INTO monthly_flow_stats SELECT * FROM cama.monthly_flow_stats")
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("SQLite integrity check failed.")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("SQLite foreign key check failed.")
            if connection.execute("SELECT COUNT(*) FROM monthly_flow_stats").fetchone()[0] != len(points) * 12:
                raise RuntimeError("Monthly flow records are missing.")
        os.replace(temp_path, output)
        return {"catchments": len(points), "monthly_flow_rows": len(points) * 12, "label_counts": dict(counts), "settings": metadata}
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cama-db", type=Path, default=DEFAULT_CAMA_DB)
    parser.add_argument("--parameters", type=Path, default=DEFAULT_PARAMETERS)
    parser.add_argument("--jrc-raster", type=Path, default=DEFAULT_JRC_RASTER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--half-width-km", type=float, default=5.0)
    parser.add_argument("--add-channel-geometry", action="store_true",
                        help="Add CaMa channel geometry to an existing direct-link database without reclassifying JRC.")
    args = parser.parse_args()
    if args.add_channel_geometry:
        with closing(sqlite3.connect(args.output)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            catchment_ids = [row[0] for row in connection.execute("SELECT catchment_id FROM catchment_links")]
            count = populate_channel_geometry(connection, args.parameters, catchment_ids)
            connection.execute(
                "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                ("channel_geometry_source", json.dumps(str(args.parameters.resolve()))),
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                ("channel_geometry_note", json.dumps(
                    "CaMa static river_width, river_height, and river_length; rectangle schematic is not a surveyed cross-section or daily water level"
                )),
            )
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Channel geometry foreign-key check failed.")
            connection.commit()
        print(f"Added channel geometry for {count:,} catchments to {args.output}")
        return
    if args.half_width_km <= 0:
        parser.error("Corridor half-width must be positive.")
    summary = build_database(args.cama_db, args.parameters, args.jrc_raster, args.output, args.half_width_km * 1000)
    summary_path = args.output.with_name(args.output.stem + "_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
