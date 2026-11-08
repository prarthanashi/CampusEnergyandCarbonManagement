"""
pages/dashboard.py
------------------
Module 1: Dashboard for Campus Energy & Carbon Management System.
Displays high-level KPI cards, consumption and emission charts by building,
and date-wise consumption comparisons using Plotly.
All data is retrieved from PostgreSQL using SQL queries.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import (
    get_dashboard_summary_metrics,
    get_building_consumption_breakdown,
    get_datewise_consumption_breakdown
)


def render_dashboard_page():
    st.header("📊 Campus Energy & Carbon Dashboard")
    st.write(
        "Real-time overview of campus electricity consumption, greenhouse gas emissions, "
        "and building efficiency metrics calculated directly from PostgreSQL."
    )

    try:
        # Retrieve aggregate metrics from PostgreSQL
        metrics = get_dashboard_summary_metrics()
        b_df = get_building_consumption_breakdown()
        d_df = get_datewise_consumption_breakdown()
    except Exception as e:
        st.error(f"Error loading dashboard data from database: {e}")
        return

    # -------------------------------------------------------------
    # 1. CORE KPI METRICS ROW
    # -------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Buildings",
            value=f"{metrics['total_buildings']}",
            help="Total campus facilities registered in database (COUNT query)"
        )

    with col2:
        st.metric(
            label="Total Electricity",
            value=f"{metrics['total_consumption_kwh']:,.1f} kWh",
            help="Cumulative electricity consumption recorded (SUM query)"
        )

    with col3:
        st.metric(
            label="Total Carbon Emissions",
            value=f"{metrics['total_emissions_kg']:,.1f} kg CO₂",
            help="Total carbon emissions calculated via SQL Join with emission factors"
        )

    with col4:
        st.metric(
            label="Average Reading",
            value=f"{metrics['avg_consumption_kwh']:,.1f} kWh",
            help="Average electricity consumed per recorded reading (AVG query)"
        )

    st.markdown("---")

    # -------------------------------------------------------------
    # 2. BUILDING-LEVEL VISUALIZATIONS
    # -------------------------------------------------------------
    st.subheader("Building-Wise Energy & Carbon Comparison")

    if not b_df.empty and b_df["Total Consumption (kWh)"].sum() > 0:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_consumption = px.bar(
                b_df,
                x="Building Name",
                y="Total Consumption (kWh)",
                color="Building Type",
                title="Electricity Consumption by Building (kWh)",
                text_auto=".1f",
                color_discrete_sequence=px.colors.qualitative.Dark2
            )
            fig_consumption.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis_title="Campus Building",
                yaxis_title="Total kWh",
                legend_title="Building Type"
            )
            st.plotly_chart(fig_consumption, use_container_width=True)

        with col_chart2:
            fig_emissions = px.bar(
                b_df,
                x="Building Name",
                y="Total Emissions (kg CO2)",
                color="Building Type",
                title="Carbon Emissions by Building (kg CO₂)",
                text_auto=".1f",
                color_discrete_sequence=px.colors.qualitative.Pastel1
            )
            fig_emissions.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis_title="Campus Building",
                yaxis_title="Carbon Emissions (kg CO₂)",
                legend_title="Building Type"
            )
            st.plotly_chart(fig_emissions, use_container_width=True)
    else:
        st.info("No energy reading data available yet to display building comparisons.")

    # -------------------------------------------------------------
    # 3. DATE-WISE CONSUMPTION & EMISSIONS COMPARISON
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("Date-Wise Consumption & Emissions Trend")

    if not d_df.empty and len(d_df) > 0:
        # Convert date to string for clean categorical timeline display
        d_df["Date String"] = d_df["Reading Date"].astype(str)

        fig_trend = go.Figure()

        # Bar for electricity consumption
        fig_trend.add_trace(go.Bar(
            x=d_df["Date String"],
            y=d_df["Total Consumption (kWh)"],
            name="Electricity Consumption (kWh)",
            marker_color="#2E7D32",
            yaxis="y1"
        ))

        # Line for carbon emissions
        fig_trend.add_trace(go.Scatter(
            x=d_df["Date String"],
            y=d_df["Total Emissions (kg CO2)"],
            name="Carbon Emissions (kg CO₂)",
            line=dict(color="#D32F2F", width=3),
            mode="lines+markers",
            yaxis="y2"
        ))

        fig_trend.update_layout(
            title="Date-Wise Total Electricity Consumption vs. Carbon Emissions",
            xaxis=dict(title="Reading Date"),
            yaxis=dict(
                title=dict(text="Electricity Consumption (kWh)", font=dict(color="#2E7D32")),
                tickfont=dict(color="#2E7D32")
            ),
            yaxis2=dict(
                title=dict(text="Carbon Emissions (kg CO₂)", font=dict(color="#D32F2F")),
                tickfont=dict(color="#D32F2F"),
                overlaying="y",
                side="right"
            ),
            legend=dict(x=0.01, y=1.1, orientation="h"),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )

        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Insufficient reading dates to display timeline comparisons.")

    # -------------------------------------------------------------
    # 4. BUILDING SUMMARY TABLE
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("Building Summary Breakdown")
    if not b_df.empty:
        st.dataframe(b_df, use_container_width=True)
    else:
        st.info("No building data found.")
