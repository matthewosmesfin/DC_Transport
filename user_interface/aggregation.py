import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st

# Handles all Aggregated Census Tract display

AGGREGATION_METRICS: dict[str, dict[str, object]] = {
	"Population": {
		"columns": ["POPULATION"],
		"label": "Population",
		"format": "{value:,.0f}",
		"color_stops": [
			[215, 231, 255, 200],
			[156, 195, 255, 220],
			[84, 144, 255, 230],
			[35, 98, 216, 235],
			[20, 58, 140, 240],
		],
	},
	"Population Density": {
		"columns": ["POPULATION_DENSITY"],
		"label": "Population Density",
		"format": "{value:,.2f}",
		"color_stops": [
			[231, 244, 221, 200],
			[189, 226, 167, 220],
			[140, 202, 116, 230],
			[92, 173, 76, 235],
			[54, 130, 45, 240],
		],
	},
	"Bus Stop Count": {
		"columns": ["BUS_STOP_COUNT"],
		"label": "Bus Stop Count",
		"format": "{value:,.0f}",
		"color_stops": [
			[255, 238, 204, 200],
			[255, 210, 153, 220],
			[255, 179, 102, 230],
			[255, 140, 0, 235],
			[204, 102, 0, 240],
		],
	},
	"Metro Station Count": {
		"columns": ["METRO_STATION_COUNT"],
		"label": "Metro Station Count",
		"format": "{value:,.0f}",
		"color_stops": [
			[242, 230, 255, 200],
			[214, 187, 255, 220],
			[176, 129, 255, 230],
			[134, 69, 255, 235],
			[89, 24, 191, 240],
		],
	},
	"Average Road Intensity": {
		"columns": ["AVERAGE_ROAD_INTENSITY"],
		"label": "Average Road Intensity",
		"format": "{value:,.2f}",
		"color_stops": [
			[204, 242, 242, 200],
			[153, 224, 224, 220],
			[102, 204, 204, 230],
			[51, 168, 168, 235],
			[20, 120, 120, 240],
		],
	},
	"Vehicle Miles Traveled": {
		"columns": ["VEHICLE_MILES_TRAVELED"],
		"label": "Vehicle Miles Traveled",
		"format": "{value:,.0f}",
		"color_stops": [
			[220, 245, 220, 200],
			[170, 230, 170, 220],
			[120, 210, 120, 230],
			[60, 180, 60, 235],
			[20, 120, 20, 240],
		],
	},
	"Maximum Total Parking Count": {
		"columns": ["MAX_TOTAL_PARKING_COUNT"],
		"label": "Maximum Total Parking Count",
		"format": "{value:,.0f}",
		"color_stops": [
			[242, 230, 220, 200],
			[224, 199, 176, 220],
			[200, 160, 120, 230],
			[165, 115, 70, 235],
			[120, 80, 40, 240],
		],
	},
	"Average Unrestricted Hours of Parking a Week": {
		"columns": ["AVG_UNRESTRICTED_HOURS_PER_WEEK"],
		"label": "Average Unrestricted Hours of Parking a Week",
		"format": "{value:,.2f}",
		"color_stops": [
			[255, 224, 238, 200],
			[255, 183, 219, 220],
			[255, 135, 196, 230],
			[235, 80, 160, 235],
			[180, 30, 120, 240],
		],
	},
	"Most Common Parking Restriction": {
		"columns": ["MOST_COMMON_PARKING_RESTRICTION"],
		"label": "Most Common Parking Restriction",
		"format": "{value}",
		"color_stops": [
			[200, 200, 200, 140],
		],
	},
}

RESTRICTION_COLORS = {
    "No Parking": [255, 140, 0, 180],                # Orange
    "No Standing": [0, 120, 255, 180],               # Blue
    "Resident Only Parking": [60, 60, 60, 200],      # Dark grey
    "Resident Permit Parking": [200, 200, 200, 140], # Light grey
    "Sweeping": [180, 140, 255, 180],                # Light purple
    "Timed": [255, 255, 0, 180],                     # Yellow
    "N/A": [200, 0, 0, 180],                         # Red for N/A
}


def _resolve_metric_column(gdf: gpd.GeoDataFrame, columns: list[str]) -> str | None:
	lower_map = {col.lower(): col for col in gdf.columns}
	for col in columns:
		if col in gdf.columns:
			return col
		col_lower = col.lower()
		if col_lower in lower_map:
			return lower_map[col_lower]
	return None


def _interpolate_color(stops: list[list[int]], t: float) -> list[int]:
	t = min(max(t, 0.0), 1.0)
	if len(stops) == 1:
		return stops[0]
	segment = t * (len(stops) - 1)
	idx = int(segment)
	frac = segment - idx
	if idx >= len(stops) - 1:
		return stops[-1]
	start = stops[idx]
	end = stops[idx + 1]
	return [int(start[i] + (end[i] - start[i]) * frac) for i in range(4)]


def _rgba_to_hex(color: list[int]) -> str:
	r, g, b, _a = color
	return f"#{r:02x}{g:02x}{b:02x}"


