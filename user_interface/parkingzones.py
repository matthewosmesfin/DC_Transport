import geopandas as gpd
import pydeck as pdk
import streamlit as st

# Handles all Parking Zones display

def prepare_parking_zones(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]
    if gdf.empty:
        return gdf

    restriction_col = "PARKINGGROUP" if "PARKINGGROUP" in gdf.columns else None
    unrestricted_hours_col = "UNRESTRICTED_HOURS_PER_WEEK" if "UNRESTRICTED_HOURS_PER_WEEK" in gdf.columns else None
    estimated_max_cars_col = "ESTIMATED_MAX_CARS" if "ESTIMATED_MAX_CARS" in gdf.columns else None

    gdf = gdf.assign(
        restriction_type=gdf[restriction_col].fillna("Unknown") if restriction_col else "Unknown",
        unrestriction_hours=gdf[unrestricted_hours_col].fillna(0).astype(int) if unrestricted_hours_col else 0,
        estimated_max_cars=gdf[estimated_max_cars_col].fillna(0).astype(int) if estimated_max_cars_col else 0,
    )

    def intensity_color(hours: int) -> list[int]:
        h = max(0, min(166, int(hours)))
        t = h / 166  # 0..1
        r = int(255 + (0 - 255) * t)
        g = int(255 + (166 - 255) * t)
        b = int(255 + (255 - 255) * t)
        return [r, g, b, 255]

    gdf = gdf.assign(
        restriction_color=gdf["unrestriction_hours"].map(intensity_color),
        line_width=3,
        tooltip_html=gdf.apply(
            lambda row: (
                f"<b>Restriction:</b> {row['restriction_type']}<br/><b>Unrestricted Hours/Week:</b> {row['unrestriction_hours']}<br/><b>Estimated Max Cars:</b> {row['estimated_max_cars']}"
            ),
            axis=1,
        ),
    )
    return gdf

def build_parking_zones_layer(gdf: gpd.GeoDataFrame) -> pdk.Layer:
    parking = prepare_parking_zones(gdf)
    return pdk.Layer(
        "GeoJsonLayer",
        data=parking,
        pickable=True,
        auto_highlight=True,
        filled=False,
        stroked=True,
        opacity=0.9,
        get_line_color="restriction_color",
        get_line_width="line_width",
        line_width_min_pixels=2,
        line_width_max_pixels=12,
    )

def render_parking_zones_legend():
    st.subheader("Parking Zones Restriction Legend")
    st.markdown(
        """
        <div style="height:12px;border-radius:6px;background:linear-gradient(90deg,#ffffff,#00a6ff);"></div>
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">
          <span>Low</span><span>High</span>
        </div>
        """,
        unsafe_allow_html=True,
    )