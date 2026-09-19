"""Focused checks for HydroRIVERS endpoint-connectivity classification."""

import sys
import unittest
from pathlib import Path

import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import LineString


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from classify_china_rivers_perennial_status import has_perennial_connection_from_start_to_end


class EndpointConnectivityTests(unittest.TestCase):
    def test_seven_by_seven_rejects_overlap_only_component(self):
        status = np.zeros((21, 21), dtype=np.uint8)
        status[10, 9:11] = 2
        line = LineString([(5.5, 10.5), (13.5, 10.5)])
        transform = from_origin(0, 21, 1, 1)
        mask = np.ones_like(status, dtype=bool)

        self.assertTrue(has_perennial_connection_from_start_to_end(line, status, mask, transform, 5))
        self.assertFalse(has_perennial_connection_from_start_to_end(line, status, mask, transform, 3))

    def test_seven_by_seven_keeps_a_genuine_endpoint_connection(self):
        status = np.zeros((21, 21), dtype=np.uint8)
        status[10, 5:14] = 2
        line = LineString([(5.5, 10.5), (13.5, 10.5)])
        transform = from_origin(0, 21, 1, 1)

        self.assertTrue(has_perennial_connection_from_start_to_end(
            line, status, np.ones_like(status, dtype=bool), transform, 3
        ))


if __name__ == "__main__":
    unittest.main()
