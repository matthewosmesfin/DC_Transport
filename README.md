
# Parking & Traffic Aggregation (DC)

This project cleans and aggregates parking, public transportation, and traffic data for Washington, DC. The analysis aligns all sources to census tracts and produces tract-level metrics for exploration and visualization.

## Contents

- data/: Raw source datasets from [Open Data DC Website](https://opendata.dc.gov/). Not available on git because of file sizes but download links will be included.
- cleaned_data/: Cleaned and transformed datasets.
- notebooks/: Jupyter notebooks for processing and analysis

## Getting Started

1. Create and activate a Python virtual environment.
2. Install dependencies (geopandas, pandas, numpy, matplotlib, and related geo libraries).
3. Open the notebooks in notebooks/ and run them top to bottom.

## Notebooks

- notebooks/aggregation.ipynb: Main pipeline that joins datasets to census tracts, computes metrics, and visualizes results.
- notebooks/parking.ipynb: Parking data cleaning and preprocessing.
- notebooks/public_transportation.ipynb: Public transportation data cleaning and preprocessing.
- notebooks/traffic.ipynb: Traffic data cleaning and preprocessing.

## Outputs

Aggregated tract-level metrics are generated in-memory in the notebooks and can be exported if needed. Cleaned GeoJSON outputs are stored in cleaned_data/.

## Notes

- All spatial operations use EPSG:3857 for consistent distance calculations.
- Road and parking segments are clipped to the DC boundary before length-based allocation across tracts.

