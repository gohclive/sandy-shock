import streamlit as st
import pandas as pd
import uuid
import os
import sys

# Ensure the 'beach_signup' directory is in the Python path
# This allows 'import data_manager as dm' and 'import utils as ut' to work correctly
# when 'streamlit run beach_signup/app.py' is executed from the project root.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import data_manager as dm
import utils as ut

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# Function to display the participant sign-up page
def show_signup_page(participant_session_id, current_participant_profile):
    st.header("📝 Sign Up For Activities")

    activities = dm.get_activities()
    timeslots = dm.get_timeslots()
    MAX_CAPACITY_PER_SLOT = 10

    grid_data = {}
    for activity in activities:
        row_data = {}
        for timeslot in timeslots:
            count = dm.get_signup_count(activity, timeslot)
            available_slots = MAX_CAPACITY_PER_SLOT - count
            row_data[timeslot] = "Full" if available_slots <= 0 else f"{available_slots} Slots Available"
        grid_data[activity] = row_data

    availability_df = pd.DataFrame.from_dict(grid_data, orient='index', columns=timeslots)

    st.subheader("Current Availability")
    def style_availability(val):
        color = ""
        if val == "Full": color = 'background-color: #FFCCCC'
        elif "Slots Available" in val:
            try:
                if int(val.split()[0]) <= 3: color = 'background-color: #FFFFCC'
            except: pass
        return color
    st.dataframe(availability_df.style.applymap(style_availability), use_container_width=True)

    st.subheader("Book Your Slot")
    # Access participant's name by index 1 if current_participant_profile is a Row object
    default_name = current_participant_profile[1] if current_participant_profile else ""

    with st.form("registration_form"):
        name = st.text_input("Your Full Name:", value=default_name, key="reg_form_name")
        email = st.text_input("Your Email:", key="reg_form_email")
        selected_activity = st.selectbox("Choose an Activity:", options=activities, key="reg_form_activity")
        selected_timeslot = st.selectbox("Choose a Timeslot:", options=timeslots, key="reg_form_timeslot")

        is_slot_full_check = False
        if selected_activity and selected_timeslot:
            if dm.get_signup_count(selected_activity, selected_timeslot) >= MAX_CAPACITY_PER_SLOT:
                is_slot_full_check = True

        submit_button = st.form_submit_button("Sign Up", disabled=is_slot_full_check)

        if submit_button:
            if not ut.validate_name(name):
                st.error("Please enter a valid name (at least 2 characters).")
                return
            if not ut.validate_email(email.strip()): # Use new validation
                st.error("Please enter a valid email address.")
                return

            current_count_on_submit = dm.get_signup_count(selected_activity, selected_timeslot)
            if current_count_on_submit >= MAX_CAPACITY_PER_SLOT:
                st.error(f"Sorry, {selected_activity} at {selected_timeslot} just became full.")
                st.rerun()
                return

            if not current_participant_profile: # If no profile exists for this session_id, create one
                dm.create_participant(participant_session_id, name.strip())

            reg_id, new_passphrase = dm.add_registration(participant_session_id, name.strip(), email.strip(), selected_activity, selected_timeslot)

            if reg_id and new_passphrase:
                st.success(f"Success! Signed up for {selected_activity} at {selected_timeslot}.")
                st.info(f"Your verification code: **{ut.format_passphrase_display(new_passphrase)}**")
                st.markdown(f"A confirmation would typically be sent to **{email.strip()}** (Email sending mocked).")
                st.balloons()
            elif not reg_id and not new_passphrase: # IntegrityError from dm.add_registration
                 st.error(f"You are already registered for an activity in the timeslot {selected_timeslot}.")
            else:
                st.error("Signup failed. Please try again.")

# Function to display the admin dashboard (placeholder for now)

