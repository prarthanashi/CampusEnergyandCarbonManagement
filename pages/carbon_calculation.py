"""
pages/carbon_calculation.py
---------------------------
Module 5: Carbon Emission Calculation for Campus Energy & Carbon Management System.
Demonstrates relational joins across BUILDING, ENERGY_READING, READING_FACTOR,
and EMISSION_FACTOR.
Calculates: Carbon Emission (kg CO2) = Consumption (kWh) * Emission Factor (kg CO2/kWh).
All calculations and aggregations are performed dynamically via SQL queries.
"""

import streamlit as st
import plotly.express as px
from database import (
    get_detailed_carbon_emissions,
    get_buildingwise_carbon_emissions,
    get_datewise_carbon_emissions
)


def render_carbon_calculation_page():
    st.header("🔬 Carbon Emission Calculation Engine")
    st.write(
        "Demonstrates dynamic calculation of greenhouse gas emissions by joining the four core "
        "relational tables (`BUILDING`, `ENERGY_READING`, `READING_FACTOR`, and `EMISSION_FACTOR`)."
    )

    # Educational Formula Callout for college project presentation
    st.info(
        "📐 **Calculation Formula:**\n\n"
        "$$\\text{Carbon Emission } (\\text{kg CO}_2) = "
        "\\text{Electricity Consumption } (\\text{kWh}) \\times "
        "\\text{Emission Factor } (\\text{kg CO}_2/\\text{kWh})$$\n\n"
        "Emissions are computed dynamically via SQL queries rather than stored statically in a column."
    )

    try:
        detailed_df = get_detailed_carbon_emissions()
        buildingwise_df = get_buildingwise_carbon_emissions()
        datewise_df = get_datewise_carbon_emissions()
    except Exception as exc:
        st.error(f"Error executing carbon calculation queries: {exc}")
        return

    # =========================================================================
    # 1. SUMMARY METRICS
    # =========================================================================
    if not detailed_df.empty:
        total_co2 = float(detailed_df["Calculated Emissions (kg CO2)"].sum())
        total_kwh = float(detailed_df["Consumption (kWh)"].sum())
        avg_intensity = (total_co2 / total_kwh) if total_kwh > 0 else 0.0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Total Campus Carbon Emissions",
                value=f"{total_co2:,.2f} kg CO₂",
                help="Sum of calculated emissions across all joined readings"
            )
        with col2:
            st.metric(
                label="Total Electricity Consumed",
                value=f"{total_kwh:,.1f} kWh"
            )
        with col3:
            st.metric(
                label="Weighted Emission Intensity",
                value=f"{avg_intensity:.4f} kg CO₂/kWh",
                help="Overall average carbon intensity for campus electricity"
            )

        st.markdown("---")

        # =====================================================================
        # 2. DETAILED JOINED RECORDS TABLE
        # =====================================================================
        st.subheader("1. Detailed Joined Reading & Emission Records")
        st.caption(
            "SQL Query: `JOIN building ... JOIN energy_reading ... JOIN reading_factor ... JOIN emission_factor`"
        )
        st.dataframe(detailed_df, use_container_width=True)

        st.markdown("---")

        # =====================================================================
        # 3. BUILDING-WISE CARBON EMISSIONS
        # =====================================================================
        st.subheader("2. Building-Wise Carbon Emissions Summary")
        st.caption(
            "SQL Aggregation: `GROUP BY b.building_id, b.building_name, b.building_type` "
            "with `SUM`, `AVG`, and `COUNT`"
        )

        col_b_table, col_b_chart = st.columns([1.1, 1])

        with col_b_table:
            st.dataframe(buildingwise_df, use_container_width=True)

        with col_b_chart:
            fig_b_emissions = px.bar(
                buildingwise_df,
                x="Building Name",
                y="Total Emissions (kg CO2)",
                color="Building Type",
                text_auto=".1f",
                title="Emissions by Building (kg CO₂)",
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            fig_b_emissions.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis_title="Building",
                yaxis_title="Total kg CO₂"
            )
            st.plotly_chart(fig_b_emissions, use_container_width=True)

        st.markdown("---")

        # =====================================================================
        # 4. DATE-WISE CARBON EMISSIONS
        # =====================================================================
        st.subheader("3. Date-Wise Carbon Emissions Summary")
        st.caption("SQL Aggregation: `GROUP BY e.reading_date ORDER BY e.reading_date ASC`")

        col_d_table, col_d_chart = st.columns([1.1, 1])

        with col_d_table:
            st.dataframe(datewise_df, use_container_width=True)

        with col_d_chart:
            # Convert date to string for clean categorical timeline display
            datewise_df_chart = datewise_df.copy()
            datewise_df_chart["Reading Date Str"] = datewise_df_chart["Reading Date"].astype(str)

            fig_d_emissions = px.line(
                datewise_df_chart,
                x="Reading Date Str",
                y="Total Emissions (kg CO2)",
                markers=True,
                title="Daily Campus Carbon Footprint (kg CO₂)",
                color_discrete_sequence=["#2E7D32"]
            )
            fig_d_emissions.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis_title="Reading Date",
                yaxis_title="Carbon Emissions (kg CO₂)"
            )
            st.plotly_chart(fig_d_emissions, use_container_width=True)

    else:
        st.info(
            "No joined energy readings and emission factor records found. "
            "Ensure that energy readings have assigned emission factors."
        )
