# Changelog

This file records important changes that affect scientific judgment, analysis
logic, reproducibility, or interpretation of results. Routine tuning and
cosmetic edits are intentionally omitted.

## 2026-09-18 - Add map annotation tools for direct-link discussion

- Impact: Add a simple pen to the separate CaMa-JRC viewer so connectivity examples can be marked up for discussion. Strokes follow map coordinates while zooming or panning, and the current view can be downloaded as a PNG with a status legend. This is presentation-only; JRC classifications, CaMa geometry, and flow data are unchanged.
- Scope: `Code/visualization/cama_jrc_link_viewer/` and `Code/README.md`.
- Verification: Browser-tested draw versus pan selection, color and size changes, zoom persistence, undo, clear, PNG export, and desktop/390 px mobile layouts; six focused tests passed.

## 2026-09-18 - Scale the CaMa channel schematic by width and depth

- Impact: The selected catchment's schematic opening and depth now vary with its static CaMa width and `river_height`, instead of keeping one fixed shape. A dashed reference shows catchment 5,517,354 (115.57 m wide, 1.36 m model bankfull depth), close to the selected-population medians. Separate fixed square-root scales and display caps keep dimensions legible; visual aspect ratio is not physical. JRC classification, channel parameters, and flow data are unchanged.
- Scope: `Code/visualization/cama_jrc_link_viewer/`, `Code/README.md`.
- Verification: Six focused tests passed; reference, 30 m by 1 m, and 306.18 m by 4.32 m catchments were compared in the browser, and the displayed geometry changed as intended.

## 2026-09-18 - Add CaMa channel geometry to direct-link inspection

- Impact: Join CaMa's static `river_width`, `river_height` (model bankfull depth), and `river_length` to each selected catchment and show a rectangular model cross-section when a catchment is selected. This lets river-size assumptions be inspected alongside JRC connectivity and 2019 flow; the drawing is not a surveyed cross-section or a daily water level. JRC classifications and monthly flow statistics are unchanged.
- Scope: `Code/processing/build_cama_jrc_link_database.py`, the existing `cama_2019_jrc_links_corridor_5km.sqlite` `channel_geometry` table, `Code/visualization/cama_jrc_link_viewer/`, and `Code/README.md`.
- Verification: Geometry was joined by catchment ID for all 18,741 selected catchments; focused database and viewer tests passed, and the updated detail view was inspected.

## 2026-09-18 - Classify CaMa downstream links directly against JRC

- Impact: Add an independent, HydroRIVERS-free comparison. Each selected 2019 CaMa catchment is linked to its immediate downstream point; blue JRC cells must form an eight-connected path through a flat-ended, 10 km-wide straight corridor from one endpoint band to the other to count as perennial. Links without that path are non-perennial; links too short to resolve or outside JRC coverage remain unknown. This measures corridor connectivity, not traced-river continuity, and compares 2019 CaMa flow with 1984-2021 JRC status.
- Scope: `Code/processing/build_cama_jrc_link_database.py`, `Code/visualization/plot_cama_jrc_links.py`, `Code/visualization/cama_jrc_link_viewer/`, new SQLite/summary/map under `Output/CamaJRCDownstreamLinks/`, `Code/README.md`, and a narrow `.gitignore` database exception. The earlier HydroRIVERS viewer and databases are unchanged.
- Verification: 18,741 links and 224,892 monthly rows passed SQLite integrity and foreign-key checks; 8,015 perennial, 10,407 non-perennial, and 319 unresolved. Five focused tests passed; desktop and mobile viewer screens were inspected.

## 2026-09-18 - Tighten JRC reach endpoint windows from 11x11 to 7x7

- Impact: Reduce the default start/end neighborhood radius from five to three aggregated JRC cells while leaving the raster, 5 km reach buffer, minimum connected component, ratio switch, and CaMa matching unchanged. This makes it harder for a nearby blue patch to satisfy both endpoints of a short reach. Save the new classification and integrated outputs with `_endpoint_7x7` names, retaining the older 11x11 files for comparison.
- Scope: `Code/processing/classify_china_rivers_perennial_status.py`, `Code/processing/build_cama_hydrorivers_jrc_database.py`, the match maps, viewer, `Code/README.md`, and new 7x7 JRC/integrated outputs.
- Verification: On all 68,413 `DIS_AV_CMS > 50` reaches, 4,361 changed from perennial to non-perennial and none changed in the other direction. In the 12,982 matched reaches, 1,035 changed from perennial to non-perennial, recoloring 1,050 CaMa catchments; 13,327 catchments and 159,924 monthly records remain linked. Endpoint neighborhoods still overlap for 5,699 of 6,808 perennial matched reaches, so 7x7 is a stricter sensitivity test, not proof of full along-river continuity. Twelve focused tests passed.

