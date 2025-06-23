"""
REST API for SVAIA Web application.

Features:
    Creating, editing & deleting both Users and Projects.
    AI Chat functionality via communication with LLM provider.
"""

# Imports
import os
import re
import time
import json
import toml
import mariadb
import requests
import numpy as np
import traceback
from urllib.parse import urlparse, urljoin
from datetime import datetime
from typing import Optional, Any
from flask import Flask, request, redirect, url_for, jsonify, make_response, current_app
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_praetorian import Praetorian, current_user, auth_required, roles_required

# from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from resources.dbmodel.database_classes import Users, Projects, DeletedProjects, ChatHistory, CVE, Notifications
from resources.dbmodel.database_engine import db

import base64

from resources.utils import send_log

app = Flask(__name__)

# Load configuration from config.toml
app.config.from_file("resources/config.toml", load=toml.load)

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

# Initialize Bcrypt for password hashing
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

def create_admin_user() -> None:
    """
    Creates the default admin user if it does not exist.
    This function checks if the admin user already exists in the database.
    If not, it creates a new admin user with predefined credentials.
    """
    try:
        with app.app_context():
            # Check if the admin user already exists
            email = app.config["ADMIN_EMAIL"]
            admin_user = Users.query.filter_by(email=email).first()
            if not admin_user:
                # Create the admin user
                new_admin = Users(
                    id=1,
                    email=email,
                    user_name="Admin",
                    user_surname="Supremo",
                    user_password=generate_password_hash(app.config["ADMIN_PASS"]),
                    role="admin",
                    active=True,
                )
                db.session.add(new_admin)
                db.session.commit()
    except mariadb.Error as e:
        print(f"Error creating admin, error: {e}", flush=True)

create_admin_user()

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


# Project managing functions
class ProjectCreate(Resource):
    """Handles project creation"""
    @auth_required
    def post(self) -> tuple[str, int]:
        if not current_user().active:
            send_log(
                "ERROR",
                current_user().email,
                "A deleted user attempted to create a project."
            )
            return {"status": "error", "message": "Current user cannot create a project"}, 403

        try:
            date = datetime.now()

            # Obtener datos del formulario
            name = request.form.get("project_name")
            about = request.form.get("about")
            file = request.files.get("project_file")

            print(f"Project name: {name}, About: {about}, File: {file}", flush=True)

            # Obtener etiquetas del formulario
            max_total_vulns = float(request.form.get('max_total_vulns'))
            min_fixable_ratio = float(request.form.get('min_fixable_ratio'))
            max_severity_level = float(request.form.get('max_severity_level'))
            composite_score = float(request.form.get('composite_score'))

            print(f"max_total_vulns: {max_total_vulns}, min_fixable_ratio: {min_fixable_ratio}, max_severity_level: {max_severity_level}, composite_score: {composite_score}", flush=True)

            file_name = file.filename if file else None
            file_data = file.read() if file else None

            new_project = Projects(
                email=current_user().email,
                project_name=name,
                about=about,
                creation_date=date,
                modification_date=date,
                file_name=file_name,
                file_data=file_data,
                max_total_vulns=max_total_vulns,
                min_fixable_ratio=min_fixable_ratio,
                max_severity_level=max_severity_level,
                composite_score=composite_score
            )

            db.session.add(new_project)
            db.session.commit()

            response = {
                "status": "success",
                "message": "Project created",
                "creation_date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "file": file_name,
                "max_total_vulns": max_total_vulns,
                "min_fixable_ratio": min_fixable_ratio,
                "max_severity_level": max_severity_level,
                "composite_score": composite_score
            }

            send_log(
                "INFO",
                current_user().email,
                f"Project '{name}' created successfully."
            )

            return response, 200

        except Exception as e:
            print(f"Error: {e}", flush=True)
            return {"status": "error", "message": "Error creating project"}, 500

api.add_resource(ProjectCreate, "/api/create_project")