def show_admin_dashboard_page():
    st.header("👑 Admin Dashboard")
    st.write("Manage activities, view registrations, and check-in participants.")

    admin_action = st.selectbox("Admin Actions:",
                                ["View Activity Status & Check-In", "Verify by Passphrase & Check-In"],
                                key="admin_main_action_select")

    if admin_action == "View Activity Status & Check-In":
        st.subheader("Activity Status & Registrations")

        activities = dm.get_activities()
        # Add a default empty option to prevent immediate selection/loading
        selected_activity = st.selectbox("Select Activity:", [""] + activities, key="admin_select_activity")

        if selected_activity: # Only proceed if an activity is chosen
            timeslots = dm.get_timeslots()
            # Add a default empty option here too
            selected_timeslot = st.selectbox("Select Timeslot:", [""] + timeslots, key="admin_select_timeslot")

            if selected_timeslot: # Only proceed if a timeslot is chosen
                st.markdown(f"**Registrations for {selected_activity} at {selected_timeslot}:**")
                registrations = dm.get_registrations_for_timeslot(selected_activity, selected_timeslot)

                if not registrations:
                    st.info("No registrations for this activity/timeslot yet.")
                else:
                    # Prepare data for display
                    display_data = []
                    for reg_row in registrations: # Renamed to avoid conflict with 'registrations' list
                        # Accessing sqlite3.Row by index as per previous findings
                        # Schema: id(0), user_id(1), participant_name(2), participant_email(3),
                        #         activity(4), timeslot(5), registration_passphrase(6),
                        #         registration_time(7), checked_in(8)
                        status = "Checked-In" if reg_row[8] == 1 else "Pending" # reg_row[8] is 'checked_in'
                        display_data.append({
                            "Reg ID": reg_row[0], # reg_row[0] is 'id'
                            "Name": reg_row[2],   # reg_row[2] is 'participant_name'
                            "Email": reg_row[3],  # reg_row[3] is 'participant_email'
                            "Passphrase": ut.format_passphrase_display(reg_row[6]), # reg_row[6] is 'registration_passphrase'
                            "Status": status,
                            "user_id_debug": reg_row[1] # reg_row[1] is 'user_id'
                        })

                    cols_header = ["Name", "Email", "Passphrase", "Status", "Action"]
                    header_cols = st.columns([2,2,2,1,1]) # Adjusted column ratios
                    for i, col_name in enumerate(cols_header):
                        header_cols[i].markdown(f"**{col_name}**")

                    st.markdown("---")

                    for item in display_data:
                        row_cols = st.columns([2,2,2,1,1]) # Adjusted column ratios
                        row_cols[0].write(item["Name"])
                        row_cols[1].write(item["Email"])
                        row_cols[2].write(item["Passphrase"])

                        if item["Status"] == "Checked-In":
                            row_cols[3].success(item["Status"])
                            row_cols[4].empty()
                        else:
                            row_cols[3].warning(item["Status"])
                            button_key = f"checkin_{item['Reg ID']}"
                            if row_cols[4].button("Check-In", key=button_key):
                                if dm.check_in_registration(item['Reg ID']):
                                    st.success(f"Checked in {item['Name']} (Reg ID: {item['Reg ID']}).")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to check in {item['Name']}. They might already be checked in, or an error occurred.")
                        st.markdown("---")

    elif admin_action == "Verify by Passphrase & Check-In":
        st.subheader("Verify by Passphrase & Check-In")

        with st.form("passphrase_verify_form"):
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input")
            verify_button = st.form_submit_button("Verify Passphrase")

        if verify_button and passphrase_input:
            # Normalize passphrase: lowercase and strip whitespace
            normalized_passphrase = passphrase_input.strip().lower()

            registration = dm.get_registration_by_passphrase(normalized_passphrase) # This is a Row object or None

            if not registration:
                st.error("Invalid or unknown passphrase. Please check the input (format: word-word-word-word).")
            else:
                # Registrations table schema indices:
                # id(0), user_id(1), participant_name(2), participant_email(3),
                # activity(4), timeslot(5), registration_passphrase(6),
                # registration_time(7), checked_in(8)
                st.success(f"Registration Found for Passphrase: **{ut.format_passphrase_display(registration[6])}**") # registration_passphrase index 6

                details_cols = st.columns(2)
                details_cols[0].markdown(f"**Name:** {registration[2]}") # participant_name index 2
                details_cols[0].markdown(f"**Email:** {registration[3]}") # participant_email index 3
                details_cols[1].markdown(f"**Activity:** {registration[4]}") # activity index 4
                details_cols[1].markdown(f"**Timeslot:** {registration[5]}") # timeslot index 5

                st.markdown("---")

                if registration[8] == 1: # checked_in index 8
                    st.warning("This participant is already checked-in.")
                else:
                    st.info("Status: Pending Check-In")
                    checkin_button_key = f"passphrase_checkin_{registration[0]}" # id index 0
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration[0]): # id index 0
                            st.success(f"Successfully checked in {registration[2]} for {registration[4]}.") # name index 2, activity index 4
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Check-in failed. The participant might have been checked in by another admin, or a database error occurred.")
        elif verify_button and not passphrase_input:
            st.warning("Please enter a passphrase to verify.")