def prepare_aggregation_polygons(
    gdf: gpd.GeoDataFrame,
    metric_key: str,
) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]
    if gdf.empty:
        return gdf
	
    print("GeoDataFrame columns:", gdf.columns)  # <-- Add here

    metric = AGGREGATION_METRICS.get(metric_key, {})
    columns = metric.get("columns", [])
    metric_col = _resolve_metric_column(gdf, columns) if columns else None

    print(f"\n\n\n\n Preparing aggregation polygons for metric: {metric_key}, using column: {metric_col} \n\n\n\n")

    if metric_key == "Most Common Parking Restriction":
        print("\n\n\n\n ENTERED MOST COMMON PARKING RESTRICTION \n\n\n\n")
        restriction_colors = RESTRICTION_COLORS
        if metric_col and metric_col in gdf.columns:
            gdf = gdf.copy()
            mapped_colors = gdf[metric_col].map(restriction_colors)
            gdf["fill_color"] = mapped_colors.apply(
				lambda x: x if isinstance(x, list) else [150, 150, 150, 140]
			)
            gdf["tooltip_html"] = gdf[metric_col].apply(lambda v: f"<b>{metric_key}</b>: {v}")
        else:
            gdf = gdf.assign(
                fill_color=[150, 150, 150, 140],
                tooltip_html=f"<b>{metric_key}</b>: N/A"
            )
        return gdf

    if metric_col is None:
        gdf = gdf.assign(metric_val=0, metric_norm=0, fill_color=[200, 200, 200, 140])
        gdf = gdf.assign(tooltip_html=f"<b>{metric_key}</b>: N/A")
        return gdf

    values = pd.to_numeric(gdf[metric_col], errors="coerce").fillna(0)
    min_val = float(values.min()) if not values.empty else 0.0
    max_val = float(values.max()) if not values.empty else 0.0
    denom = (max_val - min_val) if max_val != min_val else 1.0
    norm = (values - min_val) / denom

    color_stops = metric.get(
        "color_stops",
        [
            [215, 231, 255, 200],
            [156, 195, 255, 220],
            [84, 144, 255, 230],
            [35, 98, 216, 235],
            [20, 58, 140, 240],
        ],
    )

    label = metric.get("label", metric_key)
    value_format = metric.get("format", "{value:,.2f}")
    tooltip = values.apply(lambda v: f"<b>{label}</b>: " + value_format.format(value=v))

    gdf = gdf.assign(
        metric_val=values,
        metric_norm=norm,
        fill_color=norm.apply(lambda n: _interpolate_color(color_stops, float(n))),
        tooltip_html=tooltip,
    )
    return gdf


def build_aggregation_layer(gdf: gpd.GeoDataFrame, metric_key: str) -> pdk.Layer:
	
	polygons = prepare_aggregation_polygons(gdf, metric_key)
	return pdk.Layer(
		"GeoJsonLayer",
		data=polygons,
		pickable=True,
		auto_highlight=True,
		highlight_color=[255, 255, 0, 200],
		stroked=True,
		filled=True,
		get_fill_color="fill_color",
		get_line_color=[0, 0, 0, 230],  # <-- Black border
        line_width_min_pixels=0.75,        # <-- Thin line
		opacity=0.9,
	)


def render_aggregation_legend(gdf: gpd.GeoDataFrame, metric_key: str) -> None:
	metric = AGGREGATION_METRICS.get(metric_key, {})
	columns = metric.get("columns", [])
	metric_col = _resolve_metric_column(gdf, columns) if columns else None
	label = metric.get("label", metric_key)
	value_format = metric.get("format", "{value:,.2f}")

	if not metric_col:
		st.subheader(label)
		st.caption("No matching field found in dataset.")
		return

	# Special case for categorical legend
	if metric_key == "Most Common Parking Restriction":
		st.subheader(label)
		st.markdown("**Legend:**")
		unique_restrictions = gdf[metric_col].dropna().unique()
		for restriction in unique_restrictions:
			color = RESTRICTION_COLORS.get(restriction, [150, 150, 150, 140])
			hex_color = _rgba_to_hex(color)
			st.markdown(
				f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
				f'<div style="width:18px;height:18px;background:{hex_color};border-radius:3px;display:inline-block;margin-right:8px;border:1px solid #888;"></div>'
				f'<span style="font-size:14px;">{restriction}</span>'
				f'</div>',
				unsafe_allow_html=True,
			)
		# Add legend for any restriction types not present in the data but in RESTRICTION_COLORS
		missing_restrictions = set(RESTRICTION_COLORS.keys()) - set(unique_restrictions)
		for restriction in missing_restrictions:
			color = RESTRICTION_COLORS[restriction]
			hex_color = _rgba_to_hex(color)
			st.markdown(
				f'<div style="display:flex;align-items:center;margin-bottom:4px;opacity:0.4;">'
				f'<div style="width:18px;height:18px;background:{hex_color};border-radius:3px;display:inline-block;margin-right:8px;border:1px solid #888;"></div>'
				f'<span style="font-size:14px;">{restriction}</span>'
				f'</div>',
				unsafe_allow_html=True,
			)
		return

	values = pd.to_numeric(gdf[metric_col], errors="coerce").dropna()
	min_val = float(values.min()) if not values.empty else 0.0
	max_val = float(values.max()) if not values.empty else 0.0

	st.subheader(label)
	color_stops = metric.get(
		"color_stops",
		[
			[215, 231, 255, 200],
			[156, 195, 255, 220],
			[84, 144, 255, 230],
			[35, 98, 216, 235],
			[20, 58, 140, 240],
		],
	)
	gradient = ",".join(_rgba_to_hex(stop) for stop in color_stops)
	st.markdown(
		f"""
		<div style="height:12px;border-radius:6px;background:linear-gradient(90deg,{gradient});"></div>
		<div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">
		  <span>Low</span><span>High</span>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.caption(
		f"Range: {value_format.format(value=min_val)} – {value_format.format(value=max_val)}"
	)


