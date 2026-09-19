# Code Directory

This folder is organized by workflow stage.

## data

- `download_jrc_seasonality_tiles.py`
  Downloads JRC Global Surface Water seasonality GeoTIFF tiles.

## processing

- `aggregate_china_flow_status.py`
  Aggregates JRC seasonality tiles into China flow-status tiles.

- `aggregate_global_flow_status.py`
  Aggregates JRC seasonality tiles into global flow-status tiles.

- `classify_china_rivers_perennial_status.py`
  Classifies HydroRIVERS segments as perennial or non-perennial using the
  least-restrictive JRC flow-status mosaic and start-to-end perennial
  connectivity. The default endpoint neighborhood is now 7x7 raster cells
  (radius 3), saved separately with an `_endpoint_7x7` output suffix; older
  11x11 results remain available for comparison. It selects uncut segments
  with `DIS_AV_CMS > 50` by default and writes spatial, tabular, summary,
  plot, and SQLite outputs. An optional
  switch adds the perennial-ratio threshold as a second required condition.

- `build_cama_monthly_flow_db.py`
  Builds a SQLite database of 2019 monthly flow statistics for CaMa-Flood
  catchments in the existing China-area selection with upstream area above
  10,000 km2. Statistics are stored to three decimals; modes use daily flows
  rounded to three decimals first. It does not match catchments to HydroRIVERS.

- `match_cama_catchments_to_hydrorivers.py`
  Assigns provisional HydroRIVERS IDs to 2019 CaMa catchment points using
  the nearest point-to-line distance within the 20 km search radius by default.
  `--assignment-method topology` reproduces the earlier downstream-network
  tie-breaking rule in its original output names.
  Reads the CaMa SQLite database and full HydroRIVERS `as` GDB, including
  `NEXT_DOWN` paths. Screens all CaMa points against the unfiltered river
  network using a configurable 5 km point-to-line tolerance, then matches
  covered points against all `as` reaches regardless of discharge. The SQLite
  `coverage_screen` table and coverage CSV retain every CaMa point for
  audit; `catchment_matches` and the match CSV contain only covered points,
  with up to three ranked candidates each. Close-distance ties remain flagged
  `ambiguous`, but their assigned ID is still the nearest reach. `matched_reaches` and the accompanying
  GeoJSON retain only river reaches assigned at least one point, with their
  CaMa point counts and HydroRIVERS discharge. These reaches do not yet all
  have JRC status classifications. The 20 km candidate search is not a
  validated accuracy threshold; `ambiguous` means nearby candidates remain
  present, not that no ID was assigned. Nearest-assignment outputs are under
  `Output/CamaHydroRIVERSCatchmentMatch/` with `as_coverage_5km` in their
  names and a `_nearest` suffix. All assignments remain provisional until independently checked.

- `build_cama_hydrorivers_jrc_database.py`
  Builds one SQLite database from the all-reaches CaMa match, 2019 monthly
  flow, and the least-restrictive connectivity-only JRC classification.
  Reuses existing JRC results for matched reaches above 50 cms and applies
  the same raster and parameters to newly matched low-discharge reaches.
  `river_segments` is keyed by `hyriv_id`, `catchments` by `catchment_id`,
  and `monthly_flow_stats` by `(catchment_id, year, month)`. The
  `reach_catchment_monthly_flow` view joins all three and includes CaMa
  `downstream_id` and HydroRIVERS `hydro_next_down` separately. `jrc_status` is 1
  for non-perennial and 2 for perennial; `jrc_evidence` distinguishes
  water-cell evidence from no-water and outside-raster cases. No-water
  reaches retain the existing rule's non-perennial label, but should be
  treated separately in interpretation. JRC is multi-year, while CaMa flow
  is for 2019 only. Output is under `Output/CamaHydroRIVERSIntegrated/`.
  The default integrated output uses the 7x7 endpoint classification and
  has an `_endpoint_7x7` suffix; the previous 11x11 database is retained.

- `build_cama_jrc_link_database.py`
  Builds an independent CaMa-to-JRC SQLite database without HydroRIVERS.
  Each selected 2019 CaMa catchment is linked to its immediate downstream
  catchment coordinate, including downstream points outside the selected set
  read from `parameters_glb06.nc`. A flat-ended UTM rectangle extends 5 km
  perpendicular to either side of that straight link. A link is perennial
  only when eight-connected blue JRC pixel centers inside the rectangle
  touch separate one-pixel-diagonal bands at both ends; otherwise it is
  non-perennial. Links too short to separate the endpoint bands or outside
  raster coverage remain unresolved. This is straight-corridor connectivity,
  not proof of continuity along a winding river. Run
  `python Code/processing/build_cama_jrc_link_database.py` to create
  `Output/CamaJRCDownstreamLinks/.../cama_2019_jrc_links_corridor_5km.sqlite`.
  The database preserves 2019 monthly flow for each catchment alongside
  the long-term 1984-2021 JRC classification and its cell counts. It also
  copies per-catchment `river_width`, `river_height`, and `river_length`
  from the CaMa parameter file into `channel_geometry`. To add these
  parameters to an existing direct-link database without recalculating JRC,
  run `python Code/processing/build_cama_jrc_link_database.py --add-channel-geometry`.