class ProjectDelete(Resource):
    """Handles project deletion"""
    @auth_required
    def post(self) -> tuple[str, int]:
        # Check if the user is active
        if not current_user().active:
            send_log(
                "ERROR",
                current_user().email,
                "A deleted user attempted to delete a project."
            )
            return {"status": "error", "message": " Current user cannot delete a project"}, 403

        # Get the project name and email from the request
        if request.is_json:
            data = request.get_json()
            project_name = data.get("project_name")
            email = data.get("email", current_user().email)
            if data.get("old_email"):
                email = data.get("old_email")
        else:
            project_name = request.form.get("project_name")
            email = request.form.get("email", current_user().email)

        # Check if the email is valid and the user is authorized to delete the project
        if email != current_user().email and current_user().role != "admin":
            send_log(
                "ERROR",
                current_user().email,
                f"Unauthorized attempt to delete project '{project_name}' by user '{current_user().email}'."
            )
            return {"status": "error", "message": "No autorizado"}, 403

        # Get the project from the database
        project = Projects.query.filter_by(email=email, project_name=project_name).first()

        if project:
            d_time = datetime.now()
            about = project.about
            creation_date = project.creation_date

            # Create a new DeletedProjects object and delete the project
            project_delete = DeletedProjects(
                email=project.email,
                project_name=project.project_name,
                about=project.about,
                creation_date=project.creation_date,
                deletion_date=d_time,
                file_name=project.file_name,
                file_data=project.file_data,
                report_name=project.report_name,
                report_data=project.report_data,
                report_reasoning=project.report_reasoning,
                max_total_vulns=project.max_total_vulns,
                min_fixable_ratio=project.min_fixable_ratio,
                max_severity_level=project.max_severity_level,
                composite_score=project.composite_score

            )
            db.session.delete(project)
            db.session.add(project_delete)
            db.session.commit()

            # Create response message
            response = {
                "status": "success",
                "message": "Project deleted",
                "email": f"{email}",
                "project_name": f"{project_name}",
                "about": f"{about}",
                "creation_date": f"{creation_date}",
                "deletion_date": d_time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_name": f"{project.file_name}",
                "file_data": f"{project.file_data.decode('utf-8', errors='ignore') if project.file_data else None}",
                "report_name": f"{project.report_name}",
                "report_data": f"{project.report_data.decode('utf-8', errors='ignore')
                                   if project.report_data else None}",
                "report_reasoning": f"{project.report_reasoning.decode('utf-8', errors='ignore') if project.report_reasoning else None}",
                "max_total_vulns": f"{project.max_total_vulns}",
                "min_fixable_ratio": f"{project.min_fixable_ratio}",
                "max_severity_level": f"{project.max_severity_level}",
                "composite_score": f"{project.composite_score}"
            }

            send_log(
                "INFO",
                current_user().email,
                f"Project '{project_name}' deleted successfully."
            )

            return response, 200

        # Error handling
        else:
            return {"status": "error", "message": "Project not found"}, 404

# Register the ProjectDelete resource with the API
api.add_resource(ProjectDelete, "/api/delete_project")


class GetAllProjects(Resource):
    """Retrieves the projects associated with the current user."""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[str, int]:
        projects_list = Projects.query.order_by(Projects.creation_date.desc()).all()

        result = [project.to_dict() for project in projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved all projects successfully."
        )

        return result, 200

# Register the GetAllProjects resorce with the API
api.add_resource(GetAllProjects, "/api/get_all_projects")


class GetAllDeletedProjects(Resource):
    """Retrieves the deleted projects associated with the current user."""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[str, int]:
        deleted_projects_list = DeletedProjects.query.order_by(DeletedProjects.deletion_date.desc()).all()
        result = [project.to_dict() for project in deleted_projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved all deleted projects successfully."
        )

        return result, 200

# Register the GetAllDeletedProjects resource with the API
api.add_resource(GetAllDeletedProjects, "/api/get_all_deleted_projects")


class GetProjects(Resource):
    """Retrieves the projects associated with the current user."""
    @auth_required
    def get(self)  -> tuple[str, int]:
        projects_list = Projects.query.filter_by(email=current_user().email).order_by(Projects.creation_date.desc()).all()
        result = [project.to_dict() for project in projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved projects successfully."
        )

        return result, 200

# Register the GetAllDeletedProjects resource with the API
api.add_resource(GetProjects, "/api/get_projects")


