import streamlit as st

from session_manager import sync_session_state_with_url, initialize_user_if_needed

# --- THIS IS THE MOST IMPORTANT STEP ---
# Call the sync function AT THE VERY TOP of the script.
sync_session_state_with_url()
initialize_user_if_needed()
# -----------------------------------------

def display_minimal_session_header():
    """Display session header with clear warnings"""
    user_id = st.session_state.get('user_id')
    
    if user_id:
        # Construct URL
        base_url = st.get_option('browser.serverAddress') or 'localhost'
        full_url = f"https://tday2025.app.tc1.airbase.sg/?uid={user_id}"
        
        # Display warning and session info
        st.warning("⚠️ **Don't close this tab** You'll lose your session.")
        st.success(f"🔗 **Session Active** | Bookmark: [{full_url}]({full_url})")
        st.divider()

display_minimal_session_header()

def display_event_schedule():
    """Display the event schedule based on the provided document"""
    st.header("📅 Event Schedule - CSIT Tech Day 2025")
    
    # Event overview
    st.subheader("Event Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.info("📅 **Date:** Thursday, 10 July 2025")
    with col2:
        st.info("⏰ **Time:** 2:00 PM - 5:00 PM")
    
    st.markdown("---")
    
    # Main event schedule
    st.subheader("📋 Event Schedule")
    
    # 2:00 PM - Arrival and Introduction
    with st.expander("2:00 PM - Arrival & Introduction", expanded=True):
        st.markdown("""
        **Arrival of Guests**
        - Emcee Introduction (Talk about the activities)
        
        **Available Activities:**
        """)
        
        # Create tabs for different activity types
        fringe_tab, competitive_tab, food_tab = st.tabs(["🎨 Fringe Activities", "🏆 Competitive Activities", "🍴 Food Booths"])
        
        with fringe_tab:
            st.markdown("""
            - 💆‍♀️ SAVH Mobile Massage Team
            - 🎨 Canvas Painting
            - 🎨 Tote Bag Painting
            - 🔑 Shrink Art Keychain
            """)
        
        with competitive_tab:
            st.markdown("""
            - 🏃‍♂️ Amazing Sentosa Dash
            - 🏃‍♀️ Inflatable Obstacle Course
            - 🛶 Raft Building
            - 🏰 Sandcastle Building
            - 🎯 Tele-Matches
            - ⚽ Captain Ball
            """)
        
        with food_tab:
            st.markdown("""
            - 🌭 Hotdog Bun
            - �Swertificate
            - 🧀 Nachos Chips
            - 🍗 Chicken Nuggets
            """)
    
    # 2:15 PM - Opening Remarks
    with st.expander("2:15 PM - Opening Remarks"):
        st.markdown("""
        **Opening Remarks by Mr Darren Teo, Chief Executive, CSIT**
        """)
    
    # 2:15 PM - 2:30 PM - Fringe Activities
    with st.expander("2:15 PM - 2:30 PM - Fringe Activities & Food Stations"):
        st.markdown("""
        **Commencement of Fringe Activities & Food Stations**
        - Teams will be directed to their respective stations
        - Emcee will guide participants
        """)
    
    # 2:30 PM - Competitive Activities
    with st.expander("2:30 PM - Competitive Activities Begin"):
        st.markdown("""
        **Commencement of Competitive Activities**
        - All competitive activities begin
        - Participants can enjoy free time between activities
        """)
    
    # 2:30 PM - 4:30 PM - Free Time
    with st.expander("2:30 PM - 4:30 PM - Free Time"):
        st.markdown("""
        **Free & Easy Time**
        - Once activities are completed, participants can enjoy:
        - Food and drinks
        - Relaxation time
        - Socializing
        """)
    
    # 4:30 PM - 5:00 PM - Prize Presentation
    with st.expander("4:30 PM - 5:00 PM - Prize Presentation & Closing"):
        st.markdown("""
        **Prize Presentation by Mr Darren Teo, Chief Executive, CSIT**
        
        **Awards:**
        - 1st place winners of all Competitive Activities
        - Activities with prizes:
          - Amazing Sentosa Dash
          - Sandcastle Building
          - Tele-Matches
          - Inflatable Obstacle Course
          - Captain's Ball
          - Raft Building
        
        **Special Recognition:**
        - Overall Champion Department - Plaque presentation
        - Mass Group Photo
        """)
    
    # 5:00 PM - End of vent
    with st.expander("5:00 PM - End of Event"):
        st.markdown("""
        **Event Conclusion**
        - Thank you message
        - Safe journey home
        """)
    
    st.markdown("---")
    st.success("See you at the event! 🎉")


# Call the main function for this page
if __name__ == "__main__":
    # This part is optional for Streamlit pages but good practice
    # st.set_page_config(page_title="Sentosa QR", layout="centered") # Handled by Streamlit's multipage app structure
    display_event_schedule()