## visualization

- `create_china_flow_status_mosaic.py`
  Builds the China flow-status mosaic GeoTIFF and PNG from processed tiles.

- `create_global_flow_status_mosaic.py`
  Builds the global flow-status mosaic GeoTIFF and PNG from processed tiles.

- `compare_flow_status_parameter_runs.py`
  Compares parameter-run outputs and creates CSV, JSON, and chart summaries.

- `plot_cama_hydrorivers_catchment_matches.py`
  Maps nearest-assigned CaMa catchments by their matched reach's JRC status:
  green for perennial, red for non-perennial, and gray outside JRC coverage.
  Close-distance ties are still available in the match database, but not
  displayed as yellow points. The default map and integrated database use
  7x7 endpoint neighborhoods and retain the older 11x11 map separately.
  Use `--jrc-background` to overlay the points on the least-restrictive JRC
  flow-status mosaic while retaining the plain river-network version. The
  default input is the `as_coverage_5km` match database.

- `cama_hyriv_viewer/build_network_overlay.py`
  Builds the compressed viewer layer from every original HydroRIVERS `as`
  reach with `DIS_AV_CMS > 20`, including geometry and `NEXT_DOWN`. Run
  `python Code/visualization/cama_hyriv_viewer/build_network_overlay.py`
  once before starting the viewer. Use `--overwrite` only to refresh this
  derived display layer. It does not modify the matching or JRC databases.

- `cama_hyriv_viewer/app.py`
  Starts a local read-only, English-language viewer for the integrated SQLite
  database, matched-reach geometry, and full `>20` display layer. Run
  `python Code/visualization/cama_hyriv_viewer/app.py` and open
  `http://127.0.0.1:5006/`. The map draws all `>20` `as` reaches in gray
  and overlays matched reaches by JRC status. Gray unmatched reaches have no
  JRC reach classification or linked CaMa flow in the integrated database.
  Reaches and CaMa points can be selected; the detail panel shows matching
  evidence, monthly flow, and per-reach CSV download. The viewer does not
  modify the source databases.

- `plot_cama_jrc_links.py`
  Draws the direct CaMa downstream links over the least-restrictive JRC
  mosaic: perennial green, non-perennial red, unresolved gray. Run
  `python Code/visualization/plot_cama_jrc_links.py` after building the
  direct-link database.

- `cama_jrc_link_viewer/app.py`
  Starts a separate, read-only direct-link map on `http://127.0.0.1:5008/`.
  Search or click a catchment to inspect its downstream connection, 10 km
  corridor, JRC evidence, and 2019 monthly flow chart/table; CSV export is
  available. It also shows the static CaMa channel width, bankfull depth
  (the `river_height`/bank-height parameter), model
  channel length, and a rectangular schematic cross-section. This is not
  surveyed bathymetry or a daily water-level cross-section. The diagram
  compares each selected catchment with reference catchment 5,517,354
  (115.57 m wide, 1.36 m model bankfull depth). Width and depth vary on
  separate fixed square-root scales, capped to fit the panel; their visual
  aspect ratio is not a physical width-to-depth ratio. The map also has a
  presentation drawing toolbar: switch between Pan and Draw, choose pen
  color and size, undo or clear strokes, and download the annotated map as
  PNG with its legend. Strokes are anchored to map coordinates while the
  page is open; they do not alter the database. Run
  `python Code/visualization/cama_jrc_link_viewer/app.py`.
  The HydroRIVERS viewer on port 5006 and its outputs are unchanged.

## notebooks

- `2026-05-25_jrc_hydrorivers_exploration.ipynb`
  Early JRC and HydroRIVERS data exploration.

- `2026-06-16_flow_status_exploration.ipynb`
  Flow-status processing exploration.

- `2026-06-30_flow_status_classification_with_rivers.ipynb`
  Flow-status classification and river comparison experiment.

- `2026-06-30_flow_status_mosaic_experiment.ipynb`
  Mosaic-building experiment for regional flow-status tiles.

## archive

- `temporary_code_runner_snippet.py`
  Old temporary editor snippet kept only for reference.
