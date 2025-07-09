import streamlit as st
import uuid
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

# Call this at the top of your main script
display_minimal_session_header()

def display_site_map():
    """Display the site map section"""
    st.subheader("🗺️ Event Site Map")
    
    # Placeholder for the site map image
    try:
        st.image("images/site_map.jpg", 
                caption="Event Site Map - Shows layout of activities, food stations, and facilities", 
                use_container_width=True)
    except:
        # Placeholder when image is not found
        st.info("""
        📍 **Site Map Coming Soon**
        
        The event site map will be available here showing:
        - Activity station locations
        - Food booth locations
        - Facilities (toilets, water coolers, etc.)
        - Registration/check-in points
        - Emergency exits and first aid stations
        
        *Please save your site map image as "images/site_map.jpg" to display it here.*
        """)
    
    st.success("Enjoy your day at the beach! ☀️")

def display_siloso_beach_directions(): # Content from 03_Event_Details.py
    st.header("📍 How to Get to Siloso Beach") # Main header for this section
    
    # Add the map image and Google Maps link at the top
    st.subheader("📋 Event Location Map & Navigation")
    
    # Display the uploaded image
    # Note: Make sure to save the image file in your streamlit app directory
    # You can save the image as "siloso_beach_map.png" or similar
    try:
        st.image("images/siloso_beach_map.jpeg", 
                caption="Siloso Beach Location Map - Event venue is marked with the red arrow", 
                use_container_width =True)
    except:
        st.warning("Map image not found.")


    # Additional helpful information
    st.markdown("### 📝 Additional Tips")
    st.info("""
    💡 **Pro Tips:**
    - The event venue is located near the toilet and water cooler facilities (marked in yellow on the map)
    - Look for the red "Event Venue Here" sign when you arrive
    - Beach Station is the main transport hub - all options start from there
    - Free shuttle services run regularly throughout the day
    """)
    
    # Add Google Maps link
    st.markdown("### 🗺️ Google Maps Navigation")
    st.markdown(
        """
        **Click here to open directions in Google Maps:**
        
        🔗 [**Open Siloso Beach in Google Maps**](https://maps.app.goo.gl/BpJFQHcd9YCYxE2a6)
        
        """
    )
    st.markdown("---")
    
    st.subheader("From Beach Station (Sentosa Express):")
    st.markdown("---")
    st.markdown("### Option 1 - Beach Shuttle (Fastest)")
    st.markdown(
    '''
    - Board the Beach Shuttle at Beach Station
    - Take the Green Line heading towards Siloso Beach
    - **Journey time:** 2 minutes
    - **Cost:** FREE
    '''
    )
    st.markdown("---")
    st.markdown("### Option 2 - Bus A")
    st.markdown(
    '''
    - Board Bus A at Beach Station
    - Take 2 stops to Siloso Point
    - **Journey time:** 3-5 minutes
    - **Cost:** FREE
    '''
    )
    st.markdown("---")
    st.markdown("### Option 3 - Walking")
    st.markdown(
    '''
    - Walk from Beach Station to Siloso Beach
    - **Journey time:** 10 minutes
    - Follow signs to Siloso Beach
    '''
    )

    st.markdown("---")

def main_landing_page():
    st.title("🏖️ Welcome to T-Day 2025!")
    st.write("Join us for a fantastic day at the beach! Sign up for activities, manage your bookings, and find event details all in one place.")
    st.sidebar.success("Navigate using the links above.")

    # Ensure user_id is initialized for session persistence tracking
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"beach_{str(uuid.uuid4())[:8]}"
        st.rerun() # Rerun to allow app.py to pick up the new user_id and add to URL

    st.markdown("---")
    st.header("Explore Our App")
    # Updated markdown to reflect event details are now on this page
    st.markdown(
        """
        Use the sidebar to navigate to the:
        - **User Portal:** For signing up for new activities or viewing your existing bookings.
        - **Admin Dashboard:** For event organizers to manage registrations and check-ins.

        Scroll down further on this page for event location details.
        """
    )

    # Call the function to display event details
    display_siloso_beach_directions()
    display_site_map()

main_landing_page()