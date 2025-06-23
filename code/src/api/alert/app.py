import os
from datetime import datetime
import toml
from typing import Optional
from flask import Flask, request, redirect, url_for, jsonify, make_response, current_app
from flask_cors import CORS
from flask_restful import Api, Resource

from resources.dbmodel.database_classes import AlertPermits, Notifications
from resources.dbmodel.database_engine import db

from resources.utils import send_log

import smtplib
from email.message import EmailMessage

import markdown

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
CORS(app, allow_origins=["http://localhost:8080", "http://localhost:3300"], supports_credentials=True)
api = Api(app)

EMAIL_SERVER = os.environ.get("EMAIL_SERVER", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "notifications@svaia.com")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


class SetAlert(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se han proporcionado datos"}), 400

        user_email = data.get('user_email')
        if not user_email:
            send_log("ERROR", "SetAlert", "Atempt to create alert without user email")
            return jsonify({"error": "Se requiere un correo"}), 400
        alert_method = data.get('alert_method')
        if not alert_method:
            send_log("ERROR", user_email, "Attempt to create alert without alert method")
            return jsonify({"error": "Se necesita un metodo de alerta"}), 400
        alert_frequency = data.get('alert_frequency', "daily")

        try:
            alert = AlertPermits(
                user_email=user_email,
                alert_method=alert_method,
                alert_frequency=alert_frequency
            )
            db.session.add(alert)
            db.session.commit()

            send_log(
                "INFO",
                user_email,
                (
                    f"Alert created with method {alert_method} "
                    f"and frequency {alert_frequency}"
                )
            )

            return jsonify({"message": "Alerta creada correctamente"}), 201
        except Exception as e:
            db.session.rollback()
            send_log("ERROR", user_email, f"Error creating alert: {str(e)}")
            return jsonify({"error": "Error creando la alerta"}), 500

api.add_resource(SetAlert, '/alert/set-alert')

class GetAlerts(Resource):
    def get(self):
        user_email = request.args.get('user_email')
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

api.add_resource(GetAlerts, '/alert/get-alerts')

class DeleteAlert(Resource):
    def delete(self):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se han proporcionado datos"}), 400

        user_email = data.get('user_email')
        alert_id = data.get('alert_id')
        if not user_email or not alert_id:
            send_log("ERROR", "DeleteAlert", "Attempt to delete alert without user email or alert ID")
            return jsonify({"error": "Correo y ID de usuario son requeridos"}), 400

        try:
            alert = AlertPermits.query.filter_by(user_email=user_email, id=alert_id).first()
            if not alert:
                send_log("ERROR", user_email, f"Alert with ID {alert_id} not found")
                return jsonify({"error": "Alerta no encontrada"}), 404

            db.session.delete(alert)
            db.session.commit()

            send_log("INFO", user_email, f"Alert with ID {alert_id} deleted successfully")

            return jsonify({"message": "Alerta borrada correctamente"}), 200
        except Exception as e:
            db.session.rollback()
            send_log("ERROR", user_email, f"Error deleting alert: {str(e)}")
            return jsonify({"error": "Error borrando la alerta"}), 500

api.add_resource(DeleteAlert, '/alert/delete-alert')

class UpdateAlert(Resource):
    def put(self):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_email = data.get('user_email')
        alert_id = data.get('alert_id')
        alert_method = data.get('alert_method')
        alert_frequency = data.get('alert_frequency')

        if not user_email or not alert_id:
            send_log("ERROR", "UpdateAlert", "Attempt to update alert without user email or alert ID")
            return jsonify({"error": "Correo y ID de la alerta son requeridos"}), 400

        try:
            alert = AlertPermits.query.filter_by(user_email=user_email, id=alert_id).first()
            if not alert:
                send_log("ERROR", user_email, f"Alert with ID {alert_id} not found")
                return jsonify({"error": "Alerta no encontrada"}), 404

            if alert_method:
                alert.alert_method = alert_method
            else:
                send_log("ERROR", user_email, "Attempt to update alert without alert method")
                return jsonify({"error": "El método de alerta es requerido"}), 400
            if alert_frequency:
                alert.alert_frequency = alert_frequency
            else:
                send_log("ERROR", user_email, "Attempt to update alert without alert frequency")
                return jsonify({"error": "La frecuencia de la alerta es requerida"}), 400

            db.session.commit()

            send_log(
                "INFO",
                user_email,
                f"Alert with ID {alert_id} updated successfully"
            )

            return jsonify({"message": "Alerta actualizada correctamente"}), 200
        except Exception:
            db.session.rollback()
            send_log("ERROR", user_email, "Error updating alert")
            return jsonify({"error": "Error al actualizar la alerta"}), 500

api.add_resource(UpdateAlert, '/alert/update-alert')

def send_mail(user_email, subject, body):
    """Function to send an email notification."""

    html_body = markdown.markdown(body)

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg.set_content(body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        send_log("INFO", user_email, f"Email sent to user with subject: {subject}")
    except Exception:
        send_log("ERROR", user_email, f"Error sending email")

# Resource to send instant email notifications from other resources, in the future this will be secured and exposed as an API endpoint
class SendReport(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            print("No data provided", flush=True)
            return jsonify({"error": "No data provided"}), 400

        user_email = data.get('user_email')
        subject = data.get('subject')
        body = data.get('body')
        project_name = data.get('project_name')

        if not user_email or not subject or not body:
            print("Faltan datos", flush=True)
            return jsonify({"error": "Se requieren el correo del usuario, el asunto y el cuerpo"}), 400

        try:
            notification = Notifications(
                user_email=user_email,
                notification_title=subject,
                message="Reporte generado exitosamente, puedes revisarlo en tu correo electrónico o en la página de chat para más detalles.",
                project_name=project_name
            )

            print("Objeto creado", flush=True)
            db.session.add(notification)
            db.session.commit()
            print("Objeto guardado en la base de datos", flush=True)
            send_log("INFO", user_email, "Notification logged in database")
            print("Enviando correo", flush=True)
            send_mail(user_email, subject, body)
            print("Correo enviado", flush=True)
            send_log("INFO", user_email, "Report sent to user's email")

            return {"message": "Report sent successfully"}, 200
        except Exception  as e:
            send_log("ERROR", user_email, "Error sending report")
            print(f"Error sending report: {str(e)}", flush=True)
            db.session.rollback()
            return {"error": "Error al enviar el reporte"}, 500
api.add_resource(SendReport, '/alert/send-report')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
