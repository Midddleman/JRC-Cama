"""Match selected CaMa-Flood catchment points to the full HydroRIVERS as network."""

import argparse
import json
import math
import os
import sqlite3
import tempfile
from collections import defaultdict
from contextlib import closing
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Geod, Transformer
from shapely.geometry import box
from shapely.strtree import STRtree


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


ROOT = find_project_root(Path(__file__).resolve())
RUN_LABEL = "water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50"
DEFAULT_CAMA_DB = ROOT / "Output" / "CamaMonthlyFlow" / "cama_2019_monthly_uparea_gt_10000km2.sqlite"
DEFAULT_GDB = ROOT / "Data" / "Google Earth Engine" / "HydroRIVERS_v10_as.gdb" / "HydroRIVERS_v10_as.gdb"
DEFAULT_OUTPUT_DIR = ROOT / "Output" / "CamaHydroRIVERSCatchmentMatch" / RUN_LABEL
GEOD = Geod(ellps="WGS84")
TO_MERCATOR = Transformer.from_crs(4326, 3857, always_xy=True)
FROM_MERCATOR = Transformer.from_crs(3857, 4326, always_xy=True)


def load_cama_points(cama_db):
    with sqlite3.connect(cama_db) as connection:
        points = pd.read_sql_query(
            "SELECT catchment_id, downstream_id, basin_id, longitude, latitude, "
            "upstream_area_km2 FROM catchments ORDER BY catchment_id",
            connection,
        )
    if points["catchment_id"].duplicated().any():
        raise ValueError("CaMa database contains duplicate catchment IDs.")
    return points


def load_raw_rivers(gdb_path):
    rivers = gpd.read_file(gdb_path, columns=["HYRIV_ID", "NEXT_DOWN", "DIS_AV_CMS"])
    if rivers.crs is None or rivers.empty:
        raise ValueError("The original HydroRIVERS as layer must contain lines with a CRS.")
    if rivers["HYRIV_ID"].duplicated().any():
        raise ValueError("The original HydroRIVERS as layer contains duplicate HYRIV_ID values.")
    return rivers.to_crs(4326)


def screen_as_coverage(points, rivers, coverage_km):
    river_ids = rivers["HYRIV_ID"].to_numpy(dtype=np.int64)
    metric_lines = np.asarray(rivers.to_crs(3857).geometry.values, dtype=object)
    tree = STRtree(metric_lines)
    x, y = TO_MERCATOR.transform(points["longitude"].to_numpy(), points["latitude"].to_numpy())
    metric_points = shapely.points(x, y)
    nearest_indices = tree.nearest(metric_points)

    distances = []
    for point, river_index, longitude, latitude in zip(
        metric_points, nearest_indices, points["longitude"], points["latitude"]
    ):
        line = metric_lines[river_index]
        on_line = line.interpolate(line.project(point))
        nearest_lon, nearest_lat = FROM_MERCATOR.transform(on_line.x, on_line.y)
        distances.append(abs(GEOD.inv(longitude, latitude, nearest_lon, nearest_lat)[2]))

    coverage = points.copy()
    coverage["nearest_as_hyriv_id"] = river_ids[nearest_indices]
    coverage["nearest_as_distance_m"] = distances
    coverage["in_as_network"] = coverage["nearest_as_distance_m"] <= coverage_km * 1000.0
    return coverage


def point_candidates(points, rivers, search_km, candidate_count):
    metric_lines = np.asarray(rivers.to_crs(3857).geometry.values, dtype=object)
    river_ids = rivers["HYRIV_ID"].to_numpy(dtype=np.int64)
    tree = STRtree(metric_lines)
    search_m = search_km * 1000.0
    candidates = {}
    for index, point in enumerate(points.itertuples(index=False), start=1):
        x, y = TO_MERCATOR.transform(point.longitude, point.latitude)
        metric_point = shapely.Point(x, y)
        mercator_radius = search_m / max(math.cos(math.radians(point.latitude)), 0.3) * 1.02
        indices = tree.query(box(x - mercator_radius, y - mercator_radius, x + mercator_radius, y + mercator_radius))
        if len(indices):
            projected_distances = shapely.distance(metric_point, metric_lines[indices])
            # Check every reach in the search window in geodesic distance order.
            nearest = np.argsort(projected_distances)
            ranked = []
            for local_index in nearest:
                river_index = int(indices[local_index])
                line = metric_lines[river_index]
                on_line = line.interpolate(line.project(metric_point))
                lon, lat = FROM_MERCATOR.transform(on_line.x, on_line.y)
                distance_m = abs(GEOD.inv(point.longitude, point.latitude, lon, lat)[2])
                if distance_m <= search_m:
                    ranked.append((int(river_ids[river_index]), float(distance_m)))
            ranked.sort(key=lambda row: (row[1], row[0]))
            candidates[int(point.catchment_id)] = ranked[:candidate_count]
        else:
            candidates[int(point.catchment_id)] = []
        if index % 2000 == 0:
            print(f"Found candidates for {index:,}/{len(points):,} points", flush=True)
    return candidates


