import streamlit as st
import os
import sys

# Add the directory containing this script (beach_signup) to Python's path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

import data_manager as dm # Import after path adjustment

# Define only the pages you want to show
pages = [
    st.Page("pages/00_Home.py", title="Home"),  # Reference to your main app.py file
    st.Page("pages/01_Sentosa_QR_Code.py", title="Sentosa QR Code"),
    st.Page("pages/02_User_Portal.py", title="User Portal"),
    st.Page("pages/03_Admin_Dashboard.py", title="Admin Dashboard"),
    # test_db.py is not included, so it's hidden but accessible via st.switch_page()
]

nav = st.navigation(pages)
nav.run()



