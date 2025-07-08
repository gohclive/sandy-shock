import streamlit as st
# import pandas as pd # No longer used in this file
import uuid
import os
import sys
import datetime
import ntplib
import pytz

# Path Adjustment for imports
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_or_beach_signup_dir = os.path.dirname(current_file_dir) # This should be 'beach_signup'
if project_root_or_beach_signup_dir not in sys.path:
    sys.path.append(project_root_or_beach_signup_dir)

import data_manager as dm
import utils as ut

# --- NTP Time Function ---
def get_current_singapore_time():
    """Fetches time from NTP and converts to Singapore timezone."""
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org', version=3)
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time, datetime.timezone.utc)
        singapore_tz = pytz.timezone('Asia/Singapore')
        return ntp_time.astimezone(singapore_tz)
    except Exception as e:
        st.error(f"Error fetching NTP time: {e}. Falling back to system time for checks (this might be inaccurate).")
        # Fallback to system time in case NTP fails, but make it clear it's a fallback.
        # For a production system, you might want a more robust fallback or error handling.
        return datetime.datetime.now(pytz.timezone('Asia/Singapore'))

# ADMIN_USERNAME and ADMIN_PASSWORD removed
# show_admin_dashboard_page function removed

# Function to display the participant sign-up page
def show_signup_page(participant_session_id, current_participant_profile):
    st.header("📝 Sign Up For Activities")

    # --- Display Activity Availability Grid (Moved Up) ---
    activities = dm.get_activities()
    timeslots = dm.get_timeslots()
    MAX_CAPACITY_PER_SLOT = 10

    st.subheader("Current Availability")

    for activity_item in activities:
        with st.expander(label=activity_item, expanded=False):
            activity_timeslots_info = []
            all_slots_for_activity_full = True

            for timeslot_item in timeslots:
                count = dm.get_signup_count(activity_item, timeslot_item)
                available_slots = MAX_CAPACITY_PER_SLOT - count

                status_text = ""
                if available_slots <= 0:
                    status_text = f"**{timeslot_item}:** <font color='red'>Full</font>"
                elif available_slots <= 3:
                    status_text = f"**{timeslot_item}:** <font color='orange'>{available_slots} Slots Available</font>"
                    all_slots_for_activity_full = False
                else:
                    status_text = f"**{timeslot_item}:** <font color='green'>{available_slots} Slots Available</font>"
                    all_slots_for_activity_full = False
                activity_timeslots_info.append(status_text)

            if all_slots_for_activity_full:
                 st.markdown(f"<font color='red'>All timeslots for this activity are currently full.</font>", unsafe_allow_html=True)
            else:
                num_columns = 2
                if len(timeslots) > 6:
                     num_columns = 3

                cols = st.columns(num_columns)
                for i, info_md in enumerate(activity_timeslots_info):
                    cols[i % num_columns].markdown(info_md, unsafe_allow_html=True)

    # --- Conditional Display: Warning or Signup Form ---
    user_existing_registrations = dm.get_user_registrations(participant_session_id)

    if user_existing_registrations:
        st.warning("You already have an active booking. You can only sign up for one activity at a time.")
        st.info("Please visit the 'My Bookings' page (accessible from the sidebar if added to navigation) to view or cancel your current booking if you wish to sign up for a different activity.")
    else:
        st.subheader("Book Your Slot")
        default_name = current_participant_profile['name'] if current_participant_profile else ""

        with st.form("registration_form_no_email"):
            name = st.text_input("Your Full Name:", value=default_name, key="reg_form_name_v2")
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

                current_count_on_submit = dm.get_signup_count(selected_activity, selected_timeslot)
                if current_count_on_submit >= MAX_CAPACITY_PER_SLOT:
                    st.error(f"Sorry, {selected_activity} at {selected_timeslot} just became full.")
                    st.rerun()
                    return

                if not current_participant_profile:
                    dm.create_participant(participant_session_id, name.strip())

                reg_id, new_passphrase, status_msg = dm.add_registration(participant_session_id, name.strip(), selected_activity, selected_timeslot)

                if status_msg == "SUCCESS":
                    st.session_state.signup_success = True
                    st.session_state.last_signup_details = {
                        "activity": selected_activity,
                        "timeslot": selected_timeslot,
                        "passphrase": new_passphrase
                    }
                    st.success(f"Success! You are signed up for {selected_activity} at {selected_timeslot}.")
                    st.info(f"Your unique verification code for this booking is: **{ut.format_passphrase_display(new_passphrase)}**")
                    st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
                    st.balloons()
                    st.rerun()
                elif status_msg == "LIMIT_REACHED":
                     st.error("You already have an active booking. This form should not have been available.")
                     st.rerun()
                elif status_msg == "ALREADY_BOOKED_TIMESLOT":
                     st.error(f"It seems this specific slot ({selected_activity} at {selected_timeslot}) was booked by you in another session or there was a conflict.")
                else:
                    st.error(f"Signup failed due to an unexpected issue ({status_msg}). Please try again or contact support.")

