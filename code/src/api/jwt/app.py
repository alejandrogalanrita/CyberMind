import os
import toml
import mariadb

from typing import Optional, Any
from datetime import timedelta

from flask import Flask, Response, request, jsonify, make_response
from flask_cors import CORS
from flask_praetorian import Praetorian
from flask_bcrypt import Bcrypt, check_password_hash

from resources.dbmodel.database_classes import Users
from resources.dbmodel.database_engine import db
from resources.utils import send_log


# Initialize the Flask application
app = Flask(__name__, template_folder="application/templates", static_folder="application/static")

# Load configuration from a TOML file
app.config.from_file("resources/config.toml", load=toml.load)
app.config["JWT_ACCESS_LIFESPAN"] = timedelta(minutes=30)

# Set the CORS configuration
CORS(app, supports_credentials=True, origins=[app.config.get("WEB_URI")])

# Set the secret key for session management
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("URI_TEMPLATE").format(user=db_user, password=db_password)

# Initialize the database connection
db.init_app(app)

# Initialize the Bcrypt instance for password hashing
bcrypt = Bcrypt(app)


# Initialize the Praetorian instance
class CustomPraetorian(Praetorian):
    """Custom Praetorian to support cookie-based token retrieval and RS256"""

    def read_token_from_header(self) -> Optional[str]:
        """Override to read JWT token from cookies if available, otherwise from headers."""
        token = request.cookies.get("access_token")
        if token:
            return token

        return super().read_token_from_header()

    def _verify_password(self, raw_password: str, hashed_password: str) -> bool:
        """
        Override to use Flask-Bcrypt for password verification.

        Parameters:
            raw_password (str): The raw password provided by the user.
            hashed_password (str): The hashed password stored in the database.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(hashed_password, raw_password)

    def _get_jwt_token(self) -> str:
        return request.cookies.get("access_token") or self.extract_jwt_from_header()


guard = CustomPraetorian()
guard.init_app(app, Users)


@app.post("/api/login")
def api_login() -> tuple[str, int] | Response:
    """Handle login for API use"""

    # Get user credentials from the request
    data = request.json
    username = data.get("email")
    password = data.get("password")

    try:
        # Authenticate the user
        user = guard.authenticate(username, password)

        # Create the access token
        access_token = guard.encode_jwt_token(user)
        response = make_response(jsonify({"ok": True}), 200)

        response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Lax", max_age=3600)

        send_log(level="INFO", user=user.email, message=f"User '{user.email}' got the JWT successfully.")

        return response

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
