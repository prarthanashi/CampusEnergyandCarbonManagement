"""
pages/emission_factor_management.py
-----------------------------------
Module 4: Emission Factor Management for Campus Energy & Carbon Management System.
Allows users to add, view, update, and delete emission factors (kg CO2 / kWh).
Validates non-negative factors and enforces foreign key integrity by preventing
deletion of factors that are actively referenced by energy readings.
"""

import streamlit as st
import pandas as pd
from datetime import date
from database import (
    get_all_emission_factors,
    get_next_factor_id,
    add_emission_factor,
    update_emission_factor,
    delete_emission_factor
)


def render_emission_factor_management_page():
    st.header("🌿 Emission Factor Management")
    st.write(
        "Maintain grid emission factors (kg CO₂ / kWh) and their validity timelines. "
        "Emission factors convert raw electricity consumption into carbon footprint estimates."
    )

    tab_view, tab_add, tab_update, tab_delete = st.tabs([
        "📑 View Emission Factors",
        "➕ Add Emission Factor",
        "✏️ Update Emission Factor",
        "🗑️ Delete Emission Factor"
    ])

    # =========================================================================
    # TAB 1: VIEW FACTORS
    # =========================================================================
    with tab_view:
        st.subheader("All Registered Emission Factors")
        factors = get_all_emission_factors()

        if factors:
            df = pd.DataFrame(
                factors,
                columns=["Factor ID", "Factor Name", "kg CO2 / kWh", "Valid From"]
            )
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total Emission Factors Configured: {len(factors)}")

            st.info(
                "💡 **How Validity Works:** When an energy reading is logged, the system selects "
                "the latest factor whose `Valid From` date is on or before the reading date."
            )
        else:
            st.info("No emission factors registered in the database yet.")

    # =========================================================================
    # TAB 2: ADD EMISSION FACTOR
    # =========================================================================
    with tab_add:
        st.subheader("Add a New Emission Factor")
        next_factor_id = get_next_factor_id()

        with st.form("form_add_factor", clear_on_submit=True):
            st.caption("Suggested Factor ID is prefilled automatically.")
            col_id, col_date = st.columns(2)
            with col_id:
                factor_id = st.number_input(
                    "Factor ID",
                    min_value=1,
                    value=int(next_factor_id),
                    step=1,
                    help="Unique integer identifier for the emission factor"
                )
            with col_date:
                valid_from = st.date_input(
                    "Valid From Date",
                    value=date.today(),
                    help="Date from which this factor applies to energy readings"
                )

            factor_name = st.text_input(
                "Emission Factor Name",
                placeholder="e.g. State Grid Electricity Factor 2026",
                max_chars=100
            )

            kg_co2 = st.number_input(
                "Emission Factor Rate (kg CO₂ per kWh)",
                min_value=0.0,
                value=0.650000,
                step=0.01,
                format="%.6f",
                help="Kilograms of carbon dioxide emitted per kilowatt-hour generated (must be >= 0)"
            )

            submit_add_factor = st.form_submit_button("➕ Add Emission Factor")

        if submit_add_factor:
            if not factor_name.strip():
                st.error("Please enter a valid name for the emission factor.")
            else:
                try:
                    add_emission_factor(
                        factor_id=int(factor_id),
                        factor_name=factor_name.strip(),
                        kg_co2_per_kwh=float(kg_co2),
                        valid_from=valid_from
                    )
                    st.success(f"Emission Factor '{factor_name.strip()}' added successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not add emission factor: {exc}")

    # =========================================================================
    # TAB 3: UPDATE EMISSION FACTOR
    # =========================================================================
    with tab_update:
        st.subheader("Update an Existing Emission Factor")
        factors = get_all_emission_factors()

        if factors:
            selected_factor = st.selectbox(
                "Select an emission factor to edit",
                factors,
                format_func=lambda f: f"ID {f[0]} - {f[1]} ({float(f[2]):.4f} kg CO2/kWh | Valid: {f[3]})",
                key="select_update_factor"
            )

            with st.form(f"form_update_factor_{selected_factor[0]}"):
                st.info(f"Modifying Emission Factor ID: {selected_factor[0]}")

                updated_name = st.text_input(
                    "Emission Factor Name",
                    value=selected_factor[1],
                    max_chars=100
                )

                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    updated_kg_co2 = st.number_input(
                        "kg CO₂ per kWh",
                        min_value=0.0,
                        value=float(selected_factor[2]),
                        step=0.01,
                        format="%.6f"
                    )
                with col_u2:
                    updated_valid_from = st.date_input(
                        "Valid From Date",
                        value=selected_factor[3]
                    )

                submit_update_factor = st.form_submit_button("💾 Save Updates")

            if submit_update_factor:
                if not updated_name.strip():
                    st.error("Emission factor name cannot be empty.")
                else:
                    try:
                        update_emission_factor(
                            factor_id=selected_factor[0],
                            factor_name=updated_name.strip(),
                            kg_co2_per_kwh=float(updated_kg_co2),
                            valid_from=updated_valid_from
                        )
                        st.success(f"Emission Factor ID {selected_factor[0]} updated successfully!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update emission factor: {exc}")
        else:
            st.info("No emission factors available to update.")

    # =========================================================================
    # TAB 4: DELETE EMISSION FACTOR
    # =========================================================================
    with tab_delete:
        st.subheader("Delete an Emission Factor")
        factors = get_all_emission_factors()

        if factors:
            selected_factor_del = st.selectbox(
                "Select an emission factor to delete",
                factors,
                format_func=lambda f: f"ID {f[0]} - {f[1]} ({float(f[2]):.4f} kg CO2/kWh | Valid: {f[3]})",
                key="select_delete_factor"
            )

            st.warning(
                f"You are selecting **ID {selected_factor_del[0]} - {selected_factor_del[1]}** for deletion. "
                f"If this factor is assigned to any existing energy readings, deletion will be blocked to maintain data integrity."
            )

            confirm_delete_factor = st.checkbox(
                f"I confirm that I want to delete emission factor '{selected_factor_del[1]}'",
                key="confirm_delete_factor_box"
            )

            if st.button("🗑️ Delete Selected Factor", disabled=not confirm_delete_factor):
                try:
                    delete_emission_factor(selected_factor_del[0])
                    st.success(f"Emission Factor '{selected_factor_del[1]}' deleted successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Cannot delete emission factor: {exc}")
        else:
            st.info("No emission factors available to delete.")
