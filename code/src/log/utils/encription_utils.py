

"""
This module provides utility classes for hashing strings using SHA256 or SHA512.
"""

import hashlib

class EncriptionMethod(object):
    """
    Base class for encryption methods.
    This class is not meant to be instantiated directly.
    """

    def __init__(self) -> None:
        raise NotImplementedError("This class is not meant to be instantiated directly.")

    def hash_string(self, input_string: str) -> str:
        """
        Hash a string using the selected hashing method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

class EncriptionUtils(EncriptionMethod):
    """
    Utility class for hashing strings with a chosen method.
    args:
        hashing_method (str): The hashing method to use ('SHA256' or 'SHA512'). Default is 'SHA256'.
    methods:
        hash_string(input_string: str) -> str: Hashes the input string using the selected hashing method.
    """

    def __init__(self, hashing_method: str = 'SHA256') -> None:
        """
        Initialize the HashUtils with a specific hashing method.
        """
        hash_methods = {
            'SHA256': hashlib.sha256,
            'SHA512': hashlib.sha512
        }
        if hashing_method not in hash_methods:
            raise ValueError("Unsupported hashing method. Use 'SHA256' or 'SHA512'.")
        self.hash_func = hash_methods[hashing_method]

    def hash_string(self, input_string: str) -> str:
        """
        Hash a string using the selected hashing method.
        """
        return self.hash_func(input_string.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"<EncriptionUtils using {self.hash_func.__name__}>"
