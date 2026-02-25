import streamlit as st
from utils import page_selector

st.set_page_config(page_title="About | Layering the Curb", layout="wide")

def aboutpage():
    st.title("Layering the Curb: Project Overview")

    page_selector()

    st.markdown(
        """
        <h4>Understanding DC's Parking, Traffic, and Transit Landscape</h4>
        <p>
        This project brings together parking, traffic, and public transportation data for Washington, DC, enabling spatial analysis and visualization at both the individual dataset and aggregated census tract levels.<br><br>
        <b>Key issues explored:</b>
        <ul>
            <li>How do parking, traffic, and transit access vary across neighborhoods?</li>
            <li>Where are the mismatches between parking supply, demand, and transit?</li>
            <li>How can data-driven insights inform better curb management and urban planning?</li>
        </ul>
        </p>
        <h5>Project Organization</h5>
        <p>
        The app is organized into two main pages:
        <ul>
            <li><b>Individual Data:</b> Explore and visualize each dataset (traffic, transit) separately.</li>
            <li><b>Census Aggregated:</b> View data aggregated at the census tract level for broader spatial analysis.</li>
        </ul>
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

aboutpage()