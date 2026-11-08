"""
pages/report_generation.py
--------------------------
Module 6: Report Generation for Campus Energy & Carbon Management System.
Allows parameterized filtering by building and date range.
Generates comprehensive electricity consumption and carbon footprint audit reports,
with one-click CSV export functionality.
"""

import streamlit as st
import pandas as pd
from datetime import date
from database import (
    get_all_buildings,
    get_filtered_report_data,
    get_min_max_reading_dates
)


def render_report_generation_page():
    st.header("📑 Campus Energy & Carbon Report Generation")
    st.write(
        "Generate customized audit reports filtered by campus facility and observation timeline. "
        "Download data tables as CSV spreadsheets for compliance and academic presentations."
    )

    buildings = get_all_buildings()
    min_db_date, max_db_date = get_min_max_reading_dates()

    # Default fallback dates if no readings exist
    default_start = min_db_date if min_db_date else date(2025, 1, 1)
    default_end = max_db_date if max_db_date else date.today()

    # =========================================================================
    # FILTER CONTROLS PANEL
    # =========================================================================
    with st.expander("🔍 Report Filter Controls", expanded=True):
        col_b, col_s, col_e = st.columns(3)

        with col_b:
            # Building dropdown options with "All Buildings" as the default
            building_options = [("all", "All Campus Buildings")] + [
                (b[0], f"{b[1]} ({b[2]})") for b in buildings
            ]
            selected_option = st.selectbox(
                "Select Facility",
                options=building_options,
                format_func=lambda opt: opt[1]
            )
            selected_building_id = None if selected_option[0] == "all" else selected_option[0]

        with col_s:
            start_date = st.date_input("Start Date", value=default_start)

        with col_e:
            end_date = st.date_input("End Date", value=default_end)

    if start_date > end_date:
        st.error("Error: Start Date cannot be after End Date.")
        return

    # Fetch report using parameterized SQL query
    try:
        report_df = get_filtered_report_data(
            building_id=selected_building_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as exc:
        st.error(f"Error generating report: {exc}")
        return

    # =========================================================================
    # SUMMARY AUDIT CARDS
    # =========================================================================
    st.subheader("Filtered Period Summary")

    if not report_df.empty:
        total_kwh = float(report_df["Consumption (kWh)"].sum())
        total_co2 = float(report_df["Calculated Emissions (kg CO2)"].sum())
        record_count = len(report_df)
        avg_intensity = (total_co2 / total_kwh) if total_kwh > 0 else 0.0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", f"{record_count}")
        with col2:
            st.metric("Total Consumption", f"{total_kwh:,.1f} kWh")
        with col3:
            st.metric("Total Carbon Emissions", f"{total_co2:,.2f} kg CO₂")
        with col4:
            st.metric("Emission Intensity", f"{avg_intensity:.4f} kg/kWh")

        st.markdown("---")

        # =====================================================================
        # REPORT TABLES
        # =====================================================================
        tab_full, tab_consumption, tab_emissions = st.tabs([
            "📋 Comprehensive Report",
            "⚡ Electricity Consumption Audit",
            "🌿 Carbon Emission Audit"
        ])

        with tab_full:
            st.dataframe(report_df, use_container_width=True)

        with tab_consumption:
            consumption_df = report_df[[
                "Building Name",
                "Building Type",
                "Reading Date",
                "Consumption (kWh)"
            ]]
            st.dataframe(consumption_df, use_container_width=True)

        with tab_emissions:
            emissions_df = report_df[[
                "Building Name",
                "Reading Date",
                "Emission Factor Name",
                "Emission Factor (kg CO2/kWh)",
                "Calculated Emissions (kg CO2)"
            ]]
            st.dataframe(emissions_df, use_container_width=True)

        st.markdown("---")

        # =====================================================================
        # CSV EXPORT BUTTON
        # =====================================================================
        csv_data = report_df.to_csv(index=False).encode("utf-8")
        building_slug = "all_buildings" if selected_building_id is None else f"building_{selected_building_id}"
        csv_filename = f"campus_energy_report_{building_slug}_{start_date}_{end_date}.csv"

        st.download_button(
            label="📥 Download Report as CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            help="Click to download the currently filtered dataset as a spreadsheet file."
        )

    else:
        st.info("No records matched the selected building and date criteria.")
