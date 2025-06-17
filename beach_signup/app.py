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

    # Check for "1 activity limit" FIRST
    user_existing_registrations = dm.get_user_registrations(participant_session_id)

    if user_existing_registrations:
        st.warning("You already have an active booking. You can only sign up for one activity at a time.")
        st.info("Please visit the 'My Bookings' page (accessible from the sidebar if added to navigation) to view or cancel your current booking if you wish to sign up for a different activity.")
        # For now, just a message. User should navigate via sidebar (once 'My Bookings' is added there).
        return # Stop here if user already has a booking

    # If no existing booking, proceed with showing signup options
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
    def style_availability(val): # Copied from existing working version
        color = ""
        if val == "Full": color = 'background-color: #FFCCCC'
        elif "Slots Available" in val:
            try:
                if int(val.split()[0]) <= 3: color = 'background-color: #FFFFCC'
            except: pass
        return color
    st.dataframe(availability_df.style.applymap(style_availability), use_container_width=True)

    st.subheader("Book Your Slot")
    # Corrected: Access participant's name by index 1 if current_participant_profile is a Row object
    default_name = current_participant_profile[1] if current_participant_profile else ""

    with st.form("registration_form_no_email"): # Changed form key
        name = st.text_input("Your Full Name:", value=default_name, key="reg_form_name_v2")
        # Email field REMOVED
        selected_activity = st.selectbox("Choose an Activity:", options=activities, key="reg_form_activity_v2")
        selected_timeslot = st.selectbox("Choose a Timeslot:", options=timeslots, key="reg_form_timeslot_v2")

        is_slot_full_check = False
        if selected_activity and selected_timeslot:
            if dm.get_signup_count(selected_activity, selected_timeslot) >= MAX_CAPACITY_PER_SLOT:
                is_slot_full_check = True

        submit_button = st.form_submit_button("Sign Up", disabled=is_slot_full_check)

        if submit_button:
            if not ut.validate_name(name):
                st.error("Please enter a valid name (at least 2 characters).")
                return
            # Email validation REMOVED

            current_count_on_submit = dm.get_signup_count(selected_activity, selected_timeslot)
            if current_count_on_submit >= MAX_CAPACITY_PER_SLOT:
                st.error(f"Sorry, {selected_activity} at {selected_timeslot} just became full.")
                st.rerun()
                return

            if not current_participant_profile: # If no participant profile exists for this session_id
                dm.create_participant(participant_session_id, name.strip())

            # add_registration no longer takes email. Status messages updated in dm.py
            reg_id, new_passphrase, status_msg = dm.add_registration(participant_session_id, name.strip(), selected_activity, selected_timeslot)

            if status_msg == "SUCCESS":
                st.success(f"Success! You are signed up for {selected_activity} at {selected_timeslot}.")
                st.info(f"Your unique verification code for this booking is: **{ut.format_passphrase_display(new_passphrase)}**")
                st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.") # New Warning
                st.balloons()
                st.rerun() # Rerun to trigger the "already booked" message at the top of this page.
            elif status_msg == "LIMIT_REACHED":
                 st.error("You already have an active booking. You can only sign up for one activity at a time. This form should have been disabled.")
                 st.rerun() # Should refresh and disable form
            elif status_msg == "ALREADY_BOOKED_TIMESLOT": # Should ideally be caught by LIMIT_REACHED first
                 st.error(f"It seems you (or someone in this session) are already booked for an activity in the timeslot {selected_timeslot}, or for this specific activity/timeslot combination.")
            else: # DB_ERROR or other unexpected
                st.error(f"Signup failed due to an unexpected issue ({status_msg}). Please try again or contact support.")