def initialize_user_session():
    if 'user_id' not in st.session_state:
        query_params = st.query_params
        uid_from_url = query_params.get("uid") # .get returns None if not found
        if uid_from_url:
            # If uid is a list (can happen if param is repeated), take the first element
            st.session_state.user_id = uid_from_url[0] if isinstance(uid_from_url, list) else uid_from_url
        else:
            new_user_id = f"beach_{str(uuid.uuid4())[:8]}"
            st.session_state.user_id = new_user_id
            st.query_params["uid"] = new_user_id # Update URL

# Main application logic
def main():
    st.set_page_config(page_title="Beach Day Signup", page_icon="🏖️", layout="wide")

    dm.initialize_database()
    initialize_user_session()

    user_id = st.session_state.user_id
    participant_profile = dm.find_participant_by_id(user_id) # This is a Row object or None

    app_section = st.sidebar.radio("Navigate:", ["User Section", "Admin Dashboard"], key="main_nav")

    if app_section == "User Section":
        st.title("🏖️ Beach Day Activity Signup")
        st.sidebar.subheader("User Actions")
        if not participant_profile:
            st.header("Welcome!")
            with st.form("new_user_profile_form"):
                name = st.text_input("Enter your full name to begin:", key="profile_name_input")
                submitted = st.form_submit_button("Register Name")
                if submitted:
                    if ut.validate_name(name):
                        if dm.create_participant(user_id, name.strip()):
                            st.success(f"Welcome, {name.strip()}!")
                            st.rerun()
                        else: st.error("Could not save name. Try again.")
                    else: st.error("Valid name needed (min 2 chars).")
        else:
            # Access participant's name by index 1, as per previous findings for sqlite.Row
            participant_name_display = participant_profile[1] if participant_profile else "Guest"
            st.sidebar.info(f"Welcome, {participant_name_display}!")
            show_signup_page(user_id, participant_profile)

    elif app_section == "Admin Dashboard":
        st.title("🔒 Admin Dashboard")
        if not st.session_state.get('admin_logged_in', False):
            st.sidebar.subheader("Admin Login")
            with st.form("admin_login_form"):
                username = st.text_input("Username", key="admin_user_input")
                password = st.text_input("Password", type="password", key="admin_pass_input")
                login_button = st.form_submit_button("Login")
                if login_button:
                    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.rerun()
                    else: st.error("Invalid credentials.")
            st.info("Log in via sidebar for admin functions.")
        else:
            st.sidebar.success("Admin Logged In")
            if st.sidebar.button("Logout Admin", key="admin_logout"):
                st.session_state.admin_logged_in = False
                st.rerun()
            show_admin_dashboard_page()

if __name__ == "__main__":
    main()
