"""
Utility functions for file operations and time formatting.
"""

import os
from datetime import datetime, timezone

def file_exists(file: str) -> bool:
    """
    Checks if a file exists in the file system.
    Parameters:
        file (str): Path of the file to check.
    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.exists(file)

def file_empty(file: str) -> bool:
    """
    Checks if a file is empty.
    Parameters:
        file (str): Path of the file to check.
    Returns:
        bool: True if the file is empty, False otherwise.
    """
    return os.path.getsize(file) == 0

def create_file(file: str) -> None:
    """
    Creates a file if it does not exist.
    Parameters:
        file (str): Path of the file to create.
    Returns:
        None
    """
    if not file_exists(file):
        with open(file, 'w', encoding="utf-8"):
            pass

def get_readable_time() -> str:
    """
    Returns the current time in a readable format.
    Parameters:
        None
    Returns:
        str: Current time in the format "YYYY-MM-DD HH:MM:SS UTC".
    """
    # Get the current time in UTC
    utc_time = datetime.now(timezone.utc)

    # Format the time in UTC with the timezone
    readable_time = utc_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    return readable_time
