"""
pages/energy_monitoring.py
--------------------------
Module 3: Energy Consumption Monitoring for Campus Energy & Carbon Management System.
Allows recording daily electricity consumption (kWh) per campus building.
Automatically determines and assigns the appropriate emission factor via READING_FACTOR.
Enforces the UNIQUE(building_id, reading_date) constraint and non-negative consumption.
"""

import streamlit as st
import pandas as pd
from datetime import date
from database import (
    get_all_buildings,
    get_all_energy_readings,
    get_next_reading_id,
    get_applicable_emission_factor,
    add_energy_reading_with_factor,
    update_energy_reading,
    delete_energy_reading
)


def render_energy_monitoring_page():
    st.header("⚡ Energy Consumption Monitoring")
    st.write(
        "Log, inspect, update, and manage campus electricity meter readings (kWh). "
        "The system automatically maps each reading to the latest applicable emission factor."
    )

    tab_view, tab_add, tab_update, tab_delete = st.tabs([
        "📊 View Energy Readings",
        "➕ Record New Reading",
        "✏️ Update Reading",
        "🗑️ Delete Reading"
    ])

    # =========================================================================
    # TAB 1: VIEW READINGS
    # =========================================================================
    with tab_view:
        st.subheader("Logged Campus Energy Readings")
        readings = get_all_energy_readings()

        if readings:
            df = pd.DataFrame(
                readings,
                columns=[
                    "Reading ID",
                    "Building ID",
                    "Building Name",
                    "Building Type",
                    "Reading Date",
                    "Consumption (kWh)",
                    "Factor ID",
                    "Assigned Factor Name",
                    "Factor Rate (kg CO2/kWh)",
                    "Emissions (kg CO2)"
                ]
            )

            # Reorder columns for optimal readability
            display_df = df[[
                "Reading ID",
                "Building Name",
                "Building Type",
                "Reading Date",
                "Consumption (kWh)",
                "Assigned Factor Name",
                "Factor Rate (kg CO2/kWh)",
                "Emissions (kg CO2)"
            ]]
            st.dataframe(display_df, use_container_width=True)
            st.caption(f"Total Readings Logged: {len(readings)}")
        else:
            st.info("No energy readings found in the database.")

    # =========================================================================
    # TAB 2: RECORD NEW READING
    # =========================================================================
    with tab_add:
        st.subheader("Record New Electricity Consumption")
        buildings = get_all_buildings()

        if not buildings:
            st.warning("Please add at least one campus building before recording energy readings.")
        else:
            next_reading_id = get_next_reading_id()

            # Building selection
            selected_building = st.selectbox(
                "Select Building",
                buildings,
                format_func=lambda b: f"ID {b[0]} - {b[1]} ({b[2]})",
                key="add_reading_building_select"
            )

            col1, col2 = st.columns(2)
            with col1:
                reading_date = st.date_input(
                    "Reading Date",
                    value=date.today(),
                    help="Date on which electricity meter reading was taken"
                )
            with col2:
                reading_id_input = st.number_input(
                    "Reading ID",
                    min_value=1,
                    value=int(next_reading_id),
                    step=1,
                    help="Unique integer identifier for the energy reading"
                )

            consumption_kwh = st.number_input(
                "Electricity Consumption (kWh)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                format="%.3f",
                help="Meter reading in kilowatt-hours (must be >= 0)"
            )

            # Live preview of applicable emission factor
            applicable_factor = get_applicable_emission_factor(reading_date)
            if applicable_factor:
                st.success(
                    f"🌿 Applicable Factor Detected: **{applicable_factor[1]}** "
                    f"({float(applicable_factor[2]):.6f} kg CO₂/kWh, valid from {applicable_factor[3]})."
                )
                estimated_co2 = float(consumption_kwh) * float(applicable_factor[2])
                st.caption(f"Estimated Carbon Emission: **{estimated_co2:,.2f} kg CO₂**")
            else:
                st.error(
                    f"⚠️ No emission factor is valid on or before **{reading_date}**. "
                    f"You must create a valid emission factor in the Emission Factor module before saving this reading."
                )

            if st.button("➕ Save Energy Reading", disabled=(applicable_factor is None)):
                try:
                    add_energy_reading_with_factor(
                        reading_id=int(reading_id_input),
                        building_id=int(selected_building[0]),
                        reading_date=reading_date,
                        consumption_kwh=float(consumption_kwh)
                    )
                    st.success(
                        f"Successfully recorded reading ID {reading_id_input} for '{selected_building[1]}' "
                        f"with factor '{applicable_factor[1]}'."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not record reading: {exc}")

    # =========================================================================
    # TAB 3: UPDATE READING
    # =========================================================================
    with tab_update:
        st.subheader("Update an Existing Energy Reading")
        readings = get_all_energy_readings()
        buildings = get_all_buildings()

        if readings and buildings:
            # Map building IDs for dropdown selection
            building_map = {b[0]: b for b in buildings}

            selected_reading = st.selectbox(
                "Select a reading to edit",
                readings,
                format_func=lambda r: (
                    f"Reading ID {r[0]} | {r[2]} | Date: {r[4]} | {float(r[5]):,.1f} kWh"
                ),
                key="select_update_reading"
            )

            current_building_id = selected_reading[1]
            current_building = building_map.get(current_building_id, buildings[0])
            building_index = (
                [b[0] for b in buildings].index(current_building_id)
                if current_building_id in [b[0] for b in buildings] else 0
            )

            with st.form(f"form_update_reading_{selected_reading[0]}"):
                st.info(f"Modifying Reading ID: {selected_reading[0]}")

                updated_building = st.selectbox(
                    "Campus Building",
                    buildings,
                    index=building_index,
                    format_func=lambda b: f"ID {b[0]} - {b[1]} ({b[2]})"
                )

                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    updated_date = st.date_input(
                        "Reading Date",
                        value=selected_reading[4]
                    )
                with col_u2:
                    updated_kwh = st.number_input(
                        "Electricity Consumption (kWh)",
                        min_value=0.0,
                        value=float(selected_reading[5]),
                        step=10.0,
                        format="%.3f"
                    )

                submit_update_reading = st.form_submit_button("💾 Update Reading")

            if submit_update_reading:
                try:
                    update_energy_reading(
                        reading_id=selected_reading[0],
                        building_id=int(updated_building[0]),
                        reading_date=updated_date,
                        consumption_kwh=float(updated_kwh)
                    )
                    st.success(f"Reading ID {selected_reading[0]} updated successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not update reading: {exc}")
        else:
            st.info("No energy readings available to update.")

    # =========================================================================
    # TAB 4: DELETE READING
    # =========================================================================
    with tab_delete:
        st.subheader("Delete an Energy Reading")
        readings = get_all_energy_readings()

        if readings:
            selected_reading_del = st.selectbox(
                "Select a reading to delete",
                readings,
                format_func=lambda r: (
                    f"Reading ID {r[0]} | {r[2]} | Date: {r[4]} | {float(r[5]):,.1f} kWh"
                ),
                key="select_delete_reading"
            )

            st.warning(
                f"Deleting Reading ID **{selected_reading_del[0]}** will remove the consumption record "
                f"and its emission factor assignment from READING_FACTOR."
            )

            confirm_del_reading = st.checkbox(
                f"I confirm that I want to permanently delete Reading ID {selected_reading_del[0]}",
                key="confirm_delete_reading_box"
            )

            if st.button("🗑️ Delete Selected Reading", disabled=not confirm_del_reading):
                try:
                    delete_energy_reading(selected_reading_del[0])
                    st.success(f"Reading ID {selected_reading_del[0]} deleted successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete reading: {exc}")
        else:
            st.info("No energy readings available to delete.")
