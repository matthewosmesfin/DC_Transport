import streamlit as st
import pydeck as pdk
import geopandas as gpd
import folium

st.title("Transit Areas Map")

gdf = gpd.read_file("cleaned_data/public_transportation.geojson")
gdf = gdf.to_crs(epsg=4326)
gdf = gdf[gdf.geometry.type == "Point"].copy()
gdf["lat"] = gdf.geometry.y
gdf["lon"] = gdf.geometry.x

st.map(gdf, latitude="lat", longitude="lon")