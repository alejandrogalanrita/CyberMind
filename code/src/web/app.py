"""
SVAIA Web application that allows clients to track vulnerabilities in package dependencies.

The application takes a SBOM in CycloneDX format and uses a CVE database to locate possible issues.
This database is populated via open APIs like the one from NIST.
An LLM summarises info and provides the client with reports, graphs and possible solutions,
as well as the functionality to set up notifications whenever an issue arises or a patch is available.
"""

# Imports
import os
import re
import time
import toml
import json
import mariadb

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user


from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from urllib.parse import urlparse, urljoin

from resources.dbmodel.database_classes import Users
from resources.dbmodel.database_engine import db

from resources.utils import send_log

import base64

from datetime import timedelta

# Initialize Flask app

app = Flask(__name__, template_folder="application/templates", static_folder="application/static")
CORS(app)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # or any duration

# Load configuration from config.toml
app.config.from_file("resources/config.toml", load=toml.load)
ALLOWED_ROLES = app.config.get("ALLOWED_ROLES").split(",")

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

uri_template = "mariadb+mariadbconnector://{user}:{password}@mariadb:3306/flask_database"

app.config['SQLALCHEMY_DATABASE_URI'] = uri_template.format(
    user=db_user,
    password=db_password
)

# Instantiate the database connection
db.init_app(app)

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)


# Function to check if the email is valid
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


# Function to check if the URL is safe for redirection
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
def login() -> str:
    """Handles user login."""

    # Handle GET request
    if request.method == "GET":
        next_page = request.args.get("next")
        next_page = "/" if next_page == "None" else next_page

        return render_template("login.html", next=next_page)

    # Handle POST request
    else:
        data = request.get_json()

        # Look up the user in the database
        username = data.get("email")
        user = Users.query.filter_by(email=username).first()

        # Check if the user exists and is active
        if user and not user.active:
            registry_manager.log(
                level="WARNING",
                user=username,
                message=f"User {username} attempted to log in but is inactive."
            )
            return jsonify({"status": "error", "message": "El usuario ha sido eliminado"}), 403

        # Get the password from the request
        password = data.get("password")
        if user and check_password_hash(user.user_password, password):
            login_user(user, remember=False)
            session.permanent = True  # Make the session permanent
            session['created'] = time.time()  # Store the cookie creation time

            # Get the next page from the request
            next_page = data.get("next")
            next_page = "/" if next_page == "None" else next_page

            send_log(
                level="INFO",
                user=username,
                message=f"User '{username}' logged in successfully."
            )

            if is_safe_url(next_page):
                return jsonify({"status": "success", "url": next_page}), 200

            elif request.referrer and is_safe_url(request.referrer):
                return redirect(request.referrer)

            else:
                return redirect(url_for("home"))
        else:  # Invalid credentials
            send_log(
                level="ERROR",
                user=username,
                message=f"User '{username}' failed to log in due to invalid credentials."
            )
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route("/logout")
@login_required
def logout() -> str:
    """Handles user logout."""
    send_log(
        level="INFO",
        user=current_user.email,
        message=f"User '{current_user.email}' logged out successfully."
    )
    logout_user()

    return redirect(url_for("home"))


# Application routes
@app.get("/")
def home() -> str:
    """Renders the Home page for the web application."""
    # Get the current user for the template ID
    user = current_user if current_user.is_authenticated else None

    return render_template("index.html", user=user)


@app.route("/chat")
@login_required
def chat() -> str:
    """
    Renders the chat page for the web application
    Calls the get_projects() function to send the projects to the frontend.
    """
    # Get the current user for the template ID
    user = current_user if current_user.is_authenticated else None

    return render_template("chat.html", user=user)

@app.get("/cve")
def cve() -> str:
    """
    Returns a list of CVEs from the database.
    This route is used to fetch CVEs for the frontend.
    """
    user = current_user if current_user.is_authenticated else None

    return render_template("cve.html", user=user)

# Admin routes
@app.get("/panel")
@login_required
def panel() -> str:
    """
    Renders the admin panel for the web application.
    This route is only accessible to admin users.
    The admin panel includes the following features:
        - Displays a list of all users.
        - Displays a list of all projects.
        - Displays a list of all deleted projects.
        - Allows admin users to manage (Create, Update & Delete) Users and Projects.
    """
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
    user = current_user
    return render_template("notification.html", user=user, user_role=user.role)



# Error handling for 404
@app.errorhandler(404)
def page_not_found(e):
    """Handles 404 errors."""
    user = current_user if current_user.is_authenticated else None
    return render_template("404.html", user=user), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handles 500 errors."""
    user = current_user if current_user.is_authenticated else None
    return render_template("500.html", user=user), 500

@app.before_request
def check_cookie_expiration():
    # Only check when the user is authenticated
    if current_user.is_authenticated:
        created = session.get('created')
        now = time.time()
        # If the cookie was set and 30 minutes (1800 seconds) have passed
        if created and (now - created) > 1800:
            logout_user()
            session.clear()
            return redirect(url_for("login"))


@app.after_request
def add_cors_headers(response):
    """Adds CORS headers to the response."""
    response.headers["Access-Control-Allow-Origin"] = "localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
