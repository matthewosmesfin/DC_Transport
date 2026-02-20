import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st

# Handles all Traffic Volume display

def prepare_traffic_lines(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]
    if gdf.empty:
        return gdf

    aadt_col = "AADT" if "AADT" in gdf.columns else "aadt" if "aadt" in gdf.columns else None
    if not aadt_col:
        gdf = gdf.assign(aadt_val=0)
    else:
        gdf = gdf.assign(aadt_val=pd.to_numeric(gdf[aadt_col], errors="coerce").fillna(0))

    min_aadt = float(gdf["aadt_val"].min()) if not gdf.empty else 0
    max_aadt = float(gdf["aadt_val"].max()) if not gdf.empty else 0
    denom = (max_aadt - min_aadt) if max_aadt != min_aadt else 1.0
    gdf = gdf.assign(aadt_norm=(gdf["aadt_val"] - min_aadt) / denom)

    def aadt_color(n: float) -> list[int]:
        if n <= 0.5:
            ratio = n / 0.5
            r = int(0 + 255 * ratio)
            g = 255
            b = 0
        else:
            ratio = (n - 0.5) / 0.5
            r = 255
            g = int(255 - 255 * ratio)
            b = 0
        return [r, g, b, 255]

    gdf = gdf.assign(
        line_width=(gdf["aadt_norm"].pow(0.5) * 14 + 1.5).round(2),
        line_color=gdf["aadt_norm"].apply(aadt_color),
        tooltip_html=gdf["aadt_val"].apply(lambda v: f"<b>AADT:</b> {int(v):,}"),
    )
    return gdf


def build_traffic_layer(gdf: gpd.GeoDataFrame) -> pdk.Layer:
    traffic = prepare_traffic_lines(gdf)
    return pdk.Layer(
        "GeoJsonLayer",
        data=traffic,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 0, 255],
        opacity=0.9,
        stroked=True,
        filled=False,
        get_line_color="line_color",
        get_line_width="line_width",
        line_width_min_pixels=1,
        line_width_max_pixels=20,
    )

def render_traffic_legend(gdf: gpd.GeoDataFrame) -> None:
    aadt_col = "AADT" if "AADT" in gdf.columns else "aadt" if "aadt" in gdf.columns else None
    if aadt_col:
        aadt_vals = pd.to_numeric(gdf[aadt_col], errors="coerce").dropna()
        if not aadt_vals.empty:
            min_aadt = int(aadt_vals.min())
            max_aadt = int(aadt_vals.max())
        else:
            min_aadt, max_aadt = 0, 0
    else:
        min_aadt, max_aadt = 0, 0

    st.subheader("Traffic Volume (AADT)")
    st.markdown(
        """
        <div style="height:12px;border-radius:6px;background:linear-gradient(90deg,#00c853,#ffd600,#d50000);"></div>
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">
          <span>Low</span><span>High</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"AADT range: {min_aadt:,} – {max_aadt:,}")

