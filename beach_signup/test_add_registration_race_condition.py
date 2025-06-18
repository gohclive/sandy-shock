import threading
import sqlite3
import os
import time
from . import data_manager # Import the module itself

# Define a unique user_id for this test
TEST_USER_ID = "test_user_race_condition"
TEST_USER_NAME = "Test User Race"
DB_FILE = "beach_day.db"

# Global list to store results from threads
results = []

def register_activity(user_id, user_name, activity, timeslot):
    """Calls data_manager.add_registration and stores the result."""
    # add_registration returns: registration_id, passphrase, status
    # We are interested in the status for this test.
    _, _, status = data_manager.add_registration(user_id, user_name, activity, timeslot)
    results.append(status)

def cleanup_db(db_file, user_id):
    """Cleans up the database by deleting the test participant and their registrations."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # Delete registrations
        cursor.execute("DELETE FROM registrations WHERE user_id = ?", (user_id,))
        # Delete participant - participants table uses 'id' for the user identifier
        cursor.execute("DELETE FROM participants WHERE id = ?", (user_id,))
        conn.commit()
        # print(f"Database cleaned up for user_id: {user_id}")
    except sqlite3.Error as e:
        print(f"Database cleanup error: {e}")
    finally:
        if conn:
            conn.close()

def run_test():
    """Runs the race condition test."""
    print(f"Starting race condition test for user_id: {TEST_USER_ID}")

    # Initialize DataManager
    # Ensure the DB file is in the correct path relative to this script
    # Assuming this script is in beach_signup and db is one level up
    script_dir = os.path.dirname(__file__)
    # data_manager.py functions expect DB_FILE to be in the same directory as data_manager.py
    # The test script's DB_FILE variable is used for cleanup, make sure it points correctly.
    # beach_signup/data_manager.py and beach_signup/DB_FILE
    # So, from /app, the db is at beach_signup/beach_day.db
    db_path_for_cleanup = os.path.join(script_dir, DB_FILE) # Corrected path for cleanup

    # Clean up before test, in case of previous failed run
    # Ensure data_manager.DB_FILE is correctly located by data_manager functions
    # The data_manager functions define DB_FILE = "beach_day.db" and use __file__ to locate it.
    # So, no need to pass db_path to data_manager functions.

    # The cleanup_db function in *this* script needs the correct path.
    cleanup_db(db_path_for_cleanup, TEST_USER_ID)

    # dm = DataManager(db_path) # No longer needed

    # Reset global results list for this test run
    global results
    results = []

    # Define thread targets
    # No need to pass dm_instance anymore
    thread1 = threading.Thread(target=register_activity, args=(TEST_USER_ID, TEST_USER_NAME, "Surfing Lessons", "15:00"))
    thread2 = threading.Thread(target=register_activity, args=(TEST_USER_ID, TEST_USER_NAME, "Sunset Yoga", "16:00"))

    # Start threads
    thread1.start()
    thread2.start()

    # Wait for threads to complete
    thread1.join()
    thread2.join()

    # Analyze results
    success_count = results.count("SUCCESS")
    limit_reached_count = results.count("LIMIT_REACHED")

    test_passed = False
    reason = ""

    if success_count == 1 and limit_reached_count == 1:
        # Verify database state
        conn = None
        try:
            # Use the same db_path_for_cleanup for verification connection
            conn = sqlite3.connect(db_path_for_cleanup)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registrations WHERE user_id = ?", (TEST_USER_ID,))
            count = cursor.fetchone()[0]
            if count == 1:
                test_passed = True
                reason = "Test passed: One registration successful, one blocked by limit, and DB state is correct."
            else:
                reason = f"Test failed: DB state incorrect. Expected 1 registration, found {count} for user_id {TEST_USER_ID}."
        except sqlite3.Error as e:
            reason = f"Test failed: Database query error: {e}"
        finally:
            if conn:
                conn.close()
    elif success_count == 2:
        reason = f"Test failed: Both registrations succeeded. Expected 1 SUCCESS and 1 LIMIT_REACHED. Results: {results}"
    elif limit_reached_count == 2:
        reason = f"Test failed: Both registrations hit LIMIT_REACHED. Expected 1 SUCCESS. Results: {results}"
    else:
        reason = f"Test failed: Unexpected results. Success count: {success_count}, Limit reached count: {limit_reached_count}. Results: {results}"

    print(reason)

    # Cleanup after test
    cleanup_db(db_path_for_cleanup, TEST_USER_ID)

    return test_passed, reason

if __name__ == "__main__":
    passed, message = run_test()
    if passed:
        print("One Booking Per User Race Condition Test: PASSED")
    else:
        print(f"One Booking Per User Race Condition Test: FAILED\nReason: {message}")
