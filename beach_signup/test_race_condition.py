import sqlite3
import os
from datetime import datetime
import threading
import time

# Attempt to import from beach_signup.data_manager
try:
    from beach_signup.data_manager import (
        get_db_connection,
        initialize_database,
        create_participant,
        add_registration,
        get_signup_count,
        get_activities,
        get_timeslots,
        load_word_list, # Needed by add_registration indirectly
        generate_registration_passphrase # Needed by add_registration
    )
    print("Successfully imported from beach_signup.data_manager")
except ImportError as e:
    print(f"ImportError: {e}. Falling back to defining necessary functions (not implemented in this snippet).")
    # In a real scenario, if imports fail, we would copy definitions here.
    # For this subtask, we assume imports will work as per file structure.
    exit(f"Failed to import from data_manager.py: {e}. Please ensure the script is run in an environment where beach_signup is a package or PYTHONPATH is set.")


# Define DB_FILE and WORD_FILE_PATH for the test script's context,
# though imported functions from data_manager will use their own internal paths.
# This is more for future-proofing or if we were to copy functions.
SCRIPT_DIR = os.path.dirname(__file__)
DB_FILE = os.path.join(SCRIPT_DIR, "beach_day_test.db") # Intentionally different for now to see if it causes issues
                                                       # Or rather, to manage a test-specific DB.
                                                       # Let's reconsider this: the prompt wants to modify the *actual* DB.
                                                       # "The initialize_database function in data_manager.py already connects to beach_day.db in its own directory"
                                                       # "The key is that DB_FILE in the test script, if defined, must point to the same DB used by the imported/copied data_manager functions."
                                                       # This implies that if data_manager.py uses beach_signup/beach_day.db, my test script should also point there
                                                       # if it were to open a connection itself.
                                                       # For now, imported functions will handle their DB, so this DB_FILE is for test script's own potential direct use.

# Let's align with data_manager.py's DB for any direct operations, IF NECESSARY.
# The primary path is data_manager.py's own DB_FILE definition.
# For the test, we will be manipulating the DB used by data_manager.py.
# So, this DB_FILE definition in the test script is more of a placeholder or for direct test script DB ops.
# The functions from data_manager will use `beach_signup/beach_day.db`.

# Global dictionary to store thread results
thread_results = {}

# Test Parameters
ACTIVITY_UNDER_TEST = "Beach Volleyball"
TIMESLOT_UNDER_TEST = "14:30" # Ensure this is a valid timeslot from get_timeslots()
SUCCESS_USER_ID = "concurrent_user_success"
SUCCESS_USER_NAME = "Concurrent Success"
FAIL_USER_ID = "concurrent_user_fail_limit"
FAIL_USER_NAME = "Concurrent Fail Limit"
FAIL_USER_OTHER_ACTIVITY = "Surfing Lessons" # Must be different from ACTIVITY_UNDER_TEST
NUM_DUMMY_REGISTRATIONS = 9 # This will fill the activity to 9, leaving 1 spot (assuming limit is 10)
DUMMY_USER_ID_PREFIX = "dummy_user_"
DUMMY_USER_NAME_PREFIX = "Dummy User "

