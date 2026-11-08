"""
pages/building_management.py
----------------------------
Module 2: Building Management for Campus Energy & Carbon Management System.
Allows users to add, view, update, and delete campus buildings.
Prevents deletion when foreign key relationships exist (energy readings present)
and displays user-friendly error messages.
"""

import streamlit as st
import pandas as pd
from database import (
    get_all_buildings,
    get_next_building_id,
    add_building,
    update_building,
    delete_building
)

BUILDING_TYPES = ["Academic", "Hostel", "Library", "Dining", "Other"]


def render_building_management_page():
    st.header("🏢 Campus Building Management")
    st.write("Manage campus buildings, classify facility types, and organize campus locations.")

    # Four intuitive tabs for CRUD operations
    tab_view, tab_add, tab_update, tab_delete = st.tabs([
        "📋 View Buildings",
        "➕ Add Building",
        "✏️ Update Building",
        "🗑️ Delete Building"
    ])

    # =========================================================================
    # TAB 1: VIEW BUILDINGS
    # =========================================================================
    with tab_view:
        st.subheader("All Registered Campus Buildings")
        buildings = get_all_buildings()
        if buildings:
            df = pd.DataFrame(
                buildings,
                columns=["Building ID", "Building Name", "Building Type", "Location"]
            )
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total Buildings Registered: {len(buildings)}")
        else:
            st.info("No buildings registered in the database yet.")

    # =========================================================================
    # TAB 2: ADD BUILDING
    # =========================================================================
    with tab_add:
        st.subheader("Register a New Campus Building")
        next_id = get_next_building_id()

        with st.form("form_add_building", clear_on_submit=True):
            st.caption("Suggested Building ID has been prefilled automatically.")
            col_id, col_type = st.columns(2)
            with col_id:
                building_id = st.number_input(
                    "Building ID",
                    min_value=1,
                    value=int(next_id),
                    step=1,
                    help="Unique integer identifier for the building"
                )
            with col_type:
                building_type = st.selectbox(
                    "Building Type",
                    BUILDING_TYPES,
                    help="Select the functional category of this campus building"
                )

            name = st.text_input(
                "Building Name",
                placeholder="e.g. Science Block, Ramanujan Hostel",
                max_chars=100
            )
            location = st.text_input(
                "Campus Location / Zone",
                placeholder="e.g. North Campus, Sector 4, Main Quadrangle",
                max_chars=100
            )

            submit_add = st.form_submit_button("➕ Add Building")

        if submit_add:
            if not name.strip():
                st.error("Please enter a valid building name.")
            else:
                try:
                    add_building(
                        building_id=int(building_id),
                        name=name.strip(),
                        building_type=building_type,
                        location=location.strip()
                    )
                    st.success(f"Building '{name.strip()}' (ID: {building_id}) added successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not add building: {exc}")

    # =========================================================================
    # TAB 3: UPDATE BUILDING
    # =========================================================================
    with tab_update:
        st.subheader("Update Building Information")
        buildings = get_all_buildings()

        if buildings:
            selected_building = st.selectbox(
                "Select a building to edit",
                buildings,
                format_func=lambda b: f"ID {b[0]} - {b[1]} ({b[2]})",
                key="select_update_building"
            )

            # Using a dynamic form key so values reset cleanly when selection changes
            with st.form(f"form_update_building_{selected_building[0]}"):
                st.info(f"Editing Building ID: {selected_building[0]}")

                updated_name = st.text_input(
                    "Building Name",
                    value=selected_building[1],
                    max_chars=100
                )

                type_idx = (
                    BUILDING_TYPES.index(selected_building[2])
                    if selected_building[2] in BUILDING_TYPES else 0
                )
                updated_type = st.selectbox(
                    "Building Type",
                    BUILDING_TYPES,
                    index=type_idx
                )

                updated_location = st.text_input(
                    "Campus Location / Zone",
                    value=selected_building[3] or "",
                    max_chars=100
                )

                submit_update = st.form_submit_button("💾 Save Changes")

            if submit_update:
                if not updated_name.strip():
                    st.error("Building name cannot be empty.")
                else:
                    try:
                        update_building(
                            building_id=selected_building[0],
                            name=updated_name.strip(),
                            building_type=updated_type,
                            location=updated_location.strip()
                        )
                        st.success(f"Building ID {selected_building[0]} updated successfully!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update building: {exc}")
        else:
            st.info("No buildings available to update.")

    # =========================================================================
    # TAB 4: DELETE BUILDING
    # =========================================================================
    with tab_delete:
        st.subheader("Delete a Building")
        buildings = get_all_buildings()

        if buildings:
            selected_to_delete = st.selectbox(
                "Select a building to delete",
                buildings,
                format_func=lambda b: f"ID {b[0]} - {b[1]} ({b[2]})",
                key="select_delete_building"
            )

            st.warning(
                f"You are selecting **ID {selected_to_delete[0]} - {selected_to_delete[1]}** for deletion. "
                f"Buildings with associated energy readings cannot be deleted until those readings are removed."
            )

            confirm_delete = st.checkbox(
                f"I confirm that I want to permanently delete building '{selected_to_delete[1]}'",
                key="confirm_delete_building_box"
            )

            if st.button("🗑️ Delete Selected Building", disabled=not confirm_delete):
                try:
                    delete_building(selected_to_delete[0])
                    st.success(f"Building '{selected_to_delete[1]}' deleted successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Cannot delete building: {exc}")
        else:
            st.info("No buildings available to delete.")
