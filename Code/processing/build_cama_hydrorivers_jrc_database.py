"""Combine matched HydroRIVERS reaches, 2019 CaMa monthly flow, and JRC status."""

import argparse
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import geopandas as gpd
import numpy as np

from classify_china_rivers_perennial_status import classify_rivers


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root.")


ROOT = find_project_root(Path(__file__).resolve())
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
MATCH_STEM = "cama_2019_catchment_to_hyriv_as_coverage_5km_all_reaches_nearest"
MATCH_DIR = ROOT / "Output" / "CamaHydroRIVERSCatchmentMatch" / RUN_LABEL
DEFAULT_MATCH_DB = MATCH_DIR / f"{MATCH_STEM}.sqlite"
DEFAULT_REACH_GEOJSON = MATCH_DIR / f"{MATCH_STEM}_matched_reaches.geojson"
DEFAULT_CAMA_DB = ROOT / "Output" / "CamaMonthlyFlow" / "cama_2019_monthly_uparea_gt_10000km2.sqlite"
DEFAULT_JRC_DB = (
    ROOT / "Output" / "ChinaRiverPerennialStatus" / RUN_LABEL
    / "china_river_perennial_status_discharge_gt_50_connectivity_only_endpoint_7x7.sqlite"
)
DEFAULT_OUTPUT = ROOT / "Output" / "CamaHydroRIVERSIntegrated" / RUN_LABEL / "cama_2019_hyriv_jrc_integrated_nearest_endpoint_7x7.sqlite"


def existing_jrc_settings(jrc_db, expected_raster):
    with closing(sqlite3.connect(jrc_db)) as connection:
        metadata = {
            key: json.loads(value)
            for key, value in connection.execute("SELECT key, value FROM analysis_metadata")
        }
    required = ("flow_status", "buffer_m", "endpoint_radius_cells", "perennial_ratio_threshold", "require_perennial_ratio", "metric_crs", "min_component_cells")
    if any(key not in metadata for key in required):
        raise ValueError("Existing JRC database is missing classification settings.")
    if Path(metadata["flow_status"]).resolve() != expected_raster.resolve():
        raise ValueError("Existing JRC database uses a different raster.")
    if metadata["require_perennial_ratio"]:
        raise ValueError("Expected the connectivity-only JRC classification.")
    if metadata["endpoint_radius_cells"] != 3:
        raise ValueError("Expected 7x7 endpoint neighborhoods in the JRC classification.")
    return metadata


def classify_missing_reaches(reach_geojson, jrc_db, flow_status):
    settings = existing_jrc_settings(jrc_db, flow_status)
    rivers = gpd.read_file(reach_geojson)
    if rivers.crs is None or rivers["HYRIV_ID"].duplicated().any():
        raise ValueError("Matched reach GeoJSON needs a CRS and unique HYRIV_ID values.")
    with sqlite3.connect(jrc_db) as connection:
        existing_ids = {row[0] for row in connection.execute("SELECT hyriv_id FROM river_segments")}
    missing = rivers.loc[~rivers["HYRIV_ID"].isin(existing_ids)].copy()
    print(f"Reusing {len(rivers) - len(missing):,} JRC classifications; classifying {len(missing):,} new reaches", flush=True)
    if not missing.empty:
        missing = classify_rivers(
            rivers_region=missing.to_crs(4326),
            flow_status_path=flow_status,
            buffer_m=settings["buffer_m"],
            endpoint_radius_cells=settings["endpoint_radius_cells"],
            perennial_ratio_threshold=settings["perennial_ratio_threshold"],
            require_perennial_ratio=settings["require_perennial_ratio"],
            metric_crs=settings["metric_crs"],
            min_component_cells=settings["min_component_cells"],
        )
    return missing, settings, len(rivers)


