"""
This module defines the main Flask REST API application for CyberMind.

It provides endpoints for managing users, projects, CVE data, notifications, and authentication.
The application uses Flask extensions such as Flask-Bcrypt for password hashing, Flask-CORS for
cross-origin resource sharing, Flask-Praetorian for JWT-based authentication, and Flask-RESTful
for API resource routing. Configuration is loaded from a TOML file and environment variables.

Database interactions are managed via SQLAlchemy models and a custom database engine. The module
also includes utility functions for logging and email validation.

API Endpoints:
    - /api/create-project: Create a new project
    - /api/delete-project: Delete a project
    - /api/get-all-projects: Retrieve all projects (admin only)
    - /api/get-all-deleted-projects: Retrieve all deleted projects (admin only)
    - /api/get-projects: Retrieve projects for the current user
    - /api/edit-project: Edit a project
    - /api/get-all-users: Retrieve all users (admin only)
    - /api/register-user: Register a new user (admin only)
    - /api/delete-user: Delete a user (admin only)
    - /api/edit_user: Edit a user (admin only)
    - /api/check-generation-status: Check report generation status for current user
    - /api/check-generation-status/admin: Check report generation status (admin only)
    - /api/get-report-data: Retrieve report data for a project
    - /api/cve: Retrieve CVE data
    - /api/get-criteria: Retrieve project criteria
    - /api/notification: Retrieve notifications for current user
    - /api/notification/admin: Retrieve all notifications (admin only)

Authentication & Authorization:
    - JWT-based authentication using Flask-Praetorian
    - Role-based access control for admin endpoints

Dependencies:
    - Flask, Flask-Bcrypt, Flask-CORS, Flask-Praetorian, Flask-RESTful, SQLAlchemy, mariadb, toml
"""

import os
import traceback

from datetime import datetime
from typing import Optional

import mariadb
import toml
from flask import Flask, Response, redirect, request, url_for
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from flask_cors import CORS
from flask_praetorian import Praetorian, auth_required, current_user, roles_required
from flask_restful import Api, Resource

from resources.dbmodel.database_classes import CVE, DeletedProjects, Notifications, Projects, Users
from resources.dbmodel.database_engine import db
from resources.utils import send_log, is_valid_email

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

# Initialize the Bcrypt instance for password hashing
bcrypt = Bcrypt(app)

# Set the CORS configuration
CORS(app, supports_credentials=True, origins=[app.config.get("WEB_URI")])

# Initialize Flask RESTful API
api = Api(app)


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


def create_admin_user() -> None:
    """Creates an admin user if it does not already exist."""
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

# Create the admin user if it does not exist
create_admin_user()


# Project managing functions
class CreateProject(Resource):
    """Handles project creation"""
    @auth_required
    def post(self) -> tuple[dict[str, str], int]:
        """Handles the creation of a new project."""
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

            # Obtener etiquetas del formulario
            max_total_vulns = float(request.form.get('max_total_vulns'))
            min_fixable_ratio = float(request.form.get('min_fixable_ratio'))
            max_severity_level = float(request.form.get('max_severity_level'))
            composite_score = float(request.form.get('composite_score'))

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
            send_log(
                "ERROR",
                current_user().email,
                f"Failed to create project '{name}': {str(e)}"
            )
            return {"status": "error", "message": "Error creating project"}, 500

api.add_resource(CreateProject, "/api/create-project")


class DeleteProject(Resource):
    """Handles project deletion"""
    @auth_required
    def post(self) -> tuple[dict[str, str], int]:
        """Handles the deletion of a project."""
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
            send_log(
                "ERROR",
                current_user().email,
                f"Attempt to delete non-existent project '{project_name}' by user '{current_user().email}'."
            )
            return {"status": "error", "message": "Project not found"}, 404


api.add_resource(DeleteProject, "/api/delete-project")


class GetAllProjects(Resource):
    """Retrieves the projects associated with the current user."""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[list[str], int]:
        """Retrieves all projects from the database."""
        projects_list = Projects.query.order_by(Projects.creation_date.desc()).all()
        result = [project.to_dict() for project in projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved all projects successfully."
        )

        return result, 200


api.add_resource(GetAllProjects, "/api/get-all-projects")


class GetAllDeletedProjects(Resource):
    """Retrieves the deleted projects associated with the current user."""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[list[str], int]:
        deleted_projects_list = DeletedProjects.query.order_by(DeletedProjects.deletion_date.desc()).all()
        result = [project.to_dict() for project in deleted_projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved all deleted projects successfully."
        )

        return result, 200


api.add_resource(GetAllDeletedProjects, "/api/get-all-deleted-projects")


class GetProjects(Resource):
    """Retrieves the projects associated with the current user."""
    @auth_required
    def get(self)  -> tuple[list[str], int]:
        """Retrieves all projects associated with the current user."""
        projects_list = Projects.query.filter_by(email=current_user().email).order_by(Projects.creation_date.desc()).all()
        result = [project.to_dict() for project in projects_list]

        send_log(
            "INFO",
            current_user().email,
            "Retrieved projects successfully."
        )

        return result, 200


