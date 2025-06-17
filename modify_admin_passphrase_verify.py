import re

app_file_path = 'beach_signup/app.py'

with open(app_file_path, 'r') as f:
    content = f.read()

# Corrected implementation for the "Verify by Passphrase & Check-In" part
# Uses indexed access for sqlite3.Row objects.
# Registrations table schema indices:
# id(0), user_id(1), participant_name(2), participant_email(3),
# activity(4), timeslot(5), registration_passphrase(6),
# registration_time(7), checked_in(8)
passphrase_verify_section_code = r"""
        st.subheader("Verify by Passphrase & Check-In")

        with st.form("passphrase_verify_form"):
            passphrase_input = st.text_input("Enter 4-word Registration Passphrase (e.g., word-word-word-word):", key="admin_passphrase_input")
            verify_button = st.form_submit_button("Verify Passphrase")

        if verify_button and passphrase_input:
            # Normalize passphrase: lowercase and strip whitespace
            normalized_passphrase = passphrase_input.strip().lower()

            registration = dm.get_registration_by_passphrase(normalized_passphrase) # This is a Row object or None

            if not registration:
                st.error("Invalid or unknown passphrase. Please check the input (format: word-word-word-word).")
            else:
                st.success(f"Registration Found for Passphrase: **{ut.format_passphrase_display(registration[6])}**") # registration_passphrase index 6

                details_cols = st.columns(2)
                details_cols[0].markdown(f"**Name:** {registration[2]}") # participant_name index 2
                details_cols[0].markdown(f"**Email:** {registration[3]}") # participant_email index 3
                details_cols[1].markdown(f"**Activity:** {registration[4]}") # activity index 4
                details_cols[1].markdown(f"**Timeslot:** {registration[5]}") # timeslot index 5

                st.markdown("---")

                if registration[8] == 1: # checked_in index 8
                    st.warning("This participant is already checked-in.")
                else:
                    st.info("Status: Pending Check-In")
                    checkin_button_key = f"passphrase_checkin_{registration[0]}" # id index 0
                    if st.button("Check-In Participant", key=checkin_button_key, type="primary"):
                        if dm.check_in_registration(registration[0]): # id index 0
                            st.success(f"Successfully checked in {registration[2]} for {registration[4]}.") # name index 2, activity index 4
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Check-in failed. The participant might have been checked in by another admin, or a database error occurred.")
        elif verify_button and not passphrase_input:
            st.warning("Please enter a passphrase to verify.")

"""

# Find the placeholder line and the TODO line for replacement
# ABSOLUTELY Corrected re.compile: no comma after pattern string.
placeholder_pattern = re.compile(
    r"st\.write\(\"Placeholder for passphrase verification and check-in functionality\."\)\s*# TODO: Implement as per Plan Step 2"  # NO COMMA HERE
    , re.MULTILINE
)

match = placeholder_pattern.search(content)
if match:
    line_start_index = content.rfind('\n', 0, match.start()) + 1
    leading_whitespace_on_placeholder_line = content[line_start_index : match.start()]

    indented_replacement_lines = []
    for line in passphrase_verify_section_code.strip().split('\n'):
        indented_replacement_lines.append(leading_whitespace_on_placeholder_line + line)
    final_replacement_code = "\n".join(indented_replacement_lines)

    content = placeholder_pattern.sub(final_replacement_code, content, 1)
    print("Replaced passphrase verification placeholder with implementation in show_admin_dashboard_page().")
else:
    raise Exception("Could not find the placeholder for passphrase verification in show_admin_dashboard_page(). Check app.py content.")


with open(app_file_path, 'w') as f:
    f.write(content)

print("Modification script for admin dashboard (Passphrase Verification View) finished.")