def show_my_bookings_page(user_id, participant_profile):
    st.header("My Active Booking")

    if not participant_profile:
        st.warning("Please register your name on the 'Sign Up For Activities' page first if you are a new user.")
        return

    user_registrations = dm.get_user_registrations(user_id)

    if not user_registrations:
        st.info("You have no active bookings.")
        st.write("Feel free to sign up for an activity!")
    else:
        current_booking = user_registrations[0]

        st.subheader(f"Your booking for: {current_booking['activity']}")
        st.markdown(f"**Timeslot:** {current_booking['timeslot']}")
        st.markdown(f"**Your Name (for this booking):** {current_booking['participant_name']}")

        st.markdown("---")
        st.subheader("Your Verification Passphrase:")
        st.code(ut.format_passphrase_display(current_booking['registration_passphrase']))
        st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
        st.markdown("---")

        is_checked_in = bool(current_booking['checked_in']) # Convert 0/1 to False/True

        if is_checked_in:
            st.warning("🔒 This booking cannot be canceled as you are already checked in for the activity.")

        cancel_button_disabled = is_checked_in

        if st.button("Cancel This Booking", key=f"cancel_booking_{current_booking['id']}", type="primary", disabled=cancel_button_disabled):
            if dm.cancel_registration(current_booking['id']):
                st.success("Your booking has been successfully cancelled.")
                st.info("You can now sign up for a new activity.")
                st.balloons()
                st.rerun()
            else:
                st.error("Could not cancel the booking. Please try again or contact support.")

def initialize_user_session():
    if 'user_id' not in st.session_state:
        query_params = st.query_params
        uid_from_url = query_params.get("uid")
        if uid_from_url:
            st.session_state.user_id = uid_from_url[0] if isinstance(uid_from_url, list) else uid_from_url
        else:
            new_user_id = f"beach_{str(uuid.uuid4())[:8]}"
            st.session_state.user_id = new_user_id
            st.query_params["uid"] = new_user_id

def display_user_portal():
    # st.set_page_config removed
    # dm.initialize_database() removed (will be in main app.py)

    # --- Portal Lock Logic ---
    singapore_tz = pytz.timezone('Asia/Singapore')
    unlock_date = singapore_tz.localize(datetime.datetime(2025, 7, 10, 0, 0, 0))
    current_sg_time = get_current_singapore_time()

    if current_sg_time < unlock_date:
        st.title("🏖️ User Portal - Temporarily Closed")
        st.image("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True) # Example beach image
        st.warning(
            f"The User Portal is currently closed. "
            f"It will become accessible on **July 10, 2025** (Singapore Time)."
        )
        st.info(f"Current Singapore Time: {current_sg_time.strftime('%Y-%m-%d %I:%M %p')}")
        st.info(f"Scheduled Unlock Time: {unlock_date.strftime('%Y-%m-%d %I:%M %p')}")
        return # Stop further execution if portal is locked

    initialize_user_session()

    user_id = st.session_state.user_id
    participant_profile = dm.find_participant_by_id(user_id)

    # Logic from the former "User Section"
    if st.session_state.get('signup_success'):
        details = st.session_state.get('last_signup_details', {})
        if details:
            st.success(f"Success! You are signed up for {details.get('activity', 'N/A')} at {details.get('timeslot', 'N/A')}.")
            st.info(f"Your unique verification code for this booking is: **{ut.format_passphrase_display(details.get('passphrase', ''))}**")
            st.warning("IMPORTANT: Do not share this passphrase with anyone. It is your unique code for check-in.")
            st.balloons()
        else:
            st.success("Signup successful! Your registration details are available in 'My Bookings'.")

        del st.session_state.signup_success
        if 'last_signup_details' in st.session_state:
            del st.session_state.last_signup_details

    st.title("🏖️ User Portal") # Or "Beach Day Activity Signup"
    st.sidebar.subheader("User Actions")
    st.sidebar.caption(
        "Tip: Your session is unique to this URL. "
        "Bookmark this page to easily return to your activities and bookings."
    )

    if participant_profile:
        participant_name_display = participant_profile['name'] if participant_profile else "Guest"
        st.sidebar.info(f"Welcome, {participant_name_display}!")
        user_page_options = ["Sign Up For Activities", "My Bookings"]
        user_action = st.sidebar.selectbox("What would you like to do?", user_page_options, key="user_action_select_v2")

        if user_action == "Sign Up For Activities":
            show_signup_page(user_id, participant_profile)
        elif user_action == "My Bookings":
            show_my_bookings_page(user_id, participant_profile)

        my_registrations = dm.get_registrations_for_participant(user_id)
        if my_registrations:
            with st.expander("View My Current Registrations"):
                if not my_registrations:
                     st.write("No registrations found.")
                else:
                    for reg in my_registrations:
                        st.markdown(f"- **Activity:** {reg['activity']}")
                        st.markdown(f"  **Timeslot:** {reg['timeslot']}")
                        st.markdown(f"  **Passphrase:** {ut.format_passphrase_display(reg['registration_passphrase'])}")
                        st.markdown("---")
    else:
        st.sidebar.info("Welcome, new guest! Please sign up for an activity to register.")
        show_signup_page(user_id, participant_profile) # participant_profile will be None here

# Call the main function for this page
display_user_portal()
