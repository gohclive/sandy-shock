import sqlite3
import os # Ensure os is imported
import random
from datetime import datetime

DB_FILE = "beach_day.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_word_list():
    """Load words for passphrase generation from words.txt."""
    # Correctly locate words.txt relative to this file (data_manager.py)
    word_file_path = os.path.join(os.path.dirname(__file__), 'words.txt')
    try:
        with open(word_file_path, 'r') as f:
            return [word.strip().lower() for word in f.readlines() if word.strip()]
    except FileNotFoundError:
        print(f"Warning: {word_file_path} not found. Using fallback word list.")
        return ['apple', 'beach', 'happy', 'ocean', 'sunny', 'wave', 'blue', 'sky', 'sand', 'fun']

def generate_unique_passphrase(conn):
    """Generates a 4-word passphrase that is guaranteed to be unique in the DB."""
    words = load_word_list()
    if len(words) < 4:
        print("Error: Word list is too small. Using simplified fallback.")
        # Simplified fallback for this edge case
        base_passphrase_parts = ['default', 'pass', 'phrase', 'unique']
        # Ensure we use 4 parts, even if it means repetition (less ideal)
        while len(base_passphrase_parts) < 4:
            base_passphrase_parts.append('word')
        current_passphrase = '-'.join(random.sample(base_passphrase_parts, 4) if len(set(base_passphrase_parts)) >=4 else base_passphrase_parts[:4])

        cursor = conn.cursor()
        suffix = 0
        while True:
            passphrase_to_check = f"{current_passphrase}{'-'+str(suffix) if suffix > 0 else ''}"
            cursor.execute("SELECT 1 FROM participants WHERE passphrase = ?", (passphrase_to_check,))
            if cursor.fetchone() is None:
                return passphrase_to_check
            suffix += 1
        # This line should ideally not be reached if the loop above works.
        # However, as a very last resort, to prevent an infinite loop in an unexpected scenario:
        # return f"fallback-error-{random.randint(1000,9999)}"


    cursor = conn.cursor()
    attempts = 0
    max_attempts = 200 # Increased attempts
    while attempts < max_attempts:
        passphrase = '-'.join(random.sample(words, 4))
        cursor.execute("SELECT 1 FROM participants WHERE passphrase = ?", (passphrase,))
        if cursor.fetchone() is None:
            return passphrase
        attempts += 1

    print(f"Warning: Could not generate a unique passphrase from primary list after {max_attempts} attempts. Appending suffix.")
    # Fallback to a suffixed passphrase to ensure uniqueness if many collisions occur
    # This could happen if the word list is small and many passphrases are already in the DB
    passphrase_base = '-'.join(random.sample(words,4)) # Generate a base one more time
    suffix = 1
    while True: # Loop indefinitely until a unique one is found (DB constraint will eventually be met)
        new_passphrase = f"{passphrase_base}-{suffix}"
        cursor.execute("SELECT 1 FROM participants WHERE passphrase = ?", (new_passphrase,))
        if cursor.fetchone() is None:
            return new_passphrase
        suffix += 1


def initialize_database():
    """Creates the database and tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Participants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            passphrase TEXT NOT NULL UNIQUE,
            created_time TEXT NOT NULL
        )
    ''')
    # Signups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signups (
            participant_id TEXT,
            activity TEXT NOT NULL,
            timeslot TEXT NOT NULL,
            FOREIGN KEY (participant_id) REFERENCES participants (id),
            PRIMARY KEY (participant_id, timeslot)
        )
    ''')
    conn.commit()
    conn.close()

def create_participant(user_id, name):
    """Creates a new participant record and returns their generated passphrase."""
    conn = get_db_connection()
    # generate_unique_passphrase now requires the connection to be passed
    passphrase = generate_unique_passphrase(conn)
    created_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO participants (id, name, passphrase, created_time) VALUES (?, ?, ?, ?)",
            (user_id, name, passphrase, created_time)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in create_participant: {e}")
        conn.close() # Ensure connection is closed on error too
        return None # Indicate failure
    conn.close()
    return passphrase

def find_participant_by_id(user_id):
    """Finds a participant by their user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE id = ?", (user_id,))
    participant = cursor.fetchone()
    conn.close()
    return participant

def get_activities():
    """Returns the list of 5 activities."""
    return ["Beach Volleyball", "Surfing Lessons", "Sandcastle Building", "Beach Photography", "Sunset Yoga"]

def get_timeslots():
    """Generates 15-minute timeslots from 2:30 PM to 4:45 PM."""
    timeslots = []
    hour = 14
    minute = 30
    while not (hour == 17 and minute == 0): # Loop up to, but not including, 5:00 PM
        timeslots.append(f"{hour:02d}:{minute:02d}")
        minute += 15
        if minute >= 60:
            minute = 0
            hour += 1
        if hour >= 17: # Stop condition
            break
    return timeslots

def get_signup_count(activity, timeslot):
    """Counts current signups for a specific activity/timeslot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM signups WHERE activity = ? AND timeslot = ?", (activity, timeslot))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_signup(user_id, activity, timeslot):
    """Adds a new signup. Returns True on success, False on failure."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO signups (participant_id, activity, timeslot) VALUES (?, ?, ?)",
                     (user_id, activity, timeslot))
        conn.commit()
        success = True
    except sqlite3.IntegrityError: # Handles double booking (PK violation)
        print(f"IntegrityError: User {user_id} likely already signed up for timeslot {timeslot}.")
        success = False
    except sqlite3.Error as e: # Handles other DB errors
        print(f"SQLite error in add_signup: {e}")
        success = False
    finally:
        conn.close()
    return success

def cancel_signup(user_id, activity, timeslot):
    """Removes a signup. Returns True if a row was deleted, False otherwise."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signups WHERE participant_id = ? AND activity = ? AND timeslot = ?",
                 (user_id, activity, timeslot))
        conn.commit()
        return cursor.rowcount > 0 # Check if any row was affected
    except sqlite3.Error as e:
        print(f"SQLite error in cancel_signup: {e}")
        return False
    finally:
        conn.close()

def get_user_signups(user_id):
    """Gets all signups for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT activity, timeslot FROM signups WHERE participant_id = ? ORDER BY timeslot", (user_id,))
    signups = cursor.fetchall() # Returns a list of Row objects
    conn.close()
    return signups

def verify_participant(search_term):
    """Searches by name or passphrase for verification. Returns list of Row objects."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Search by name (case-insensitive) or exact passphrase match (passphrases are stored lowercase)
    query = """
        SELECT p.name, p.passphrase, s.activity, s.timeslot
        FROM participants p
        LEFT JOIN signups s ON p.id = s.participant_id
        WHERE lower(p.name) LIKE lower(?) OR p.passphrase = lower(?)
        ORDER BY p.name, s.timeslot
    """
    # Prepare search term for LIKE query
    like_search_term = f'%{search_term}%'
    results = cursor.execute(query, (like_search_term, search_term)).fetchall()
    conn.close()
    return results
