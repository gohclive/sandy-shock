# Beach Day Activity Signup - Streamlit Web Application

This application allows participants to sign up for various beach day activities. It features unique passphrases for each registration for on-site verification and an admin dashboard for staff to manage activities and check-in participants. The app is now structured as a multi-page application for better organization of user, admin, and informational content.

## Recent Enhancements

The application has been significantly updated with the following improvements:

**Application Structure & UI:**
- **Multi-Page Structure:** Converted to a multi-page application with a main landing page (including event details), and separate pages in the `pages/` directory for the User Portal and Admin Dashboard.
- **Mobile-Friendly Availability Display:** Activity availability on the User Portal now uses expandable cards for each activity, showing timeslot details within, significantly improving mobile usability.

**User Experience & Workflow:**
- **Streamlined Onboarding:** The initial name registration and activity signup are combined into a single, smoother step for new users.
- **"My Registrations" View:** Users can view a list of all activities they are currently signed up for via an expander in the User Portal.
- **Disabled Cancel for Checked-In Users:** Users cannot cancel their booking via "My Bookings" if they are already checked in for the activity, with an explanatory message provided.
- **URL Bookmark Advisory:** The User Portal sidebar includes a tip for bookmarking the page URL to retain session access.
- **Persistent Success Messages:** Signup success messages now persist across page reruns for better user feedback.

**Admin Dashboard:**
- **Interactive Registration Grid & Unchecking:** The admin view for registrations per activity/timeslot uses an interactive data editor. Admins can directly check-in and *uncheck* participants by toggling a checkbox in the grid.
- **Overall Metrics Overview:** The admin dashboard displays key metrics: "Total Registrations," "Participants Checked-In," and "Check-In Rate (%)."
- **Per-Activity Admin Stats:** The admin dashboard now also shows detailed statistics (total registrations, checked-in count, and check-in rate) for each specific activity when selected.

**Code Quality & Setup:**
- **Secure Admin Credentials:** Hardcoded admin credentials have been removed. The application now uses Streamlit Secrets (`st.secrets`).
- **Robust Data Access:** Internal data handling has been refactored to use dictionary-based access.
- **`requirements.txt`:** Added a `requirements.txt` file for easier dependency management.

## Recent Enhancements

The application has been significantly updated with the following improvements:

**User Experience & Workflow:**
- **Streamlined Onboarding:** The initial name registration and activity signup are now combined into a single, smoother step for new users.
- **"My Registrations" View:** Users can now easily view a list of all activities they are currently signed up for via an expander in the user section.

**Admin Dashboard:**
- **Interactive Registration Grid:** The admin view for registrations per activity/timeslot now uses an interactive data editor. Admins can directly check-in participants by toggling a checkbox in the grid.
- **Metrics Overview:** The admin dashboard now displays key metrics at a glance: "Total Registrations," "Participants Checked-In," and "Check-In Rate (%)."

**Code Quality & Security:**
- **Secure Admin Credentials:** Hardcoded admin credentials have been removed. The application now uses Streamlit Secrets (`st.secrets`). See the "Setup for Admin Credentials" section for configuration.
- **Robust Data Access:** Internal data handling has been refactored to use dictionary-based access, making the code more readable and maintainable.

## Features

**Landing Page (`app.py`):**
- Displays a welcome message and general information.
- Provides navigation guidance to other sections of the app.
- Includes integrated "Event Details" with directions to Siloso Beach.

**User Portal (`pages/01_User_Portal.py`):**
- **Activity Viewing & Availability:** Users see a list of available activities. Each activity is an expandable card showing timeslot availability (Full, X Slots Available with color-coding for urgency) in a mobile-friendly format.
- **Sign-Up:** Users provide their Name to register for an activity in an available timeslot.
- **Unique Passphrase:** Upon successful registration, a unique 4-word passphrase is generated.
- **Confirmation:** Persistent on-screen confirmation displays the activity, time, and unique passphrase.
- **"My Bookings" Page:**
    - View details of the current active booking.
    - Option to cancel the booking.
    - **Booking Management:** "Cancel Booking" button is disabled with an explanatory message if the user is already checked-in.
- **"My Registrations" View:** An expander lists all current registrations for the user.
- **Session Persistence Tip:** Advisory in the sidebar on how to bookmark the URL to return to the session.

**Admin Dashboard (`pages/02_Admin_Dashboard.py`):**
- **Secure Access:** Password-protected section for staff, configured via Streamlit Secrets.
- **Overall Event Metrics:** Displays "Total Registrations," "Participants Checked-In," and "Check-In Rate (%)."
- **Activity Management & Per-Activity Statistics:**
    - Admins can select an activity to view its specific statistics (total registrations, checked-in, check-in rate).
    - Drill down to see registrations per timeslot for the selected activity.
