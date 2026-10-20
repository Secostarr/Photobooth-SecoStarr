"""Printing module for Photobooth v4.0 (Windows support)."""
import os
import subprocess

def print_photo(file_path):
    """
    Print photo via Windows default print verb.
    This uses the OS default association for image files (e.g., Photos app).
    """
    if not os.path.exists(file_path):
        return False, "File not found."

    try:
        # Use shell execution to trigger default print verb
        # Note: This may open the app briefly or require user confirmation
        os.startfile(file_path, "print")
        return True, "Print command sent."
    except Exception as e:
        return False, str(e)
