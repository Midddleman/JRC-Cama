"""Smoke tests for the local integrated-data viewer."""

import gzip
import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "visualization" / "cama_hyriv_viewer"))
from app import app


class ViewerTests(unittest.TestCase):
    def test_map_and_reach_detail_share_the_integrated_database(self):
        client = app.test_client()
        overview = client.get("/api/overview")
        self.assertEqual(overview.status_code, 200)
        data = overview.get_json()
        self.assertGreater(len(data["reaches"]), 0)
        self.assertGreater(len(data["points"]), 0)
        reach_status = {row["hyriv_id"]: row for row in data["reaches"]}
        self.assertTrue(all(
            point["jrc_status"] == reach_status[point["hyriv_id"]]["jrc_status"]
            and point["jrc_evidence"] == reach_status[point["hyriv_id"]]["jrc_evidence"]
            for point in data["points"]
        ))

        network_response = client.get("/api/network")
        self.assertEqual(network_response.status_code, 200)
        self.assertEqual(network_response.headers["Content-Encoding"], "gzip")
        network = json.loads(gzip.decompress(network_response.data))
        self.assertEqual(network["threshold_cms"], 20)
        self.assertEqual(len(network["reaches"]), 113648)
        self.assertTrue(all(row[1] > 20 for row in network["reaches"]))
        self.assertTrue(all(len(row) == 4 for row in network["reaches"]))

        reach_id = data["reaches"][0]["hyriv_id"]
        detail = client.get(f"/api/reach/{reach_id}")
        self.assertEqual(detail.status_code, 200)
        payload = detail.get_json()
        self.assertEqual(payload["reach"]["catchment_count"], len(payload["catchments"]))
        self.assertEqual(len(payload["months"]), 12 * len(payload["catchments"]))

        csv_response = client.get(f"/api/reach/{reach_id}/csv")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("downstream_id", csv_response.data.decode("utf-8-sig").splitlines()[0])
        self.assertEqual(client.get("/api/reach/1").status_code, 404)
        self.assertIn("River Reaches &amp; Flow", client.get("/").data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
