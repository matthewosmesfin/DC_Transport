import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st
import pydeck as pdk

# Handles all Public Transportation display
def prepare_public_transportation_points(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]
    if gdf.empty:
        return gdf
    
    name_col = "NAME" if "NAME" in gdf.columns else None
    type_col = "TYPE" if "TYPE" in gdf.columns else None
    lines_col = "NUM_LINES" if "NUM_LINES" in gdf.columns else None
    lines_type_col = "LINE" if "LINE" in gdf.columns else None


    if "lon" not in gdf.columns or "lat" not in gdf.columns:
        if gdf.geom_type.isin(["MultiPoint"]).any():
            gdf = gdf.explode(index_parts=False)
        gdf = gdf[gdf.geom_type.isin(["Point"])]
        gdf = gdf.assign(lon=gdf.geometry.x, lat=gdf.geometry.y)


    gdf = gdf.assign(
        mode=gdf[type_col].astype(str) if type_col else "Other",
        lines_count=gdf[lines_col].fillna(1).astype(int) if lines_col else 1,
        label=gdf[name_col].fillna("Unknown") if name_col else "Unknown",
        lines=gdf[lines_type_col].fillna("Unknown") if lines_type_col else "Unknown",
    )

    gdf = gdf.assign(
        radius=gdf.apply(
            lambda row: 30 + min(row["lines_count"], 6) * 8
            if row["mode"] == "METRO STATION"
            else 10,
            axis=1,
        ),
        color=gdf.apply(
            lambda row: [0, 102, 204, 210]
            if row["mode"] == "METRO STATION"
            else [255, 140, 0, 200]
            if row["mode"] == "BUS STOP"
            else [120, 120, 120, 180],
            axis=1,
        ),
        tooltip_html=gdf.apply(
            lambda row: (
                f"<b>{row['label']}</b><br/>Type: {row['mode']}<br/>Num of Lines: {row['lines_count']}<br/>Lines: {row['lines']}"
                if row["mode"] == "METRO STATION"
                else f"<b>{row['label']}</b><br/>Type: {row['mode']}"
            ),
            axis=1,
        ),
    )
    return gdf


def build_public_transport_layer(gdf: gpd.GeoDataFrame) -> pdk.Layer:
    points = prepare_public_transportation_points(gdf)
    return pdk.Layer(
        "ScatterplotLayer",
        data=points,
        get_position="[lon, lat]",
        get_radius="radius",
        radius_min_pixels=1,
        radius_max_pixels=30,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        opacity=0.9,
    )

def render_public_transport_legend() -> None:
    st.subheader("Public Transportation Legend")
    st.markdown(
        """
        <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
          <div><span style="display:inline-block;width:12px;height:12px;background:rgb(0,102,204);margin-right:8px;border-radius:50%;"></span>Metro Station</div>
          <div><span style="display:inline-block;width:12px;height:12px;background:rgb(255,140,0);margin-right:8px;border-radius:50%;"></span>Bus Stop</div>
        </div>
        <div style="margin-top:8px;">For Metro Stations, size of circle corresponds to the number of lines.</div>
        """,
        unsafe_allow_html=True,
    )