## 2026-09-18 - Guard against stale viewer APIs showing every point red

- Impact: The viewer now treats missing JRC point status as unknown and rejects an outdated map API instead of painting all catchments non-perennial. Restarted the original `5006` viewer so its Python API and current JavaScript agree. Matching databases and JRC classifications did not change.
- Scope: `Code/visualization/cama_hyriv_viewer/static/app.js` and the local viewer process.
- Verification: The refreshed `5006` API returns 7,989 perennial and 5,338 non-perennial catchments; the static JRC map visibly contains both green and red points.

## 2026-09-18 - Assign CaMa catchments to nearest HydroRIVERS reaches

- Impact: The default match now assigns every CaMa point that passes the existing 5 km raw-network screen to its shortest-distance HydroRIVERS `as` reach within the 20 km search, without topology overriding that ID. Close-distance ties remain flagged `ambiguous` for review. Maps color catchments by their assigned reach's multi-year JRC status (perennial green, non-perennial red), not by matching confidence; points outside JRC coverage would be gray. The earlier topology-based outputs remain available unchanged.
- Scope: `Code/processing/match_cama_catchments_to_hydrorivers.py`, `Code/processing/build_cama_hydrorivers_jrc_database.py`, the match plot and interactive viewer, `_nearest` SQLite/GeoJSON/CSV/map outputs, and `Code/README.md`.
- Verification: All 13,327 covered points matched the rank-1 distance candidate; 556 assigned reach IDs differ from the previous topology-based output. The new 12,982 reaches and 159,924 monthly records passed SQLite integrity checks. The JRC map has 7,989 perennial and 5,338 non-perennial catchment points; focused matching, integration, and viewer tests passed, and desktop/mobile map views were inspected.

## 2026-09-18 - Show all HydroRIVERS as reaches above 20 cms in the viewer

- Impact: Add every original `as` reach with `DIS_AV_CMS > 20` as a gray network layer beneath JRC-colored matched reaches, so gaps caused by retaining only CaMa-matched reaches are visible as omitted classifications rather than apparent breaks in HydroRIVERS. Unmatched gray reaches display their ID, discharge, and `NEXT_DOWN` without assigning a JRC status. Translate the viewer UI to English. Matching, classification, and integrated scientific data are unchanged.
- Scope: `Code/visualization/cama_hyriv_viewer/`, its compressed `hydrorivers_as_dis_gt_20_map.json.gz` display output, `Code/tests/test_cama_hyriv_viewer.py`, and `Code/README.md`.
- Verification: The GDB-derived layer contains 113,648 unique reaches, all above 20 cms. Desktop and 390 px mobile browser views, matched and unmatched reach lookup, and API tests were checked.

## 2026-09-18 - Add interactive reach and catchment viewer

- Impact: Provide a local, read-only map and detail workflow for inspecting JRC status, provisional CaMa-to-reach assignments, and each catchment's 2019 monthly flow without aggregating upstream and downstream points together. No scientific classifications or source data change.
- Scope: `Code/visualization/cama_hyriv_viewer/`, `Code/tests/test_cama_hyriv_viewer.py`, and `Code/README.md`.
- Verification: Flask endpoints and CSV export checked; desktop and 390 px mobile browser screenshots inspected; Hydro ID search, map selection, and flow-metric switching exercised.

## 2026-09-18 - Expose both downstream IDs in the integrated view

- Impact: Add CaMa `downstream_id` and HydroRIVERS `hydro_next_down` to the reach-catchment-monthly view, so the two distinct network links are visible without extra joins. Source tables and classifications are unchanged.
- Scope: `Code/processing/build_cama_hydrorivers_jrc_database.py` and the existing `cama_2019_hyriv_jrc_integrated.sqlite` view.
- Verification: The view was queried for both IDs and its row count checked; focused integration and matching tests passed.

