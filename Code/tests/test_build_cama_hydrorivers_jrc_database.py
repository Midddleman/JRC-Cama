"""Focused tests for the integrated reach, catchment, and monthly-flow database."""

import json
import sqlite3
import sys
import unittest
from contextlib import ExitStack, closing
from pathlib import Path
from uuid import uuid4

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from build_cama_hydrorivers_jrc_database import DEFAULT_OUTPUT, build_database, existing_jrc_settings


class IntegratedDatabaseTests(unittest.TestCase):
    def test_rejects_old_endpoint_radius(self):
        path = DEFAULT_OUTPUT.parent / f"test_{uuid4().hex}_old_jrc.sqlite"
        raster = DEFAULT_OUTPUT.parent / "test_flow_status.tif"
        try:
            with closing(sqlite3.connect(path)) as connection, connection:
                connection.execute("CREATE TABLE analysis_metadata (key TEXT PRIMARY KEY, value TEXT)")
                settings = {
                    "flow_status": str(raster), "buffer_m": 5000,
                    "endpoint_radius_cells": 5, "perennial_ratio_threshold": 0.5,
                    "require_perennial_ratio": False, "metric_crs": "EPSG:3857",
                    "min_component_cells": 2,
                }
                connection.executemany(
                    "INSERT INTO analysis_metadata VALUES (?, ?)",
                    ((key, json.dumps(value)) for key, value in settings.items()),
                )
            with self.assertRaisesRegex(ValueError, "7x7"):
                existing_jrc_settings(path, raster)
        finally:
            path.unlink(missing_ok=True)

    def test_existing_and_new_jrc_reaches_keep_their_catchment_months(self):
        with ExitStack() as stack:
            root = DEFAULT_OUTPUT.parent
            stem = uuid4().hex
            match_db, cama_db, jrc_db, output = (
                root / f"test_{stem}_{name}.sqlite"
                for name in ("match", "cama", "jrc", "integrated")
            )
            for path in (match_db, cama_db, jrc_db, output):
                stack.callback(path.unlink, missing_ok=True)
            with closing(sqlite3.connect(match_db)) as connection, connection:
                connection.executescript(
                    """
                    CREATE TABLE matched_reaches (
                        hyriv_id INTEGER, next_down INTEGER, dis_av_cms REAL, catchment_count INTEGER
                    );
                    CREATE TABLE catchment_matches (
                        catchment_id INTEGER, hyriv_id INTEGER, downstream_id INTEGER,
                        basin_id INTEGER, longitude REAL, latitude REAL, upstream_area_km2 REAL,
                        distance_m REAL, match_status TEXT, downstream_support INTEGER, upstream_support INTEGER
                    );
                    INSERT INTO matched_reaches VALUES (10, 0, 60.0, 1), (20, 0, 2.0, 1);
                    INSERT INTO catchment_matches VALUES
                        (101, 10, 0, 1, 100.0, 30.0, 11000.0, 50.0, 'candidate', 0, 0),
                        (102, 20, 0, 1, 101.0, 30.0, 12000.0, 60.0, 'ambiguous', 0, 0);
                    """
                )
            with closing(sqlite3.connect(cama_db)) as connection, connection:
                connection.execute(
                    """CREATE TABLE monthly_flow_stats (
                        catchment_id INTEGER, year INTEGER, month INTEGER, days_in_month INTEGER,
                        valid_days INTEGER, min_flow_cms REAL, q25_flow_cms REAL,
                        median_flow_cms REAL, mean_flow_cms REAL, q75_flow_cms REAL,
                        max_flow_cms REAL, mode_flow_cms REAL, mode_frequency INTEGER
                    )"""
                )
                connection.executemany(
                    "INSERT INTO monthly_flow_stats VALUES (?, 2019, ?, 30, 30, 1, 2, 3, 4, 5, 6, 7, 2)",
                    ((catchment_id, month) for catchment_id in (101, 102) for month in range(1, 13)),
                )
            with closing(sqlite3.connect(jrc_db)) as connection, connection:
                connection.executescript(
                    """
                    CREATE TABLE river_segments (
                        hyriv_id INTEGER, intermittent_count INTEGER, perennial_count INTEGER,
                        water_count INTEGER, perennial_ratio REAL, connected_perennial INTEGER,
                        ratio_rule_passed INTEGER, segment_status INTEGER, segment_label TEXT
                    );
                    INSERT INTO river_segments VALUES
                        (10, 1, 9, 10, 0.9, 1, 1, 2, 'Perennial_connected');
                    """
                )
            new_reaches = pd.DataFrame([{
                "HYRIV_ID": 20, "NEXT_DOWN": 0, "DIS_AV_CMS": 2.0,
                "catchment_count": 1, "intermittent_count": 0,
                "perennial_count": 0, "water_count": 0,
                "perennial_ratio": float("nan"), "connected_perennial": False,
                "ratio_rule_passed": False, "segment_status": 1,
                "segment_label": "Non-perennial_no_water",
            }])
            summary = build_database(match_db, cama_db, jrc_db, new_reaches, {}, output)
            self.assertEqual((summary["river_segments"], summary["catchments"], summary["monthly_flow_rows"]), (2, 2, 24))
            with closing(sqlite3.connect(output)) as connection:
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(
                    connection.execute(
                        "SELECT hyriv_id, jrc_status, jrc_evidence FROM river_segments ORDER BY hyriv_id"
                    ).fetchall(),
                    [(10, 2, "water_cells"), (20, 1, "no_water_cells")],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT catchment_id, COUNT(*) FROM reach_catchment_monthly_flow GROUP BY catchment_id ORDER BY catchment_id"
                    ).fetchall(),
                    [(101, 12), (102, 12)],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT hydro_next_down, downstream_id FROM reach_catchment_monthly_flow WHERE catchment_id = 101 LIMIT 1"
                    ).fetchone(),
                    (0, 0),
                )


if __name__ == "__main__":
    unittest.main()
