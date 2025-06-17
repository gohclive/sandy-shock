import re

def validate_name(name):
    """Checks if a name is valid."""
    if name and len(name.strip()) >= 2:
        return True
    return False

def format_passphrase_display(passphrase):
    """Formats the passphrase for display (e.g., capitalize words, join with spaces)."""
    if not passphrase:
        return ""
    return ' '.join(word.capitalize() for word in passphrase.split('-'))

def validate_email(email):
    """Validates an email address using a simple regex pattern."""
    if not email:
        return False
    # Basic regex for email validation: something@something.something
    # This is a common basic pattern, not fully RFC 5322 compliant but good for most cases.
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return False