def setup_initial_database_state():
    """
    Sets up the database to a predefined state for testing race conditions.
    - Clears existing participant and registration data.
    - Populates dummy registrations for ACTIVITY_UNDER_TEST to near its limit.
    - Creates a user (FAIL_USER_ID) who has already registered for another activity.
    - Creates a user (SUCCESS_USER_ID) who has no prior registrations.
    """
    print("Setting up initial database state...")

    # Initialize database (ensures tables are created using data_manager's DB context)
    initialize_database()
    print(f"Database initialized (tables ensured). Using DB associated with data_manager.py.")

    # Get a connection (this will be to data_manager's DB_FILE)
    # The path used by get_db_connection() is internal to data_manager.py
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Clear existing data from relevant tables
        print("Clearing existing registrations and participants...")
        cursor.execute("DELETE FROM registrations")
        cursor.execute("DELETE FROM participants")
        conn.commit()
        print("Data cleared.")

        # Populate Participants and Registrations
        print(f"Populating {NUM_DUMMY_REGISTRATIONS} dummy users for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}...")
        for i in range(1, NUM_DUMMY_REGISTRATIONS + 1):
            user_id = f"{DUMMY_USER_ID_PREFIX}{i}"
            name = f"{DUMMY_USER_NAME_PREFIX}{i}"

            if not create_participant(user_id, name):
                print(f"Error creating dummy participant {user_id}. Skipping registration.")
                continue

            # Add registration - using imported add_registration
            # It handles its own connection internally.
            # For setup, we don't expect "LIMIT_REACHED" for these dummy users as they are new.
            _, _, status = add_registration(user_id, name, ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST)
            if status != "SUCCESS":
                print(f"Error registering dummy user {user_id} for {ACTIVITY_UNDER_TEST}: {status}")
        print(f"Dummy users populated for {ACTIVITY_UNDER_TEST}.")

        # Create FAIL_USER_ID participant and register them for a *different* activity
        # This is to make them hit the "1 activity per user" limit later.
        print(f"Creating participant {FAIL_USER_ID} ({FAIL_USER_NAME})...")
        if not create_participant(FAIL_USER_ID, FAIL_USER_NAME):
             print(f"Error creating participant {FAIL_USER_ID}. This might affect test logic.")
        else:
            print(f"Registering {FAIL_USER_ID} for {FAIL_USER_OTHER_ACTIVITY}...")
            # Ensure the timeslot is valid for the other activity; using TIMESLOT_UNDER_TEST for simplicity if valid for all.
            # Or, pick the first available timeslot.
            available_timeslots = get_timeslots()
            other_activity_timeslot = available_timeslots[0] if available_timeslots else "14:00" # Fallback

            if FAIL_USER_OTHER_ACTIVITY not in get_activities():
                print(f"Warning: {FAIL_USER_OTHER_ACTIVITY} is not in get_activities(). Test logic might be flawed.")

            _, _, status = add_registration(FAIL_USER_ID, FAIL_USER_NAME, FAIL_USER_OTHER_ACTIVITY, other_activity_timeslot)
            if status != "SUCCESS":
                print(f"Error registering {FAIL_USER_ID} for {FAIL_USER_OTHER_ACTIVITY}: {status}")
            else:
                print(f"{FAIL_USER_ID} registered for {FAIL_USER_OTHER_ACTIVITY} at {other_activity_timeslot}.")


        # Create SUCCESS_USER_ID participant (should have no prior registrations)
        print(f"Creating participant {SUCCESS_USER_ID} ({SUCCESS_USER_NAME})...")
        if not create_participant(SUCCESS_USER_ID, SUCCESS_USER_NAME):
            print(f"Error creating participant {SUCCESS_USER_ID}. This might affect test logic.")
        else:
            print(f"Participant {SUCCESS_USER_ID} created. They have no registrations yet.")

        conn.commit()
        print("Database setup complete.")

    except sqlite3.Error as e:
        print(f"An error occurred during database setup: {e}")
        conn.rollback() # Rollback changes if any error occurs during setup
    finally:
        conn.close()
        print("Database connection closed.")

def registration_thread_worker(user_id, name, activity, timeslot, thread_name):
    """
    Target function for registration threads.
    Attempts to register a user and stores the result status in thread_results.
    """
    print(f"{thread_name}: Attempting registration for user {user_id} ('{name}') for {activity} @ {timeslot}")
    # Using the directly imported add_registration function
    _, _, status = add_registration(user_id, name, activity, timeslot)
    thread_results[thread_name] = status
    print(f"{thread_name}: Registration attempt for user {user_id} completed with status: {status}")

