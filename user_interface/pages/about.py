import streamlit as st
from utils import page_selector

st.set_page_config(page_title="About | Layering the Curb", layout="wide")

# Our About Page, where we provide an overview of the project, its goals, and the data sources used.
def aboutpage():
    st.title("Layering the Curb: Project Overview")

    page_selector()

    st.markdown(
        """
        <h4>Understanding DC's Parking, Traffic, and Transit Landscape</h4>
        <p>
        This project synthesizes parking, traffic, and public transportation data for Washington, DC, and uses spatial analysis and visualization at both the individual dataset and aggregated census tract levels.<br><br>
        <h5>Key issues explored:</h5>
        <ul>
            <li>How do parking, traffic, and transit access vary across neighborhoods?</li>
            <li>Where are the mismatches between parking supply, demand, and transit?</li>
            <li>How can data-driven insights inform better curb management and urban planning?</li>
            <li>Do our assumptions about parking and transit access hold true when we look at the data?</li>
        </ul>
        </p>
        <h5>Organization</h5>
        <p>
        The app is organized into two main pages:
        <ul>
            <li><b>Individual Data:</b> Explore and visualize each dataset (traffic, transit) separately.</li>
            <li><b>Census Aggregated:</b> View data aggregated at the census tract level for broader spatial analysis.</li>
        </ul>
        </p>
        <h5>Data Sources</h5>
       All data is sourced from publicly available datasets provided by the DC government, on the DC Open Data portal. The links are included below:
        <ul>
            <li><a href="https://opendata.dc.gov/datasets/DCGIS::parking-zones/about" target="_blank">DC Parking Zones</a></li>
            <li><a href="https://opendata.dc.gov/datasets/DCGIS::2023-traffic-volume/about" target="_blank">DC Traffic Volume</a></li>
            <li><a href="https://opendata.dc.gov/datasets/DCGIS::metro-bus-stops/about" target="_blank">DC Bus Stops</a></li>
            <li><a href="https://opendata.dc.gov/datasets/DCGIS::metro-stations-regional/about" target="_blank">DC Metro Rail Stations</a></li>
            <li><a href="https://opendata.dc.gov/datasets/DCGIS::census-tracts-in-2020" target="_blank">DC Census Tracts</a></li>
            <li><a href="https://catalog.data.gov/dataset/washington-dc-boundary-stone-area/resource/9244e169-36a8-4c3b-9c4e-e3d1b6fa6014" target="_blank">DC Boundary</a></li>
        </ul>
        <p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

aboutpage()