def build_database(match_db, cama_db, jrc_db, classified_missing, metadata, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(output_path)
    with tempfile.NamedTemporaryFile(prefix="cama_hyriv_jrc_", suffix=".sqlite", dir=output_path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with closing(sqlite3.connect(temp_path)) as connection:
            connection.execute("ATTACH DATABASE ? AS matching", (str(match_db.resolve()),))
            connection.execute("ATTACH DATABASE ? AS cama", (str(cama_db.resolve()),))
            connection.execute("ATTACH DATABASE ? AS jrc", (str(jrc_db.resolve()),))
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE river_segments (
                    hyriv_id INTEGER PRIMARY KEY,
                    next_down INTEGER,
                    dis_av_cms REAL,
                    catchment_count INTEGER NOT NULL CHECK (catchment_count > 0),
                    intermittent_count INTEGER NOT NULL,
                    perennial_count INTEGER NOT NULL,
                    water_count INTEGER NOT NULL,
                    perennial_ratio REAL,
                    connected_perennial INTEGER NOT NULL,
                    ratio_rule_passed INTEGER NOT NULL,
                    jrc_status INTEGER CHECK (jrc_status IN (1, 2) OR jrc_status IS NULL),
                    jrc_label TEXT NOT NULL,
                    jrc_evidence TEXT NOT NULL,
                    jrc_source TEXT NOT NULL
                );
                CREATE TABLE catchments (
                    catchment_id INTEGER PRIMARY KEY,
                    hyriv_id INTEGER NOT NULL REFERENCES river_segments(hyriv_id),
                    downstream_id INTEGER NOT NULL,
                    basin_id INTEGER NOT NULL,
                    longitude REAL NOT NULL,
                    latitude REAL NOT NULL,
                    upstream_area_km2 REAL NOT NULL,
                    match_distance_m REAL,
                    match_status TEXT NOT NULL,
                    downstream_support INTEGER NOT NULL,
                    upstream_support INTEGER NOT NULL
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
                CREATE INDEX catchments_hyriv ON catchments(hyriv_id);
                CREATE INDEX river_segments_jrc_status ON river_segments(jrc_status);
                CREATE INDEX monthly_flow_stats_year_month ON monthly_flow_stats(year, month);
                CREATE VIEW reach_catchment_monthly_flow AS
                    SELECT r.hyriv_id, r.next_down AS hydro_next_down,
                           r.jrc_status, r.jrc_label, r.jrc_evidence,
                           r.dis_av_cms, r.catchment_count,
                           c.catchment_id, c.downstream_id, c.match_status, c.match_distance_m,
                           f.year, f.month, f.days_in_month, f.valid_days,
                           f.min_flow_cms, f.q25_flow_cms, f.median_flow_cms,
                           f.mean_flow_cms, f.q75_flow_cms, f.max_flow_cms,
                           f.mode_flow_cms, f.mode_frequency
                    FROM river_segments r
                    JOIN catchments c ON c.hyriv_id = r.hyriv_id
                    JOIN monthly_flow_stats f ON f.catchment_id = c.catchment_id;
                """
            )
            connection.execute(
                """INSERT INTO river_segments
                   SELECT m.hyriv_id, m.next_down, m.dis_av_cms, m.catchment_count,
                          j.intermittent_count, j.perennial_count, j.water_count,
                          j.perennial_ratio, j.connected_perennial, j.ratio_rule_passed,
                          CASE WHEN j.segment_label = 'Non-perennial_outside_raster' THEN NULL ELSE j.segment_status END,
                          j.segment_label,
                          CASE WHEN j.segment_label = 'Non-perennial_outside_raster' THEN 'outside_raster'
                               WHEN j.water_count = 0 THEN 'no_water_cells' ELSE 'water_cells' END,
                          'existing_jrc_db'
                   FROM matching.matched_reaches m
                   JOIN jrc.river_segments j ON j.hyriv_id = m.hyriv_id"""
            )
            connection.executemany(
                "INSERT INTO river_segments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        int(row.HYRIV_ID),
                        None if np.isnan(row.NEXT_DOWN) else int(row.NEXT_DOWN),
                        None if np.isnan(row.DIS_AV_CMS) else float(row.DIS_AV_CMS),
                        int(row.catchment_count),
                        int(row.intermittent_count), int(row.perennial_count), int(row.water_count),
                        None if np.isnan(row.perennial_ratio) else float(row.perennial_ratio),
                        int(row.connected_perennial), int(row.ratio_rule_passed),
                        None if row.segment_label == "Non-perennial_outside_raster" else int(row.segment_status),
                        row.segment_label,
                        "outside_raster" if row.segment_label == "Non-perennial_outside_raster" else "no_water_cells" if row.water_count == 0 else "water_cells",
                        "newly_classified",
                    )
                    for row in classified_missing.itertuples(index=False)
                ),
            )
            connection.execute(
                """INSERT INTO catchments
                   SELECT catchment_id, hyriv_id, downstream_id, basin_id,
                          longitude, latitude, upstream_area_km2, distance_m,
                          match_status, downstream_support, upstream_support
                   FROM matching.catchment_matches WHERE hyriv_id IS NOT NULL"""
            )
            connection.execute(
                """INSERT INTO monthly_flow_stats
                   SELECT f.* FROM cama.monthly_flow_stats f
                   JOIN catchments c ON c.catchment_id = f.catchment_id"""
            )
            connection.executemany(
                "INSERT INTO metadata VALUES (?, ?)",
                ((key, json.dumps(value, ensure_ascii=False)) for key, value in metadata.items()),
            )
            expected = connection.execute("SELECT COUNT(*) FROM matching.matched_reaches").fetchone()[0]
            reach_count = connection.execute("SELECT COUNT(*) FROM river_segments").fetchone()[0]
            point_count = connection.execute("SELECT COUNT(*) FROM catchments").fetchone()[0]
            monthly_count = connection.execute("SELECT COUNT(*) FROM monthly_flow_stats").fetchone()[0]
            if reach_count != expected or point_count != connection.execute("SELECT COUNT(*) FROM matching.catchment_matches WHERE hyriv_id IS NOT NULL").fetchone()[0]:
                raise RuntimeError("Integrated reach or catchment counts do not match the source.")
            if monthly_count != point_count * 12:
                raise RuntimeError("Some matched catchments lack 12 monthly flow records.")
            mismatched_counts = connection.execute(
                """SELECT COUNT(*) FROM river_segments r WHERE r.catchment_count !=
                   (SELECT COUNT(*) FROM catchments c WHERE c.hyriv_id = r.hyriv_id)"""
            ).fetchone()[0]
            if mismatched_counts:
                raise RuntimeError("Stored reach catchment counts do not match the linked catchments.")
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Integrated SQLite integrity or foreign key check failed.")
            summary = {
                "river_segments": reach_count,
                "catchments": point_count,
                "monthly_flow_rows": monthly_count,
                "jrc_status_counts": dict(connection.execute("SELECT COALESCE(CAST(jrc_status AS TEXT), 'unknown'), COUNT(*) FROM river_segments GROUP BY jrc_status")),
                "jrc_evidence_counts": dict(connection.execute("SELECT jrc_evidence, COUNT(*) FROM river_segments GROUP BY jrc_evidence")),
            }
            connection.commit()
        if output_path.exists():
            raise FileExistsError(output_path)
        os.replace(temp_path, output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-db", type=Path, default=DEFAULT_MATCH_DB)
    parser.add_argument("--reach-geojson", type=Path, default=DEFAULT_REACH_GEOJSON)
    parser.add_argument("--cama-db", type=Path, default=DEFAULT_CAMA_DB)
    parser.add_argument("--jrc-db", type=Path, default=DEFAULT_JRC_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    with sqlite3.connect(args.jrc_db) as connection:
        flow_status = Path(json.loads(connection.execute("SELECT value FROM analysis_metadata WHERE key = 'flow_status'").fetchone()[0]))
    classified_missing, settings, reach_count = classify_missing_reaches(args.reach_geojson, args.jrc_db, flow_status)
    metadata = {
        "match_db": str(args.match_db.resolve()),
        "cama_db": str(args.cama_db.resolve()),
        "jrc_db": str(args.jrc_db.resolve()),
        "jrc_raster": str(flow_status.resolve()),
        "jrc_settings": {key: settings[key] for key in ("buffer_m", "endpoint_radius_cells", "perennial_ratio_threshold", "require_perennial_ratio", "metric_crs", "min_component_cells")},
        "reach_geojson": str(args.reach_geojson.resolve()),
        "selected_reach_count": reach_count,
        "newly_classified_reaches": len(classified_missing),
        "interpretation": "2019 CaMa monthly discharge is compared with a multi-year JRC status mosaic; reach connectivity uses 7x7 endpoint neighborhoods; CaMa points use nearest HydroRIVERS reach within the search radius, with close-tie flags retained; no-water and outside-raster evidence are flagged separately; match IDs remain provisional",
    }
    summary = build_database(args.match_db, args.cama_db, args.jrc_db, classified_missing, metadata, args.output)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
