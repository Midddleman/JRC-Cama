"""Focused tests for provisional CaMa-to-HydroRIVERS matching."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from match_cama_catchments_to_hydrorivers import (
    choose_matches,
    choose_nearest_matches,
    make_reachability,
    point_candidates,
    screen_as_coverage,
)


class CatchmentMatchTests(unittest.TestCase):
    def test_low_discharge_reach_is_still_a_candidate(self):
        points = pd.DataFrame(
            [(1, 100.01, 30.0005)],
            columns=["catchment_id", "longitude", "latitude"],
        )
        rivers = gpd.GeoDataFrame(
            {"HYRIV_ID": [10], "DIS_AV_CMS": [2.0]},
            geometry=[LineString([(100.0, 30.0), (100.02, 30.0)])],
            crs="EPSG:4326",
        )
        self.assertEqual(point_candidates(points, rivers, 20.0, 3)[1][0][0], 10)

    def test_as_coverage_uses_lines_not_a_latitude_cutoff(self):
        points = pd.DataFrame(
            [(1, 100.01, 60.0005), (2, 100.01, 59.0)],
            columns=["catchment_id", "longitude", "latitude"],
        )
        rivers = gpd.GeoDataFrame(
            {"HYRIV_ID": [10]},
            geometry=[LineString([(100.0, 60.0), (100.02, 60.0)])],
            crs="EPSG:4326",
        )
        coverage = screen_as_coverage(points, rivers, 5.0)
        self.assertTrue(coverage.loc[0, "in_as_network"])
        self.assertFalse(coverage.loc[1, "in_as_network"])
        self.assertEqual(coverage.loc[0, "nearest_as_hyriv_id"], 10)

    def test_topology_resolves_a_close_tie(self):
        points = pd.DataFrame(
            [(1, 2), (2, 0)],
            columns=["catchment_id", "downstream_id"],
        )
        candidates = {
            1: [(11, 100.0), (10, 110.0)],
            2: [(20, 100.0)],
        }
        matches = choose_matches(points, candidates, {10: 20, 11: 0, 20: 0}, 2000, 1.25, 20)
        first = matches.set_index("catchment_id").loc[1]
        self.assertEqual(first.hyriv_id, 10)
        self.assertEqual(first.match_status, "topology_resolved")
        self.assertEqual(first.downstream_support, 1)

    def test_nearest_assignment_keeps_close_tie_flag(self):
        points = pd.DataFrame([(1, 2), (2, 0)], columns=["catchment_id", "downstream_id"])
        candidates = {1: [(11, 100.0), (10, 110.0)], 2: [(20, 100.0)]}
        matches = choose_nearest_matches(points, candidates, 2000, 1.25).set_index("catchment_id")
        self.assertEqual(matches.loc[1, "hyriv_id"], 11)
        self.assertEqual(matches.loc[1, "distance_m"], 100.0)
        self.assertEqual(matches.loc[1, "match_status"], "ambiguous")
        self.assertEqual(matches.loc[1, "downstream_support"], 0)

    def test_distance_ratio_prevents_overbroad_ambiguity(self):
        points = pd.DataFrame([(1, 0)], columns=["catchment_id", "downstream_id"])
        candidates = {1: [(10, 100.0), (11, 300.0)]}
        row = choose_matches(points, candidates, {}, 2000, 1.25, 20).iloc[0]
        self.assertEqual(row.hyriv_id, 10)
        self.assertEqual(row.match_status, "candidate")

    def test_unresolved_tie_and_no_candidate_are_explicit(self):
        points = pd.DataFrame([(1, 0), (2, 0)], columns=["catchment_id", "downstream_id"])
        candidates = {1: [(10, 100.0), (11, 105.0)], 2: []}
        matches = choose_matches(points, candidates, {}, 2000, 1.25, 20).set_index("catchment_id")
        self.assertEqual(matches.loc[1, "match_status"], "ambiguous")
        self.assertEqual(matches.loc[2, "match_status"], "no_candidate")
        self.assertTrue(pd.isna(matches.loc[2, "hyriv_id"]))

    def test_reachability_follows_multiple_unfiltered_reaches(self):
        reachable = make_reachability({10: 12, 12: 13, 13: 20, 20: 0}, 10)
        self.assertTrue(reachable(10, 20))
        self.assertFalse(reachable(20, 10))


if __name__ == "__main__":
    unittest.main()
