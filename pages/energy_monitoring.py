import streamlit as st
from datetime import date
from database import (
    get_all_buildings,
    get_all_energy_readings,
    get_next_reading_id,
    add_energy_reading,
    update_energy_reading,
    delete_energy_reading
)


def render_energy_monitoring_page():
    st.header("⚡ Energy Consumption Monitoring")
    st.write("Monitor electricity consumption across campus buildings.")

    buildings = get_all_buildings()
    readings = get_all_energy_readings()

    if readings:
        header = st.columns([1, 1.8, 1.3, 1.2, 1.3, 1.7])
        labels = [
            "Reading ID", "Building", "Building Type",
            "Reading Date", "Consumption (kWh)", "Actions"
        ]
        for column, label in zip(header, labels):
            column.markdown(f"**{label}**")

        for reading in readings:
            row = st.columns([1, 1.8, 1.3, 1.2, 1.3, 1.7])
            row[0].write(reading[0])
            row[1].write(reading[2])
            row[2].write(reading[3])
            row[3].write(reading[4])
            row[4].write(f"{reading[5]:,.3f}")
            edit_button, delete_button = row[5].columns(2)

            if edit_button.button("Edit", key=f"edit_reading_{reading[0]}"):
                st.session_state["editing_reading_id"] = reading[0]
                st.session_state.pop("deleting_reading_id", None)

            if delete_button.button("Delete", key=f"delete_reading_{reading[0]}"):
                st.session_state["deleting_reading_id"] = reading[0]
                st.session_state.pop("editing_reading_id", None)

        st.caption(f"Total Readings: {len(readings)}")

        editing_id = st.session_state.get("editing_reading_id")
        selected_reading = next(
            (reading for reading in readings if reading[0] == editing_id),
            None
        )
        if selected_reading:
            st.subheader(f"Edit Reading {selected_reading[0]}")
            building_index = next(
                (
                    index for index, building in enumerate(buildings)
                    if building[0] == selected_reading[1]
                ),
                0
            )
            with st.form("edit_energy_reading_form"):
                building = st.selectbox(
                    "Select Building",
                    buildings,
                    index=building_index,
                    format_func=lambda item: f"{item[1]} ({item[2]})"
                )
                reading_date = st.date_input(
                    "Reading Date", value=selected_reading[4]
                )
                consumption = st.number_input(
                    "Electricity Consumption (kWh)",
                    min_value=0.0,
                    value=float(selected_reading[5]),
                    step=10.0,
                    format="%.3f"
                )
                save_column, cancel_column = st.columns(2)
                with save_column:
                    submitted = st.form_submit_button("Save Changes")
                with cancel_column:
                    cancelled = st.form_submit_button("Cancel")

                if submitted:
                    try:
                        update_energy_reading(
                            selected_reading[0],
                            int(building[0]),
                            reading_date,
                            float(consumption)
                        )
                        st.session_state.pop("editing_reading_id", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update reading: {exc}")

                if cancelled:
                    st.session_state.pop("editing_reading_id", None)
                    st.rerun()
    else:
        st.info("No electricity readings recorded yet.")

    deleting_id = st.session_state.get("deleting_reading_id")
    selected_for_deletion = next(
        (reading for reading in readings if reading[0] == deleting_id),
        None
    )
    if selected_for_deletion:
        st.warning(
            f"Delete reading {deleting_id} for {selected_for_deletion[2]}?"
        )
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm Delete", key="confirm_delete_reading"):
            try:
                delete_energy_reading(deleting_id)
                st.session_state.pop("deleting_reading_id", None)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not delete reading: {exc}")

        if cancel.button("Cancel", key="cancel_delete_reading"):
            st.session_state.pop("deleting_reading_id", None)
            st.rerun()

    st.divider()

    with st.expander("➕ Add Electricity Reading"):
        if not buildings:
            st.warning("Add a building before recording electricity consumption.")
        else:
            with st.form("add_energy_reading", clear_on_submit=True):
                reading_id = st.number_input(
                    "Reading ID",
                    min_value=1,
                    value=int(get_next_reading_id()),
                    step=1
                )

                building = st.selectbox(
                    "Select Building",
                    buildings,
                    format_func=lambda item: f"{item[1]} ({item[2]})"
                )

                reading_date = st.date_input(
                    "Reading Date", value=date.today()
                )

                consumption = st.number_input(
                    "Electricity Consumption (kWh)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    format="%.3f"
                )

                submitted = st.form_submit_button("Add Reading")

                if submitted:
                    try:
                        add_energy_reading(
                            reading_id=int(reading_id),
                            building_id=int(building[0]),
                            reading_date=reading_date,
                            consumption_kwh=float(consumption)
                        )
                        st.success("Electricity reading added successfully!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not add reading: {exc}")
