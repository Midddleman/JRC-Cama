# Changelog

This file records important changes that affect scientific judgment, analysis
logic, reproducibility, or interpretation of results. Routine tuning and
cosmetic edits are intentionally omitted.

## 2026-09-18 - Classify HydroRIVERS segments with connectivity-first JRC rule

- Impact: Select intact HydroRIVERS segments with `DIS_AV_CMS > 50` inside the JRC mosaic extent and classify them as perennial only when a perennial-cell path connects the segment endpoints. The optional ratio switch now adds `perennial_ratio >= 0.50` as a required condition instead of acting as an alternative route to perennial status; no-water segments are explicitly non-perennial.
- Scope: `Code/processing/classify_china_rivers_perennial_status.py`, `Code/README.md`, and new GeoJSON, CSV, summary, plot, and SQLite outputs under the least-restrictive `Output/ChinaRiverPerennialStatus/water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50/` run.
- Verification: Classified 68,413 unique segments. Results contain 40,678 perennial and 27,735 non-perennial segments; SQLite integrity passed, all perennial records passed connectivity, and all output geometries retained their original `Shape_Length`.

## 2026-09-18 - Round monthly flow values and recompute modes

- Impact: Store monthly CaMa flow statistics to three decimals and compute modes from daily values rounded to three decimals. This changes the interpretation and availability of mode values; ties or no repeats remain NULL.
- Scope: `Code/processing/build_cama_monthly_flow_db.py` and the regenerated 2019 SQLite database in `Output/CamaMonthlyFlow/`.
- Verification: Regenerated 18,741 catchments and 224,892 monthly rows; SQLite integrity passed, all stored flow values have at most three decimals, and a rounded mode matches the source NC. Non-NULL modes increased from 58 to 5,952. The original database was retained as a backup.

## 2026-09-17 - Add 2019 CaMa-Flood monthly flow database

- Impact: Summarize daily 2019 CaMa-Flood outflow into monthly min, max, mean, quartiles, and an unambiguous exact-value mode for each selected catchment. No HydroRIVERS match is made at this stage.
- Scope: `Code/processing/build_cama_monthly_flow_db.py`, `Code/README.md`, and a new SQLite database under `Output/CamaMonthlyFlow/` for the existing China-area catchments above 10,000 km2.
- Verification: Boundary-checked statistics and compared a sample January mean with the source NC. The completed SQLite database has 18,741 catchments and 224,892 monthly rows, 12 months per catchment, no missing daily values, and passes SQLite integrity and foreign-key checks.

## 2026-09-17 - Add binary CaMa-to-flow-status continuity check

- Impact: Add a simple good/bad edge check based on both endpoints being within 2 km of water and sharing the same nearest-water component. The original three-level score remains available for comparison.
- Scope: `Code/processing/analyze_cama_match_continuity.py`; separate binary edge CSV and summary JSON under `Output/CamaFlowStatusMatch/`.
- Verification: Regenerated 18,545 edges; the original counts remain 15,054 good / 2,183 uncertain / 1,308 poor. The binary rule gives 15,043 good / 3,502 bad; boundary checks passed.

<!--
Add new entries above older entries using this format:

## YYYY-MM-DD - Short title

- Impact: What changed and why it matters for interpretation or decisions.
- Scope: Main affected files, data products, or outputs.
- Verification: Relevant checks or tests performed.
-->
