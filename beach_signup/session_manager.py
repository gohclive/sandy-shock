# session_manager.py
import streamlit as st

def sync_session_state_with_url():
    """
    Ensures that session state and URL query parameters are in sync.
    
    This function should be called at the beginning of every page script
    to provide a persistent cross-page session via the URL.
    
    It reads from the URL to update session_state first, and then writes
    from session_state back to the URL. This ensures that the session_state
    is the ultimate source of truth.
    """
    # Define the mapping between session state keys and URL parameter keys
    keys_to_sync = {
        "user_id": "uid",
        "admin_auth_token": "admin_token"
    }

    # --- Part 1: Update Session State from URL ---
    # This runs first to allow loading state from a shared URL.
    for state_key, url_key in keys_to_sync.items():
        url_value = st.query_params.get(url_key)
        if url_value is not None:
            # If the value in the URL is different from session_state, update session_state
            if st.session_state.get(state_key) != url_value:
                st.session_state[state_key] = url_value

    # --- Part 2: Update URL from Session State ---
    # This runs second to ensure the URL always reflects the authoritative session_state.
    # This is the part that "fixes" the URL after a navigation event.
    for state_key, url_key in keys_to_sync.items():
        state_value = st.session_state.get(state_key)
        
        # If the state has a value, make sure the URL reflects it
        if state_value is not None:
            if str(st.query_params.get(url_key)) != str(state_value):
                st.query_params[url_key] = state_value
        # If the state value is None, remove it from the URL
        elif url_key in st.query_params:
            del st.query_params[url_key]