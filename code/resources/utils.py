"""This module provides utility functions for logging, email validation, and URL safety checks."""

import re
import requests

from flask import request
from urllib.parse import urlparse, urljoin


def send_log(level, user, message):
    payload = {"level": level, "user": user, "message": message}
    requests.post("http://host.docker.internal:3330/log", json=payload)


def is_valid_email(email: str) -> bool:
    """
    Verifies the format of the email address.

    Parameters:
        email (str): The email address to be validated.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    return re.match(pattern, email) is not None and email != "temp@svaia.com"


def is_safe_url(target: str) -> bool:
    """
    Verifies if the target URL is safe for redirection.

    Parameters:
        target (str): The target URL to be validated.

    Returns:
        bool: True if the URL is safe, False otherwise.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
