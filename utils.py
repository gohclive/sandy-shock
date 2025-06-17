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
