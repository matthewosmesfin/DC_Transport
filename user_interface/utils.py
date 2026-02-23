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
    "Neighborhood Labels": {
        "path": BASE_DIR / "cleaned_data" / "neighborhood_labels.geojson",
        "color": [255, 215, 0, 120],
        "line_color": [255, 215, 0],
        "tooltip": "Neighborhood: {NAME}"
    },
    "Public Transportation": {
        "path": BASE_DIR / "cleaned_data" / "public_transportation.geojson",
        "color": [138, 43, 226, 140],
        "line_color": [138, 43, 226],
        "tooltip": "Transit: {NAME}"
    },
    "Census Tracts": {
        "path": BASE_DIR / "cleaned_data" / "census_tracts_with_labels.geojson",
        "color": [112, 128, 144, 80],
        "line_color": [112, 128, 144],
        "tooltip": "Tract: {GEOID}"
    },
    "DC Boundary": {
        "path": BASE_DIR / "data" / "Washington_DC_Boundary_Stone_Area.geojson",
        "color": [0, 0, 0, 0],
        "line_color": [0, 0, 0],
        "tooltip": "DC Boundary"
    },
    
}

AGGREGATION_DATASETS = ["Population", "Population Density", "Bus Stop Count", "Metro Station Count", "Average Road Intensity", "Vehicle Miles Traveled", "Maximum Total Parking Count", "Average Unrestricted Hours of Parking a Week"]

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

    #blurring out areas outside DC boundary for better focus, if boundary data is available
    if "DC Boundary" in DATASETS:
        boundary_gdf = load_geojson(DATASETS["DC Boundary"]["path"])
        if not boundary_gdf.empty:
            boundary_union = boundary_gdf.union_all()
            minx, miny, maxx, maxy = boundary_union.bounds
            padding_x = (maxx - minx) * 0.5
            padding_y = (maxy - miny) * 0.5
            outer = box(minx - padding_x, miny - padding_y, maxx + padding_x, maxy + padding_y)

            buffer_deg = 0.002
            buffered_boundary = boundary_union.buffer(buffer_deg)

            mask_geom = outer.difference(buffered_boundary)
            mask_gdf = gpd.GeoDataFrame(geometry=[mask_geom], crs="EPSG:4326")
            layers.append(
                pdk.Layer(
                    "GeoJsonLayer",
                    data=mask_gdf,
                    pickable=False,
                    auto_highlight=False,
                    opacity=0.8,
                    stroked=False,
                    filled=True,
                    get_fill_color=[0, 0, 0, 160],
                )
            )
    
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
        metric_key = selected_names[0] if selected_names else "Population"
        layers.append(build_aggregation_layer(gdf, metric_key))

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
            list(DATASETS.keys()),
            default=[default] if default in DATASETS else ["Traffic Volume", "Public Transportation"],
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



