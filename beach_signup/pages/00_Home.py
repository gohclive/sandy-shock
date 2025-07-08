import streamlit as st
import os
import sys
import data_manager as dm # Import after path adjustment

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

def display_siloso_beach_directions(): # Content from 03_Event_Details.py
    st.header("📍 How to Get to Siloso Beach") # Main header for this section
    
    # Add the map image and Google Maps link at the top
    st.subheader("📋 Event Location Map & Navigation")
    
    # Display the uploaded image
    # Note: Make sure to save the image file in your streamlit app directory
    # You can save the image as "siloso_beach_map.png" or similar
    try:
        st.image("../images/siloso_beach_map.jpeg", 
                caption="Siloso Beach Location Map - Event venue is marked with the red arrow", 
                use_container_width =True)
    except:
        st.warning("Map image not found.")
    
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
    
    # Additional helpful information
    st.markdown("### 📝 Additional Tips")
    st.info("""
    💡 **Pro Tips:**
    - The event venue is located near the toilet and water cooler facilities (marked in yellow on the map)
    - Look for the red "Event Venue Here" sign when you arrive
    - Beach Station is the main transport hub - all options start from there
    - Free shuttle services run regularly throughout the day
    """)
    
    st.success("Enjoy your day at the beach! ☀️")

def main_landing_page():
    dm.initialize_database() # Initialize DB once when the app starts

    st.title("🏖️ Welcome to T-Day 2025!")
    st.write("Join us for a fantastic day at the beach! Sign up for activities, manage your bookings, and find event details all in one place.")
    st.sidebar.success("Navigate using the links above.")

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
    st.markdown("---")

    # Call the function to display event details
    display_siloso_beach_directions()

main_landing_page()