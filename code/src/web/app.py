"""
This module defines the main Flask web application for CyberMind.

It handles user authentication (login, logout), session management, and routing for various pages
including the home page, chat, CVE database, notifications, and admin/user panels. The application
uses Flask extensions such as Flask-Bcrypt for password hashing, Flask-Login for user session
management, and Flask-CORS for cross-origin resource sharing. Configuration is loaded from a TOML
file and environment variables.

Database interactions are managed via SQLAlchemy models and a custom database engine. The module
also includes error handlers for common HTTP errors and a session expiration check to enforce
security.

Routes:
    - /login: User login (GET/POST)
    - /logout: User logout
    - /: Home page
    - /chat: Chat page (login required)
    - /cve: CVE database page
    - /panel: Admin/User panel (login required)
    - /notification: Notifications panel (login required)

Error Handlers:
    - 404: Page not found
    - 500: Internal server error

Session Management:
    - Session lifetime is set to 30 minutes.
    - Automatic logout and session clearing after expiration.

Dependencies:
    - Flask, Flask-Bcrypt, Flask-CORS, Flask-Login, SQLAlchemy, mariadb, toml
"""

import os
import time

from typing import Optional
from datetime import timedelta

import mariadb
import toml

from flask import Flask, Response, render_template, request, redirect, url_for, jsonify, session
from flask_bcrypt import Bcrypt, check_password_hash
from flask_cors import CORS
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from resources.dbmodel.database_classes import Users
from resources.dbmodel.database_engine import db
from resources.utils import send_log, is_safe_url

# Initialize the Flask application
app = Flask(__name__, template_folder="application/templates", static_folder="application/static")

# Load configuration from a TOML file
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config.from_file("resources/config.toml", load=toml.load)

# Set the CORS configuration
CORS(app, supports_credentials=True, origins=[app.config.get("DB_URI")])

# Set the secret key for session management
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("URI_TEMPLATE").format(user=db_user, password=db_password)

# Initialize the database connection
db.init_app(app)

# Initialize the Bcrypt instance for password hashing
bcrypt = Bcrypt(app)

# Instantiate the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/login"


@login_manager.user_loader
def load_user(email: str) -> Users:
    """
    Loads the user from the database using the email.

    Parameters:
        email (str): The email address of the user to be loaded.

    Returns:
        Users: The user object if found, None otherwise.
    """

    return Users.query.get(email)


# Login routes
@app.route("/login", methods=["GET", "POST"])
def login() -> tuple[Response, int] | str:
    """
    Handles user login.

    This route supports both GET and POST requests:
        - GET: Renders the login page.
        - POST: Processes the login form submission.
    """

    def handle_get() -> str:
        """Handles GET requests for the login route."""
        next_page = request.args.get("next")
        next_page = "/" if next_page == "None" else next_page

        return render_template("login.html", next=next_page)

    def handle_inactive_user(username: str) -> tuple[Response, int]:
        """Handles the case where the user is inactive."""
        send_log(level="WARNING", user=username, message=f"User {username} attempted to log in but is inactive.")

        return jsonify({"status": "error", "message": "El usuario ha sido eliminado"}), 403

    def handle_successful_login(user: Users, username: str, next_page: str) -> Response | tuple[Response, int]:
        """
        Handles successful login.

        Parameters:
            user (Users): The user object.
            username (str): The username of the user.
            next_page (str): The page to redirect to after login.

        Returns:
            tuple: A tuple containing a JSON response and the HTTP status code.
        """
        login_user(user, remember=False)

        # Make the session permanent
        session.permanent = True

        # Store the cookie creation time
        session["created"] = time.time()

        send_log(level="INFO", user=username, message=f"User '{username}' logged in successfully.")

        if is_safe_url(next_page):
            return jsonify({"status": "success", "url": next_page}), 200
        if request.referrer and is_safe_url(request.referrer):
            return redirect(request.referrer)

        return redirect(url_for("home"))

    def handle_invalid_credentials(username: str) -> tuple[Response, int]:
        """
        Handles invalid login credentials.

        Parameters:
            username (str): The username of the user attempting to log in.
        Returns:
            tuple: A tuple containing a JSON response and the HTTP status code.
        """
        send_log(
            level="ERROR", user=username, message=f"User '{username}' failed to log in due to invalid credentials."
        )
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    if request.method == "GET":
        return handle_get()

    # POST request
    data = request.get_json()
    username = data.get("email")
    user = Users.query.filter_by(email=username).first()

    if user and not user.active:
        response, status = handle_inactive_user(username)
        return response, status

    password = data.get("password")
    if user and check_password_hash(user.user_password, password):
        next_page = data.get("next")
        next_page = "/" if next_page == "None" else next_page
        response, status = handle_successful_login(user, username, next_page)
        return response, status

    response, status = handle_invalid_credentials(username)
    return response, status


@app.route("/logout")
@login_required
def logout() -> Response:
    """Handles user logout."""
    send_log(level="INFO", user=current_user.email, message=f"User '{current_user.email}' logged out successfully.")
    logout_user()

    return redirect(url_for("home"))


# Application routes
@app.get("/")
def home() -> str:
    """Renders the Home page for the web application."""
    return render_template("index.html", user=current_user or None)


@app.route("/chat")
@login_required
def chat() -> str:
    """Renders the Chat page for the web application."""
    return render_template("chat.html", user=current_user or None)


@app.get("/cve")
def cve() -> str:
    """Renders the CVE database page for the web application."""
    return render_template("cve.html", user=current_user or None)


# Admin routes
@app.get("/panel")
@login_required
def panel() -> str:
    """Renders the Admin or User Panel page for the web application."""
    # Check if the user is an admin
    if current_user.role != "admin":
        return render_template("account.html", user=current_user)

    # Get the current user for the template ID
    users = Users.query.order_by(Users.id).all()
    return render_template(
        "admin_panel.html",
        user=current_user,
        users=users,
    )


@app.get("/notification")
@login_required
def notifications() -> str:
    """Renders the notifications panel page for the web application."""
    return render_template("notification.html", user=current_user, user_role=current_user.role)


# Error handling
@app.errorhandler(404)
def page_not_found(e: Exception) -> tuple[Response, int]:
    """Handles 404 errors."""
    return render_template("404.html", user=current_user or None), 404


@app.errorhandler(500)
def internal_server_error(e: Exception) -> tuple[Response, int]:
    """Handles 500 errors."""
    return render_template("500.html", user=current_user), 500


# Request lifecycle management
@app.before_request
def check_cookie_expiration() -> Optional[Response]:
    """Checks if the session cookie has expired and logs out the user if necessary."""
    # Only check when the user is authenticated
    if current_user.is_authenticated:
        created = session.get("created")
        now = time.time()
        # If the cookie was set and 30 minutes (1800 seconds) have passed
        if created and (now - created) > 1800:
            logout_user()
            session.clear()
            return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
