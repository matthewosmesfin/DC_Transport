#Basics Functions used across the app, such as loading geojson files, building layers, and getting default view settings.
import streamlit as st

import geopandas as gpd
from pathlib import Path
import pydeck as pdk
from shapely.geometry import box
from publictransport import prepare_public_transportation_points, build_public_transport_layer, render_public_transport_legend
from trafficvolume import prepare_traffic_lines, build_traffic_layer, render_traffic_legend
from aggregation import build_aggregation_layer


# For getting our data sets
BASE_DIR = Path(__file__).resolve().parents[1]

DATASETS = {
    "Traffic Volume": {
        "path": BASE_DIR / "cleaned_data" / "traffic_data.geojson",
        "color": [255, 99, 71, 140],
        "line_color": [255, 99, 71],
        "tooltip": "Traffic: {AADT}"
    },
    "Public Transportation": {
        "path": BASE_DIR / "cleaned_data" / "public_transportation.geojson",
        "color": [138, 43, 226, 140],
        "line_color": [138, 43, 226],
        "tooltip": "Transit: {NAME}"
    },
    "Neighborhood Labels": {
        "path": BASE_DIR / "cleaned_data" / "neighborhood_labels.geojson",
        "color": [255, 215, 0, 120],
        "line_color": [255, 215, 0],
        "tooltip": "Neighborhood: {NAME}"
    },
    "Census Tracts": {
        "path": BASE_DIR / "cleaned_data" / "census_tracts_with_labels.geojson",
        "color": [112, 128, 144, 80],
        "line_color": [112, 128, 144],
        "tooltip": "Tract: {GEOID}"
    },
    
}

AGGREGATION_DATASETS = ["Population", "Population Density", "Bus Stop Count", "Metro Station Count", "Average Road Intensity", "Vehicle Miles Traveled", "Maximum Total Parking Count", "Average Unrestricted Hours of Parking a Week", "Most Common Parking Restriction"]

def load_geojson(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]

    if gdf.crs is None:
        minx, miny, maxx, maxy = gdf.total_bounds
        in_lonlat = (
            -180 <= minx <= 180
            and -180 <= maxx <= 180
            and -90 <= miny <= 90
            and -90 <= maxy <= 90
        )
        if in_lonlat:
            gdf = gdf.set_crs(epsg=4326, allow_override=True)
        else:
            max_abs = max(abs(minx), abs(miny), abs(maxx), abs(maxy))
            if max_abs <= 20037508:
                gdf = gdf.set_crs(epsg=3857, allow_override=True)
            else:
                gdf = gdf.set_crs(epsg=26918, allow_override=True)

    return gdf.to_crs(epsg=4326)

#Buidling layers for our map based on user selection, with appropriate styling and interactivity
def build_layers(selected_names: list[str], type: str) -> list[pdk.Layer]:
    layers: list[pdk.Layer] = []

    if type == "single":
        for name in selected_names:
            dataset = DATASETS[name]
            gdf = load_geojson(dataset["path"])
            if name == "Public Transportation":
                layers.append(build_public_transport_layer(gdf))
            elif name == "Traffic Volume":
                layers.append(build_traffic_layer(gdf))

    if type == "aggregation":
        dataset = DATASETS["Census Tracts"]
        gdf = load_geojson(dataset["path"])
        metric_key = selected_names[0] if selected_names and selected_names[0] in AGGREGATION_DATASETS else "Population"
        # Set a different opacity for the aggregation layer
        aggregation_layer = build_aggregation_layer(gdf, metric_key)
        aggregation_layer.opacity = 0.5  # Set your desired opacity here (e.g., 0.5)
        layers.append(aggregation_layer)

    return layers

def map_sidebar(type, default):
    if type == "aggregation":
        selected_layers = st.sidebar.selectbox(
            "Choose dataset",
            AGGREGATION_DATASETS,
            index=0,
        )
        return [selected_layers]
    if type == "single":
        selected_layers = st.sidebar.multiselect(
            "Choose datasets",
            list(DATASETS.keys())[:2],
            default=[default] if default in list(DATASETS.keys())[:2] else [list(DATASETS.keys())[0]],
        )
        return selected_layers
    return []
    
def get_default_view(selected_names: list[str]) -> pdk.ViewState:
    if not selected_names:
        return pdk.ViewState(latitude=38.9072, longitude=-77.0369, zoom=10, pitch=0)

    gdf = load_geojson(DATASETS[selected_names[0]]["path"])
    if gdf.empty:
        return pdk.ViewState(latitude=38.9072, longitude=-77.0369, zoom=10, pitch=0)

    minx, miny, maxx, maxy = gdf.total_bounds
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2
    return pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=11, pitch=0)


def page_selector():
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="large")
    with col1:
        if st.button("Census Aggregated View"):
            st.switch_page("pages/census_aggregated.py")
    with col2:
        if st.button("Fine Grained View"):
            st.switch_page("pages/fine_grained.py")
    with col3:
        if st.button("About Page"):
            st.switch_page("pages/about.py")
    with col4:
        st.link_button("Github", "https://github.com/matthewosmesfin/DC_Transport", width="stretch")