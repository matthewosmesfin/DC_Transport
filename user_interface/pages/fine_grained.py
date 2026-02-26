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
from utils import load_geojson, DATASETS, build_layers, map_sidebar, get_default_view

@contextlib.contextmanager
def suppress_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

# Fine Grained Page, where we show individual datasets separately, allowing users to explore the specific details and spatial patterns of each dataset without the influence of the others.
st.set_page_config(page_title="Layering the Curb: Spatial Insights gathered DC Transportation Data", layout="wide")

DEFAULT_PAGE = "Public Transportation"

st.sidebar.header("Map Layers")
selected_layers = map_sidebar("single", default=DEFAULT_PAGE)

st.title(f"Transportation & Traffic Map (Single Dataset View)")

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

layers = build_layers(selected_layers, type="single")
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
if "Public Transportation" in selected_layers or "Traffic Volume" in selected_layers:
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