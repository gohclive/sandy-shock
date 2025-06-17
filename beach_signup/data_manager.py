import sqlite3
import os
import random
from datetime import datetime

DB_FILE = "beach_day.db"

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), DB_FILE)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_word_list():
    word_file_path = os.path.join(os.path.dirname(__file__), 'words.txt')
    try:
        with open(word_file_path, 'r') as f:
            words = [word.strip().lower() for word in f.readlines() if word.strip() and len(word.strip()) >= 3]
            if not words: raise FileNotFoundError
            return words
    except FileNotFoundError:
        print(f"Warning: {word_file_path} not found or empty. Using fallback word list.")
        return ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india', 'juliet', 'kilo', 'lima']

def generate_registration_passphrase(conn):
    words = load_word_list()
    cursor = conn.cursor()
    if len(words) < 4:
        idx = 1
        while True:
            passphrase = f"reg-code-{idx}"
            cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (passphrase,))
            if cursor.fetchone() is None: return passphrase
            idx += 1
    attempts = 0
    max_attempts = 300
    while attempts < max_attempts:
        passphrase = '-'.join(random.sample(words, 4))
        cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (passphrase,))
        if cursor.fetchone() is None: return passphrase
        attempts += 1
    base_passphrase = '-'.join(random.sample(words,4)) if words else "fallback-pass"
    suffix = 1
    while True:
        new_passphrase = f"{base_passphrase}-{suffix}"
        cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (new_passphrase,))
        if cursor.fetchone() is None: return new_passphrase
        suffix += 1

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_time TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            participant_name TEXT NOT NULL,
            activity TEXT NOT NULL,
            timeslot TEXT NOT NULL,
            registration_passphrase TEXT NOT NULL UNIQUE,
            registration_time TEXT NOT NULL,
            checked_in INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES participants (id),
            UNIQUE (user_id, activity, timeslot) -- Prevents user from booking same activity/slot again if they somehow bypass UI
                                                -- Note: The overall "1 activity per user" limit is handled in add_registration logic
        )
    ''')
    conn.commit()
    conn.close()

def create_participant(user_id, name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM participants WHERE id = ?", (user_id,))
        if cursor.fetchone():
            # print(f"Participant {user_id} already exists.") # Less verbose
            return True
        created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute( "INSERT INTO participants (id, name, created_time) VALUES (?, ?, ?)", (user_id, name, created_time) )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in create_participant: {e}")
        return False
    finally: conn.close()

def find_participant_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE id = ?", (user_id,))
    participant = cursor.fetchone()
    conn.close()
    return dict(participant) if participant else None

def get_user_registrations(user_id): # Crucial for the 1-activity limit and "My Bookings"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ? ORDER BY registration_time DESC", (user_id,))
    registrations = cursor.fetchall()
    conn.close()
    return [dict(reg) for reg in registrations]

# add_registration now implements the "1 activity per user" limit
def add_registration(user_id, name, activity, timeslot):
    conn = get_db_connection()
    try:
        # Check for "1 activity per user" limit FIRST
        # This check uses a separate connection via get_user_registrations.
        # For high-concurrency, this could be a point of optimization or require transaction management if done within the same conn.
        existing_registrations = get_user_registrations(user_id)
        if existing_registrations: # If list is not empty, user already has a booking
            print(f"User {user_id} already has an existing registration. Cannot add another.")
            return None, None, "LIMIT_REACHED"

        # Proceed with generating passphrase and inserting if limit not reached
        passphrase = generate_registration_passphrase(conn) # Uses current connection
        reg_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.cursor() # Use the connection already opened for this function
        cursor.execute(
            "INSERT INTO registrations (user_id, participant_name, activity, timeslot, registration_passphrase, registration_time) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, activity, timeslot, passphrase, reg_time)
        )
        registration_id = cursor.lastrowid
        conn.commit()
        return registration_id, passphrase, "SUCCESS"
    except sqlite3.IntegrityError as e:
        # This could still happen if, by an extreme coincidence, two requests for the SAME user_id (who has no bookings)
        # pass the initial check and then one inserts before the other.
        # The UNIQUE (user_id, activity, timeslot) constraint would catch this.
        # Or if somehow the generate_registration_passphrase was not unique (should not happen).
        print(f"Integrity error in add_registration for user {user_id} (likely duplicate activity/slot attempt, or rare passphrase collision): {e}")
        return None, None, "ALREADY_BOOKED_TIMESLOT" # Re-using this status, though context is slightly different
    except sqlite3.Error as e:
        print(f"Database error in add_registration for user {user_id}: {e}")
        return None, None, "DB_ERROR"
    finally: conn.close()

def get_signup_count(activity, timeslot):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE activity = ? AND timeslot = ?", (activity, timeslot))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def cancel_registration(registration_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in cancel_registration: {e}")
        return False
    finally: conn.close()

def get_registration_by_passphrase(passphrase):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE registration_passphrase = ?", (passphrase,))
    registration = cursor.fetchone()
    conn.close()
    return dict(registration) if registration else None

def check_in_registration(registration_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT checked_in FROM registrations WHERE id = ?", (registration_id,))
        result = cursor.fetchone() # result is a Row object here
        if result is None:
            return False
        # Access by key for consistency, though result[0] would also work for Row object
        if result['checked_in'] == 1:
            return False
        cursor.execute("UPDATE registrations SET checked_in = 1 WHERE id = ?", (registration_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in check_in_registration: {e}")
        return False
    finally: conn.close()

def get_registrations_for_timeslot(activity, timeslot):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE activity = ? AND timeslot = ? ORDER BY registration_time", (activity, timeslot))
    registrations = cursor.fetchall()
    conn.close()
    return [dict(reg) for reg in registrations]

def get_registrations_for_participant(participant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ?", (participant_id,))
    registrations = cursor.fetchall()
    conn.close()
    return [dict(reg) for reg in registrations]

def get_total_registration_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_checked_in_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE checked_in = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_activities():
    return ["Beach Volleyball", "Surfing Lessons", "Sandcastle Building", "Beach Photography", "Sunset Yoga"]

def get_timeslots():
    timeslots = []
    hour = 14; minute = 30
    while not (hour == 17 and minute == 0):
        timeslots.append(f"{hour:02d}:{minute:02d}")
        minute += 15
        if minute >= 60: minute = 0; hour += 1
        if hour >= 17: break
    return timeslots
