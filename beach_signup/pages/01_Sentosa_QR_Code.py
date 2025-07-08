import streamlit as st

def display_sentosa_qr_page():
    st.title("🎫 Sentosa Entry QR Code")

    # Placeholder QR code URL
    qr_code_url = "beach_signup/images/qr-code.png"
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
