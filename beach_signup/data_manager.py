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
        print("Error: Word list too small. Using numbered fallback passphrases.")
        # Fallback for critically small word list
        idx = 1
        while True:
            passphrase = f"reg-code-{idx}" # Simple but unique
            cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (passphrase,))
            if cursor.fetchone() is None:
                return passphrase
            idx += 1

    # Main logic
    attempts = 0
    max_attempts = 300 # Increased attempts for very busy systems
    while attempts < max_attempts:
        passphrase = '-'.join(random.sample(words, 4))
        cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (passphrase,))
        if cursor.fetchone() is None:
            return passphrase
        attempts += 1

    # Absolute fallback if many collisions (should be extremely rare)
    print(f"Warning: High collision rate after {max_attempts} attempts. Using suffixed passphrase.")
    base_passphrase = '-'.join(random.sample(words,4)) if words else "fallback-pass" # Ensure words exist
    suffix = 1
    while True:
        new_passphrase = f"{base_passphrase}-{suffix}"
        cursor.execute("SELECT 1 FROM registrations WHERE registration_passphrase = ?", (new_passphrase,))
        if cursor.fetchone() is None:
            return new_passphrase
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
            participant_email TEXT NOT NULL,
            activity TEXT NOT NULL,
            timeslot TEXT NOT NULL,
            registration_passphrase TEXT NOT NULL UNIQUE,
            registration_time TEXT NOT NULL,
            checked_in INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES participants (id),
            UNIQUE (user_id, activity, timeslot)
        )
    ''')
    conn.commit()
    conn.close()

def create_participant(user_id, name):
    """Creates a new participant record if one doesn't exist for this user_id."""
    conn = get_db_connection()
    try:
        # Check if participant already exists to avoid error on primary key conflict
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM participants WHERE id = ?", (user_id,))
        if cursor.fetchone():
            # Participant already exists, perhaps update name or just return
            # For now, let's assume name doesn't change once set or this is handled in app logic
            print(f"Participant {user_id} already exists.")
            return True # Or some indicator that it's fine

        created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO participants (id, name, created_time) VALUES (?, ?, ?)",
            (user_id, name, created_time)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in create_participant: {e}")
        return False
    finally:
        conn.close()

def find_participant_by_id(user_id):
    """Finds a participant by their user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE id = ?", (user_id,))
    participant = cursor.fetchone()
    conn.close()
    return participant

def add_registration(user_id, name, email, activity, timeslot):
    """Adds a new registration and returns (registration_id, passphrase) or (None, None)."""
    conn = get_db_connection()
    try:
        passphrase = generate_registration_passphrase(conn)
        reg_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO registrations (user_id, participant_name, participant_email, activity, timeslot, registration_passphrase, registration_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, email, activity, timeslot, passphrase, reg_time)
        )
        registration_id = cursor.lastrowid
        conn.commit()
        return registration_id, passphrase
    except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations
        print(f"Integrity error in add_registration (likely user already booked this slot): {e}")
        return None, None
    except sqlite3.Error as e:
        print(f"Database error in add_registration: {e}")
        return None, None
    finally:
        conn.close()

def get_signup_count(activity, timeslot):
    """Counts current active (not cancelled) signups for a specific activity/timeslot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Assuming registrations are permanent once made, unless explicitly cancelled by a mechanism not yet defined in this table directly
    # If cancellations mean deleting rows, then COUNT(*) is fine.
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE activity = ? AND timeslot = ?", (activity, timeslot))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_user_registrations(user_id):
    """Gets all registrations for a specific user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ? ORDER BY registration_time DESC", (user_id,))
    registrations = cursor.fetchall()
    conn.close()
    return registrations

def cancel_registration(registration_id):
    """Removes a registration by its ID. Returns True if successful."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
        conn.commit()
        return cursor.rowcount > 0 # True if a row was deleted
    except sqlite3.Error as e:
        print(f"Database error in cancel_registration: {e}")
        return False
    finally:
        conn.close()

def get_registration_by_passphrase(passphrase):
    """Fetches a registration by its unique registration_passphrase."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE registration_passphrase = ?", (passphrase,))
    registration = cursor.fetchone()
    conn.close()
    return registration

def check_in_registration(registration_id):
    """Marks a registration as checked_in. Returns True if successful, False if already checked_in or not found."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT checked_in FROM registrations WHERE id = ?", (registration_id,))
        result = cursor.fetchone()
        if result is None:
            return False # Not found
        if result['checked_in'] == 1:
            return False # Already checked in

        cursor.execute("UPDATE registrations SET checked_in = 1 WHERE id = ?", (registration_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in check_in_registration: {e}")
        return False
    finally:
        conn.close()

def get_registrations_for_timeslot(activity, timeslot):
    """Fetches all registrations for a specific activity and timeslot for admin view."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE activity = ? AND timeslot = ? ORDER BY registration_time", (activity, timeslot))
    registrations = cursor.fetchall()
    conn.close()
    return registrations

def get_activities():
    return ["Beach Volleyball", "Surfing Lessons", "Sandcastle Building", "Beach Photography", "Sunset Yoga"]

def get_timeslots():
    timeslots = []
    hour = 14
    minute = 30
    while not (hour == 17 and minute == 0):
        timeslots.append(f"{hour:02d}:{minute:02d}")
        minute += 15
        if minute >= 60:
            minute = 0
            hour += 1
        if hour >= 17: break
    return timeslots