## 2026-09-18 - Integrate matched reaches, CaMa flow, and JRC status

- Impact: Create a reach-keyed SQLite linking each matched HydroRIVERS reach to its CaMa catchments and each catchment's 12 monthly 2019 flow summaries. Reuse the existing connectivity-only JRC classification for 8,470 reaches and classify 4,482 newly matched low-discharge reaches with the same raster and parameters. Distinguish JRC water-cell evidence from the original rule's no-water non-perennial label, and record the 2019 versus multi-year temporal mismatch.
- Scope: `Code/processing/build_cama_hydrorivers_jrc_database.py`, `Code/README.md`, and `Output/CamaHydroRIVERSIntegrated/water_ratio_0.05_min_conn_10_perennial_10_perennial_ratio_0.50/cama_2019_hyriv_jrc_integrated.sqlite`.
- Verification: 12,952 reaches, 13,327 catchments, and 159,924 monthly rows; every reach count and 12-month record checked. SQLite integrity, foreign keys, and the joined view passed; 637 reaches have no JRC water cells and are flagged separately.

## 2026-09-18 - Match CaMa points against all HydroRIVERS as reaches

- Impact: Remove the `DIS_AV_CMS > 50` candidate filter after the existing 5 km raw-network coverage screen. Every covered CaMa point can now match an `as` reach regardless of HydroRIVERS discharge; retain only reaches assigned at least one point. These assignments remain provisional, and newly included low-discharge reaches do not yet have JRC reach classifications.
- Scope: `Code/processing/match_cama_catchments_to_hydrorivers.py`, match-map defaults, `Code/README.md`, and new `all_reaches` SQLite/CSV/GeoJSON/map outputs. Previous `dis_gt_50` outputs remain unchanged.
- Verification: Six focused tests passed. Of 18,741 CaMa points, 13,327 passed the raw-network screen and all 13,327 received candidates; 12,952 reaches were retained, including 4,482 with `DIS_AV_CMS <= 50`. SQLite integrity, foreign keys, coverage exclusion, and assigned-reach membership checks passed.

## 2026-09-18 - Screen CaMa points by the actual HydroRIVERS as network

- Impact: Replace the previous latitude-only exclusion with a spatial coverage screen against every unscreened `as` river reach. A provisional 5 km point-to-line tolerance determines which CaMa points enter the existing `DIS_AV_CMS > 50` match; the full nearest-raw-reach distance and ID are retained for audit. This changes the study population and the interpretation of red no-candidate points.
- Scope: `Code/processing/match_cama_catchments_to_hydrorivers.py`, the matching visualization defaults, and new `as_coverage_5km` SQLite/CSV/maps under `Output/CamaHydroRIVERSCatchmentMatch/`. Older outputs are retained for comparison. The least-restrictive JRC mosaic remains the JRC default.
- Verification: Five focused tests passed; 13,327 of 18,741 points fell within 5 km of the raw `as` network. The corrected SQLite passed integrity and foreign-key checks, excluded points do not appear in matches, and all assigned/candidate river IDs are valid. The corrected JRC overlay was regenerated and inspected.

## 2026-09-18 - Add provisional CaMa catchment-to-HydroRIVERS matching

- Impact: Match 2019 CaMa catchment coordinates to the existing `DIS_AV_CMS > 50` HydroRIVERS segments using nearby point-to-line candidates, with `downstream_id`/`NEXT_DOWN` consistency used only to break close ties. Preserve distances, alternate candidates, unresolved ties, and no-candidate cases rather than treating nearest lines as verified matches.
- Scope: `Code/processing/match_cama_catchments_to_hydrorivers.py`, focused tests, and SQLite/CSV/summary outputs under `Output/CamaHydroRIVERSCatchmentMatch/`. The two source databases are unchanged.
- Verification: Four focused tests passed. Processed 16,169 catchments after excluding 2,572 north of the source GDB limit; 10,626 had a candidate within 20 km and 5,543 had none. SQLite integrity and foreign keys passed; all assigned/candidate IDs exist in the classified river database, and 20 sampled no-candidate points were farther than 20 km from their nearest eligible segment.

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
