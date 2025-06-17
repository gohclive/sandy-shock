import streamlit as st
import pandas as pd # Keep for potential future use in display, even if grid is custom
import uuid
import os # For potential path manipulations if needed, though data_manager handles its own
# To import local modules correctly when running streamlit run app.py from project root:
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Adds 'beach_signup' directory to path
import data_manager as dm
import utils as ut

# Placeholder functions for pages - to be implemented in later steps

def show_signup_page(participant):
    st.header("Sign Up For Activities")

    activities = dm.get_activities()
    timeslots = dm.get_timeslots()
    participant_id = participant['id']

    # Create availability grid data
    grid_data = {}
    MAX_CAPACITY_PER_SLOT = 10 # Define slot capacity

    for activity in activities:
        row_data = {}
        for timeslot in timeslots:
            count = dm.get_signup_count(activity, timeslot)
            if count >= MAX_CAPACITY_PER_SLOT:
                row_data[timeslot] = f"{count} (Full)"
            else:
                row_data[timeslot] = f"{count}"
        grid_data[activity] = row_data

    availability_df = pd.DataFrame.from_dict(grid_data, orient='index', columns=timeslots)

    st.subheader("Current Availability (Signups per Slot)")
    # Display the DataFrame. Apply styling to highlight "Full" slots if desired.
    # For example, using st.table or st.dataframe. st.dataframe is good for larger tables.
    st.dataframe(availability_df.style.applymap(lambda x: 'background-color: #FFCCCC' if "(Full)" in str(x) else ''), use_container_width=True)


    st.subheader("Book Your Slot")
    # Check if participant has any existing bookings to display a relevant message
    user_current_signups = dm.get_user_signups(participant_id)
    booked_timeslots = {signup['timeslot'] for signup in user_current_signups}

    with st.form("signup_form"):
        selected_activity = st.selectbox("Choose an Activity:", options=activities)
        # Filter timeslots to only show those the user isn't already booked for,
        # or disable selection for booked slots. For simplicity, we'll allow selection
        # and handle the conflict in validation.
        selected_timeslot = st.selectbox("Choose a Timeslot:", options=timeslots)
        submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            if not selected_activity or not selected_timeslot:
                st.error("Please select both an activity and a timeslot.")
                return # Avoid further processing

            current_slot_occupancy = dm.get_signup_count(selected_activity, selected_timeslot)
            if current_slot_occupancy >= MAX_CAPACITY_PER_SLOT:
                st.warning(f"The slot for {selected_activity} at {selected_timeslot} is currently full. Please choose another.")
            elif selected_timeslot in booked_timeslots:
                # Find which activity they are booked for at that time
                conflicting_activity = ""
                for signup in user_current_signups:
                    if signup['timeslot'] == selected_timeslot:
                        conflicting_activity = signup['activity']
                        break
                st.error(f"You are already signed up for '{conflicting_activity}' at {selected_timeslot}. You can only sign up for one activity per timeslot. Please cancel your existing booking if you wish to change.")
            else:
                # Proceed with signup
                success = dm.add_signup(participant_id, selected_activity, selected_timeslot)
                if success:
                    st.success(f"Successfully signed up for {selected_activity} at {selected_timeslot}!")
                    st.balloons() # Add some flair!
                    st.rerun()
                else:
                    # This case should be rare now due to the checks above, but could be a DB issue
                    st.error("Signup failed due to an unexpected issue. Please try again.")



def show_my_schedule_page(participant):
    st.header("My Schedule")
    participant_id = participant['id']

    st.info(f"Your verification code: **{ut.format_passphrase_display(participant['passphrase'])}**")
    st.caption("Keep this code safe for check-in on event day!")

    user_signups = dm.get_user_signups(participant_id)

    if not user_signups:
        st.write("You haven't signed up for any activities yet.")
        if st.button("Go to Sign Up Page"):
            # To switch pages, we can't directly call another show_... function here
            # A common way in Streamlit is to use session state to manage the current page view
            # if the main app structure supports it, or simply guide the user.
            # For this app structure, the user uses the sidebar. So, just a prompt.
            st.info("Use the sidebar to navigate to 'Sign Up For Activities'.")
    else:
        st.subheader("Your Current Signups:")
        # Using columns for a slightly better layout for activity, timeslot, and cancel button
        col_defs = [{"header": "Activity", "field": "activity"},
                    {"header": "Timeslot", "field": "timeslot"},
                    {"header": "Action", "field": "cancel_action"}] # For potential future st.data_editor

        for signup in user_signups:
            activity = signup['activity']
            timeslot = signup['timeslot']

            cols = st.columns([3, 2, 1.5]) # Adjust ratios as needed
            cols[0].write(f"**{activity}**")
            cols[1].write(f"at {timeslot}")

            # Create a unique key for each cancel button
            button_key = f"cancel_{participant_id}_{activity}_{timeslot}"
            if cols[2].button("Cancel Signup", key=button_key, type="secondary"):
                success = dm.cancel_signup(participant_id, activity, timeslot)
                if success:
                    st.success(f"Cancelled signup for {activity} at {timeslot}.")
                    st.rerun() # Rerun to refresh the schedule
                else:
                    st.error("Could not cancel signup. Please try again.")
            st.markdown("---") # Separator