class ProjectEdit(Resource):
    """Handles project editing."""
    @auth_required
    def post(self) -> tuple[str, int]:
        # Check if the user is active
        if current_user().active == False:

            send_log(
                "ERROR",
                current_user().email,
                "A deleted user attempted to edit a project."
            )

            return {"status": "error", "message": "Current user cannot edit a project"}, 403
        try:
            print("1", flush=True)
            print("Request form data:", request.form, flush=True)
            project_name = request.form.get("project_name")
            new_project_name = request.form.get("new_project_name") or None
            new_about = request.form.get("new_about") or None
            new_max_total_vulns = request.form.get('new_max_total_vulns') or None
            new_min_fixable_ratio = request.form.get('new_min_fixable_ratio') or None
            new_max_severity_level = request.form.get('new_max_severity_level') or None
            new_composite_score = request.form.get('new_composite_score') or None

            new_email = None
            if current_user().role == "admin":
                email = request.form.get("email", current_user().email)
                new_email = request.form.get("new_email") or None
            else:
                email = current_user().email

            file = request.files.get("project_file")
            new_file_name = file.filename if file else None
            new_file_data = file.read() if file else None

            # Get the project from the database
            print(f"Email: {email}, Project Name: {project_name}, New Project Name: {new_project_name}, New Email: {new_email}, New About: {new_about}, New File Name: {new_file_name}", flush=True)
            project = Projects.query.filter_by(email=email, project_name=project_name).first()
            print(f"2", project, flush=True)
            if project:
                modification_date = datetime.now()
                if new_project_name is not None:
                    project.project_name = new_project_name
                if new_email is not None and is_valid_email(request.form.get("new_email")):
                    project.email = new_email
                if new_about is not None:
                    project.about = new_about
                project.modification_date = modification_date
                if new_file_name is not None and new_file_data is not None:
                    project.file_name = new_file_name
                    project.file_data = new_file_data
                    project.report_name = None
                    project.report_data = None
                if new_max_total_vulns is not None:
                    project.max_total_vulns = new_max_total_vulns
                if new_max_severity_level is not None:
                    project.max_severity_level = new_max_severity_level
                if new_composite_score is not None:
                    project.composite_score = new_composite_score
                if new_min_fixable_ratio is not None:
                    project.min_fixable_ratio = new_min_fixable_ratio

                # Update the project details
                db.session.commit()
                print("3", flush=True)
                # Create response message
                response = {
                    "status": "success",
                    "message": "Project updated",
                    "modification_date": modification_date.strftime("%Y-%m-%d %H:%M:%S"),
                }

                send_log(
                    "INFO",
                    current_user().email,
                    f"Project '{project_name}' updated successfully."
                )

                return response, 200

            # Error handling
            else:
                return {"status": "error", "message": "Project not found"}, 404

        # Error handling
        except Exception as e:
            send_log(
                    "INFO",
                    current_user().email,
                    f"Failed to update project '{project_name}'"
            )
            return {"status": "error", "message": "Error updating project"}, 500

# Register the ProjectEdit resource with the API
api.add_resource(ProjectEdit, "/api/edit_project")


# User managing functions
class GetAllUsers(Resource):
    """Returns all the registerd users"""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[str, int]:
        # Check if the user is an admin
        if current_user().role != "admin":
            return redirect(url_for("home"))

        users_list = Users.query.order_by(Users.id.desc()).all()
        result = [user.to_dict() for user in users_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved all users successfully."
        )

        return result, 200

api.add_resource(GetAllUsers, "/api/get_all_users")

class UserRegister(Resource):
    """Handles user registration"""
    @auth_required
    @roles_required("admin")
    def post(self) -> Optional[tuple[str, int]]:
        # Check if the user is an admin
        if current_user().role != "admin":

            send_log(
                "ERROR",
                current_user().email,
                "A non-admin user attempted to register a new user."
            )

            return redirect(url_for("home"))
        try:
            email = request.form.get("email")
            if not email or not is_valid_email(email):
                return {"status": "error", "message": "Formato de email inválido"}, 400

            # Check if the role is valid
            role = request.form.get("role").lower()

            if role not in ALLOWED_ROLES:
                return {"status": "error", "message": "Invalid role"}, 400


            # Create a new user
            new_user = Users(
                id=Users.query.count() + 1,
                email=email,
                user_name=request.form.get("user_name"),
                user_surname=request.form.get("user_surname"),
                user_password=generate_password_hash(request.form.get("password")),
                role=role,
                active=True,
            )
            db.session.add(new_user)
            db.session.commit()

            send_log(
                "INFO",
                current_user().email,
                f"User '{email}' created successfully."
            )

            return {"status": "success", "message": "User created"}, 200

        # Error handling
        except Exception as e:
            print(f"Error: {e}", flush=True)
            return {"status": "error", "message": e}, 500

# Register the UserRegister resource with the API
api.add_resource(UserRegister, "/api/register_user")