- **Participant List & Check-In/Uncheck (Grid View):** For each timeslot, view a list of registered participants. Admins can directly check-in or uncheck participants using an interactive grid.
- **On-Site Verification (Passphrase View):** Staff can verify and check-in participants by searching for their unique registration passphrase.

## Setup for Admin Credentials (Using Streamlit Secrets)

Admin credentials are now managed using Streamlit Secrets for improved security. To configure:

1.  **Create `secrets.toml` file:**
    *   In the root directory of your project (the same directory that contains the `beach_signup` folder), create a new folder named `.streamlit`.
    *   Inside the `.streamlit` folder, create a new file named `secrets.toml`.

2.  **Add credentials to `secrets.toml`:**
    Open `secrets.toml` and add the following content:
    ```toml
    [admin]
    username = "your_admin_username"  # Replace with your desired admin username
    password = "your_admin_password"  # Replace with your desired admin password
    ```
    *(For development, you can use `admin` and `password123` as example values, but choose strong credentials for any real deployment).*

3.  **Add `secrets.toml` to `.gitignore`:**
    Ensure that your secrets file is not committed to your Git repository. Add the following line to your `.gitignore` file (create one in the project root if it doesn't exist):
    ```
    .streamlit/secrets.toml
    ```
The application will automatically pick up these credentials when run.

## Technical Design & Considerations

- **Frontend:** Streamlit
- **Multi-Page Navigation:** Implemented using Streamlit's native multi-page app structure with a main `app.py` and a `pages/` directory.
- **Data Persistence:** SQLite (`beach_day.db` created in the `beach_signup` directory).
- **User Session Identification:** A unique `user_id` (generated UUID fragment like `beach_xxxxxxx`) is stored in `st.session_state` and persisted in the URL via query parameters (`?uid=...`) on the User Portal page.
- **Participant Profile:** When a user first signs up for an activity via the User Portal, their name is captured. If they have no existing profile for their session `user_id`, one is created. This name is then pre-filled for subsequent activity signups within the same session.
- **Per-Registration Passphrases:** Each individual booking gets its own unique 4-word passphrase from `words.txt`.
- **Admin Credentials:** Managed via Streamlit Secrets.
- **UI:** Mobile-first considerations applied to the activity availability display (expandable cards) in the User Portal.
- **Error Handling:** Basic error messages are provided for common issues.
- **Data Access:** Functions in `data_manager.py` return dictionaries, and application pages use dictionary key-based access.

## Project Structure

```
.streamlit/
└── secrets.toml       # For admin credentials (user-created, add to .gitignore)
beach_signup/
├── app.py                 # Main Streamlit application (Landing Page & Event Details)
├── pages/                 # Directory for additional app pages
│   ├── 01_User_Portal.py
│   └── 02_Admin_Dashboard.py
├── data_manager.py        # SQLite database interactions
├── utils.py               # Helper functions
├── words.txt              # Word list for passphrases
├── beach_day.db           # SQLite database file (created on first run)
└── README.md              # This file
requirements.txt           # Project dependencies (at project root)
.gitignore                 # Should contain .streamlit/secrets.toml and .venv/ (if applicable)
```

## Setup and Installation

1.  **Clone the repository (if applicable) or ensure you have the project files.**
2.  **Install dependencies:**
    Make sure you have Python 3.7+ installed. Then, navigate to the project root directory (the one containing `requirements.txt`) and run:
    ```bash
    pip install -r requirements.txt
    ```
    *(Pandas is used for the admin data grid and activity availability display).*
    
3.  **Configure Admin Credentials:** Follow the steps in the "Setup for Admin Credentials (Using Streamlit Secrets)" section.

## How to Run the Application

1.  Navigate to the root directory of the project (the one containing the `beach_signup` folder).
2.  Run the Streamlit application using the following command:
    ```bash
    streamlit run beach_signup/app.py
    ```
3.  The application should open in your web browser automatically. It will launch as a multi-page app with navigation available in the sidebar.

## Current Implementation Status

The application is largely feature-complete based on the described enhancements. Key areas include:
- **Core Functionality:** User registration, booking, cancellation (with check-in restrictions), admin dashboard for metrics, user lookup, and check-in/uncheck capabilities are implemented.
- **Structure:** Multi-page app structure is in place.
- **UI Enhancements:** Mobile-friendly availability display and persistent success messages are implemented.
- **Security:** Admin credentials use Streamlit Secrets.
- **Data Handling:** Database interactions are established, and data access patterns have been refactored.
- **Documentation:** `README.md` and `requirements.txt` are up-to-date.
