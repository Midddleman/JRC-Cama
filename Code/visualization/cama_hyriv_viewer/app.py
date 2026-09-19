"""Local interactive viewer for matched HydroRIVERS, CaMa, and JRC data."""

import csv
import io
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, send_file


ROOT = Path(__file__).resolve().parents[3]
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
MATCH_STEM = "cama_2019_catchment_to_hyriv_as_coverage_5km_all_reaches_nearest"
DB_PATH = ROOT / "Output" / "CamaHydroRIVERSIntegrated" / RUN_LABEL / "cama_2019_hyriv_jrc_integrated_nearest_endpoint_7x7.sqlite"
GEOMETRY_PATH = ROOT / "Output" / "CamaHydroRIVERSCatchmentMatch" / RUN_LABEL / f"{MATCH_STEM}_matched_reaches.geojson"
NETWORK_PATH = ROOT / "Output" / "CamaHydroRIVERSIntegrated" / RUN_LABEL / "hydrorivers_as_dis_gt_20_map.json.gz"
JRC_PATH = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.png"

app = Flask(__name__)


@contextmanager
def database():
    connection = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/overview")
def overview():
    with database() as connection:
        reaches = [dict(row) for row in connection.execute(
            "SELECT hyriv_id, jrc_status, jrc_evidence, catchment_count, dis_av_cms "
            "FROM river_segments ORDER BY hyriv_id"
        )]
        points = [dict(row) for row in connection.execute(
            "SELECT c.catchment_id, c.hyriv_id, c.longitude, c.latitude, c.match_status, "
            "r.jrc_status, r.jrc_evidence FROM catchments c "
            "JOIN river_segments r ON r.hyriv_id = c.hyriv_id ORDER BY c.catchment_id"
        )]
    return jsonify({"reaches": reaches, "points": points})


@app.get("/api/geometry")
def geometry():
    return send_file(GEOMETRY_PATH, mimetype="application/geo+json", conditional=True)


@app.get("/api/network")
def network():
    response = send_file(NETWORK_PATH, mimetype="application/json", conditional=True)
    response.headers["Content-Encoding"] = "gzip"
    return response


@app.get("/api/jrc.png")
def jrc_image():
    return send_file(JRC_PATH, mimetype="image/png", conditional=True)


def reach_data(hyriv_id):
    with database() as connection:
        reach = connection.execute(
            "SELECT * FROM river_segments WHERE hyriv_id = ?", (hyriv_id,)
        ).fetchone()
        if reach is None:
            return None
        catchments = [dict(row) for row in connection.execute(
            "SELECT * FROM catchments WHERE hyriv_id = ? ORDER BY catchment_id", (hyriv_id,)
        )]
        months = [dict(row) for row in connection.execute(
            "SELECT f.* FROM monthly_flow_stats f JOIN catchments c "
            "ON c.catchment_id = f.catchment_id WHERE c.hyriv_id = ? "
            "ORDER BY f.catchment_id, f.year, f.month", (hyriv_id,)
        )]
    return {"reach": dict(reach), "catchments": catchments, "months": months}


@app.get("/api/reach/<int:hyriv_id>")
def reach(hyriv_id):
    data = reach_data(hyriv_id)
    if data is None:
        abort(404)
    return jsonify(data)


@app.get("/api/reach/<int:hyriv_id>/csv")
def reach_csv(hyriv_id):
    data = reach_data(hyriv_id)
    if data is None:
        abort(404)
    output = io.StringIO()
    fields = [
        "hyriv_id", "jrc_status", "jrc_label", "jrc_evidence", "catchment_id",
        "downstream_id", "match_status", "match_distance_m", "year", "month",
        "days_in_month", "valid_days", "min_flow_cms", "q25_flow_cms",
        "median_flow_cms", "mean_flow_cms", "q75_flow_cms", "max_flow_cms",
        "mode_flow_cms", "mode_frequency",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    catchments = {row["catchment_id"]: row for row in data["catchments"]}
    for month in data["months"]:
        point = catchments[month["catchment_id"]]
        writer.writerow({
            **{key: data["reach"].get(key) for key in fields},
            **{key: point.get(key) for key in fields if key in point},
            **{key: month.get(key) for key in fields if key in month},
        })
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=hyriv_{hyriv_id}_cama_2019.csv"},
    )


@app.get("/health")
def health():
    return jsonify({
        "database": DB_PATH.exists(), "geometry": GEOMETRY_PATH.exists(),
        "network": NETWORK_PATH.exists(), "jrc": JRC_PATH.exists(),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5006, debug=False)
