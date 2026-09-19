"""Read-only viewer for direct CaMa downstream-link / JRC classifications."""

import csv
import io
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, send_file


ROOT = Path(__file__).resolve().parents[3]
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
DB_PATH = ROOT / "Output" / "CamaJRCDownstreamLinks" / RUN_LABEL / "cama_2019_jrc_links_corridor_5km.sqlite"
JRC_PATH = ROOT / "Output" / "ChinaFlowStatusMosaic" / RUN_LABEL / f"china_flow_status_factor33_{RUN_LABEL}.png"
REFERENCE_CATCHMENT_ID = 5517354

HERE = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(HERE / "templates"), static_folder=str(HERE / "static"))


def database():
    connection = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/overview")
def overview():
    with closing(database()) as connection:
        links = [dict(row) for row in connection.execute(
            "SELECT catchment_id, downstream_id, longitude, latitude, "
            "downstream_longitude, downstream_latitude, jrc_status, jrc_label "
            "FROM catchment_links ORDER BY catchment_id"
        )]
        reference = connection.execute(
            "SELECT catchment_id, river_width_m, river_height_m "
            "FROM channel_geometry WHERE catchment_id = ?", (REFERENCE_CATCHMENT_ID,)
        ).fetchone()
    return jsonify({"links": links, "channel_reference": dict(reference) if reference else None})


@app.get("/api/jrc.png")
def jrc_image():
    return send_file(JRC_PATH, mimetype="image/png", conditional=True)


def catchment_data(catchment_id):
    with closing(database()) as connection:
        link = connection.execute(
            "SELECT * FROM catchment_links WHERE catchment_id = ?", (catchment_id,)
        ).fetchone()
        if link is None:
            return None
        months = [dict(row) for row in connection.execute(
            "SELECT * FROM monthly_flow_stats WHERE catchment_id = ? "
            "ORDER BY year, month", (catchment_id,)
        )]
        geometry = connection.execute(
            "SELECT river_width_m, river_height_m, river_length_m "
            "FROM channel_geometry WHERE catchment_id = ?", (catchment_id,)
        ).fetchone()
    record = dict(link)
    record["corridor"] = json.loads(record.pop("corridor_json")) if record["corridor_json"] else None
    return {"link": record, "months": months, "channel": dict(geometry) if geometry else None}


@app.get("/api/catchment/<int:catchment_id>")
def catchment(catchment_id):
    data = catchment_data(catchment_id)
    if data is None:
        abort(404)
    return jsonify(data)


@app.get("/api/catchment/<int:catchment_id>/csv")
def catchment_csv(catchment_id):
    data = catchment_data(catchment_id)
    if data is None:
        abort(404)
    fields = [
        "catchment_id", "downstream_id", "jrc_status", "jrc_label", "link_length_m",
        "river_width_m", "river_height_m", "river_length_m",
        "sampled_cell_count", "valid_cell_count", "perennial_count", "intermittent_count",
        "connected_path_cells", "year", "month", "days_in_month", "valid_days",
        "min_flow_cms", "q25_flow_cms", "median_flow_cms", "mean_flow_cms",
        "q75_flow_cms", "max_flow_cms", "mode_flow_cms", "mode_frequency",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for month in data["months"]:
        writer.writerow({key: month.get(key, data["link"].get(key, (data["channel"] or {}).get(key))) for key in fields})
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=cama_{catchment_id}_jrc_link.csv"},
    )


@app.get("/health")
def health():
    return jsonify({"database": DB_PATH.exists(), "jrc": JRC_PATH.exists()})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5008, debug=False)
