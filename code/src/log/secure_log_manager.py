"""
This module provides the SecureLogManager class for securely logging events using a hash chain to ensure log integrity.
"""

import logging
from typing import Optional
from .utils.encription_utils import EncriptionMethod, EncriptionUtils
from .utils import basic_utils as bu
import re
from threading import Lock

# Regex para buscar el hash en el log
RE_HASH = r"'([a-fA-F0-9]{64})'"
# Regex para buscar el mensaje en el log
RE_MESSAGE = r"\| '[a-fA-F0-9]{64}': (.*?) \|"

class SecureLogManager(object):
    """
    Class to manage the logging of security events using a secure hash chain.
    """

    def __init__(
        self,
        log_name: str,
        log_file: str,
        encripter: Optional[EncriptionMethod] = None,
        debug_mode: int = 0
    ) -> None:
        self.log_name = log_name
        self.log_file = log_file
        self.encripter = encripter or EncriptionUtils()
        self.debug_mode = debug_mode
        self._lock = Lock()  # Lock for thread safety
        self._debuger_print(f"{self.log_name} - {self.log_file} - {self.encripter} - {self.debug_mode}")
        self.logger = self._configure_logger()

    def _debuger_print(self, message: str) -> None:
        if self.debug_mode:
            print(f"[DEBUG] {message}")

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.log_name)
        logger.setLevel(logging.DEBUG)

        # Elimina handlers previos para evitar duplicación
        if logger.hasHandlers():
            logger.handlers.clear()

        handler = logging.FileHandler(self.log_file, encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s: %(levelname)-8s | %(message)s |', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def initialize_log(self) -> None:
        first_log = None
        if not bu.file_exists(self.log_file):
            bu.create_file(self.log_file)
            self._debuger_print("Fichero creado.")
        if  bu.file_empty(self.log_file):
            time = bu.get_readable_time()
            message = f"Inicialización del log en el tiempo {time}"
            self._write_log("INFO", None, message)
            first_log = self.get_last_log()
        else:
            self._debuger_print("Log ya inicializado, no se requiere inicialización adicional.")
        return first_log

    def _get_last_log_hash(self) -> Optional[str]:
        result = None
        last_log = self.get_last_log()
        if last_log is not None:
            try:
                match = re.search(RE_HASH, last_log)
                if match:
                    result = match.group(1)
            except IndexError:
                pass
        return result

    def _generate_log_message(self, user: Optional[str], message: str) -> str:
        previous_hash = self._get_last_log_hash()
        hash_input = f"{message}{previous_hash}" if previous_hash else message
        new_hash = self.encripter.hash_string(hash_input)
        if user:
            return f"{user} | '{new_hash}': {message}"
        else:
            return f"'{new_hash}': {message}"

    def _write_log(self, level: str, user: Optional[str], message: str) -> None:
        with self._lock:  # Ensure thread safety
            log_message = self._generate_log_message(user, message)
            self.logger.log(getattr(logging, level.upper()), log_message)
            self._debuger_print(f"Logged: {log_message}")

    def log(self, level: str, user: str, message: str) -> None:
        if level.upper() not in ["INFO", "WARNING", "ERROR"]:
            raise ValueError("Invalid log level. Use INFO, WARNING or ERROR.")
        if not user:
            raise ValueError("User cannot be empty.")
        if not message:
            raise ValueError("Message cannot be empty.")
        self._write_log(level.upper(), user, message)

    def get_last_log(self) -> Optional[str]:
        if not bu.file_exists(self.log_file):
            return None
        with open(self.log_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-1].strip() if lines else None

    def _get_hash_chain(self) -> list[str]:
        if not bu.file_exists(self.log_file):
            return []
        with open(self.log_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            result = []
            for line in lines:
                try:
                    # Use regex to extract the hash between single quotes (64 hex chars)
                    match = re.search(RE_HASH, line)
                    if match:
                        result.append(match.group(1))
                except Exception:
                    continue
            return result

    def _get_message_chain(self) -> list[str]:
        if not bu.file_exists(self.log_file):
            return []
        with open(self.log_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            result = []
            for line in lines:
                try:
                    match = re.search(RE_MESSAGE, line)
                    if match:
                        result.append(match.group(1))
                except Exception:
                    continue
            return result

    def verify_hash_chain(self) -> bool:
        hashes = self._get_hash_chain()
        messages = self._get_message_chain()
        if len(hashes) != len(messages):
            self._debuger_print("Mismatch between hash and message chain lengths.")
            return False

        for i in range(1, len(hashes)):
            expected_hash = self.encripter.hash_string(messages[i] + hashes[i - 1])
            if expected_hash != hashes[i]:
                self._debuger_print(f"Hash mismatch at line {i + 1}")
                return False
        return True
