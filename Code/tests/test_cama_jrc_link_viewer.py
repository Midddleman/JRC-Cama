"""Smoke tests for the independent CaMa-to-JRC link viewer."""

import importlib.util
import unittest
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "visualization" / "cama_jrc_link_viewer" / "app.py"
spec = importlib.util.spec_from_file_location("cama_jrc_link_viewer_app", APP_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LinkViewerTests(unittest.TestCase):
    def test_overview_detail_months_and_export(self):
        client = module.app.test_client()
        self.assertEqual(client.get("/health").get_json(), {"database": True, "jrc": True})
        overview = client.get("/api/overview")
        self.assertEqual(overview.status_code, 200)
        links = overview.get_json()["links"]
        reference = overview.get_json()["channel_reference"]
        self.assertEqual(reference["catchment_id"], 5517354)
        self.assertAlmostEqual(reference["river_width_m"], 115.57238, places=4)
        self.assertAlmostEqual(reference["river_height_m"], 1.355064, places=5)
        self.assertEqual(len(links), 18741)
        self.assertEqual(sum(link["jrc_status"] == 2 for link in links), 8015)
        self.assertEqual(sum(link["jrc_status"] == 1 for link in links), 10407)
        first = next(link for link in links if link["jrc_status"] == 2)

        detail = client.get(f"/api/catchment/{first['catchment_id']}")
        self.assertEqual(detail.status_code, 200)
        data = detail.get_json()
        self.assertEqual(len(data["months"]), 12)
        self.assertEqual(data["link"]["jrc_status"], 2)
        self.assertEqual(len(data["link"]["corridor"]), 4)
        self.assertEqual(data["link"]["downstream_id"], first["downstream_id"])
        self.assertGreater(data["channel"]["river_width_m"], 0)
        self.assertGreater(data["channel"]["river_height_m"], 0)
        self.assertGreater(data["channel"]["river_length_m"], 0)

        csv_response = client.get(f"/api/catchment/{first['catchment_id']}/csv")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("downstream_id", csv_response.data.decode("utf-8-sig").splitlines()[0])
        self.assertIn("river_width_m", csv_response.data.decode("utf-8-sig").splitlines()[0])
        self.assertEqual(client.get("/api/catchment/1").status_code, 404)
        html = client.get("/").data.decode("utf-8")
        self.assertIn("CaMa Downstream Links", html)
        self.assertIn('id="mode-draw"', html)
        self.assertIn('id="draw-save"', html)


if __name__ == "__main__":
    unittest.main()
