"""
This module defines the main Flask API application for CyberMind alert management.

It provides RESTful endpoints for creating, retrieving, updating, and deleting user alerts,
as well as sending notification reports via email. The application uses Flask extensions such as
Flask-RESTful for API resource routing and Flask-CORS for cross-origin resource sharing.
Configuration is loaded from a TOML file and environment variables.

Database interactions are managed via SQLAlchemy models and a custom database engine.
Email notifications are sent using SMTP, with support for Markdown-formatted messages.

Endpoints:
    - /alert/set-alert: Create a new alert for a user (POST)
    - /alert/get-alerts: Retrieve alerts for a user (GET)
    - /alert/delete-alert: Delete a user's alert (DELETE)
    - /alert/update-alert: Update an existing alert (PUT)
    - /alert/send-report: Send a report to a user via email (POST)

Dependencies:
    - Flask, Flask-RESTful, Flask-CORS, SQLAlchemy, smtplib, markdown, toml
"""

import os
import smtplib

from email.message import EmailMessage
from typing import Final

import markdown
import toml

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource

from resources.dbmodel.database_classes import AlertPermits, Notifications
from resources.dbmodel.database_engine import db
from resources.utils import send_log

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

# Set the CORS configuration
CORS(app, allow_origins=[app.config.get("WEB_URI"), app.config.get("CHAT_URI")], supports_credentials=True)

# Initialize the Flask-RESTful API
api = Api(app)

# Load email configuration from environment variables
_EMAIL_SERVER: Final = os.environ.get("EMAIL_SERVER", "localhost")
_EMAIL_PORT: Final = int(os.environ.get("EMAIL_PORT"))
_SENDER_EMAIL: Final = os.environ.get("SENDER_EMAIL", "notifications@svaia.com")
_SMTP_USERNAME: Final = os.environ.get("SMTP_USERNAME")
_SMTP_PASSWORD: Final = os.environ.get("SMTP_PASSWORD")


class SetAlert(Resource):
    """Endpoint to set an alert for a user."""

    def post(self) -> tuple[str, int]:
        """Create a new alert for the user."""
        data = request.get_json()
        response = None
        status_code = None

        if not data:
            response = jsonify({"error": "No se han proporcionado datos"})
            status_code = 400
        else:
            user_email = data.get("user_email")
            if not user_email:
                send_log("ERROR", "SetAlert", "Atempt to create alert without user email")
                response = jsonify({"error": "Se requiere un correo"})
                status_code = 400
            else:
                alert_method = data.get("alert_method")
                if not alert_method:
                    send_log("ERROR", user_email, "Attempt to create alert without alert method")
                    response = jsonify({"error": "Se necesita un metodo de alerta"})
                    status_code = 400
                else:
                    alert_frequency = data.get("alert_frequency", "daily")
                    try:
                        alert = AlertPermits(
                            user_email=user_email, alert_method=alert_method, alert_frequency=alert_frequency
                        )
                        db.session.add(alert)
                        db.session.commit()

                        send_log(
                            "INFO",
                            user_email,
                            (f"Alert created with method {alert_method} and frequency {alert_frequency}"),
                        )

                        response = jsonify({"message": "Alerta creada correctamente"})
                        status_code = 201

                    except Exception as e:
                        db.session.rollback()
                        send_log("ERROR", user_email, f"Error creating alert: {str(e)}")
                        response = jsonify({"error": "Error creando la alerta"})
                        status_code = 500

        return response, status_code


api.add_resource(SetAlert, "/alert/set-alert")


class GetAlerts(Resource):
    """Endpoint to retrieve alerts for a user."""

    def get(self) -> tuple[str, int]:
        """Retrieve all alerts for a user."""
        user_email = request.args.get("user_email")
        if not user_email:
            send_log("ERROR", "GetAlerts", "Attempt to retrieve alerts without user email")
            return jsonify({"error": "User email is required"}), 400

        try:
            alerts = AlertPermits.query.filter_by(user_email=user_email).all()
            alert_list = [alert.to_dict() for alert in alerts]
            send_log("INFO", user_email, "Retrieved alerts successfully")

            return jsonify(alert_list), 200

        except Exception:
            send_log("ERROR", user_email, "Error retrieving alerts")

            return jsonify({"error": "Error consiguiendo alertas"}), 500


api.add_resource(GetAlerts, "/alert/get-alerts")


