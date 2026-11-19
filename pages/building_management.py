import streamlit as st
from database import (
    get_all_buildings,
    get_next_building_id,
    add_building,
    update_building,
    delete_building
)

BUILDING_TYPES = ["Academic", "Hostel", "Library", "Dining", "Laboratory", "Other"]


def render_building_management_page():
    st.header("🏢 Building Management")

    buildings = get_all_buildings()

    if buildings:
        header = st.columns([1, 2, 1.5, 1.5])
        for column, label in zip(
            header, ["Building ID", "Building Name", "Building Type", "Actions"]
        ):
            column.markdown(f"**{label}**")

        for building in buildings:
            row = st.columns([1, 2, 1.5, 1.5])
            row[0].write(building[0])
            row[1].write(building[1])
            row[2].write(building[2])
            edit_button, delete_button = row[3].columns(2)

            if edit_button.button("Edit", key=f"edit_building_{building[0]}"):
                st.session_state["editing_building_id"] = building[0]
                st.session_state.pop("deleting_building_id", None)

            if delete_button.button("Delete", key=f"delete_building_{building[0]}"):
                st.session_state["deleting_building_id"] = building[0]
                st.session_state.pop("editing_building_id", None)

        st.caption(f"Total Buildings: {len(buildings)}")

        editing_id = st.session_state.get("editing_building_id")
        selected_building = next(
            (building for building in buildings if building[0] == editing_id),
            None
        )
        if selected_building:
            st.subheader(f"Edit Building {selected_building[0]}")
            types = list(BUILDING_TYPES)
            if selected_building[2] not in types:
                types.append(selected_building[2])

            with st.form("edit_building_form"):
                name = st.text_input("Building Name", value=selected_building[1])
                building_type = st.selectbox(
                    "Building Type",
                    types,
                    index=types.index(selected_building[2])
                )
                save_column, cancel_column = st.columns(2)
                with save_column:
                    submitted = st.form_submit_button("Save Changes")
                with cancel_column:
                    cancelled = st.form_submit_button("Cancel")

                if submitted:
                    if not name.strip():
                        st.error("Enter a building name.")
                    else:
                        try:
                            update_building(
                                selected_building[0],
                                name.strip(),
                                building_type
                            )
                            st.session_state.pop("editing_building_id", None)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not update building: {exc}")

                if cancelled:
                    st.session_state.pop("editing_building_id", None)
                    st.rerun()
    else:
        st.info("No buildings registered yet.")

    deleting_id = st.session_state.get("deleting_building_id")
    selected_for_deletion = next(
        (building for building in buildings if building[0] == deleting_id),
        None
    )
    if selected_for_deletion:
        st.warning(
            f"Delete {selected_for_deletion[1]} permanently?"
        )
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm Delete", key="confirm_delete_building"):
            try:
                delete_building(selected_for_deletion[0])
                st.session_state.pop("deleting_building_id", None)
                st.rerun()
            except Exception as exc:
                st.error(f"Cannot delete building: {exc}")
        if cancel.button("Cancel", key="cancel_delete_building"):
            st.session_state.pop("deleting_building_id", None)
            st.rerun()

    st.divider()

    with st.expander("➕ Add Building"):
        with st.form("add_building_form", clear_on_submit=True):
            building_id = st.number_input(
                "Building ID", min_value=1,
                value=int(get_next_building_id())
            )
            name = st.text_input("Building Name")
            building_type = st.selectbox("Building Type", BUILDING_TYPES)

            submitted = st.form_submit_button("Add Building")

            if submitted:
                if not name.strip():
                    st.error("Enter a building name.")
                else:
                    try:
                        add_building(
                            building_id=int(building_id),
                            name=name.strip(),
                            building_type=building_type
                        )
                        st.success("Building added successfully!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not add building: {exc}")
