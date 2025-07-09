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

def display_sentosa_qr_page():
    st.title("🎫 Sentosa Entry QR Code")

    # Placeholder QR code URL
    qr_code_url = "images/qr-code.png"
    st.image(qr_code_url, width=250)

    st.subheader("Important Information")
    st.markdown("""
    ## Sentosa Access QR Code
        
    This QR code provides **access to Sentosa Express and Vehicular Gantry** for CSIT personnel only.

    **⚠️ IMPORTANT SECURITY NOTICE:**
    - This access code is **strictly confidential** and intended solely for our organization's use
    - **Do not share, forward, or screenshot** this QR code
    """)


# Call the main function for this page
if __name__ == "__main__":
    # This part is optional for Streamlit pages but good practice
    # st.set_page_config(page_title="Sentosa QR", layout="centered") # Handled by Streamlit's multipage app structure
    display_sentosa_qr_page()
