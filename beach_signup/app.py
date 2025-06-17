import streamlit as st
import os
import sys

# Add the directory containing this script (beach_signup) to Python's path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

import data_manager as dm # Import after path adjustment

def main_landing_page():
    st.set_page_config(page_title="Beach Day Signup", page_icon="🏖️", layout="wide")

    dm.initialize_database() # Initialize DB once when the app starts

    st.title("🏖️ Welcome to Beach Day Signup!")
    st.write("Join us for a fantastic day at the beach! Sign up for activities, manage your bookings, and find event details all in one place.")
    st.sidebar.success("Navigate using the links above.") # Streamlit auto-populates sidebar from 'pages'

    # Placeholder for an image, if desired
    # try:
    #     st.image("https.example.com/beach_image.jpg", caption="Enjoy the sunny beach!") # Replace with a real image URL
    # except Exception:
    #     st.caption("Sunny beach image placeholder")

    st.markdown("---")
    st.header("Explore")
    # Using direct string without markdown list markers for the subtask
    # For actual markdown rendering with bullets, ensure each starts with '-' or '*' on a new line.
    # The current string will render as a single paragraph.
    # For bullet points, it should be:
    # st.markdown(
    #     "- **User Portal:** Sign up for new activities or view your existing bookings.\n"
    #     "- **Admin Dashboard:** For event organizers to manage registrations and check-ins.\n"
    #     "- **Event Details:** Find useful information about the event, including directions.\n\n"
    #     "Select an option from the sidebar to get started!"
    # )
    # Correcting for desired bullet point rendering:
    st.markdown(
        """
        - **User Portal:** Sign up for new activities or view your existing bookings.
        - **Admin Dashboard:** For event organizers to manage registrations and check-ins.
        - **Event Details:** Find useful information about the event, including directions.

        Select an option from the sidebar to get started!
        """
    )

main_landing_page()
