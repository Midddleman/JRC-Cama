"""Checks for direct CaMa-to-JRC corridor classification."""

import sys
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from rasterio.transform import array_bounds, from_origin, xy
from rasterio.coords import BoundingBox


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from build_cama_jrc_link_database import classify_link, populate_channel_geometry


class CorridorTests(unittest.TestCase):
    def setUp(self):
        self.transform = from_origin(100, 30.33, 0.00825, 0.00825)
        west, south, east, north = array_bounds(40, 40, self.transform)
        self.bounds = BoundingBox(west, south, east, north)
        self.raster = np.zeros((40, 40), dtype=np.uint8)
        self.start = xy(self.transform, 20, 5)
        self.end = xy(self.transform, 20, 20)

    def classify(self, end=None):
        return classify_link(self.start, end or self.end, self.raster, self.transform, self.bounds, 5000)

    def test_blue_path_across_corridor_is_perennial(self):
        self.raster[20, 5:21] = 2
        result = self.classify()
        self.assertEqual(result["status"], 2)
        self.assertEqual(result["label"], "perennial_connected")
        self.assertEqual(result["perennial_count"], 16)
        self.assertIsNotNone(result["corridor"])

    def test_blue_gap_cannot_be_bridged_by_orange(self):
        self.raster[20, 5:21] = 2
        self.raster[20, 12] = 1
        result = self.classify()
        self.assertEqual(result["status"], 1)
        self.assertEqual(result["label"], "nonperennial_no_connected_path")

    def test_parallel_blue_path_outside_corridor_is_ignored(self):
        self.raster[30, 5:21] = 2
        result = self.classify()
        self.assertEqual(result["status"], 1)
        self.assertEqual(result["perennial_count"], 0)

    def test_short_link_is_unknown(self):
        self.raster[20, 5:7] = 2
        result = self.classify(xy(self.transform, 20, 6))
        self.assertIsNone(result["status"])
        self.assertEqual(result["label"], "unresolved_below_raster_resolution")


class ChannelGeometryTests(unittest.TestCase):
    def test_parameters_join_by_catchment_id_and_missing_values_stay_null(self):
        class FakeDataset:
            variables = {
                name: np.asarray(values) for name, values in {
                    "catchment_id": [30, 10, 20],
                    "river_width": [300, 100, 200],
                    "river_height": [3, 1, 0],
                    "river_length": [3000, 1000, 2000],
                }.items()
            }

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        with patch("build_cama_jrc_link_database.Dataset", return_value=FakeDataset()):
            with sqlite3.connect(":memory:") as connection:
                connection.execute("CREATE TABLE catchment_links (catchment_id INTEGER PRIMARY KEY)")
                connection.executemany("INSERT INTO catchment_links VALUES (?)", [(10,), (20,)])
                self.assertEqual(populate_channel_geometry(connection, "unused.nc", [20, 10]), 2)
                rows = connection.execute(
                    "SELECT catchment_id, river_width_m, river_height_m, river_length_m "
                    "FROM channel_geometry ORDER BY catchment_id"
                ).fetchall()
                self.assertEqual(rows, [(10, 100, 1, 1000), (20, 200, None, 2000)])


if __name__ == "__main__":
    unittest.main()