if __name__ == "__main__":
    print("Running test_race_condition.py script...")

    # Validate that ACTIVITY_UNDER_TEST and TIMESLOT_UNDER_TEST are valid
    if ACTIVITY_UNDER_TEST not in get_activities():
        print(f"FATAL: ACTIVITY_UNDER_TEST '{ACTIVITY_UNDER_TEST}' is not a valid activity. Test cannot proceed.")
        exit(1)
    if TIMESLOT_UNDER_TEST not in get_timeslots():
        print(f"FATAL: TIMESLOT_UNDER_TEST '{TIMESLOT_UNDER_TEST}' is not a valid timeslot. Test cannot proceed.")
        exit(1)
    if FAIL_USER_OTHER_ACTIVITY not in get_activities():
         print(f"WARNING: FAIL_USER_OTHER_ACTIVITY '{FAIL_USER_OTHER_ACTIVITY}' is not a valid activity. Test logic for FAIL_USER_ID might be impacted.")


    setup_initial_database_state()

    print("\nVerifying initial database counts (using imported get_signup_count):")

    # Connect to the database (again, using data_manager's context) to verify counts
    # get_signup_count handles its own connection.

    count_volleyball = get_signup_count(ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST)
    print(f"Initial count for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}: {count_volleyball} (Expected: {NUM_DUMMY_REGISTRATIONS})")

    # Determine the timeslot used for FAIL_USER_OTHER_ACTIVITY for accurate count check
    # For simplicity, assuming it was the first timeslot if setup logic ran as expected.
    # This part of verification might need to be more robust if timeslot selection is dynamic.
    available_timeslots = get_timeslots()
    fail_user_other_activity_timeslot = available_timeslots[0] if available_timeslots else "14:00"

    count_other_activity = get_signup_count(FAIL_USER_OTHER_ACTIVITY, fail_user_other_activity_timeslot)
    print(f"Initial count for {FAIL_USER_OTHER_ACTIVITY} @ {fail_user_other_activity_timeslot}: {count_other_activity} (Expected: 1 if setup for FAIL_USER_ID succeeded)")

    # Additional verification: Check total registrations for FAIL_USER_ID
    # This requires a function like get_user_registrations from data_manager.py
    try:
        from beach_signup.data_manager import get_user_registrations
        fail_user_regs = get_user_registrations(FAIL_USER_ID)
        print(f"Registrations for {FAIL_USER_ID} ({FAIL_USER_NAME}): {len(fail_user_regs)}")
        if len(fail_user_regs) == 1:
            print(f"  - {fail_user_regs[0]['activity']} @ {fail_user_regs[0]['timeslot']}")

        success_user_regs = get_user_registrations(SUCCESS_USER_ID)
        print(f"Registrations for {SUCCESS_USER_ID} ({SUCCESS_USER_NAME}): {len(success_user_regs)}")

    except ImportError:
        print("Could not import get_user_registrations for detailed verification.")
    except Exception as e:
        print(f"Error during detailed verification: {e}")

    print("\nTest script setup phase finished.")
    # print("Next steps would involve simulating concurrent calls to add_registration.") # This is now being done.

    print("\nStarting concurrent registration attempts...")
    thread1 = threading.Thread(
        target=registration_thread_worker,
        args=(SUCCESS_USER_ID, SUCCESS_USER_NAME, ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST, "Thread-SuccessUser")
    )
    thread2 = threading.Thread(
        target=registration_thread_worker,
        args=(FAIL_USER_ID, FAIL_USER_NAME, ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST, "Thread-FailUser")
    )

    # Start threads as close as possible
    thread1.start()
    # time.sleep(0.001) # Optional small delay to influence thread interleaving for testing, not usually needed.
    thread2.start()

    # Wait for both threads to complete
    thread1.join()
    thread2.join()

    print("\nConcurrent registration attempts finished.")
    success_user_result = thread_results.get('Thread-SuccessUser', 'NOT_RUN')
    fail_user_result = thread_results.get('Thread-FailUser', 'NOT_RUN')

    print(f"Result for {SUCCESS_USER_ID} (Thread-SuccessUser): {success_user_result}")
    print(f"Result for {FAIL_USER_ID} (Thread-FailUser): {fail_user_result}")

    # Renaming for clarity in assertions
    status_success_user = success_user_result
    status_fail_user = fail_user_result

    print("\nVerifying results with assertions...")

    assert status_success_user == "SUCCESS", f"Assertion Failed: Expected SUCCESS_USER_ID status to be 'SUCCESS', got {status_success_user}"
    print(f"Assertion PASSED: {SUCCESS_USER_ID} registration status is 'SUCCESS'.")

    assert status_fail_user == "LIMIT_REACHED", f"Assertion Failed: Expected FAIL_USER_ID status to be 'LIMIT_REACHED', got {status_fail_user}"
    print(f"Assertion PASSED: {FAIL_USER_ID} registration status is 'LIMIT_REACHED'.")
    # print(f"Reported status for failed registration ({FAIL_USER_ID}): {status_fail_user}") # Redundant with above

    # Add Assertions for Database State
    print("\nVerifying final database state with assertions...")

    # Verify final count for the activity/timeslot
    final_count_volleyball = get_signup_count(ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST)
    print(f"Final count for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}: {final_count_volleyball}")
    expected_final_count = NUM_DUMMY_REGISTRATIONS + 1 # SUCCESS_USER_ID should have registered
    assert final_count_volleyball == expected_final_count, \
        f"Assertion Failed: Expected final count for {ACTIVITY_UNDER_TEST} to be {expected_final_count}, got {final_count_volleyball}"
    print(f"Assertion PASSED: Final count for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST} is {expected_final_count}.")

    # Verify specific user registrations for the target slot
    # This requires a direct DB connection to fetch the list of users for the specific slot
    conn = get_db_connection() # Uses data_manager's DB context
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM registrations WHERE activity = ? AND timeslot = ?", (ACTIVITY_UNDER_TEST, TIMESLOT_UNDER_TEST))
    registered_users_for_slot = [row[0] for row in cursor.fetchall()] # Assuming user_id is the first column
    conn.close()
    print(f"Registered users for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}: {registered_users_for_slot}")

    assert SUCCESS_USER_ID in registered_users_for_slot, \
        f"Assertion Failed: {SUCCESS_USER_ID} should be in registered list for the slot {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}."
    print(f"Assertion PASSED: {SUCCESS_USER_ID} is registered for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}.")

    assert FAIL_USER_ID not in registered_users_for_slot, \
        f"Assertion Failed: {FAIL_USER_ID} should NOT be in registered list for the slot {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}."
    print(f"Assertion PASSED: {FAIL_USER_ID} is NOT registered for {ACTIVITY_UNDER_TEST} @ {TIMESLOT_UNDER_TEST}.")

    # Verify FAIL_USER_ID still has their original registration for the other activity
    try:
        from beach_signup.data_manager import get_user_registrations # Already imported earlier, but good for logical block
        fail_user_registrations = get_user_registrations(FAIL_USER_ID)
        assert len(fail_user_registrations) == 1, \
            f"Assertion Failed: {FAIL_USER_ID} should have exactly 1 registration, found {len(fail_user_registrations)}."
        assert fail_user_registrations[0]['activity'] == FAIL_USER_OTHER_ACTIVITY, \
            f"Assertion Failed: {FAIL_USER_ID}'s registration should be for {FAIL_USER_OTHER_ACTIVITY}, found {fail_user_registrations[0]['activity']}."
        print(f"Assertion PASSED: {FAIL_USER_ID} correctly has 1 registration for {FAIL_USER_OTHER_ACTIVITY}.")
    except Exception as e: # Catch if get_user_registrations fails or list is empty
        assert False, f"Error during FAIL_USER_ID registration check: {e}"


    # Verify SUCCESS_USER_ID has only one registration (the one they just made)
    try:
        from beach_signup.data_manager import get_user_registrations
        success_user_registrations = get_user_registrations(SUCCESS_USER_ID)
        assert len(success_user_registrations) == 1, \
            f"Assertion Failed: {SUCCESS_USER_ID} should have exactly 1 registration, found {len(success_user_registrations)}."
        assert success_user_registrations[0]['activity'] == ACTIVITY_UNDER_TEST, \
            f"Assertion Failed: {SUCCESS_USER_ID}'s registration should be for {ACTIVITY_UNDER_TEST}, found {success_user_registrations[0]['activity']}."
        print(f"Assertion PASSED: {SUCCESS_USER_ID} correctly has 1 registration for {ACTIVITY_UNDER_TEST}.")
    except Exception as e:
        assert False, f"Error during SUCCESS_USER_ID registration check: {e}"


    print("\nAll assertions passed. Test completed successfully!")
    print("\nEnd of test_race_condition.py script.")
