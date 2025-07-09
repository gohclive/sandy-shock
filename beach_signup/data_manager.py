import pyodbc
import os
import random
from datetime import datetime
import streamlit as st # Added for secrets access

# DB_FILE = "beach_day.db" # No longer needed for Azure SQL

def get_db_connection():
    # Read Azure SQL connection info from Streamlit secrets
    server = st.secrets["azure_sql"]["server"]
    database = st.secrets["azure_sql"]["database"]
    username = st.secrets["azure_sql"]["username"]
    password = st.secrets["azure_sql"]["password"]
    driver = st.secrets["azure_sql"].get("driver", "{ODBC Driver 17 for SQL Server}") # Default driver

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    # conn.row_factory = pyodbc.Row # pyodbc cursors return Row objects by default when iterating
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
    # Note: Azure SQL uses 'IF OBJECT_ID' for checking existence, but CREATE TABLE IF NOT EXISTS is simpler if supported or for general use.
    # For Azure SQL, it's generally better to ensure tables are created via a separate script or migration tool.
    # However, for this exercise, we'll adapt it to run, acknowledging it might warn if tables exist.
    # Or, we can query INFORMATION_SCHEMA.TABLES first. Let's try a more robust way for Azure SQL.

    # Check if participants table exists
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'participants'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE participants (
                id NVARCHAR(255) PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                created_time DATETIME2 NOT NULL
            )
        ''')
        print("Created participants table.")
    else:
        print("Participants table already exists.")

    # Check if registrations table exists
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'registrations'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE registrations (
                id INT PRIMARY KEY IDENTITY(1,1),
                user_id NVARCHAR(255) NOT NULL,
                participant_name NVARCHAR(255) NOT NULL,
                activity NVARCHAR(100) NOT NULL,
                timeslot NVARCHAR(50) NOT NULL,
                registration_passphrase NVARCHAR(255) NOT NULL UNIQUE,
                registration_time DATETIME2 NOT NULL,
                checked_in INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES participants (id),
                CONSTRAINT UQ_user_activity_timeslot UNIQUE (user_id, activity, timeslot)
            )
        ''')
        print("Created registrations table.")
    else:
        print("Registrations table already exists.")

    # Check if competitive_games table exists
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'competitive_games'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE competitive_games (
                id INT PRIMARY KEY IDENTITY(1,1),
                name NVARCHAR(255) NOT NULL UNIQUE
            )
        ''')
        print("Created competitive_games table.")
    else:
        print("Competitive_games table already exists.")

    # Check if teams table exists
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'teams'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE teams (
                id INT PRIMARY KEY IDENTITY(1,1),
                name NVARCHAR(255) NOT NULL UNIQUE
            )
        ''')
        print("Created teams table.")
    else:
        print("Teams table already exists.")

    # Check if game_scores table exists
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'game_scores'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE game_scores (
                id INT PRIMARY KEY IDENTITY(1,1),
                game_id INT NOT NULL,
                team_id INT NOT NULL,
                score INT DEFAULT 0,
                last_updated_time DATETIME2 NOT NULL,
                FOREIGN KEY (game_id) REFERENCES competitive_games (id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
                CONSTRAINT UQ_game_team UNIQUE (game_id, team_id)
            )
        ''')
        print("Created game_scores table.")
    else:
        print("Game_scores table already exists.")

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
        created_time = datetime.now() # Store as datetime object, will be handled by pyodbc
        cursor.execute( "INSERT INTO participants (id, name, created_time) VALUES (?, ?, ?)", (user_id, name, created_time) )
        conn.commit()
        return True
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in create_participant: {e}")
        # Consider specific error codes for "already exists" if needed, e.g., 2627 for unique constraint violation
        conn.rollback() # Rollback on error
        return False
    finally:
        if conn: conn.close()

def find_participant_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE id = ?", (user_id,))
    row = cursor.fetchone() # pyodbc.Row object
    conn.close()
    # Convert pyodbc.Row to dict
    return {desc[0]: value for desc, value in zip(cursor.description, row)} if row else None


def get_user_registrations(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ? ORDER BY registration_time DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    # Convert list of pyodbc.Row to list of dicts
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]


def add_registration(user_id, name, activity, timeslot):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Step 1: Check for existing registrations for this user_id
        cursor.execute("SELECT 1 FROM registrations WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.rollback()
            conn.close()
            return None, None, "LIMIT_REACHED"

        # Step 2: Proceed with generating passphrase and inserting
        passphrase = generate_registration_passphrase(conn)
        reg_time = datetime.now() # Store as datetime object

        cursor.execute(
            "INSERT INTO registrations (user_id, participant_name, activity, timeslot, registration_passphrase, registration_time) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, activity, timeslot, passphrase, reg_time)
        )
        # Get the last inserted ID using SCOPE_IDENTITY() for SQL Server
        cursor.execute("SELECT SCOPE_IDENTITY()")
        registration_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return registration_id, passphrase, "SUCCESS"

    except pyodbc.IntegrityError as e: # Specific error for integrity issues
        if conn: conn.rollback()
        if conn: conn.close()
        if e.args[0] in ('23000', '2627', '2601'): # Check for unique constraint violation
             return None, None, "ALREADY_BOOKED_TIMESLOT" # Or a more specific "LIMIT_REACHED" if only user_id is unique
        return None, None, "DB_ERROR" # Generic database error
    except pyodbc.Error as e: # General pyodbc error
        # print(f"Database error in add_registration for user {user_id}: {e}")
        if conn: conn.rollback()
        if conn: conn.close()
        return None, None, "DB_ERROR"


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
        return cursor.rowcount > 0 # rowcount indicates number of rows affected
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in cancel_registration: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_registration_by_passphrase(passphrase):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE registration_passphrase = ?", (passphrase,))
    row = cursor.fetchone()
    conn.close()
    return {desc[0]: value for desc, value in zip(cursor.description, row)} if row else None


def check_in_registration(registration_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT checked_in FROM registrations WHERE id = ?", (registration_id,))
        result_row = cursor.fetchone()
        if result_row is None:
            conn.close()
            return False
        # pyodbc.Row can be accessed by column name
        if result_row.checked_in == 1: # Access by column name
            conn.close()
            return False
        cursor.execute("UPDATE registrations SET checked_in = 1 WHERE id = ?", (registration_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in check_in_registration: {e}")
        if conn: conn.rollback()
        if conn: conn.close()
        return False

def uncheck_in_registration(registration_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE registrations SET checked_in = 0 WHERE id = ?", (registration_id,))
        conn.commit()
        success = cursor.rowcount > 0
        # print(f"Uncheck registration ID {registration_id} - success: {success}, rows affected: {cursor.rowcount}")
        conn.close()
        return success
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in uncheck_in_registration for ID {registration_id}: {e}")
        if conn: conn.rollback()
        if conn: conn.close()
        return False


def get_registrations_for_timeslot(activity, timeslot):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE activity = ? AND timeslot = ? ORDER BY registration_time", (activity, timeslot))
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]


def get_registrations_for_participant(participant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id = ?", (participant_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]


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

def get_total_registration_count_for_activity(activity):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE activity = ?", (activity,))
        count = cursor.fetchone()[0]
        return count
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in get_total_registration_count_for_activity for {activity}: {e}")
        return 0
    finally:
        if conn: conn.close()


def get_checked_in_count_for_activity(activity):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE checked_in = 1 AND activity = ?", (activity,))
        count = cursor.fetchone()[0]
        return count
    except pyodbc.Error as e: # Changed to pyodbc.Error
        print(f"Database error in get_checked_in_count_for_activity for {activity}: {e}")
        return 0
    finally:
        if conn: conn.close()

def get_activities():
    return [activity["name"] for activity in ACTIVITIES]

# Define activities with their properties
ACTIVITIES = [
    {"name": "Massage by SAVH", "slots": 15, "duration": 20, "id": "massage_SAVH"},
]

def get_activity_details(activity_name):
    for activity in ACTIVITIES:
        if activity["name"] == activity_name:
            return activity
    return None

def get_timeslots(activity_duration_minutes):
    """
    Generates timeslots based on activity duration.
    Activities start at intervals equal to their duration (no overlap).
    The event runs from 14:30 to 17:00.
    
    For example:
    - A 45-minute activity: 14:30-15:15, then 15:15-16:00, then 16:00-16:45
    - A 20-minute activity: 14:30-14:50, then 14:50-15:10, then 15:10-15:30, etc.
    """
    timeslots = []
    event_start_hour, event_start_minute = 14, 30
    event_end_hour, event_end_minute = 17, 0
    
    # Convert event times to minutes for easier calculation
    event_start_minutes = event_start_hour * 60 + event_start_minute
    event_end_minutes = event_end_hour * 60 + event_end_minute
    
    current_minutes = event_start_minutes
    
    while True:
        # Calculate when this activity would end if it started now
        activity_end_minutes = current_minutes + activity_duration_minutes
        
        # Check if this activity would finish before or at the event end time
        if activity_end_minutes <= event_end_minutes:
            # Convert back to hours and minutes for display
            current_hour = current_minutes // 60
            current_minute = current_minutes % 60
            timeslots.append(f"{current_hour:02d}:{current_minute:02d}")
            
            # Move to next start time (after this activity ends)
            current_minutes += activity_duration_minutes
        else:
            # Activity would run past event end time, so stop
            break
            
    return timeslots

# --- Competitive Games Functions ---

def add_competitive_game(name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO competitive_games (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except pyodbc.IntegrityError: # Handles unique constraint violation for name
        conn.rollback()
        return False # Game name likely already exists
    except pyodbc.Error as e:
        print(f"Database error in add_competitive_game: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_competitive_games():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM competitive_games ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]

def delete_competitive_game(game_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Scores related to this game will be deleted due to ON DELETE CASCADE
        cursor.execute("DELETE FROM competitive_games WHERE id = ?", (game_id,))
        conn.commit()
        return cursor.rowcount > 0
    except pyodbc.Error as e:
        print(f"Database error in delete_competitive_game: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- Teams Functions ---

def add_team(name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except pyodbc.IntegrityError: # Handles unique constraint violation for name
        conn.rollback()
        return False # Team name likely already exists
    except pyodbc.Error as e:
        print(f"Database error in add_team: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_teams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM teams ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]

def delete_team(team_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Scores related to this team will be deleted due to ON DELETE CASCADE
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
        return cursor.rowcount > 0
    except pyodbc.Error as e:
        print(f"Database error in delete_team: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- Game Scores Functions ---

def update_score(game_id, team_id, score):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now()
        # Upsert logic: Insert if not exists, update if exists
        # Check if score entry exists
        cursor.execute("SELECT id FROM game_scores WHERE game_id = ? AND team_id = ?", (game_id, team_id))
        existing_score = cursor.fetchone()

        if existing_score:
            cursor.execute(
                "UPDATE game_scores SET score = ?, last_updated_time = ? WHERE id = ?",
                (score, current_time, existing_score[0])
            )
        else:
            cursor.execute(
                "INSERT INTO game_scores (game_id, team_id, score, last_updated_time) VALUES (?, ?, ?, ?)",
                (game_id, team_id, score, current_time)
            )
        conn.commit()
        return True
    except pyodbc.Error as e:
        print(f"Database error in update_score: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_all_scores():
    """
    Fetches all scores and structures them for easy display, e.g., a pivot table like structure.
    Returns a dictionary where keys are team names and values are dictionaries of game_name: score.
    Also returns lists of all game names and team names for header/row generation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all games and teams first to ensure all are represented
    cursor.execute("SELECT id, name FROM competitive_games ORDER BY name")
    games_list = [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, name FROM teams ORDER BY name")
    teams_list = [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in cursor.fetchall()]

    # Fetch all scores with game and team names
    sql = """
    SELECT t.name as team_name, cg.name as game_name, gs.score
    FROM game_scores gs
    JOIN teams t ON gs.team_id = t.id
    JOIN competitive_games cg ON gs.game_id = cg.id
    """
    cursor.execute(sql)
    scores_raw = cursor.fetchall()
    conn.close()

    # Initialize score_data with all teams and games, defaulting scores to 0 or None
    score_data = {team['name']: {game['name']: 0 for game in games_list} for team in teams_list}

    for score_row in scores_raw:
        score_data[score_row.team_name][score_row.game_name] = score_row.score
    
    game_names = [game['name'] for game in games_list]
    team_names = [team['name'] for team in teams_list]

    return score_data, game_names, team_names


def get_scores_for_game(game_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    SELECT t.name as team_name, gs.score, gs.last_updated_time
    FROM game_scores gs
    JOIN teams t ON gs.team_id = t.id
    WHERE gs.game_id = ?
    ORDER BY t.name
    """
    cursor.execute(sql, game_id)
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]

def get_scores_for_team(team_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    SELECT cg.name as game_name, gs.score, gs.last_updated_time
    FROM game_scores gs
    JOIN competitive_games cg ON gs.game_id = cg.id
    WHERE gs.team_id = ?
    ORDER BY cg.name
    """
    cursor.execute(sql, team_id)
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]

def get_team_total_scores():
    """Calculates total scores for each team."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    SELECT t.name as team_name, SUM(gs.score) as total_score
    FROM teams t
    LEFT JOIN game_scores gs ON t.id = gs.team_id
    GROUP BY t.id, t.name
    ORDER BY total_score DESC, t.name
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]
