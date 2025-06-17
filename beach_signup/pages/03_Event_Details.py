import streamlit as st

def show_event_details():
    # st.set_page_config(page_title="Event Details - Beach Day", page_icon="🏖️", layout="wide") # Config should be in main app.py
    st.title("🎉 Event Details")

    st.header("📍 How to Get to Siloso Beach")

    st.subheader("From Beach Station (Sentosa Express):")

    st.markdown("---")

    st.markdown("### Option 1 - Beach Shuttle (Fastest)")
    st.markdown('''
    - Board the Beach Shuttle at Beach Station
    - Take the Green Line heading towards Siloso Beach
    - **Journey time:** 2 minutes
    - **Cost:** FREE
    ''')

    st.markdown("---")

    st.markdown("### Option 2 - Bus A")
    st.markdown('''
    - Board Bus A at Beach Station
    - Take 2 stops to Siloso Point
    - **Journey time:** 3-5 minutes
    - **Cost:** FREE
    ''')

    st.markdown("---")

    st.markdown("### Option 3 - Walking")
    st.markdown('''
    - Walk from Beach Station to Siloso Beach
    - **Journey time:** 10 minutes
    - Follow signs to Siloso Beach
    ''')

    st.markdown("---")
    st.info("Enjoy your day at the beach! ☀️")

# Call the function to render the page when Streamlit navigates to it
show_event_details()
