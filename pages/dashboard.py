"""
pages/dashboard.py
Dashboard and Reports for Campus Energy & Carbon Management System.
"""

import streamlit as st
import plotly.express as px
from database import (
    get_building_consumption_breakdown,
    get_monthly_dashboard_data
)


def render_dashboard_page():
    st.header("📊 Campus Energy & Carbon Dashboard")

    try:
        building_df = get_building_consumption_breakdown()
        monthly_df = get_monthly_dashboard_data()
    except Exception as e:
        st.error(f"Could not load dashboard data: {e}")
        return

    if building_df.empty:
        st.info("No building data is available yet.")
    else:
        electricity_df = building_df[building_df["total_consumption_kwh"] > 0]
        emissions_df = building_df[building_df["total_emissions_kg"] > 0]

        st.subheader("Highest Consuming and Emitting Buildings")
        col1, col2 = st.columns(2)

        with col1:
            if not electricity_df.empty:
                highest = electricity_df.loc[electricity_df["total_consumption_kwh"].idxmax()]
                st.metric(
                    "Highest Electricity Consumption",
                    highest["building_name"],
                    f'{highest["total_consumption_kwh"]:,.2f} kWh'
                )
            else:
                st.info("No electricity readings recorded yet.")

        with col2:
            if not emissions_df.empty:
                highest = emissions_df.loc[emissions_df["total_emissions_kg"].idxmax()]
                st.metric(
                    "Highest Carbon Emissions",
                    highest["building_name"],
                    f'{highest["total_emissions_kg"]:,.2f} kg CO₂'
                )
            else:
                st.info("No emission activities recorded yet.")

        st.divider()
        st.subheader("Building-wise Distribution")
        col1, col2 = st.columns(2)

        with col1:
            if not electricity_df.empty:
                fig = px.pie(
                    electricity_df,
                    names="building_name",
                    values="total_consumption_kwh",
                    title="Electricity Consumption by Building",
                    hole=0.35,
                    color_discrete_sequence=px.colors.sequential.Greens
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No electricity data available for the pie chart.")

        with col2:
            if not emissions_df.empty:
                fig = px.pie(
                    emissions_df,
                    names="building_name",
                    values="total_emissions_kg",
                    title="Carbon Emissions by Building",
                    hole=0.35,
                    color_discrete_sequence=px.colors.sequential.Greens
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No emission data available for the pie chart.")

    st.divider()
    st.subheader("Month-wise Trends")

    if monthly_df.empty:
        st.info("No monthly data is available yet.")
        return

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            monthly_df,
            x="month",
            y="total_consumption_kwh",
            title="Monthly Electricity Consumption",
            labels={
                "month": "Month",
                "total_consumption_kwh": "Electricity (kWh)"
            },
            color_discrete_sequence=["#2E7D32"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            monthly_df,
            x="month",
            y="total_emissions_kg",
            title="Monthly Carbon Emissions",
            labels={
                "month": "Month",
                "total_emissions_kg": "Emissions (kg CO₂)"
            },
            color_discrete_sequence=["#2E7D32"]
        )
        st.plotly_chart(fig, use_container_width=True)
