
# Parking & Traffic Aggregation (DC)

This project cleans and aggregates parking, public transportation, and traffic data for Washington, DC. The analysis aligns all sources to census tracts and produces tract-level metrics for exploration and visualization.

**Live Application:**  
https://dc-transport-analysis.streamlit.app

## Contents

- data/: Raw source datasets from [Open Data DC Website](https://opendata.dc.gov/). Not available on git because of file sizes but download links are found on the deployed application about page.
- cleaned_data/: Cleaned and transformed datasets.
- notebooks/: Jupyter notebooks for processing and analysis
- user_interface/: Streamlit application that displays the processed and transformed spatial data.

## Getting Started

To set up the project environment, activate the <b>myenv</b> enviroment. Download the necessary data from [Open Data DC Website](https://opendata.dc.gov/) and add to data folder. Run the jupyer notebooks in the `notebooks` folder (making sure to run aggregation.ipynb last).

To run the application, call `streamlit run user_interface/main.py` in the root folder.

## Notebooks

- notebooks/aggregation.ipynb: Main pipeline that joins datasets to census tracts, computes metrics, and visualizes results.
- notebooks/parking.ipynb: Parking data cleaning and preprocessing.
- notebooks/public_transportation.ipynb: Public transportation data cleaning and preprocessing.
- notebooks/traffic.ipynb: Traffic data cleaning and preprocessing.

## Outputs

Streamlit application that can be run locally, or found [here](https://dc-transport-analysis.streamlit.app)

## Notes

- All spatial operations use EPSG:3857 for consistent distance calculations.
- Road and parking segments are clipped to the DC boundary before length-based allocation across tracts.
- Parking Zone data required certain liberties and assumptions during processing. In cases where fields were missing or ambiguous, additional calculations and estimations were performed to derive necessary attributes for analysis.