class DeleteAlert(Resource):
    """Endpoint to delete an alert for a user."""

    def delete(self) -> tuple[str, int]:
        """Delete an alert for a user."""
        data = request.get_json()
        response = None
        status_code = None

        if not data:
            response = jsonify({"error": "No se han proporcionado datos"})
            status_code = 400
        else:
            user_email = data.get("user_email")
            alert_id = data.get("alert_id")
            if not user_email or not alert_id:
                send_log("ERROR", "DeleteAlert", "Attempt to delete alert without user email or alert ID")
                response = jsonify({"error": "Correo y ID de usuario son requeridos"})
                status_code = 400
            else:
                try:
                    alert = AlertPermits.query.filter_by(user_email=user_email, id=alert_id).first()
                    if not alert:
                        send_log("ERROR", user_email, f"Alert with ID {alert_id} not found")
                        response = jsonify({"error": "Alerta no encontrada"})
                        status_code = 404
                    else:
                        db.session.delete(alert)
                        db.session.commit()
                        send_log("INFO", user_email, f"Alert with ID {alert_id} deleted successfully")
                        response = jsonify({"message": "Alerta borrada correctamente"})
                        status_code = 200
                except Exception as e:
                    db.session.rollback()
                    send_log("ERROR", user_email, f"Error deleting alert: {str(e)}")
                    response = jsonify({"error": "Error borrando la alerta"})
                    status_code = 500

        return response, status_code


api.add_resource(DeleteAlert, "/alert/delete-alert")


class UpdateAlert(Resource):
    """Endpoint to update an existing alert for a user."""

    _NO_DATA_PROVIDED: Final = "No data provided"

    def put(self) -> tuple[str, int]:
        """Update an existing alert for a user."""
        data = request.get_json()
        response = None
        status_code = None

        if not data:
            response = jsonify({"error": self._NO_DATA_PROVIDED})
            status_code = 400
        else:
            user_email = data.get("user_email")
            alert_id = data.get("alert_id")
            alert_method = data.get("alert_method")
            alert_frequency = data.get("alert_frequency")

            if not user_email or not alert_id:
                send_log("ERROR", "UpdateAlert", "Attempt to update alert without user email or alert ID")
                response = jsonify({"error": "Correo y ID de la alerta son requeridos"})
                status_code = 400
            else:
                try:
                    alert = AlertPermits.query.filter_by(user_email=user_email, id=alert_id).first()
                    if not alert:
                        send_log("ERROR", user_email, f"Alert with ID {alert_id} not found")
                        response = jsonify({"error": "Alerta no encontrada"})
                        status_code = 404
                    elif not alert_method:
                        send_log("ERROR", user_email, "Attempt to update alert without alert method")
                        response = jsonify({"error": "El método de alerta es requerido"})
                        status_code = 400
                    elif not alert_frequency:
                        send_log("ERROR", user_email, "Attempt to update alert without alert frequency")
                        response = jsonify({"error": "La frecuencia de la alerta es requerida"})
                        status_code = 400
                    else:
                        alert.alert_method = alert_method
                        alert.alert_frequency = alert_frequency
                        db.session.commit()
                        send_log("INFO", user_email, f"Alert with ID {alert_id} updated successfully")
                        response = jsonify({"message": "Alerta actualizada correctamente"})
                        status_code = 200
                except Exception:
                    db.session.rollback()
                    send_log("ERROR", user_email, "Error updating alert")
                    response = jsonify({"error": "Error al actualizar la alerta"})
                    status_code = 500

        return response, status_code


api.add_resource(UpdateAlert, "/alert/update-alert")


class SendReport(Resource):
    """Endpoint to send a report to the user via email."""

    def post(self):
        """Send a report to the user via email."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_email = data.get("user_email")
        subject = data.get("subject")
        body = data.get("body")
        project_name = data.get("project_name")

        if not user_email or not subject or not body:
            return jsonify({"error": "Se requieren el correo del usuario, el asunto y el cuerpo"}), 400

        try:
            notification = Notifications(
                user_email=user_email,
                notification_title=subject,
                message=(
                    "Reporte generado exitosamente, puedes revisarlo en tu correo electrónico "
                    "o en la página de chat para más detalles."
                ),
                project_name=project_name,
            )

            db.session.add(notification)
            db.session.commit()

            send_log("INFO", user_email, "Notification logged in database")
            send_mail(user_email, subject, body)
            send_log("INFO", user_email, "Report sent to user's email")

            return {"message": "Report sent successfully"}, 200

        except Exception as e:
            send_log("ERROR", user_email, "Error sending report")
            print(f"Error sending report: {str(e)}", flush=True)
            db.session.rollback()
            return jsonify({"error": "Error al enviar el reporte"}), 500


api.add_resource(SendReport, "/alert/send-report")


def send_mail(user_email: str, subject: str, body: str) -> None:
    """
    Sends an email to the user with the specified subject and body.

    Parameters:
        user_email (str): The email address of the user to send the email to.
        subject (str): The subject of the email.
        body (str): The body of the email in Markdown format.

    Raises:
        Exception: If there is an error sending the email.
    """

    html_body = markdown.markdown(body)

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = _SENDER_EMAIL
        msg["To"] = user_email
        msg.set_content(body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(_EMAIL_SERVER, _EMAIL_PORT) as server:
            server.starttls()
            server.login(_SMTP_USERNAME, _SMTP_PASSWORD)
            server.send_message(msg)
        send_log("INFO", user_email, f"Email sent to user with subject: {subject}")
    except Exception:
        send_log("ERROR", user_email, "Error sending email")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
