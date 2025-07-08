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

from session_manager import sync_session_state_with_url

# --- THIS IS THE MOST IMPORTANT STEP ---
# Call the sync function AT THE VERY TOP of the script.
sync_session_state_with_url()
# -----------------------------------------

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
    all_activities_details = dm.ACTIVITIES # Get the full list of activity dicts
    
    st.subheader("Current Availability")

    """Display disclaimer about limited material sets."""
    st.info("📦 **Limited materials (200 sets each) - while supplies last! Canvas & Tote Bag stations will close once materials run out**")


    for activity_detail in all_activities_details:
        activity_name = activity_detail["name"]
        activity_duration = activity_detail["duration"]
        activity_capacity = activity_detail["slots"]
        
        with st.expander(label=f"{activity_name} (Duration: {activity_duration} mins)", expanded=False):
            activity_specific_timeslots = dm.get_timeslots(activity_duration)
            activity_timeslots_info = []
            all_slots_for_activity_full = True

            if not activity_specific_timeslots:
                st.markdown("<font color='orange'>No timeslots available for this activity based on its duration and event schedule.</font>", unsafe_allow_html=True)
                continue

            for timeslot_item in activity_specific_timeslots:
                count = dm.get_signup_count(activity_name, timeslot_item)
                available_slots = activity_capacity - count

                status_text = ""
                if available_slots <= 0:
                    status_text = f"**{timeslot_item}:** <font color='red'>Full</font>"
                elif available_slots <= (activity_capacity * 0.1): # e.g., <= 3 if capacity is 30
                    status_text = f"**{timeslot_item}:** <font color='orange'>{available_slots} Slots Available</font>"
                    all_slots_for_activity_full = False
                else:
                    status_text = f"**{timeslot_item}:** <font color='green'>{available_slots} Slots Available</font>"
                    all_slots_for_activity_full = False
                activity_timeslots_info.append(status_text)

            if all_slots_for_activity_full and activity_specific_timeslots: # only show if timeslots existed
                 st.markdown(f"<font color='red'>All timeslots for this activity are currently full.</font>", unsafe_allow_html=True)
            
            if activity_timeslots_info: # Check if there's any info to display
                num_columns = 2
                if len(activity_specific_timeslots) > 6: # Base columns on number of actual timeslots
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
        
        activity_names_list = dm.get_activities() # Get just the names for the first selectbox

        with st.form("registration_form_no_email"):
            name = st.text_input("Your Full Name:", value=default_name, key="reg_form_name_v2")
            
            # Simplified activity selection without callbacks
            selected_activity_name = st.selectbox( 
                "Choose an Activity:", 
                options=activity_names_list, 
                key="reg_form_activity_select_key"
            )
            
            activity_details = dm.get_activity_details(selected_activity_name)
            
            selected_timeslot = None 
            activity_specific_timeslots = [] 

            if activity_details:
                activity_specific_timeslots = dm.get_timeslots(activity_details["duration"])
                if not activity_specific_timeslots:
                    st.warning(f"No available timeslots for {selected_activity_name} based on its duration and event times. Please select another activity.", icon="⚠️")
                else:
                    selected_timeslot = st.selectbox(
                        "Choose a Timeslot:", 
                        options=activity_specific_timeslots, 
                        key=f"reg_form_timeslot_v2_{activity_details['id']}" 
                    )
            elif activity_names_list: # Only show error if there were activities to select from but details were not found
                st.error("Could not find details for the selected activity. Please refresh or contact support.")
            # If activity_names_list is empty, no error, form will just be mostly disabled.

            is_slot_full_check = False 
            current_activity_capacity = 0 
            if activity_details and selected_timeslot : 
                current_activity_capacity = activity_details["slots"]
                if dm.get_signup_count(activity_details["name"], selected_timeslot) >= current_activity_capacity:
                    is_slot_full_check = True
            
            submit_button_disabled = is_slot_full_check or not selected_timeslot or not activity_specific_timeslots or not activity_details
            submit_button = st.form_submit_button("Sign Up", disabled=submit_button_disabled)

            if submit_button:
                final_selected_activity_name = selected_activity_name
                final_selected_timeslot = selected_timeslot 

                if not ut.validate_name(name):
                    st.error("Please enter a valid name (at least 2 characters).")
                    return

                final_activity_details = dm.get_activity_details(final_selected_activity_name)
                if not final_activity_details:
                    st.error("Critical error: Activity details not found on submit. Please refresh.")
                    return
                
                final_activity_capacity = final_activity_details["slots"]
                current_count_on_submit = dm.get_signup_count(final_selected_activity_name, final_selected_timeslot)
                
                if current_count_on_submit >= final_activity_capacity:
                    st.error(f"Sorry, {final_selected_activity_name} at {final_selected_timeslot} just became full as you were submitting.")
                    st.rerun()
                    return

                if not current_participant_profile: 
                    dm.create_participant(participant_session_id, name.strip())
                
                reg_id, new_passphrase, status_msg = dm.add_registration(
                    participant_session_id, 
                    name.strip(), 
                    final_selected_activity_name, 
                    final_selected_timeslot
                )

                if status_msg == "SUCCESS":
                    st.session_state.signup_success = True
                    st.session_state.last_signup_details = {
                        "activity": final_selected_activity_name,
                        "timeslot": final_selected_timeslot,
                        "passphrase": new_passphrase
                    }
                    st.rerun()
                elif status_msg == "LIMIT_REACHED":
                     st.error("You already have an active booking. This form should not have been available.")
                     st.rerun()
                elif status_msg == "ALREADY_BOOKED_TIMESLOT": 
                     st.error(f"It seems you have already booked this specific slot ({final_selected_activity_name} at {final_selected_timeslot}) or another conflicting booking.")
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



def display_user_portal():
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