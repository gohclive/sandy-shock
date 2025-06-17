# Beach Day Activity Signup - Streamlit Web Application

This application allows participants to sign up for various beach day activities. It features unique passphrases for each registration for on-site verification and an admin dashboard for staff to manage activities and check-in participants.

## Features

**Participant Flow:**
- **Activity Viewing:** See a list of available activities and their timeslots.
- **Availability:** Timeslots display the number of available slots remaining or "Full".
- **Sign-Up:** Users provide their Name and Email to register for an activity in an available timeslot.
- **Unique Passphrase:** Upon successful registration, a unique 4-word passphrase is generated for that specific booking. This acts as a "ticket" for check-in.
- **Confirmation:** On-screen confirmation displays the activity, time, and the unique passphrase. Email confirmation is currently mocked.

**Admin Dashboard (Planned & Partially Implemented):**
- **Secure Access:** Intended to be a password-protected section for staff. (Hardcoded credentials for current version).
- **Activity Management:** View all activities and drill down to see registrations per timeslot.
- **Participant List:** For each timeslot, view a list of registered participants including their name, email, unique registration passphrase, and check-in status.
- **On-Site Verification:**
    - **Primary:** Staff can verify and check-in participants by searching for their unique registration passphrase.
    - **Fallback:** Staff can manually find and check-in participants by name within the activity/timeslot view.
- **Check-In:** Marking a participant as "Checked-In" prevents reuse of the same registration passphrase for check-in.

## Technical Design & Considerations

- **Frontend:** Streamlit
- **Data Persistence:** SQLite (`beach_day.db` created in the `beach_signup` directory).
- **User Session Identification:** A unique `user_id` (generated UUID fragment like `beach_xxxxxxx`) is stored in `st.session_state` and persisted in the URL via query parameters (`?uid=...`). This `user_id` links multiple registrations made during the same browser session by an individual.
- **Participant Profile:** When a user first provides their name for a registration within a session, a basic participant profile (session `user_id`, `name`) is created. This name is then pre-filled for subsequent registrations within the same session.
- **Per-Registration Passphrases:** Each individual booking (a specific user for a specific activity at a specific time) gets its own unique 4-word passphrase from `words.txt`. This is a key change from a per-participant passphrase system.
- **Admin Credentials:** Currently planned to be hardcoded constants in `app.py` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- **Email Confirmation:** Functionality is mocked. In a production environment, this would integrate with an email sending service (e.g., SendGrid, AWS SES, or an SMTP server).
- **Error Handling:** Basic error messages are provided for common issues like invalid input, full slots, or duplicate bookings for the same timeslot by the same user.

## Project Structure

```
beach_signup/
├── app.py                 # Main Streamlit application
├── data_manager.py        # SQLite database interactions
├── utils.py               # Helper functions (validation, formatting)
├── words.txt              # Word list for passphrases
├── beach_day.db           # SQLite database file (created on first run)
└── README.md              # This file
```

## Setup and Installation

1.  **Clone the repository (if applicable) or ensure you have the project files.**
2.  **Install dependencies:**
    Make sure you have Python 3.7+ installed. Then, install the required packages:
    ```bash
    pip install streamlit pandas
    ```
    *(Pandas is used for displaying the availability grid).*

## How to Run the Application

1.  Navigate to the root directory of the project (the one containing the `beach_signup` folder).
2.  Run the Streamlit application using the following command:
    ```bash
    streamlit run beach_signup/app.py
    ```
3.  The application should open in your web browser automatically.

## Current Implementation Status

- **Data Layer (`data_manager.py`):** Fully implemented with the new schema (participants, registrations), per-registration passphrases, and all necessary data access functions.
- **Utility Functions (`utils.py`):** Includes helpers for name validation, email validation, and passphrase formatting.
- **Participant Signup Flow (`show_signup_page` in `app.py`):** Fully implemented. Collects Name/Email, uses new data manager functions, and displays per-registration passphrases.
- **Admin Dashboard & Login (`app.py`):**
    - Admin login/logout mechanism is implemented (using hardcoded credentials).
    - **Activity/Timeslot View:** Implemented. Admins can view registrations by activity/timeslot and check-in participants.
    - **Passphrase Verification View:** Implemented. Admins can search for a registration by its unique passphrase and check-in the participant.
- **User Session Management:** Implemented using URL parameters (`?uid=...`) and `st.session_state`.