def make_reachability(next_down, max_hops):
    @lru_cache(maxsize=250000)
    def reachable(upstream_id, downstream_id):
        if upstream_id == downstream_id:
            return True
        current = upstream_id
        seen = {current}
        for _ in range(max_hops):
            current = next_down.get(current, 0)
            if current == downstream_id:
                return True
            if current <= 0 or current in seen:
                return False
            seen.add(current)
        return False

    return reachable


def choose_matches(points, candidates, next_down, ambiguity_m, ambiguity_ratio, max_hops):
    reachable = make_reachability(next_down, max_hops)
    upstream_ids = defaultdict(list)
    by_id = points.set_index("catchment_id")
    for point in points.itertuples(index=False):
        if point.downstream_id in by_id.index:
            upstream_ids[int(point.downstream_id)].append(int(point.catchment_id))

    results = []
    for point in points.itertuples(index=False):
        catchment_id = int(point.catchment_id)
        ranked = candidates[catchment_id]
        if not ranked:
            results.append((catchment_id, None, None, None, None, 0, 0, "no_candidate"))
            continue

        nearest_distance = ranked[0][1]
        second_distance = ranked[1][1] if len(ranked) > 1 else None
        tie_limit = min(nearest_distance + ambiguity_m, max(nearest_distance, 100.0) * ambiguity_ratio)
        ambiguous = second_distance is not None and second_distance <= tie_limit
        considered = [item for item in ranked if item[1] <= tie_limit] if ambiguous else ranked[:1]
        downstream_candidates = candidates.get(int(point.downstream_id), [])
        upstream_candidates = [
            candidates[upstream_id][0][0]
            for upstream_id in upstream_ids[catchment_id]
            if candidates[upstream_id]
        ]

        def support(hyriv_id):
            downstream_ok = bool(
                downstream_candidates and reachable(hyriv_id, downstream_candidates[0][0])
            )
            upstream_ok = any(reachable(upstream_hyriv, hyriv_id) for upstream_hyriv in upstream_candidates)
            return int(downstream_ok), int(upstream_ok)

        options = [(hyriv_id, distance, *support(hyriv_id)) for hyriv_id, distance in considered]
        if ambiguous:
            options.sort(key=lambda row: (-(row[2] + row[3]), row[1], row[0]))
        chosen_id, chosen_distance, downstream_ok, upstream_ok = options[0]
        if ambiguous:
            winner_support = downstream_ok + upstream_ok
            runner_up_support = options[1][2] + options[1][3]
            status = "topology_resolved" if winner_support > runner_up_support else "ambiguous"
        else:
            status = "candidate"
        results.append(
            (
                catchment_id,
                chosen_id,
                chosen_distance,
                nearest_distance,
                second_distance,
                downstream_ok,
                upstream_ok,
                status,
            )
        )
    return pd.DataFrame(
        results,
        columns=[
            "catchment_id",
            "hyriv_id",
            "distance_m",
            "nearest_distance_m",
            "second_distance_m",
            "downstream_support",
            "upstream_support",
            "match_status",
        ],
    )


def choose_nearest_matches(points, candidates, ambiguity_m, ambiguity_ratio):
    results = []
    for point in points.itertuples(index=False):
        catchment_id = int(point.catchment_id)
        ranked = candidates[catchment_id]
        if not ranked:
            results.append((catchment_id, None, None, None, None, 0, 0, "no_candidate"))
            continue
        hyriv_id, distance = ranked[0]
        second_distance = ranked[1][1] if len(ranked) > 1 else None
        tie_limit = min(distance + ambiguity_m, max(distance, 100.0) * ambiguity_ratio)
        status = "ambiguous" if second_distance is not None and second_distance <= tie_limit else "candidate"
        results.append((catchment_id, hyriv_id, distance, distance, second_distance, 0, 0, status))
    return pd.DataFrame(
        results,
        columns=[
            "catchment_id", "hyriv_id", "distance_m", "nearest_distance_m",
            "second_distance_m", "downstream_support", "upstream_support", "match_status",
        ],
    )