def show_verification_page():
    st.header("Verify Participant (Staff)")

    search_term = st.text_input("Enter participant's name or verification code:", key="staff_search_term")

    if st.button("Search Participant", key="staff_search_button") and search_term:
        results = dm.verify_participant(search_term.strip())

        if not results:
            st.info(f"No participants found matching '{search_term}'. Please check the name or code.")
        else:
            st.subheader("Search Results:")
            # Group results by participant (name, passphrase) because a participant might have multiple signups
            # dm.verify_participant returns a list of rows, each potentially a signup.
            # Each row contains: p.name, p.passphrase, s.activity, s.timeslot

            verified_participants_details = {} # Key: (name, passphrase), Value: list of (activity, timeslot)

            for row in results:
                participant_key = (row['name'], row['passphrase'])
                activity_info = (row['activity'], row['timeslot']) if row['activity'] else ("No activities signed up", "")

                if participant_key not in verified_participants_details:
                    verified_participants_details[participant_key] = []

                # Add activity if it's not already listed (e.g. if JOIN produced multiple rows for same signup somehow, though not expected with current query)
                # Or if there are genuinely multiple signups for this person
                if activity_info[0] != "No activities signed up" or not verified_participants_details[participant_key]:
                     verified_participants_details[participant_key].append(activity_info)


            for (name, passphrase), activities_list in verified_participants_details.items():
                st.markdown(f"**Name:** {name}")
                st.markdown(f"**Verification Code:** {ut.format_passphrase_display(passphrase)}")
                if activities_list and activities_list[0][0] != "No activities signed up":
                    st.markdown("**Signed-up Activities:**")
                    for activity, timeslot in activities_list:
                        st.write(f"- {activity} at {timeslot}")
                else:
                    st.write("No activities signed up.")
                st.markdown("---")
    elif st.session_state.get("staff_search_button") and not search_term: # If button was clicked but search term is empty
        st.warning("Please enter a name or verification code to search.")


def initialize_user_session():
    """Handles user identification via URL or creates new session."""
    if 'user_id' not in st.session_state:
        # Try to get 'uid' from query params
        query_params = st.query_params
        if "uid" in query_params and query_params["uid"]:
            # Ensure it's a single value, not a list
            uid_val = query_params["uid"]
            st.session_state.user_id = uid_val[0] if isinstance(uid_val, list) else uid_val
        else:
            # Generate a new user_id and set it in session state and query_params
            user_id = f"beach_{str(uuid.uuid4())[:8]}"
            st.session_state.user_id = user_id
            # This will update the URL, making it bookmarkable
            st.query_params["uid"] = user_id

def main():
    st.set_page_config(page_title="Beach Day Signup", page_icon="🏖️", layout="wide")
    st.title("🏖️ Beach Day Activity Signup")

    dm.initialize_database() # Ensures DB and tables exist
    initialize_user_session() # Sets up st.session_state.user_id and URL

    user_id = st.session_state.user_id
    participant = dm.find_participant_by_id(user_id)

    if not participant:
        # New user flow
        st.header("Welcome to Beach Day!")
        with st.form("new_user_form"):
            name = st.text_input("Please enter your full name to get started:")
            submitted = st.form_submit_button("Let's Go!")

            if submitted:
                if ut.validate_name(name):
                    new_passphrase = dm.create_participant(user_id, name.strip())
                    if new_passphrase:
                        st.success(f"Welcome, {name.strip()}! You're all set up. Your verification code will be shown on the next page. Redirecting...")
                        # Set flag to avoid query param issues on rerun, or just rerun
                        st.rerun()
                    else:
                        st.error("Could not create participant. Please try again.")
                else:
                    st.error("Please enter a valid name (at least 2 characters).")
    else:
        # Returning user flow
        st.sidebar.header(f"Welcome, {participant['name']}!")

        # Construct the unique link
        # For local development, st.get_option('server.baseUrlPath') might be empty.
        # A more robust way to get the base URL is harder with Streamlit if not behind a proxy.
        # Simplest for now, assuming localhost and default port.
        # Consider making this configurable if deploying.
        try:
            # This is an experimental feature and might change
            # For newer streamlit versions:
            # from streamlit.web.server.server_util import get_url
            # current_url = get_url("") # This gets the base path
            # base_url = current_url.split('?')[0]
            # However, st.get_option is more standard for now if available for this purpose
            # For a direct query param link:
            base_url = st.get_option('server.baseUrlPath') or "" # this is often empty or just a path
            # A common pattern is to just reconstruct it if you know your domain
            # For local:
            host = "localhost"
            port = st.get_option('server.port') or 8501
            base_url_for_link = f"http://{host}:{port}/{base_url}".strip('/')

        except Exception: # Fallback if options are not available
            base_url_for_link = "http://localhost:8501"


        unique_link = f"{base_url_for_link}?uid={user_id}"

        st.sidebar.info("Your personal link to manage signups:")
        st.sidebar.code(unique_link)
        st.sidebar.warning(f"Your verification code is:\n**{ut.format_passphrase_display(participant['passphrase'])}**")
        st.sidebar.caption("Save this code for check-in on event day!")

        page_options = ["Sign Up For Activities", "My Schedule", "Verify Participant (Staff)"]
        page = st.sidebar.selectbox("Choose action:", page_options)

        if page == "Sign Up For Activities":
            show_signup_page(participant)
        elif page == "My Schedule":
            show_my_schedule_page(participant)
        elif page == "Verify Participant (Staff)":
            show_verification_page() # No participant object needed here

if __name__ == "__main__":
    main()
