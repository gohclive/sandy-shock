# Beach Signup App

This is a simple Flask web application for users to sign up for beach notifications.

## Project Structure

- `app.py`: Main Flask application file. Contains routes for index, signup, and verification.
- `data_manager.py`: Handles data storage for signups (using a JSON file).
- `utils.py`: Utility functions, including random word generation and email validation.
- `words.txt`: A list of words used for the verification step.
- `templates/`: HTML templates for the web pages.
  - `index.html`: The main signup page.
  - `verify.html`: Page for users to enter the verification word.
  - `success.html`: Confirmation page after successful signup.
- `data/`: Directory to store the `signups.json` file (created automatically).

## Setup and Running

1.  **Prerequisites:**
    *   Python 3.x
    *   Flask (`pip install Flask`)

2.  **Clone the repository (or download the files).**

3.  **Navigate to the `beach_signup` directory.**

4.  **Run the application:**
    ```bash
    python app.py
    ```

5.  Open your web browser and go to `http://127.0.0.1:5000/`.

## How it Works

1.  Users enter their email on the main page.
2.  The app validates the email format and checks if it's already signed up.
3.  If the email is new and valid, a random "verification word" is chosen from `words.txt`.
    *   **Note:** In a real-world application, this word would be sent to the user's email address. For this demo, it's printed to the console where the Flask app is running.
4.  The user is redirected to a verification page and must enter the correct word.
5.  If the word matches, their email is saved to `data/signups.json`.
6.  A success message is displayed.

## Error Handling

-   Invalid email format.
-   Email already signed up.
-   Incorrect verification word.

## Data Storage

-   Signups are stored in `data/signups.json`. Each entry is an object with an "email" key.
-   The `data` directory and `signups.json` file are created automatically if they don't exist when the app starts.

## Verification Words

-   The list of possible verification words is in `words.txt`. You can modify this file to change the words.
-   If `words.txt` is missing or empty, "defaultword" will be used as the verification word.