api.add_resource(GetProjects, "/api/get-projects")


class EditProject(Resource):
    """Handles project editing."""
    @auth_required
    def post(self) -> tuple[dict[str, str], int]:
        # Check if the user is active
        if current_user().active == False:
            send_log(
                "ERROR",
                current_user().email,
                "A deleted user attempted to edit a project."
            )
            return {"status": "error", "message": "Current user cannot edit a project"}, 403

        try:
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
            project = Projects.query.filter_by(email=email, project_name=project_name).first()
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


api.add_resource(EditProject, "/api/edit-project")


# User managing functions
class GetAllUsers(Resource):
    """Returns all the registerd users"""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[list[str], int] | Response:
        """Retrieves all users from the database."""
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


api.add_resource(GetAllUsers, "/api/get-all-users")


class RegisterUser(Resource):
    """Handles user registration"""
    @auth_required
    @roles_required("admin")
    def post(self) -> Optional[tuple[str, int]] | Response:
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

            if role not in app.config.get("ALLOWED_ROLES").split(","): 
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
            send_log(
                "ERROR",
                current_user().email,
                f"Failed to register user '{email}': {str(e)}"
            )
            return {"status": "error", "message": e}, 500


api.add_resource(RegisterUser, "/api/register-user")


class DeleteUser(Resource):
    """Handles user deletion"""
    @auth_required
    @roles_required("admin")
    def post(self) -> tuple[str, int] | Response:
        """Handles the deletion of a user."""
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
            send_log(
                "ERROR",
                current_user().email,
                f"Attempt to delete non-existent user '{email}'."
            )
            return {"status": "error", "message": "El usuario no se ha encontrado"}, 404


api.add_resource(DeleteUser, "/api/delete-user")


class EditUser(Resource):
    """Handles user editing"""
    @auth_required
    @roles_required("admin")
    def post(self) -> tuple[str, int] | Response:
        if current_user().role != "admin":
            send_log(
                "ERROR",
                current_user().email,
                "A non-admin user attempted to edit a user."
            )
            return redirect(url_for("home"))

        data = request.get_json()
        original_email = data.get("original_email", "").strip()
        user = Users.query.filter_by(email=original_email).first()

        try:
            if not user:
                return {"status": "error", "message": "Usuario no encontrado"}, 404

            if user.email == "admin@svaia.com":
                # Allow ONLY password change for the admin account
                new_password = data.get("password")
                if new_password:
                    user.user_password = generate_password_hash(new_password)
                    db.session.commit()
                    send_log("INFO", user.email, "Admin password updated successfully.")
                    return {"status": "success", "message": "Contraseña del administrador actualizada"}, 200
                else:
                    return {"status": "error", "message": "No se proporcionó nueva contraseña"}, 400

            # For other users, allow full update
            if data.get("password"):
                user.user_password = generate_password_hash(data["password"])

            if data.get("role") and data["role"].lower() in app.config.get("ALLOWED_ROLES").split(","):
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
                        return {"status": "error", "message": "Este email ya está en uso"}, 403
                if not is_valid_email(new_email):
                    return {"status": "error", "message": "Formato de email inválido"}, 403
                update_email(original_email, new_email)
                user = Users.query.filter_by(email=new_email).first()

            if data.get("active") is not None:
                user.active = data.get("active").lower() == "true"

            db.session.commit()
            send_log("INFO", user.email, f"User '{user.email}' updated successfully.")

            return {
                "status": "success",
                "message": "Usuario actualizado correctamente",
                "active": str(user.active).lower(),
            }, 200

        except Exception as e:
            send_log(
                "ERROR",
                current_user().email,
                f"Failed to update user '{original_email}': {str(e)}"
            )
            db.session.rollback()
            return {"status": "error", "message": "Error al actualizar el usuario"}, 500


api.add_resource(EditUser, "/api/edit-user")


class CheckGenerationStatus(Resource):
    """Check the status of a project report generation task."""

    @auth_required
    def get(self) -> tuple[dict[str, list[str]], int]:
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
    def post(self) -> tuple[dict[str, str], int]:
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
    def get(self) -> tuple[list[str], int]:
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
    def post(self) -> tuple[dict[str, float], int]:
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
        """Retrieves notifications for the current user."""
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
            return {"message": "Error retrieving notifications"}, 500


api.add_resource(GetUserNotifications, "/api/notification")


class GetAllNotifications(Resource):
    """Handles notifications for admin users"""
    @auth_required
    @roles_required("admin")
    def get(self) -> tuple[list[dict[str, str]], int]:
        """Retrieves all notifications for admin users."""
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
            return {"message": "Error retrieving notifications"}, 500


api.add_resource(GetAllNotifications, "/api/notification/admin")


@auth_required
def update_email(old_email: str, new_email: str) -> None:
    """
    Updates the email of a user and their associated projects.

    Parameters:
        old_email (str): The current email of the user.
        new_email (str): The new email to be set for the user.
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

    except Exception:
        db.session.rollback()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