class UserDelete(Resource):
    """Handles user deletion"""
    @auth_required
    @roles_required("admin")
    def post(self) -> tuple[str, int]|None:
        # Check if the user is an admin
        if current_user().role != "admin":

            send_log(
                "ERROR",
                current_user().email,
                "A non-admin user attempted to delete a user."
            )

            return redirect(url_for("home"))

        data = request.get_json()
        email = data.get("email").strip()

        # Prevent deletion of the default admin user
        if email == "admin@svaia.com":
            send_log(
                "ERROR",
                current_user().email,
                "An attempt was made to delete the admin user."
            )
            return {"status": "error", "message": "No se puede borrar al usuario administrador"}, 400

        # Get the user from the database
        user = Users.query.filter_by(email=email).first()
        if user:
            # Check if the user is active
            if user.active:
                user.active = False
                db.session.commit()
                send_log(
                    "WARNING",
                    current_user().email,
                    f"User '{email}' deleted successfully."
                )
                return {"status": "success", "message": "User deleted"}, 200
            # Error handling
            else:
                send_log(
                    "WARNING",
                    current_user().email,
                    f"Attempt to delete already deleted user '{email}'."
                )
                return {"status": "error", "message": "El usuario ya ha sido eliminado"}, 400

        # Error handling
        else:
            return {"status": "error", "message": "El usuario no se ha encontrado"}, 404

api.add_resource(UserDelete, "/api/delete_user")


# Update email function
@auth_required
def update_email(old_email: str, new_email: str) -> None:
    """
    Updates the email address in the database for both users and projects.
    This function first creates a temporary user with a dummy email address to avoid conflicts
    during the update process. It then updates the email address in both the Users and Projects
    tables. Finally, it deletes the temporary user and commits the changes to the database.
    If any error occurs during the process, it rolls back the changes to maintain data integrity.

    Parameters:
        old_email (str): The old email address to be replaced.
        new_email (str): The new email address to be set.

    Returns:
        None
    """
    try:
        temp_email = "temp@svaia.com"
        temp_user = Users(
            id=Users.query.count() + 1,
            email=temp_email,
            user_name="Temp",
            user_surname="User",
            user_password="temporarypassword",
            role="usuario",
            active=True,
        )
        db.session.add(temp_user)
        db.session.commit()

        db.session.query(Projects).filter(Projects.email == old_email).update(
            {Projects.email: temp_email}, synchronize_session=False
        )

        db.session.query(Users).filter(Users.email == old_email).update({Users.email: new_email})

        db.session.query(Projects).filter(Projects.email == temp_email).update(
            {Projects.email: new_email}, synchronize_session=False
        )

        db.session.delete(temp_user)
        db.session.commit()

        db.session.commit()

    except Exception as e:

        db.session.rollback()
        print(f"Error inesperado: {e}")


class UserEdit(Resource):
    """Handles user editing"""
    @auth_required
    @roles_required("admin")
    def post(self) -> tuple[str, int]|None:
        # Check if the user is an admin
        if current_user().role != "admin":
            send_log(
                "ERROR",
                current_user().email,
                "A non-admin user attempted to edit a user."
            )
            return redirect(url_for("home"))

        data = request.get_json()
        original_email = data.get("original_email", "").strip()

        # Get the user from the database
        user = Users.query.filter_by(email=original_email).first()

        try:
            if user:
                if user.email != "admin@svaia.com":
                    if data.get("password"):
                        user.user_password = generate_password_hash(data["password"], method="pbkdf2:sha256")
                    if data.get("role") and data["role"].lower() in ALLOWED_ROLES:
                        user.role = data["role"].lower().strip()
                    if data.get("user_name"):
                        user.user_name = data["user_name"]
                    if data.get("user_surname"):
                        user.user_surname = data["user_surname"].strip()
                    if data.get("email"):
                        new_email = data["email"].strip()
                        if new_email != original_email:
                            existing_user = Users.query.filter_by(email=new_email).first()
                            if existing_user:
                                return (
                                    {"status": "error", "message": "Este email ya está en uso"},
                                    403,
                                )
                        if not is_valid_email(new_email):
                            return {"status": "error", "message": "Formato de email inválido"}, 403
                        update_email(original_email, new_email)
                        user = Users.query.filter_by(email=new_email).first()
                    if data.get("active") is not None:
                        new_active = True if data.get("active").lower() == "true" else False
                        user.active = new_active
                # Error handling
                else:
                    return (
                        {"status": "error", "message": "El usuario administrador no puede ser modificado"},
                        403,
                    )

                # Update the user details
                db.session.commit()
                print("2", flush=True)

                send_log(
                    "INFO",
                    user.email,
                    f"User '{user.email}' updated successfully."
                )
                print("3", flush=True)

                # Create response message
                response = {
                    "status": "success",
                    "message": "Usuario actualizado correctamente",
                    "active": f"{new_active}".lower(),
                }

                return response, 200

            # Error handling
            else:
                return {"status": "error", "message": "Usuario no encontrado"}, 404

        # Error handling
        except Exception as e:
            print(f"Error: {e}", flush=True)
            # Rollback the session in case of error
            db.session.rollback()
            return {"status": "error", "message": "Error al actualizar el usuario"}, 500

