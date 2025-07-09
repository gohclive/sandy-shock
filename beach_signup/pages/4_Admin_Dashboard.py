import streamlit as st
import pandas as pd
import secrets
import os
import sys

# Path adjustment for imports (data_manager, utils)
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_or_beach_signup_dir = os.path.dirname(current_file_dir)
if project_root_or_beach_signup_dir not in sys.path:
    sys.path.append(project_root_or_beach_signup_dir)


from session_manager import sync_session_state_with_url, initialize_user_if_needed

# --- THIS IS THE MOST IMPORTANT STEP ---
# Call the sync function AT THE VERY TOP of the script.
sync_session_state_with_url()
initialize_user_if_needed()
# -----------------------------------------

import data_manager as dm
import utils as ut

# Admin Credentials
ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# show_admin_dashboard_page() function definition (updated for new timeslot structure)
def show_admin_dashboard_page():
    st.header("👑 Admin Dashboard")

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

    admin_action_options = [
        "View Activity Status & Check-In", 
        "Verify by Passphrase & Check-In",
        "Manage Competitive Games & Scores"
    ]
    admin_action = st.selectbox("Admin Actions:",
                                admin_action_options,
                                key="admin_main_action_select_page")

    if admin_action == "View Activity Status & Check-In":
        st.subheader("Activity Status & Registrations")
        
        # Get the single activity (first one in the list)
        activities = dm.get_activities()
        
        if not activities:
            st.error("No activities available in the system.")
            return
        
        # Use the first (and only) activity
        selected_activity = activities[0]
        
        st.markdown(f"### Activity: {selected_activity}")
        st.info("Only one activity is configured for this event.")
        
        activity_total_regs = dm.get_total_registration_count_for_activity(selected_activity)
        activity_checked_in = dm.get_checked_in_count_for_activity(selected_activity)
        activity_check_in_rate = (activity_checked_in / activity_total_regs) * 100 if activity_total_regs > 0 else 0

        act_col1, act_col2, act_col3 = st.columns(3)
        act_col1.metric(f"Total Registrations", activity_total_regs)
        act_col2.metric(f"Checked-In", activity_checked_in)
        act_col3.metric(f"Check-In Rate", f"{activity_check_in_rate:.2f}%")
        st.markdown("---")

        # Get timeslots for the selected activity
        activity_details = dm.get_activity_details(selected_activity)
        if activity_details:
            timeslots = dm.get_timeslots(activity_details["duration"])
            
            if not timeslots:
                st.warning("No timeslots available for this activity.")
                return
                
            selected_timeslot = st.selectbox("Select Timeslot:", [""] + timeslots, key="admin_select_timeslot_page")

            if selected_timeslot:
                st.markdown(f"**Registrations for {selected_activity} at {selected_timeslot}:**")
                registrations = dm.get_registrations_for_timeslot(selected_activity, selected_timeslot)
                if not registrations:
                    st.info("No registrations for this timeslot yet.")
                else:
                    display_data = []
                    for reg in registrations:
                        is_checked_in = bool(reg['checked_in'])
                        display_data.append({
                            "Reg ID": reg['id'],
                            "Name": reg['participant_name'],
                            "Passphrase": ut.format_passphrase_display(reg['registration_passphrase']),
                            "Checked In": is_checked_in,
                            "Remove": False,  # New column for deletion
                        })
                    registrations_df = pd.DataFrame(display_data)
                    if not registrations_df.empty:
                        disabled_columns = [col for col in registrations_df.columns if col not in ["Checked In", "Remove"]]
                        edited_df = st.data_editor(
                            registrations_df,
                            disabled=disabled_columns,
                            key="admin_registrations_editor_page",
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Remove": st.column_config.CheckboxColumn(
                                    "🗑️ Remove",
                                    help="Check to remove this registration",
                                    default=False,
                                )
                            }
                        )
                        
                        # Handle check-in/uncheck-in changes
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
                        
                        # Handle removal requests
                        registrations_to_remove = []
                        for i in range(len(edited_df)):
                            if edited_df.loc[i, "Remove"]:
                                reg_id = edited_df.loc[i, "Reg ID"]
                                name = edited_df.loc[i, "Name"]
                                registrations_to_remove.append((reg_id, name))
                        
                        if registrations_to_remove:
                            st.warning(f"⚠️ You are about to remove {len(registrations_to_remove)} registration(s). This action cannot be undone!")
                            for reg_id, name in registrations_to_remove:
                                st.write(f"- {name} (ID: {reg_id})")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Confirm Removal", type="primary", key="confirm_bulk_remove"):
                                    removed_count = 0
                                    for reg_id, name in registrations_to_remove:
                                        if dm.cancel_registration(int(reg_id)):
                                            removed_count += 1
                                        else:
                                            st.error(f"Failed to remove registration for {name}")
                                    
                                    if removed_count > 0:
                                        st.success(f"Successfully removed {removed_count} registration(s)")
                                        st.rerun()
                            with col2:
                                if st.button("❌ Cancel", key="cancel_bulk_remove"):
                                    st.rerun()
                    else:
                        st.info("No registrations data to display in editor.")
        else:
            st.error("Activity details not found. Please check your data_manager configuration.")

    elif admin_action == "Verify by Passphrase & Check-In":
        st.subheader("Verify by Passphrase & Check-In")
        with st.form("passphrase_verify_form_page"):
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input_page")
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
                    checkin_button_key = f"passphrase_checkin_verify_view_page_{registration['id']}"
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration['id']):
                            st.success(f"Successfully checked in {registration['participant_name']} for {registration['activity']}.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Check-in failed.")
        elif verify_button and not passphrase_input:
            st.warning("Please enter a passphrase to verify.")

    elif admin_action == "Manage Competitive Games & Scores":
        st.subheader("🏅 Manage Competitive Games & Scores")
        tab1, tab2, tab3 = st.tabs(["Manage Scores", "Manage Games", "Manage Teams"])

        with tab1: # Manage Scores
            st.markdown("#### Update Team Scores")
            
            games = dm.get_competitive_games()
            teams = dm.get_teams()

            if not games or not teams:
                st.warning("Please add games and teams first using the 'Manage Games' and 'Manage Teams' tabs before updating scores.")
            else:
                # Fetch current scores for display and editing
                score_data, game_names, team_names = dm.get_all_scores()

                if not game_names or not team_names:
                    st.info("No games or teams available to score. Add them in the respective tabs.")
                else:
                    # Create a DataFrame for st.data_editor
                    # Rows: Teams, Columns: Game Names, Values: Scores
                    editor_data = []
                    for team_name in team_names:
                        row = {'Team': team_name}
                        # Ensure all games are columns for each team
                        for game_name in game_names:
                            row[game_name] = score_data.get(team_name, {}).get(game_name, 0)
                        editor_data.append(row)
                    
                    scores_df = pd.DataFrame(editor_data)
                    
                    # Get team and game maps for ID lookup
                    team_map = {team['name']: team['id'] for team in teams}
                    game_map = {game['name']: game['id'] for game in games}

                    edited_df = st.data_editor(
                        scores_df,
                        key="edit_scores_data_editor",
                        num_rows="dynamic", # Should be static if teams are predefined
                        disabled=["Team"], # Team names are not editable here
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if st.button("Save All Score Changes", key="save_all_scores_button"):
                        changes_made = 0
                        errors = 0
                        for index, row in edited_df.iterrows():
                            team_name = row['Team']
                            if team_name not in team_map:
                                st.error(f"Team '{team_name}' not found in mapping. Skipping.")
                                errors +=1
                                continue
                            
                            team_id = team_map[team_name]
                            
                            for game_name in game_names: # Iterate through game_names to ensure all are checked
                                if game_name not in game_map:
                                    st.error(f"Game '{game_name}' not found in mapping. Skipping for team {team_name}.")
                                    errors +=1
                                    continue
                                
                                game_id = game_map[game_name]
                                new_score = row[game_name]
                                
                                # Check if score actually changed to avoid unnecessary DB calls
                                original_score = score_data.get(team_name, {}).get(game_name, 0)
                                try:
                                    new_score_val = int(new_score) # Ensure score is an int
                                except ValueError:
                                    st.error(f"Invalid score '{new_score}' for {team_name} in {game_name}. Must be a number. Score not updated.")
                                    errors +=1
                                    continue

                                if new_score_val != original_score:
                                    if dm.update_score(game_id, team_id, new_score_val):
                                        changes_made += 1
                                    else:
                                        st.error(f"Failed to update score for {team_name} in {game_name}.")
                                        errors += 1
                        
                        if changes_made > 0:
                            st.success(f"{changes_made} score(s) updated successfully!")
                        if errors == 0 and changes_made == 0:
                            st.info("No changes detected or made.")
                        elif errors > 0 :
                             st.warning(f"Completed with {errors} error(s).")
                        st.rerun()


        with tab2: # Manage Games
            st.markdown("#### Add New Competitive Game")
            with st.form("add_game_form", clear_on_submit=True):
                new_game_name = st.text_input("Game Name", key="new_game_name_input")
                submit_add_game = st.form_submit_button("Add Game")
                if submit_add_game and new_game_name:
                    if dm.add_competitive_game(new_game_name.strip()):
                        st.success(f"Game '{new_game_name.strip()}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to add game '{new_game_name.strip()}'. It might already exist or there was a database error.")
                elif submit_add_game and not new_game_name:
                    st.warning("Please enter a game name.")
            
            st.markdown("---")
            st.markdown("#### Existing Competitive Games")
            current_games = dm.get_competitive_games()
            if not current_games:
                st.info("No competitive games added yet.")
            else:
                games_df = pd.DataFrame(current_games)
                for index, row in games_df.iterrows():
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.write(row['name'])
                    if col2.button("🗑️ Delete", key=f"delete_game_{row['id']}", help=f"Delete game '{row['name']}'. This will also delete all associated scores."):
                        if dm.delete_competitive_game(row['id']):
                            st.success(f"Game '{row['name']}' and its scores deleted.")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete game '{row['name']}'.")
        
        with tab3: # Manage Teams
            st.markdown("#### Add New Team")
            with st.form("add_team_form", clear_on_submit=True):
                new_team_name = st.text_input("Team Name", key="new_team_name_input")
                submit_add_team = st.form_submit_button("Add Team")
                if submit_add_team and new_team_name:
                    if dm.add_team(new_team_name.strip()):
                        st.success(f"Team '{new_team_name.strip()}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to add team '{new_team_name.strip()}'. It might already exist or there was a database error.")
                elif submit_add_team and not new_team_name:
                    st.warning("Please enter a team name.")

            st.markdown("---")
            st.markdown("#### Existing Teams")
            current_teams = dm.get_teams()
            if not current_teams:
                st.info("No teams added yet.")
            else:
                teams_df = pd.DataFrame(current_teams)
                for index, row in teams_df.iterrows():
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.write(row['name'])
                    if col2.button("🗑️ Delete", key=f"delete_team_{row['id']}", help=f"Delete team '{row['name']}'. This will also delete all associated scores."):
                        if dm.delete_team(row['id']):
                            st.success(f"Team '{row['name']}' and its scores deleted.")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete team '{row['name']}'.")

def display_admin_page():
    st.title("🔒 Admin Dashboard")

    if not st.session_state.get('admin_auth_token'):
        with st.form("admin_login_form_page"):
            st.subheader("Admin Login")
            username = st.text_input("Username", key="admin_user_input_page")
            password = st.text_input("Password", type="password", key="admin_pass_input_page")
            login_button = st.form_submit_button("Login")
            if login_button:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    # On success, just set the session state token.
                    # app.py will automatically add it to the URL.
                    st.session_state.admin_auth_token = secrets.token_hex(16)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        # If logged in, show the dashboard and logout button.
        st.sidebar.success("Admin Logged In")
        if st.sidebar.button("Logout Admin", key="admin_logout_page_sidebar"):
            # On logout, we must explicitly clear BOTH session state and the URL param.
            if 'admin_auth_token' in st.session_state:
                del st.session_state.admin_auth_token
            
            # This is the critical addition to prevent the "zombie session" on refresh
            st.query_params.clear() 
            
            st.rerun()
        show_admin_dashboard_page()

# Call the main function for this page
display_admin_page()