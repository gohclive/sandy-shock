import streamlit as st
import uuid
from session_manager import sync_session_state_with_url

# --- THIS IS THE MOST IMPORTANT STEP ---
# Call the sync function AT THE VERY TOP of the script.
sync_session_state_with_url()
# -----------------------------------------

def initialize_user_session():
    if 'user_id' not in st.session_state:
        query_params = st.query_params
        uid_from_url = query_params.get("uid")
        if uid_from_url:
            st.session_state.user_id = uid_from_url[0] if isinstance(uid_from_url, list) else uid_from_url
        else:
            new_user_id = f"{str(uuid.uuid4())[:12]}"
            st.session_state.user_id = new_user_id
            st.query_params["uid"] = new_user_id

def display_minimal_session_header():
    """Display session header with clear warnings"""
    user_id = st.session_state.get('user_id')
    
    if user_id:
        # Construct URL
        base_url = st.get_option('browser.serverAddress') or 'localhost'
        port = st.get_option('server.port') or 8501
        
        if base_url == 'localhost':
            full_url = f"http://localhost:{port}?uid={user_id}"
        else:
            protocol = "https" if port == 443 else "http"
            full_url = f"{protocol}://{base_url}:{port}?uid={user_id}"
        
        # Display warning and session info
        st.warning("⚠️ **Don't close this tab or refresh!** You'll lose your session.")
        st.success(f"🔗 **Session Active** | Bookmark: [{full_url}]({full_url})")
        st.divider()

# Call this at the top of your main script
initialize_user_session()
display_minimal_session_header()


# Define your pages
pages = [
    st.Page("pages/00_Home.py", title="Home"),
    st.Page("pages/01_Sentosa_QR_Code.py", title="Sentosa QR Code"),
    st.Page("pages/02_User_Portal.py", title="User Portal"),
    st.Page("pages/03_Admin_Dashboard.py", title="Admin Dashboard"),
]

nav = st.navigation(pages)
nav.run()