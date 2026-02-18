# A streamlit app to visualize parking and traffic data on maps
import streamlit as st
import geopandas as gpd
import pandas as pd
import contextlib
import warnings
import pydeck as pdk
from shapely.geometry import box
from pathlib import Path

@contextlib.contextmanager
def suppress_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

st.set_page_config(page_title="Layering the Curb: Spatial Insights gathered DC Transportation Data", layout="wide")

DEFAULT_PAGE = "Traffic Volume"

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


#PUBLIC TRANSPORTATION POINTS PREPARATION: Exploding multipoints, filtering to points, and adding styling attributes for map visualization
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

#traffic data
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
            points = prepare_public_transportation_points(gdf)
            layers.append(
                pdk.Layer(
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
            )
        elif name == "Traffic Volume":
            traffic = prepare_traffic_lines(gdf)
            layers.append(
                pdk.Layer(
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
            )
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



show_legend = st.sidebar.checkbox("Show legend", value=True)
show_scale = st.sidebar.checkbox("Show scale", value=True)

title_suffix = ", ".join(selected_layers) if selected_layers else "No layers selected"
st.title(f"Parking & Traffic Map — {title_suffix}")

st.caption("Hover on features to see dataset-specific details.")

selected_row = None
highlight_layer = None

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
    st.pydeck_chart(deck, width="stretch")
    if show_scale:
        st.caption("Scale: zoom in/out to view neighborhood- or block-level detail.")

with col_legend:
    if show_legend and selected_layers:
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
        aadt_col = "AADT" if "AADT" in traffic_gdf.columns else "aadt" if "aadt" in traffic_gdf.columns else None
        if aadt_col:
            aadt_vals = pd.to_numeric(traffic_gdf[aadt_col], errors="coerce").dropna()
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

    if "Public Transportation" in selected_layers:
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

