"""login api endpoint for jwt authentication"""

# Imports
import os
import re
import time
import json
import toml
import mariadb
import requests
import numpy as np

from urllib.parse import urlparse, urljoin
from datetime import datetime
from typing import Optional, Any
from flask import Flask, request, redirect, url_for, jsonify, make_response, current_app
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_praetorian import Praetorian, current_user, auth_required, roles_required

from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from resources.dbmodel.database_classes import Users, Projects, DeletedProjects, ChatHistory, CVE
from resources.dbmodel.database_engine import db

from resources.utils import send_log

import base64

from datetime import timedelta

app = Flask(__name__)

# Load configuration from config.toml
app.config.from_file("resources/config.toml", load=toml.load)
app.config['JWT_ACCESS_LIFESPAN'] = timedelta(minutes=30)

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

uri_template = "mariadb+mariadbconnector://{user}:{password}@mariadb:3306/flask_database"

app.config['SQLALCHEMY_DATABASE_URI'] = uri_template.format(
    user=db_user,
    password=db_password
)

# Instantiate the database connection
db.init_app(app)

# Initialize Flask app
CORS(app, allow_origins=["http://localhost:8080"], supports_credentials=True)
api = Api(app)

ALLOWED_ROLES = app.config.get("ALLOWED_ROLES").split(",")

# Initialize bcrypt for password hashing
bcrypt = Bcrypt(app)


class CustomPraetorian(Praetorian):
    """Custom Praetorian to support cookie-based token retrieval and RS256"""

    def read_token_from_header(self) -> Optional[str]:
        # 1. Try cookie first
        token = request.cookies.get('access_token')
        if token:
            return token
        # 2. Fallback to header
        return super().read_token_from_header()

    def _verify_password(self, raw_password: str, hashed_password: str) -> bool:
        # Optional: Override if needed
        return check_password_hash(hashed_password, raw_password)

    def _get_jwt_token(self) -> str:
        return request.cookies.get("access_token") or self.extract_jwt_from_header()

guard = CustomPraetorian()
guard.init_app(app, Users)

@app.post('/api/login')
def api_login() -> dict[str, Any]:
    """Handle login for API use"""

    # Get user credentials from the request
    data = request.json
    username = data.get('email')
    password = data.get('password')

    try:
        # Authenticate the user
        user = guard.authenticate(username, password)

        # Create the access token
        access_token = guard.encode_jwt_token(user)
        response = make_response(jsonify({"ok": True}), 200)

        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=3600
        )

        send_log(
            level="INFO",
            user=user.email,
            message=f"User '{user.email}' got the JWT successfully."
        )

        return response

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