# Register the UserEdit resource with the API
api.add_resource(UserEdit, "/api/edit_user")

class CheckGenerationStatus(Resource):
    """Check the status of a project report generation task."""

    @auth_required
    def get(self):
        """Check the status of a project report generation task."""
        projects = Projects.query.filter_by(email=current_user().email).where(Projects.in_process == True).all()

        return {"projects": [project.project_name for project in projects]}, 200

api.add_resource(CheckGenerationStatus, "/api/check-generation-status")

class CheckGenerationStatusAdmin(Resource):
    """Check the status of a project report generation task."""

    @auth_required
    @roles_required("admin")
    def get(self):
        """Check the status of a project report generation task."""

        projects = Projects.query.where(Projects.in_process == True).all()

        return {"projects": [[project.email, project.project_name] for project in projects]}, 200

api.add_resource(CheckGenerationStatusAdmin, "/api/check-generation-status/admin")

class GetReportData(Resource):
    """Check the status of a project report generation task."""

    @auth_required
    def post(self):
        """Check the status of a project report generation task."""
        if request.is_json:
            data = request.get_json()
            project_name = data.get("project_name")
            user_email = data.get("email", current_user().email)
        project = Projects.query.filter_by(email=user_email, project_name=project_name).first()

        payload = {
            "report_name": project.report_name,
            "report_data": project.report_data.decode('utf-8', errors='ignore') if project.report_data else None,
            "report_reasoning": project.report_reasoning.decode('utf-8', errors='ignore') if project.report_reasoning else None,
        }

        return {"ok": True, "content": payload}, 200

api.add_resource(GetReportData, "/api/get-report-data")

class CVEResource(Resource):
    """Handles CVE data retrieval and embedding"""
    def get(self) -> tuple[str, int]:
        cves = CVE.query.all()
        result = []
        for cve in cves:
            result.append({
                "cve_id": cve.cve_id,
                "description": cve.description,
                "published_date": cve.published_date.isoformat() if cve.published_date else None,
                "last_modified_date": cve.last_modified_date.isoformat() if cve.last_modified_date else None,
                "cvss_score": cve.cvss_score,
                "vector_string": cve.vector_string,
                "severity": cve.severity,
                "cwe_id": cve.cwe_id,
            })

        return result, 200

api.add_resource(CVEResource, "/api/cve")

class GetCriteria(Resource):
    """Handles retrieval of rules for CVE embedding"""
    @auth_required
    def post(self):
        """Check the status of a project report generation task."""
        if request.is_json:
            data = request.get_json()
            project_name = data.get("project_name")
            user_email = data.get("email", current_user().email)
        project = Projects.query.filter_by(email=user_email, project_name=project_name).first()

        payload = {
            "max_total_vulns": project.max_total_vulns,
            "min_fixable_ratio": project.min_fixable_ratio,
            "max_severity_level": project.max_severity_level,
            "composite_score": project.composite_score,
        }

        return {"ok": True, "content": payload}, 200

api.add_resource(GetCriteria, "/api/get-criteria")

class GetUserNotifications(Resource):
    """Handles notifications"""

    @auth_required
    def get(self) -> tuple[str, int]:
        """
        Returns a notification message.
        This is a placeholder for future notification functionality.
        """
        try:
            user_notifications = Notifications.query.filter_by(user_email=current_user().email).all()
            notifications = [notification.to_dict() for notification in user_notifications]
            if not notifications:
                return {"message": "No notifications available"}, 200
            else:
                Notifications.query.filter_by(user_email=current_user().email).update({"is_read": True})
                db.session.commit()
            return {"notifications": notifications}, 200
        except Exception as e:
            traceback.print_exc()
            print(f"Error retrieving notifications: {e}", flush=True)
            return {"message": "Error retrieving notifications"}, 500

api.add_resource(GetUserNotifications, "/api/notification")

class GetAllNotifications(Resource):

    @auth_required
    @roles_required("admin")
    def get(self):
        try:
            user_notifications = Notifications.query.all()
            notifications = [notification.to_dict() for notification in user_notifications]
            if not notifications:
                return {"message": "No notifications available"}, 200
            else:
                Notifications.query.filter_by(user_email=current_user().email).update({"is_read": True})
                db.session.commit()
            return {"notifications": notifications}, 200
        except Exception as e:
            traceback.print_exc()
            print(f"Error retrieving notifications: {e}", flush=True)
            return {"message": "Error retrieving notifications"}, 500

api.add_resource(GetAllNotifications, "/api/notification/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
