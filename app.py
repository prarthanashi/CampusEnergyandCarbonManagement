"""
app.py
------
Main application for the Campus Energy & Carbon Management System.
Provides sidebar navigation and routes to each application module.
The Dashboard also serves as the Reports & Analytics page.
"""

import streamlit as st

from database import test_connection
from pages.dashboard import render_dashboard_page
from pages.building_management import render_building_management_page
from pages.energy_monitoring import render_energy_monitoring_page
from pages.carbon_emissions import render_carbon_emissions_page


# ---------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Campus Energy & Carbon Management System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------------------
# CUSTOM STYLING - KEEPING THE EXISTING GREEN AND WHITE THEME
# ---------------------------------------------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #F9FBF9;
        color: #1C2D27;
    }

    h1, h2, h3 {
        color: #1B5E20 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #C8E6C9;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    div[data-testid="stMetricLabel"] {
        color: #2E7D32 !important;
        font-weight: 600;
        font-size: 0.95rem;
    }

    div[data-testid="stMetricValue"] {
        color: #1B5E20 !important;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background-color: #E8F5E9 !important;
        border-right: 1px solid #C8E6C9;
    }

    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 1rem;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #1B5E20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# SIDEBAR NAVIGATION AND DATABASE STATUS
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🌱 Campus Energy")
    st.caption("DBMS Course Project • PostgreSQL • Streamlit")
    st.markdown("---")

    selected_module = st.radio(
        "Navigation",
        options=[
            "Dashboard / Reports",
            "Building Management",
            "Energy Consumption Monitoring",
            "Carbon Emission Calculation"
        ],
        format_func=lambda option: {
            "Dashboard / Reports": "📊  Dashboard & Reports",
            "Building Management": "🏢  Building Management",
            "Energy Consumption Monitoring": "⚡  Energy Monitoring",
            "Carbon Emission Calculation": "🔬  Carbon Emissions"
        }[option]
    )

    st.markdown("---")
    st.markdown("### 🔌 Database Connection")

    db_connected, db_message = test_connection()

    if db_connected:
        st.success("● Connected to PostgreSQL")
        st.caption("Database: `campus_energy_db`")
    else:
        st.error("● Database Disconnected")
        st.caption(f"Error: {db_message}")

    st.markdown("---")
    st.caption(
        "Computer Science & Engineering\n\n"
        "Course: Database System Design\n\n"
        "Stack: Streamlit • psycopg2 • Plotly"
    )


# ---------------------------------------------------------------------
# MAIN PAGE ROUTING
# ---------------------------------------------------------------------

if not db_connected:
    st.error(
        "Unable to connect to PostgreSQL. Check your "
        ".streamlit/secrets.toml credentials and make sure "
        "the PostgreSQL server is running."
    )
    st.code(db_message)

elif selected_module == "Dashboard / Reports":
    render_dashboard_page()

elif selected_module == "Building Management":
    render_building_management_page()

elif selected_module == "Energy Consumption Monitoring":
    render_energy_monitoring_page()

elif selected_module == "Carbon Emission Calculation":
    render_carbon_emissions_page()
