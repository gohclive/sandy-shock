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

ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# Function to display the participant sign-up page

def show_signup_page(participant_session_id, current_participant_profile):
    st.header("📝 Sign Up For Activities")

    # --- Display Activity Availability Grid (Moved Up) ---
    activities = dm.get_activities()
    timeslots = dm.get_timeslots()
    MAX_CAPACITY_PER_SLOT = 10 # Define this early if not already global/class member

    grid_data = {}
    for activity_item in activities: # Renamed to avoid conflict with selected_activity later
        row_data = {}
        for timeslot_item in timeslots: # Renamed to avoid conflict
            count = dm.get_signup_count(activity_item, timeslot_item)
            available_slots = MAX_CAPACITY_PER_SLOT - count
            row_data[timeslot_item] = "Full" if available_slots <= 0 else f"{available_slots} Slots Available"
        grid_data[activity_item] = row_data

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
    st.markdown("---") # Optional: Add a separator after the grid

    # --- Conditional Display: Warning or Signup Form ---
    user_existing_registrations = dm.get_user_registrations(participant_session_id)

    if user_existing_registrations:
        st.warning("You already have an active booking. You can only sign up for one activity at a time.")
        st.info("Please visit the 'My Bookings' page (accessible from the sidebar if added to navigation) to view or cancel your current booking if you wish to sign up for a different activity.")
        # Note: The 'return' statement that was here is removed.
    else:
        # Show signup form only if no existing booking
        st.subheader("Book Your Slot")
        default_name = current_participant_profile['name'] if current_participant_profile else ""

        with st.form("registration_form_no_email"): # Changed form key
            name = st.text_input("Your Full Name:", value=default_name, key="reg_form_name_v2")
            # 'activities' and 'timeslots' are already defined from the grid display part
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
                    return # Return from form submission if invalid

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
                    # Store success info in session state before rerun
                    st.session_state.signup_success = True
                    st.session_state.last_signup_details = {
                        "activity": selected_activity,
                        "timeslot": selected_timeslot,
                        "passphrase": new_passphrase
                    }
                    # These messages will flash briefly, persistent ones handled in main()
                    st.success(f"Success! You are signed up for {selected_activity} at {selected_timeslot}.")
                    st.info(f"Your unique verification code for this booking is: **{ut.format_passphrase_display(new_passphrase)}**")
                    st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.") # New Warning
                    st.balloons()
                    st.rerun() # Rerun to trigger the "already booked" message at the top of this page.
                elif status_msg == "LIMIT_REACHED":
                     st.error("You already have an active booking. This form should not have been available.") # Adjusted message
                     st.rerun() # Should refresh and disable form
                elif status_msg == "ALREADY_BOOKED_TIMESLOT": # Should ideally be caught by LIMIT_REACHED first
                     st.error(f"It seems this specific slot ({selected_activity} at {selected_timeslot}) was booked by you in another session or there was a conflict.")
                else: # DB_ERROR or other unexpected
                    st.error(f"Signup failed due to an unexpected issue ({status_msg}). Please try again or contact support.")