def save_results(coverage, points, candidates, matches, rivers, output_db, output_csv, coverage_csv, river_geojson, metadata):
    output_db.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="cama_hyriv_match_", suffix=".sqlite", dir=output_db.parent, delete=False
    ) as handle:
        temp_path = Path(handle.name)
    try:
        with closing(sqlite3.connect(temp_path)) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE coverage_screen (
                    catchment_id INTEGER PRIMARY KEY,
                    longitude REAL NOT NULL,
                    latitude REAL NOT NULL,
                    nearest_as_hyriv_id INTEGER NOT NULL,
                    nearest_as_distance_m REAL NOT NULL,
                    in_as_network INTEGER NOT NULL CHECK (in_as_network IN (0, 1))
                );
                CREATE TABLE catchment_matches (
                    catchment_id INTEGER PRIMARY KEY REFERENCES coverage_screen(catchment_id),
                    downstream_id INTEGER NOT NULL,
                    basin_id INTEGER NOT NULL,
                    longitude REAL NOT NULL,
                    latitude REAL NOT NULL,
                    upstream_area_km2 REAL NOT NULL,
                    hyriv_id INTEGER,
                    distance_m REAL,
                    nearest_distance_m REAL,
                    second_distance_m REAL,
                    downstream_support INTEGER NOT NULL,
                    upstream_support INTEGER NOT NULL,
                    match_status TEXT NOT NULL
                );
                CREATE TABLE candidates (
                    catchment_id INTEGER NOT NULL REFERENCES catchment_matches(catchment_id),
                    candidate_rank INTEGER NOT NULL,
                    hyriv_id INTEGER NOT NULL,
                    distance_m REAL NOT NULL,
                    PRIMARY KEY (catchment_id, candidate_rank)
                );
                CREATE TABLE matched_reaches (
                    hyriv_id INTEGER PRIMARY KEY,
                    next_down INTEGER,
                    dis_av_cms REAL,
                    catchment_count INTEGER NOT NULL CHECK (catchment_count > 0)
                );
                CREATE INDEX catchment_matches_hyriv ON catchment_matches(hyriv_id);
                CREATE INDEX catchment_matches_status ON catchment_matches(match_status);
                CREATE INDEX coverage_screen_in_as ON coverage_screen(in_as_network);
                """
            )
            connection.executemany(
                "INSERT INTO coverage_screen VALUES (?, ?, ?, ?, ?, ?)",
                (
                    (
                        int(row.catchment_id),
                        float(row.longitude),
                        float(row.latitude),
                        int(row.nearest_as_hyriv_id),
                        float(row.nearest_as_distance_m),
                        int(row.in_as_network),
                    )
                    for row in coverage.itertuples(index=False)
                ),
            )
            joined = points.merge(matches, on="catchment_id", validate="one_to_one")
            connection.executemany(
                "INSERT INTO catchment_matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    tuple(None if pd.isna(value) else value.item() if isinstance(value, np.generic) else value for value in row)
                    for row in joined.itertuples(index=False, name=None)
                ),
            )
            connection.executemany(
                "INSERT INTO candidates VALUES (?, ?, ?, ?)",
                (
                    (catchment_id, rank, hyriv_id, distance)
                    for catchment_id, ranked in candidates.items()
                    for rank, (hyriv_id, distance) in enumerate(ranked, start=1)
                ),
            )
            counts = matches["hyriv_id"].dropna().astype(np.int64).value_counts()
            retained = rivers[rivers["HYRIV_ID"].isin(counts.index)].copy()
            retained["catchment_count"] = retained["HYRIV_ID"].map(counts).astype(int)
            if len(retained) != len(counts):
                raise RuntimeError("Some assigned reaches are absent from the source GDB.")
            connection.executemany(
                "INSERT INTO matched_reaches VALUES (?, ?, ?, ?)",
                (
                    (
                        int(row.HYRIV_ID),
                        None if pd.isna(row.NEXT_DOWN) else int(row.NEXT_DOWN),
                        None if pd.isna(row.DIS_AV_CMS) else float(row.DIS_AV_CMS),
                        int(row.catchment_count),
                    )
                    for row in retained.itertuples(index=False)
                ),
            )
            connection.executemany(
                "INSERT INTO metadata VALUES (?, ?)",
                ((key, json.dumps(value, ensure_ascii=False)) for key, value in metadata.items()),
            )
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Output SQLite integrity check failed.")
            if connection.execute("SELECT COUNT(*) FROM catchment_matches").fetchone()[0] != len(points):
                raise RuntimeError("Output SQLite row count mismatch.")
            if connection.execute("SELECT COUNT(*) FROM coverage_screen").fetchone()[0] != len(coverage):
                raise RuntimeError("Output SQLite coverage row count mismatch.")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Output SQLite foreign key check failed.")
        if output_db.exists():
            raise FileExistsError(output_db)
        os.replace(temp_path, output_db)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    joined.to_csv(output_csv, index=False, encoding="utf-8-sig")
    coverage.to_csv(coverage_csv, index=False, encoding="utf-8-sig")
    retained.to_file(river_geojson, driver="GeoJSON")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cama-db", type=Path, default=DEFAULT_CAMA_DB)
    parser.add_argument("--hydrorivers-gdb", type=Path, default=DEFAULT_GDB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--coverage-km", type=float, default=5.0)
    parser.add_argument("--search-km", type=float, default=20.0)
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--ambiguity-km", type=float, default=2.0)
    parser.add_argument("--ambiguity-ratio", type=float, default=1.25)
    parser.add_argument("--max-topology-hops", type=int, default=200)
    parser.add_argument("--assignment-method", choices=("nearest", "topology"), default="nearest")
    args = parser.parse_args()
    if (
        args.coverage_km <= 0
        or args.search_km <= 0
        or args.candidate_count < 2
        or args.ambiguity_km < 0
        or args.ambiguity_ratio <= 1
        or args.max_topology_hops <= 0
    ):
        parser.error("Search distance and topology hops must be positive; candidate count >= 2; ambiguity distance >= 0; ambiguity ratio > 1.")

    all_points = load_cama_points(args.cama_db)
    rivers = load_raw_rivers(args.hydrorivers_gdb)
    coverage = screen_as_coverage(all_points, rivers, args.coverage_km)
    points = coverage.loc[coverage["in_as_network"], all_points.columns].copy()
    outside_count = len(all_points) - len(points)
    print(
        f"Matching {len(points):,} points; excluded {outside_count:,} farther than "
        f"{args.coverage_km:g} km from the original as network",
        flush=True,
    )
    print(f"Candidate river segments: {len(rivers):,}", flush=True)

    candidates = point_candidates(points, rivers, args.search_km, args.candidate_count)
    if args.assignment_method == "nearest":
        matches = choose_nearest_matches(
            points, candidates, args.ambiguity_km * 1000.0, args.ambiguity_ratio,
        )
    else:
        next_down = dict(zip(rivers["HYRIV_ID"].astype(int), rivers["NEXT_DOWN"].fillna(0).astype(int)))
        matches = choose_matches(
            points, candidates, next_down, args.ambiguity_km * 1000.0,
            args.ambiguity_ratio, args.max_topology_hops,
        )
    settings = {
        "cama_db": str(args.cama_db.resolve()),
        "hydrorivers_gdb": str(args.hydrorivers_gdb.resolve()),
        "coverage_km": args.coverage_km,
        "search_km": args.search_km,
        "candidate_count": args.candidate_count,
        "ambiguity_km": args.ambiguity_km,
        "ambiguity_ratio": args.ambiguity_ratio,
        "max_topology_hops": args.max_topology_hops,
        "assignment_method": args.assignment_method,
        "excluded_outside_as_network": outside_count,
        "method": "screen against all as reaches, then match to all as reaches within the search radius; retain only reaches assigned a CaMa point; nearest mode uses the minimum computed geodesic point-to-line distance and preserves close-tie flags; JRC status is not yet classified for the retained network",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_stem = f"cama_2019_catchment_to_hyriv_as_coverage_{args.coverage_km:g}km_all_reaches"
    if args.assignment_method == "nearest":
        output_stem += "_nearest"
    output_db = args.output_dir / f"{output_stem}.sqlite"
    output_csv = args.output_dir / f"{output_stem}.csv"
    coverage_csv = args.output_dir / f"{output_stem}_coverage.csv"
    river_geojson = args.output_dir / f"{output_stem}_matched_reaches.geojson"
    save_results(coverage, points, candidates, matches, rivers, output_db, output_csv, coverage_csv, river_geojson, settings)
    summary = {
        "settings": settings,
        "total_cama_points": len(all_points),
        "inside_as_network": len(points),
        "outside_as_network": outside_count,
        "processed_points": len(points),
        "with_candidate": int(matches["hyriv_id"].notna().sum()),
        "without_candidate": int(matches["hyriv_id"].isna().sum()),
        "matched_reaches": int(matches["hyriv_id"].nunique()),
        "status_counts": matches["match_status"].value_counts().to_dict(),
        "distance_km_quantiles": {
            str(q): float(matches["distance_m"].dropna().quantile(q) / 1000.0)
            for q in (0.5, 0.9, 0.95, 0.99)
        },
    }
    summary_path = args.output_dir / f"{output_stem}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    print(f"Saved {output_db}", flush=True)


if __name__ == "__main__":
    main()
