import streamlit as st
import pandas as pd
# import uuid # Likely not needed for admin page
import os
import sys

# Path adjustment for imports (data_manager, utils)
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_or_beach_signup_dir = os.path.dirname(current_file_dir)
if project_root_or_beach_signup_dir not in sys.path:
    sys.path.append(project_root_or_beach_signup_dir)

import data_manager as dm
import utils as ut

# Admin Credentials
ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# show_admin_dashboard_page() function definition (copied from app.py before restructuring)
def show_admin_dashboard_page():
    st.header("👑 Admin Dashboard") # This header is fine, page title is handled by display_admin_page
    # st.write("Manage activities, view registrations, and check-in participants.") # This can be removed if redundant

    # --- Admin Metrics Overview ---
    total_registrations = dm.get_total_registration_count()
    checked_in_count = dm.get_checked_in_count()

    if total_registrations > 0:
        check_in_rate = (checked_in_count / total_registrations) * 100
    else:
        check_in_rate = 0

    st.subheader("Event Snapshot")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registrations", total_registrations)
    col2.metric("Participants Checked-In", checked_in_count)
    col3.metric("Check-In Rate (%)", f"{check_in_rate:.2f}%")
    st.markdown("---")

    admin_action = st.selectbox("Admin Actions:",
                                ["View Activity Status & Check-In", "Verify by Passphrase & Check-In"],
                                key="admin_main_action_select_page") # Unique key

    if admin_action == "View Activity Status & Check-In":
        st.subheader("Activity Status & Registrations")
        activities = dm.get_activities()
        selected_activity = st.selectbox("Select Activity:", [""] + activities, key="admin_select_activity_page") # Unique key

        if selected_activity:
            st.markdown(f"### Statistics for {selected_activity}")
            activity_total_regs = dm.get_total_registration_count_for_activity(selected_activity)
            activity_checked_in = dm.get_checked_in_count_for_activity(selected_activity)
            activity_check_in_rate = (activity_checked_in / activity_total_regs) * 100 if activity_total_regs > 0 else 0

            act_col1, act_col2, act_col3 = st.columns(3)
            act_col1.metric(f"Total Registrations ({selected_activity})", activity_total_regs)
            act_col2.metric(f"Checked-In ({selected_activity})", activity_checked_in)
            act_col3.metric(f"Check-In Rate ({selected_activity})", f"{activity_check_in_rate:.2f}%")
            st.markdown("---")

            timeslots = dm.get_timeslots()
            selected_timeslot = st.selectbox("Select Timeslot:", [""] + timeslots, key="admin_select_timeslot_page") # Unique key

            if selected_timeslot:
                st.markdown(f"**Registrations for {selected_activity} at {selected_timeslot}:**")
                registrations = dm.get_registrations_for_timeslot(selected_activity, selected_timeslot)
                if not registrations:
                    st.info("No registrations for this activity/timeslot yet.")
                else:
                    display_data = []
                    for reg in registrations:
                        is_checked_in = bool(reg['checked_in'])
                        display_data.append({
                            "Reg ID": reg['id'],
                            "Name": reg['participant_name'],
                            "Passphrase": ut.format_passphrase_display(reg['registration_passphrase']),
                            "Checked In": is_checked_in,
                        })
                    registrations_df = pd.DataFrame(display_data)
                    if not registrations_df.empty:
                        disabled_columns = [col for col in registrations_df.columns if col != "Checked In"]
                        edited_df = st.data_editor(
                            registrations_df,
                            disabled=disabled_columns,
                            key="admin_registrations_editor_page", # Unique key
                            use_container_width=True,
                            hide_index=True
                        )
                        for i in range(len(registrations_df)):
                            original_status = registrations_df.loc[i, "Checked In"]
                            edited_status = edited_df.loc[i, "Checked In"]
                            reg_id = registrations_df.loc[i, "Reg ID"]
                            if not original_status and edited_status:
                                if dm.check_in_registration(int(reg_id)):
                                    st.success(f"Checked in participant with Reg ID: {reg_id}.")
                                else:
                                    st.error(f"Failed to check in participant with Reg ID: {reg_id}.")
                                st.rerun()
                            elif original_status and not edited_status:
                                if dm.uncheck_in_registration(int(reg_id)):
                                    st.success(f"Unchecked participant with Reg ID: {reg_id}.")
                                else:
                                    st.error(f"Failed to uncheck participant with Reg ID: {reg_id}.")
                                st.rerun()
                    else:
                        st.info("No registrations data to display in editor.")
    elif admin_action == "Verify by Passphrase & Check-In":
        st.subheader("Verify by Passphrase & Check-In")
        with st.form("passphrase_verify_form_page"): # Unique key
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input_page") # Unique key
            verify_button = st.form_submit_button("Verify Passphrase")
        if verify_button and passphrase_input:
            normalized_passphrase = passphrase_input.strip().lower()
            registration = dm.get_registration_by_passphrase(normalized_passphrase)
            if not registration:
                st.error("Invalid or unknown passphrase. Please check the input (format: word-word-word-word).")
            else:
                st.success(f"Registration Found for Passphrase: **{ut.format_passphrase_display(registration['registration_passphrase'])}**")
                details_cols = st.columns(2)
                details_cols[0].markdown(f"**Name:** {registration['participant_name']}")
                details_cols[1].markdown(f"**Activity:** {registration['activity']}")
                details_cols[1].markdown(f"**Timeslot:** {registration['timeslot']}")
                st.markdown("---")
                if bool(registration['checked_in']):
                    st.warning("This participant is already checked-in.")
                else:
                    st.info("Status: Pending Check-In")
                    checkin_button_key = f"passphrase_checkin_verify_view_page_{registration['id']}" # Unique key
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration['id']):
                            st.success(f"Successfully checked in {registration['participant_name']} for {registration['activity']}.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Check-in failed.")
        elif verify_button and not passphrase_input:
            st.warning("Please enter a passphrase to verify.")
    
    if st.button("Go to Test DB"):
        st.switch_page("pages/.test_db.py")

def display_admin_page():
    st.title("🔒 Admin Dashboard")

    if not st.session_state.get('admin_logged_in', False):
        # st.sidebar.subheader("Admin Login") # Login can be in the main page area for this page
        with st.form("admin_login_form_page"):
            st.subheader("Admin Login") # Moved subheader here
            username = st.text_input("Username", key="admin_user_input_page")
            password = st.text_input("Password", type="password", key="admin_pass_input_page")
            login_button = st.form_submit_button("Login")
            if login_button:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        # st.info("Log in to access admin functions.")
    else:
        # For a cleaner look on the admin page itself, logout can be just in sidebar.
        # If preferred, st.sidebar.button can be here too or instead.
        st.sidebar.success("Admin Logged In") # Keep consistent feedback in sidebar
        if st.sidebar.button("Logout Admin", key="admin_logout_page_sidebar"):
            st.session_state.admin_logged_in = False
            st.rerun()
        show_admin_dashboard_page()

# Call the main function for this page
display_admin_page()
