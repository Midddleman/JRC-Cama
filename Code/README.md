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
  Classifies China HydroRIVERS segments as intermittent or perennial using
  aggregated flow-status cells, segment buffers, and perennial connectivity
  from river start to end.

## visualization

- `create_china_flow_status_mosaic.py`
  Builds the China flow-status mosaic GeoTIFF and PNG from processed tiles.

- `create_global_flow_status_mosaic.py`
  Builds the global flow-status mosaic GeoTIFF and PNG from processed tiles.

- `compare_flow_status_parameter_runs.py`
  Compares parameter-run outputs and creates CSV, JSON, and chart summaries.

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
