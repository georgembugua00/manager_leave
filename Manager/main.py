
import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# Page configuration
st.set_page_config(
    page_title="Leave Request Manager",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)



# ========== PAGE SETUP ==========

landing_page = st.Page(
    page="home_page.py",
    title=" Home",
    icon=":material/support_agent:",
    default=True
)



team_overview = st.Page(
    page="team_leaves.py",
    title="Team Overview",
    icon=":material/cognition:"
)



# ========== NAVIGATION ==========
page_navigator = st.navigation({
    "Home Page" : [landing_page],
    "Team Overview": [team_overview],
})

page_navigator.run()