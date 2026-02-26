# run the about page
import streamlit as st
from utils import page_selector

#Main page, where users land when opening the application.
if __name__ == "__main__":
    st.markdown(
        """
        <h1 style='text-align: center; font-size: 5em; letter-spacing: 0.05em; margin-top: 2em; margin-bottom: 0.2em;'>
            LAYERING THE CURB:<br>PROJECT OVERVIEW
        </h1>
        <p style='text-align: center; font-size: 1.5em; color: gray; margin-bottom: 2em;'>
            <i>A Project by Matthewos Mesfin</i>
        </p>
        """,
        unsafe_allow_html=True
    )

    page_selector()