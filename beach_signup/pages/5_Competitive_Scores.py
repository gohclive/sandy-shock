import streamlit as st
import pandas as pd
import os
import sys

# Path adjustment for imports
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_or_beach_signup_dir = os.path.dirname(current_file_dir)
if project_root_or_beach_signup_dir not in sys.path:
    sys.path.append(project_root_or_beach_signup_dir)

import data_manager as dm
from session_manager import sync_session_state_with_url, initialize_user_if_needed

# --- THIS IS THE MOST IMPORTANT STEP ---
# Call the sync function AT THE VERY TOP of the script.
sync_session_state_with_url()
initialize_user_if_needed()
# -----------------------------------------

def show_competitive_scores_page():
    st.set_page_config(layout="wide")
    st.title("🏆 Competitive Games Scoreboard 🏆")
    st.markdown("---")

    score_data, game_names, team_names = dm.get_all_scores()
    team_total_scores = dm.get_team_total_scores()

    if not team_names or not game_names:
        st.info("No teams or games found. Scores will be displayed once games and teams are added by an admin.")
        return

    st.subheader("🚀 Overall Team Standings")
    if team_total_scores:
        # Create a DataFrame for total scores
        total_scores_df = pd.DataFrame(team_total_scores)
        total_scores_df.index = total_scores_df.index + 1 # Rank starting from 1
        total_scores_df.rename(columns={'team_name': 'Team', 'total_score': 'Total Score'}, inplace=True)
        
        # Display with medals for top 3
        def highlight_top_three(row):
            if row.name == 1: # Rank 1
                return ['background-color: gold; color: black'] * len(row)
            elif row.name == 2: # Rank 2
                return ['background-color: silver; color: black'] * len(row)
            elif row.name == 3: # Rank 3
                return ['background-color: #CD7F32; color: white'] * len(row) # Bronze
            return [''] * len(row)

        st.dataframe(
            total_scores_df.style.apply(highlight_top_three, axis=1),
            use_container_width=True,
            hide_index=False,
            column_config={
                "Team": st.column_config.TextColumn(label="Team"),
                "Total Score": st.column_config.NumberColumn(label="Total Score", format="%d"),
            }
        )
    else:
        st.info("No scores recorded yet to display overall standings.")
    
    st.markdown("---")
    st.subheader("📊 Detailed Scores per Game")

    if not score_data:
        st.info("No scores recorded yet.")
        return

    # Prepare data for the main scoreboard DataFrame
    # Rows: Teams, Columns: Games, Values: Scores
    df_data = []
    for team_name in team_names:
        row = {'Team': team_name}
        for game_name in game_names:
            row[game_name] = score_data.get(team_name, {}).get(game_name, 0)
        df_data.append(row)

    scores_df = pd.DataFrame(df_data)
    scores_df = scores_df.set_index('Team')

    # Calculate total scores for each team and add as a new column
    scores_df['Total Score'] = scores_df.sum(axis=1)
    
    # Sort by Total Score descending
    scores_df = scores_df.sort_values(by='Total Score', ascending=False)

    # Display the DataFrame
    st.dataframe(scores_df.style.format("{:.0f}"), use_container_width=True)

    st.markdown("---")
    st.caption("Scores are updated live as admins input them.")

# Entry point for the page
if __name__ == "__main__":
    # Initialize database if it hasn't been (e.g., when running this page directly after pulling changes)
    # This is more for robustness during development/first run.
    # In a deployed app, initialization typically happens at app startup.
    try:
        dm.initialize_database() 
    except Exception as e:
        print(f"Could not initialize database (might be already initialized or connection issue): {e}")
    
    show_competitive_scores_page()
