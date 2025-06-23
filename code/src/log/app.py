"""
This module defines the main Flask web application for the secure logging system in CyberMind.

It sets up the Flask app, loads configuration from a TOML file and environment variables, and
initializes extensions such as Flask-CORS and Flask-RESTful. The application manages a secure
append-only log using the SecureLogManager, storing log entries both in a file and in a database
via SQLAlchemy models.

Key Features:
    - Secure, tamper-evident logging with hash chain verification.
    - RESTful API endpoint (/log) for adding log entries.
    - CORS support for multiple frontend origins.
    - Database integration for persistent log storage.

Initialization:
    - Loads configuration and database credentials.
    - Initializes the secure log and verifies its integrity.
    - Adds the first log entry to the database if needed.

Dependencies:
    - Flask, Flask-CORS, Flask-RESTful, SQLAlchemy, toml

Usage:
    - Run this module to start the Flask application and expose the /log endpoint.
"""

import os
from typing import Final

import toml

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource

from .secure_log_manager import SecureLogManager
from resources.dbmodel.database_classes import Log
from resources.dbmodel.database_engine import db

# Initialize the Flask application
app = Flask(__name__)

# Load configuration from a TOML file
app.config.from_file("resources/config.toml", load=toml.load)

# Set the secret key for session management
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("URI_TEMPLATE").format(user=db_user, password=db_password)

# Initialize the database connection
db.init_app(app)

# Initialize Flask app
CORS(
    app,
    allow_origins=[
        app.config.get("WEB_URI"),
        app.config.get("LOGIN_URI"),
        app.config.get("CHAT_URI"),
        app.config.get("DB_URI"),
        app.config.get("ALERT_URI"),
    ],
    supports_credentials=True,
)

# Initialize Flask-RESTful API
api = Api(app)

# Initialize the SecureLogManager

_REGISTRY_FILE: Final = app.config.get("REGISTRY_FILE", "registry.log")

registry_manager = SecureLogManager(log_name="secure_registry", log_file=_REGISTRY_FILE, debug_mode=0)

first_log = registry_manager.initialize_log()
if first_log:
    print(f"Log inicializado con el primer registro: '{first_log}'", flush=True)

    with app.app_context():
        # Add the first log entry to the database
        log_db = Log(details=first_log)
        db.session.add(log_db)
        db.session.commit()

# Verify the integrity of the log file
if registry_manager.verify_hash_chain():
    print(f"El log del fichero '{_REGISTRY_FILE}' está intacto.", flush=True)
else:
    print(f"El log del fichero '{_REGISTRY_FILE}' ha sido modificado o está corrupto.", flush=True)


class AddLog(Resource):
    """Resource to add a log entry to the secure log."""

    def post(self):
        """Handles POST requests to add a log entry."""
        try:
            data = request.get_json()
            if not data or "message" not in data:
                return jsonify({"error": "Invalid input"}), 400

            message = data["message"]
            user = data.get("user", "anonymous")
            level = data.get("level", "INFO").upper()

            # Log the message
            registry_manager.log(level, user, message)
            log_entry = registry_manager.get_last_log()
            log_db = Log(details=log_entry)
            db.session.add(log_db)
            db.session.commit()

        except Exception as e:
            print(f"Error adding log: {str(e)}", flush=True)


api.add_resource(AddLog, "/log")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
