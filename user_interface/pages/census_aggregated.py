import streamlit as st
import pydeck as pdk
from pathlib import Path
from aggregation import render_aggregation_legend
from utils import load_geojson, DATASETS, build_layers, map_sidebar, get_default_view, dataset_details

# Census Aggregated Page, where we show data aggregated at the census tract level, allowing users to explore broader spatial patterns and relationships across the city.
DEFAULT_PAGE = "Population"

st.set_page_config(page_title="Layering the Curb: Spatial Insights gathered DC Transportation Data", layout="wide")

st.sidebar.header("Map Layers")

selected_layers = map_sidebar("aggregation", default=DEFAULT_PAGE)

st.title("Transportation & Traffic Map (Aggregated Dataset View)")

st.caption("Hover on census tracts to see specific details.")

selected_row = None
highlight_layer = None

layers = build_layers(selected_layers, type="aggregation")
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
    view_state = get_default_view(["Census Tracts"])

tooltip = {"html": "{tooltip_html}"}

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

    st.markdown("---")
    st.subheader("How This Metric Was Compiled")
    metric_explanations = {
        "Population": "<b>Population:</b> Census tract population from the 2020 Census. <i>(Unit: persons)</i>",
        "Population Density": "<b>Population Density:</b> Calculated as population divided by tract area. <i>(Unit: persons/km²)</i>",
        "Bus Stop Count": "<b>Bus Stop Count:</b> Spatial join assigns bus stops to tracts, counts summed per tract. <i>(Unit: stops)</i>",
        "Metro Station Count": "<b>Metro Station Count:</b> Spatial join assigns metro stations to tracts, counts summed per tract. <i>(Unit: stations)</i>",
        "Average Road Intensity": "<b>Average Road Intensity:</b> Traffic volume (AADT) weighted by road length within each tract, averaged for each tract. <i>(Unit: vehicles/day per mile of road)</i>",
        "Vehicle Miles Traveled": "<b>Vehicle Miles Traveled:</b> Sum of AADT × road segment length (in miles) within each tract. <i>(Unit: vehicle-miles/day)</i>",
        "Maximum Total Parking Count": "<b>Maximum Total Parking Count:</b> Parking segments spatially joined to tracts, counts adjusted for overlap, summed per tract. <i>(Unit: spaces)</i>",
        "Average Unrestricted Hours of Parking a Week": "<b>Average Unrestricted Hours of Parking:</b> Weighted average of unrestricted hours per week, weighted by parking capacity in each tract. <i>(Unit: hours/week)</i>",
        "Most Common Parking Restriction": "<b>Most Common Parking Restriction Type:</b> The most frequently occurring parking restriction type in each tract. <i>(Unit: restriction type)</i>"
    }
    metric_key = selected_layers[0] if selected_layers else DEFAULT_PAGE
    explanation = metric_explanations.get(metric_key)
    st.markdown(explanation + "<br><small>See the github link above for full data pipeline and processing steps</small>", unsafe_allow_html=True)

with col_legend:
    st.subheader("Selected Metric")
    for name in selected_layers:
        st.markdown(
            f"<span style='display:inline-block;width:12px;height:12px;background:#2362d8;margin-right:8px;border-radius:2px;'></span>{name}",
            unsafe_allow_html=True,
        )

    census_gdf = load_geojson(DATASETS["Census Tracts"]["path"])
    metric_key = selected_layers[0] if selected_layers else DEFAULT_PAGE
    render_aggregation_legend(census_gdf, metric_key)

dataset_details("aggregation", DATASETS, selected_layers=None, selected_row=None)