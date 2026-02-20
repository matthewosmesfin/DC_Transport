# A streamlit app to visualize parking and traffic data on maps
import streamlit as st
import geopandas as gpd
import pandas as pd
import contextlib
import warnings
import pydeck as pdk
from shapely.geometry import box
from pathlib import Path
from publictransport import prepare_public_transportation_points, build_public_transport_layer, render_public_transport_legend
from trafficvolume import prepare_traffic_lines, build_traffic_layer, render_traffic_legend
from parkingzones import prepare_parking_zones, build_parking_zones_layer, render_parking_zones_legend

# IMPLEMENT STREAMLIT CACHE FOR DATA LOADING AND PROCESSING, TO SPEED UP INTERACTIONS
# REMOVE SNOW PAKRING ZONES FROM ORIGINAL IPYNB, AS THEY ARE NOT REAL PARKING ZONES AND ADDING CONFUSION, AND REPLACE WITH OUR CLEANED PARKING ZONES DATASET
# ALSO ADJUST FUNCTION FOR CALCULATING MAX CARS
@contextlib.contextmanager
def suppress_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

st.set_page_config(page_title="Layering the Curb: Spatial Insights gathered DC Transportation Data", layout="wide")

DEFAULT_PAGE = "Parking Zones"

# For getting our data sets
BASE_DIR = Path(__file__).resolve().parents[1]

DATASETS = {
    "Traffic Volume": {
        "path": BASE_DIR / "cleaned_data" / "traffic_data.geojson",
        "color": [255, 99, 71, 140],
        "line_color": [255, 99, 71],
        "tooltip": "Traffic: {AADT}"
    },
    "Parking Zones": {
        "path": BASE_DIR / "cleaned_data" / "cleaned_parking_zones.geojson",
        "color": [34, 139, 34, 110],
        "line_color": [34, 139, 34],
        "tooltip": "Zone: {ZONE}"
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

# Function to load out geojson files, with caching and CRS handling
@st.cache_data(show_spinner=False)
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
def build_layers(selected_names: list[str]) -> list[pdk.Layer]:
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
    for name in selected_names:
        dataset = DATASETS[name]
        gdf = load_geojson(dataset["path"])
        if name == "Public Transportation":
            layers.append(build_public_transport_layer(gdf))
        elif name == "Traffic Volume":
            layers.append(build_traffic_layer(gdf))
        elif name == "Parking Zones":
            layers.append(build_parking_zones_layer(gdf))
        else:
            layers.append(
                pdk.Layer(
                    "GeoJsonLayer",
                    data=gdf,
                    pickable=True,
                    auto_highlight=True,
                    opacity=0.6,
                    stroked=True,
                    filled=True,
                    get_fill_color=dataset["color"],
                    get_line_color=dataset["line_color"],
                    line_width_min_pixels=1,
                )
            )
    return layers


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


st.sidebar.header("Map Layers")
selected_layers = st.sidebar.multiselect(
    "Choose datasets",
    list(DATASETS.keys()),
    default=[DEFAULT_PAGE] if DEFAULT_PAGE in DATASETS else ["Traffic Volume", "Parking Zones"],
)

title_suffix = ", ".join(selected_layers) if selected_layers else "No layers selected"
st.title(f"Parking & Traffic Map — {title_suffix}")

st.caption("Hover on features to see dataset-specific details.")

selected_row = None
highlight_layer = None

# Search Engine for Public Transportation layer
if "Public Transportation" in selected_layers:
    transit_points = prepare_public_transportation_points(
        load_geojson(DATASETS["Public Transportation"]["path"])
    )
    if not transit_points.empty:
        st.subheader("Search Metro Stations and Bus Stops")
        if "reset_tick" not in st.session_state:
            st.session_state["reset_tick"] = 0
        reset_clicked = st.button("Reset map", type="secondary")
        options = transit_points["label"].astype(str).tolist()
        selection = st.selectbox(
            "Select a stop or station",
            options,
            index=None,
            placeholder="Select a stop or station",
            key=f"transit_selection_{st.session_state['reset_tick']}",
        )
        if reset_clicked:
            st.session_state["reset_tick"] += 1
            st.rerun()
        if selection:
            selected_row = transit_points[transit_points["label"].astype(str) == selection].head(1)
            if not selected_row.empty:
                highlight_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=selected_row,
                    get_position="[lon, lat]",
                    get_radius=80,
                    radius_min_pixels=6,
                    radius_max_pixels=80,
                    get_fill_color=[255, 255, 0, 220],
                    get_line_color=[255, 255, 255],
                    line_width_min_pixels=2,
                    pickable=False,
                    opacity=0.9,
                )

layers = build_layers(selected_layers)
if highlight_layer is not None:
    layers = layers + [highlight_layer]

if selected_row is not None and not selected_row.empty:
    selected_lon = float(selected_row.iloc[0]["lon"])
    selected_lat = float(selected_row.iloc[0]["lat"])
    view_state = pdk.ViewState(
        latitude=selected_lat,
        longitude=selected_lon,
        zoom=14,
        pitch=0,
    )
else:
    view_state = get_default_view(selected_layers)

tooltip = None
if "Public Transportation" in selected_layers or "Traffic Volume" in selected_layers or "Parking Zones" in selected_layers:
    tooltip = {"html": "{tooltip_html}"}
elif selected_layers:
    tooltip = {"text": DATASETS[selected_layers[0]]["tooltip"]}


deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style=None,
    tooltip=tooltip,
)

col_map, col_legend = st.columns([3, 1], gap="large")

with col_map:
    st.pydeck_chart(deck, use_container_width=True)
    st.caption("Scale: zoom in/out to view neighborhood- or block-level detail.")

with col_legend:
    st.subheader("Selected Layers")
    for name in selected_layers:
        color = DATASETS[name]["color"]
        color_rgb = f"rgb({color[0]}, {color[1]}, {color[2]})"
        st.markdown(
            f"<span style='display:inline-block;width:12px;height:12px;background:{color_rgb};margin-right:8px;border-radius:2px;'></span>{name}",
            unsafe_allow_html=True,
        )

    if "Traffic Volume" in selected_layers:
        traffic_gdf = load_geojson(DATASETS["Traffic Volume"]["path"])
        render_traffic_legend(traffic_gdf)

    if "Public Transportation" in selected_layers:
        render_public_transport_legend()

    if "Parking Zones" in selected_layers:
        render_parking_zones_legend()

with st.expander("Dataset details"):
    for name in selected_layers:
        gdf = load_geojson(DATASETS[name]["path"])
        st.write(f"**{name}**")
        st.write(f"Features: {len(gdf):,}")
        preview = gdf.drop(columns="geometry", errors="ignore").head()
        st.dataframe(preview)

if selected_row is not None and not selected_row.empty:
    st.subheader("Public Transportation Details")
    st.write("Selected feature details:")
    st.dataframe(selected_row.drop(columns="geometry", errors="ignore"))

