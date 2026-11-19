import streamlit as st
import pandas as pd
from datetime import date
from database import (
    get_all_buildings,
    get_emission_sources_with_factors,
    get_next_activity_id,
    add_activity,
    update_activity,
    delete_activity,
    get_all_activities_with_emissions
)


def render_carbon_emissions_page():
    st.header("🌱 Carbon Emissions")

    activity_tab, calculation_tab = st.tabs(
        ["Activity Entry", "Carbon Calculation"]
    )

    with activity_tab:
        st.subheader("Emission Sources and Factors")
        sources = get_emission_sources_with_factors()

        if sources:
            source_df = pd.DataFrame(
                sources,
                columns=[
                    "Source ID", "Emission Source", "Measurement Unit",
                    "Factor ID", "Emission Factor", "Factor Unit"
                ]
            )
            st.dataframe(
                source_df[
                    ["Emission Source", "Measurement Unit",
                     "Emission Factor", "Factor Unit"]
                ],
                hide_index=True,
                use_container_width=True
            )
            st.caption("Emission factors are fixed and cannot be changed here.")
        else:
            st.info("No emission sources or factors are available.")

        st.divider()
        st.subheader("Add Activity Quantity")
        buildings = get_all_buildings()

        if not buildings:
            st.warning("Add a building before recording an activity.")
        elif not sources:
            st.warning("Add emission sources and factors before recording an activity.")
        else:
            with st.form("add_emission_activity", clear_on_submit=True):
                activity_id = st.number_input(
                    "Activity ID", min_value=1,
                    value=int(get_next_activity_id()), step=1
                )
                building = st.selectbox(
                    "Select Building", buildings,
                    format_func=lambda b: f"{b[1]} ({b[2]})"
                )
                source = st.selectbox(
                    "Select Emission Source", sources,
                    format_func=lambda s: f"{s[1]} ({s[2]})"
                )
                activity_date = st.date_input("Activity Date", value=date.today())
                quantity = st.number_input(
                    f"Activity Quantity ({source[2]})",
                    min_value=0.001, value=1.0, step=1.0, format="%.3f"
                )
                submitted = st.form_submit_button("Add Activity")

                if submitted:
                    try:
                        add_activity(
                            activity_id=int(activity_id),
                            building_id=int(building[0]),
                            source_id=int(source[0]),
                            activity_date=activity_date,
                            quantity=float(quantity),
                            factor_id=int(source[3])
                        )
                        st.success("Activity quantity added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not add activity: {e}")

    with calculation_tab:
        st.subheader("Carbon Emission Calculation")
        st.caption("Emissions = Activity Quantity × Emission Factor")
        activities = get_all_activities_with_emissions()

        # This database function already returns a DataFrame.
        if not activities.empty:
            st.subheader("Activity Records")
            headers = st.columns(
                [0.75, 1.1, 1.2, 1.0, 0.8, 1.0, 0.9, 1.1, 1.5]
            )
            labels = [
                "Activity ID", "Building", "Emission Source", "Date",
                "Quantity", "Unit", "Factor", "Emissions (kg)", "Actions"
            ]
            for column, label in zip(headers, labels):
                column.markdown(f"**{label}**")

            for _, activity in activities.iterrows():
                row = st.columns(
                    [0.75, 1.1, 1.2, 1.0, 0.8, 1.0, 0.9, 1.1, 1.5]
                )
                row[0].write(activity["activity_id"])
                row[1].write(activity["building_name"])
                row[2].write(activity["source_name"])
                row[3].write(activity["activity_date"])
                row[4].write(f'{float(activity["quantity"]):,.3f}')
                row[5].write(activity["measurement_unit"])
                row[6].write(f'{float(activity["factor_value"]):,.6f}')
                row[7].write(
                    f'{float(activity["calculated_emissions"]):,.3f}'
                )
                edit_button, delete_button = row[8].columns(2)

                activity_id = activity["activity_id"]
                if edit_button.button(
                    "Edit", key=f"edit_activity_{activity_id}"
                ):
                    st.session_state["editing_activity_id"] = activity_id
                    st.session_state.pop("deleting_activity_id", None)

                if delete_button.button(
                    "Delete", key=f"delete_activity_{activity_id}"
                ):
                    st.session_state["deleting_activity_id"] = activity_id
                    st.session_state.pop("editing_activity_id", None)

            editing_id = st.session_state.get("editing_activity_id")
            selected_activity = activities.loc[
                activities["activity_id"] == editing_id
            ]
            if not selected_activity.empty:
                activity = selected_activity.iloc[0]
                st.subheader(f"Edit Activity {activity['activity_id']}")

                if buildings and sources:
                    building_index = next(
                        (
                            index for index, building in enumerate(buildings)
                            if building[0] == activity["building_id"]
                        ),
                        0
                    )
                    source_index = next(
                        (
                            index for index, source in enumerate(sources)
                            if source[0] == activity["source_id"]
                            and source[3] == activity["factor_id"]
                        ),
                        0
                    )

                    with st.form("edit_activity_form"):
                        building = st.selectbox(
                            "Select Building",
                            buildings,
                            index=building_index,
                            format_func=lambda item: f"{item[1]} ({item[2]})"
                        )
                        source = st.selectbox(
                            "Select Emission Source and Factor",
                            sources,
                            index=source_index,
                            format_func=lambda item: (
                                f"{item[1]} ({item[2]}, "
                                f"{item[4]} {item[5]})"
                            )
                        )
                        activity_date = st.date_input(
                            "Activity Date", value=activity["activity_date"]
                        )
                        quantity = st.number_input(
                            f"Activity Quantity ({source[2]})",
                            min_value=0.0,
                            value=float(activity["quantity"]),
                            step=1.0,
                            format="%.3f"
                        )
                        save_column, cancel_column = st.columns(2)
                        with save_column:
                            submitted = st.form_submit_button("Save Changes")
                        with cancel_column:
                            cancelled = st.form_submit_button("Cancel")

                        if submitted:
                            try:
                                update_activity(
                                    int(activity["activity_id"]),
                                    int(building[0]),
                                    int(source[0]),
                                    activity_date,
                                    float(quantity),
                                    int(source[3])
                                )
                                st.session_state.pop(
                                    "editing_activity_id", None
                                )
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not update activity: {exc}")

                        if cancelled:
                            st.session_state.pop("editing_activity_id", None)
                            st.rerun()
                else:
                    st.error(
                        "Could not load buildings and emission factors "
                        "for editing this activity."
                    )

            deleting_id = st.session_state.get("deleting_activity_id")
            selected_for_deletion = activities.loc[
                activities["activity_id"] == deleting_id
            ]
            if not selected_for_deletion.empty:
                activity = selected_for_deletion.iloc[0]
                st.warning(
                    f"Delete activity {deleting_id} for "
                    f"{activity['building_name']}?"
                )
                confirm, cancel = st.columns(2)
                if confirm.button(
                    "Confirm Delete", key="confirm_delete_activity"
                ):
                    try:
                        delete_activity(int(deleting_id))
                        st.session_state.pop("deleting_activity_id", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not delete activity: {exc}")

                if cancel.button(
                    "Cancel", key="cancel_delete_activity"
                ):
                    st.session_state.pop("deleting_activity_id", None)
                    st.rerun()

            df = activities.rename(columns={
                "activity_id": "Activity ID",
                "building_name": "Building",
                "source_name": "Emission Source",
                "activity_date": "Activity Date",
                "quantity": "Quantity",
                "measurement_unit": "Measurement Unit",
                "factor_value": "Emission Factor",
                "factor_unit": "Factor Unit",
                "calculated_emissions": "Emissions (kg CO2)"
            })

            total_emissions = df["Emissions (kg CO2)"].sum()
            st.metric("Total Direct CO₂ Emissions", f"{total_emissions:,.2f} kg")

            st.subheader("Emissions by Source")
            source_summary = (
                df.groupby("Emission Source", as_index=False)["Emissions (kg CO2)"]
                .sum()
            )
            st.dataframe(
                source_summary.round(3),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No activity quantities have been recorded yet.")