def show_admin_dashboard_page():
    st.header("👑 Admin Dashboard")
    st.write("Manage activities, view registrations, and check-in participants.")

    # --- Admin Metrics Overview ---
    total_registrations = dm.get_total_registration_count()
    checked_in_count = dm.get_checked_in_count()

    if total_registrations > 0:
        check_in_rate = (checked_in_count / total_registrations) * 100
    else:
        check_in_rate = 0

    st.subheader("Event Snapshot") # Added a subheader for the metrics section
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registrations", total_registrations)
    col2.metric("Participants Checked-In", checked_in_count)
    col3.metric("Check-In Rate (%)", f"{check_in_rate:.2f}%") # Format to 2 decimal places

    st.markdown("---") # Add a horizontal rule after metrics
    # --- End Admin Metrics Overview ---

    admin_action = st.selectbox("Admin Actions:",
                                ["View Activity Status & Check-In", "Verify by Passphrase & Check-In"],
                                key="admin_main_action_select_v2") # New key if needed

    if admin_action == "View Activity Status & Check-In":
        st.subheader("Activity Status & Registrations")

        activities = dm.get_activities()
        selected_activity = st.selectbox("Select Activity:", [""] + activities, key="admin_select_activity_v2")

        if selected_activity:
            # --- Per-Activity Metrics ---
            st.markdown(f"### Statistics for {selected_activity}") # Subheader for activity stats
            activity_total_regs = dm.get_total_registration_count_for_activity(selected_activity)
            activity_checked_in = dm.get_checked_in_count_for_activity(selected_activity)

            if activity_total_regs > 0:
                activity_check_in_rate = (activity_checked_in / activity_total_regs) * 100
            else:
                activity_check_in_rate = 0

            act_col1, act_col2, act_col3 = st.columns(3)
            act_col1.metric(f"Total Registrations ({selected_activity})", activity_total_regs)
            act_col2.metric(f"Checked-In ({selected_activity})", activity_checked_in)
            act_col3.metric(f"Check-In Rate ({selected_activity})", f"{activity_check_in_rate:.2f}%")
            st.markdown("---") # Visual separator
            # --- End Per-Activity Metrics ---

            timeslots = dm.get_timeslots()
            selected_timeslot = st.selectbox("Select Timeslot:", [""] + timeslots, key="admin_select_timeslot_v2")

            if selected_timeslot:
                st.markdown(f"**Registrations for {selected_activity} at {selected_timeslot}:**")
                registrations = dm.get_registrations_for_timeslot(selected_activity, selected_timeslot)

                if not registrations:
                    st.info("No registrations for this activity/timeslot yet.")
                else:
                    display_data = []
                    for reg in registrations: # reg is now a dict
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
                            key="admin_registrations_editor", # Added a key for stability
                            use_container_width=True,
                            hide_index=True # Usually good for display DFs
                        )

                        # Handle Edits for Check-In
                        for i in range(len(registrations_df)):
                            original_status = registrations_df.loc[i, "Checked In"]
                            edited_status = edited_df.loc[i, "Checked In"]
                            reg_id = registrations_df.loc[i, "Reg ID"] # Or edited_df, "Reg ID" is not editable

                            if not original_status and edited_status: # Changed from False to True
                                # Ensure reg_id is an integer before passing
                                # Ensure reg_id is an integer before passing
                                if dm.check_in_registration(int(reg_id)):
                                    st.success(f"Checked in participant with Reg ID: {reg_id}.")
                                else:
                                    st.error(f"Failed to check in participant with Reg ID: {reg_id}.")
                                st.rerun() # Rerun after the first successful check-in
                            # Add new logic here for unchecking
                            elif original_status and not edited_status: # Changed from True to False (Uncheck)
                                if dm.uncheck_in_registration(int(reg_id)):
                                    st.success(f"Unchecked participant with Reg ID: {reg_id}.")
                                else:
                                    st.error(f"Failed to uncheck participant with Reg ID: {reg_id}.")
                                st.rerun()
                    else:
                        st.info("No registrations data to display in editor.")


    elif admin_action == "Verify by Passphrase & Check-In":
        st.subheader("Verify by Passphrase & Check-In")

        with st.form("passphrase_verify_form_v2"):
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input_v2")
            verify_button = st.form_submit_button("Verify Passphrase")

        if verify_button and passphrase_input:
            normalized_passphrase = passphrase_input.strip().lower()
            registration = dm.get_registration_by_passphrase(normalized_passphrase) # Now a dict or None

            if not registration:
                st.error("Invalid or unknown passphrase. Please check the input (format: word-word-word-word).")
            else:
                st.success(f"Registration Found for Passphrase: **{ut.format_passphrase_display(registration['registration_passphrase'])}**")

                details_cols = st.columns(2)
                details_cols[0].markdown(f"**Name:** {registration['participant_name']}")
                # Email display removed from here
                details_cols[1].markdown(f"**Activity:** {registration['activity']}")
                details_cols[1].markdown(f"**Timeslot:** {registration['timeslot']}")

                st.markdown("---")

                if bool(registration['checked_in']): # Use bool() for clarity, 1 is True
                    st.warning("This participant is already checked-in.")
                else:
                    st.info("Status: Pending Check-In")
                    checkin_button_key = f"passphrase_checkin_verify_view_{registration['id']}"
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration['id']):
                            st.success(f"Successfully checked in {registration['participant_name']} for {registration['activity']}.")
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
        current_booking = user_registrations[0] # This gets the first dict from the list

        st.subheader(f"Your booking for: {current_booking['activity']}")
        st.markdown(f"**Timeslot:** {current_booking['timeslot']}")
        st.markdown(f"**Your Name (for this booking):** {current_booking['participant_name']}")

        st.markdown("---")
        st.subheader("Your Verification Passphrase:")
        st.code(ut.format_passphrase_display(current_booking['registration_passphrase']))
        st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
        st.markdown("---")

        if st.button("Cancel This Booking", key=f"cancel_booking_{current_booking['id']}", type="primary"):
            if dm.cancel_registration(current_booking['id']):
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
        # Display persistent signup success message if available
        if st.session_state.get('signup_success'):
            details = st.session_state.get('last_signup_details', {})
            if details: # Check if details exist
                st.success(f"Success! You are signed up for {details.get('activity', 'N/A')} at {details.get('timeslot', 'N/A')}.")
                st.info(f"Your unique verification code for this booking is: **{ut.format_passphrase_display(details.get('passphrase', ''))}**")
                st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
                st.balloons() # Show balloons again with the persistent message
            else:
                # Fallback if details somehow got lost, though unlikely with this logic
                st.success("Signup successful! Your registration details are available in 'My Bookings'.")

            # Clear the flag and details to prevent re-displaying on next interaction/rerun
            del st.session_state.signup_success
            if 'last_signup_details' in st.session_state:
                del st.session_state.last_signup_details

        st.title("🏖️ Beach Day Activity Signup")
        st.sidebar.subheader("User Actions")
        # participant_profile is still fetched

        # If participant_profile exists, show welcome and options
        if participant_profile:
            # Access participant's name by key 'name'
            participant_name_display = participant_profile['name'] if participant_profile else "Guest"
            st.sidebar.info(f"Welcome, {participant_name_display}!")
            user_page_options = ["Sign Up For Activities", "My Bookings"]
            user_action = st.sidebar.selectbox("What would you like to do?", user_page_options, key="user_action_select_v2") # New key

            if user_action == "Sign Up For Activities":
                show_signup_page(user_id, participant_profile)
            elif user_action == "My Bookings":
                show_my_bookings_page(user_id, participant_profile)

            # Add the "View My Current Registrations" expander here
            my_registrations = dm.get_registrations_for_participant(user_id)
            if my_registrations:
                with st.expander("View My Current Registrations"):
                    # This inner check is a bit redundant if my_registrations list is already checked,
                    # but kept for safety / clarity from original instruction.
                    if not my_registrations:
                         st.write("No registrations found.")
                    else:
                        for reg in my_registrations: # reg is now a dict
                            st.markdown(f"- **Activity:** {reg['activity']}")
                            st.markdown(f"  **Timeslot:** {reg['timeslot']}")
                            st.markdown(f"  **Passphrase:** {ut.format_passphrase_display(reg['registration_passphrase'])}")
                            st.markdown("---")
        else:
            # If no profile, directly show signup page.
            # Profile creation will be handled within show_signup_page.
            st.sidebar.info("Welcome, new guest! Please sign up for an activity to register.") # Or similar
            show_signup_page(user_id, participant_profile) # participant_profile will be None here

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
