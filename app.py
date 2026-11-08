"""
app.py
------
Main Application for Campus Energy & Carbon Management System.
Provides the title banner, modern cool-tone green styling, sidebar navigation,
live database connection checking, and routes to each course project module.
"""

import streamlit as st
from database import test_connection
from pages.dashboard import render_dashboard_page
from pages.building_management import render_building_management_page
from pages.energy_monitoring import render_energy_monitoring_page
from pages.emission_factor_management import render_emission_factor_management_page
from pages.carbon_calculation import render_carbon_calculation_page
from pages.report_generation import render_report_generation_page

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION (must be the first Streamlit call)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Campus Energy & Carbon Management System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM STYLING (Cool-tone light green and off-white aesthetic)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container background and text */
    .stApp {
        background-color: #F9FBF9;
        color: #1C2D27;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        color: #1B5E20 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Metric card styling */
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

    /* Sidebar container styling */
    section[data-testid="stSidebar"] {
        background-color: #E8F5E9 !important;
        border-right: 1px solid #C8E6C9;
    }

    /* Button styling */
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & SYSTEM STATUS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌱 Campus Energy")
    st.caption("DBMS Course Project • PostgreSQL • Streamlit")
    st.markdown("---")

    selected_module = st.radio(
        "Navigation",
        options=[
            "Dashboard",
            "Building Management",
            "Energy Consumption Monitoring",
            "Emission Factor Management",
            "Carbon Emission Calculation",
            "Report Generation"
        ],
        format_func=lambda opt: {
            "Dashboard": "📊  Dashboard",
            "Building Management": "🏢  Building Management",
            "Energy Consumption Monitoring": "⚡  Energy Monitoring",
            "Emission Factor Management": "🌿  Emission Factors",
            "Carbon Emission Calculation": "🔬  Carbon Calculation",
            "Report Generation": "📑  Report Generation"
        }[opt],
        index=0
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
        "Course: Database Management Systems (DBMS)\n\n"
        "Stack: Streamlit • psycopg2 • Plotly"
    )


# -----------------------------------------------------------------------------
# MAIN CONTENT ROUTING
# -----------------------------------------------------------------------------
if not db_connected:
    st.error(
        "❌ Unable to connect to the PostgreSQL database. "
        "Please check your `.streamlit/secrets.toml` credentials and ensure your PostgreSQL server is running."
    )
    st.code(db_message)
else:
    if selected_module == "Dashboard":
        render_dashboard_page()

    elif selected_module == "Building Management":
        render_building_management_page()

    elif selected_module == "Energy Consumption Monitoring":
        render_energy_monitoring_page()

    elif selected_module == "Emission Factor Management":
        render_emission_factor_management_page()

    elif selected_module == "Carbon Emission Calculation":
        render_carbon_calculation_page()

    elif selected_module == "Report Generation":
        render_report_generation_page()