def show_admin_dashboard_page():
    st.header("👑 Admin Dashboard")
    st.write("Manage activities, view registrations, and check-in participants.")

    admin_action = st.selectbox("Admin Actions:",
                                ["View Activity Status & Check-In", "Verify by Passphrase & Check-In"],
                                key="admin_main_action_select_v2") # New key if needed

    if admin_action == "View Activity Status & Check-In":
        st.subheader("Activity Status & Registrations")

        activities = dm.get_activities()
        selected_activity = st.selectbox("Select Activity:", [""] + activities, key="admin_select_activity_v2")

        if selected_activity:
            timeslots = dm.get_timeslots()
            selected_timeslot = st.selectbox("Select Timeslot:", [""] + timeslots, key="admin_select_timeslot_v2")

            if selected_timeslot:
                st.markdown(f"**Registrations for {selected_activity} at {selected_timeslot}:**")
                registrations = dm.get_registrations_for_timeslot(selected_activity, selected_timeslot)

                if not registrations:
                    st.info("No registrations for this activity/timeslot yet.")
                else:
                    display_data = []
                    for reg in registrations: # Assuming reg is a Row object
                        status = "Checked-In" if reg[7] == 1 else "Pending" # checked_in is index 7
                        display_data.append({
                            "Reg ID": reg[0],
                            "Name": reg[2],
                            # Email field removed from here
                            "Passphrase": ut.format_passphrase_display(reg[5]),
                            "Status": status,
                        })

                    cols_header = ["Name", "Passphrase", "Status", "Action"] # Email removed from header
                    # Adjust column ratios: Name (2), Passphrase (2), Status (1), Action (1) -> Total 6
                    header_cols = st.columns([2, 2, 1, 1])
                    for i, col_name in enumerate(cols_header):
                        header_cols[i].markdown(f"**{col_name}**")

                    st.markdown("---")

                    for item in display_data:
                        row_cols = st.columns([2, 2, 1, 1]) # Match header column ratios
                        row_cols[0].write(item["Name"])
                        row_cols[1].write(item["Passphrase"]) # Passphrase is now at index 1 of display cols

                        # Status is now at index 2 of display cols
                        if item["Status"] == "Checked-In":
                            row_cols[2].success(item["Status"])
                            row_cols[3].empty()
                        else:
                            row_cols[2].warning(item["Status"])
                            # Action is now at index 3 of display cols
                            button_key = f"checkin_activity_view_{item['Reg ID']}"
                            if row_cols[3].button("Check-In", key=button_key):
                                if dm.check_in_registration(item['Reg ID']):
                                    st.success(f"Checked in {item['Name']} (Reg ID: {item['Reg ID']}).")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to check in {item['Name']}.")
                        st.markdown("---")

    elif admin_action == "Verify by Passphrase & Check-In":
        st.subheader("Verify by Passphrase & Check-In")

        with st.form("passphrase_verify_form_v2"):
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input_v2")
            verify_button = st.form_submit_button("Verify Passphrase")

        if verify_button and passphrase_input:
            normalized_passphrase = passphrase_input.strip().lower()
            registration = dm.get_registration_by_passphrase(normalized_passphrase) # Row object

            if not registration:
                st.error("Invalid or unknown passphrase. Please check the input (format: word-word-word-word).")
            else:
                st.success(f"Registration Found for Passphrase: **{ut.format_passphrase_display(registration[5])}**") # Passphrase at index 5

                details_cols = st.columns(2)
                details_cols[0].markdown(f"**Name:** {registration[2]}") # Name at index 2
                # Email display removed from here
                details_cols[1].markdown(f"**Activity:** {registration[3]}") # Activity at index 3
                details_cols[1].markdown(f"**Timeslot:** {registration[4]}") # Timeslot at index 4

                st.markdown("---")

                if registration[7] == 1: # checked_in at index 7
                    st.warning("This participant is already checked-in.")
                else:
                    st.info("Status: Pending Check-In")
                    checkin_button_key = f"passphrase_checkin_verify_view_{registration[0]}" # Reg ID at index 0
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration[0]): # Reg ID at index 0
                            st.success(f"Successfully checked in {registration[2]} for {registration[3]}.") # Name (idx 2), Activity (idx 3)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Check-in failed.")
        elif verify_button and not passphrase_input:
            st.warning("Please enter a passphrase to verify.")





def show_my_bookings_page(user_id, participant_profile):
    st.header("My Active Booking")

    if not participant_profile: # Should ideally not happen if they access this page via normal flow
        st.warning("Please register your name on the 'Sign Up For Activities' page first if you are a new user.")
        return

    user_registrations = dm.get_user_registrations(user_id)

    if not user_registrations:
        st.info("You have no active bookings.")
        st.write("Feel free to sign up for an activity!")
    else:
        # Due to the "1 activity limit", there should only be one registration.
        current_booking = user_registrations[0]

        st.subheader(f"Your booking for: {current_booking[3]}") # activity index 3
        st.markdown(f"**Timeslot:** {current_booking[4]}") # timeslot index 4
        st.markdown(f"**Your Name (for this booking):** {current_booking[2]}") # participant_name index 2

        st.markdown("---")
        st.subheader("Your Verification Passphrase:")
        st.code(ut.format_passphrase_display(current_booking[5])) # registration_passphrase index 5
        st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
        st.markdown("---")

        if st.button("Cancel This Booking", key=f"cancel_booking_{current_booking[0]}", type="primary"): # id index 0
            if dm.cancel_registration(current_booking[0]): # id index 0
                st.success("Your booking has been successfully cancelled.")
                st.info("You can now sign up for a new activity.")
                st.balloons()
                st.rerun() # Refresh the page to show "no active bookings"
            else:
                st.error("Could not cancel the booking. Please try again or contact support.")


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
            user_page_options = ["Sign Up For Activities", "My Bookings"]
            user_action = st.sidebar.selectbox("What would you like to do?", user_page_options, key="user_action_select_v2") # New key

            if user_action == "Sign Up For Activities":
                show_signup_page(user_id, participant_profile)
            elif user_action == "My Bookings":
                show_my_bookings_page(user_id, participant_profile)

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
