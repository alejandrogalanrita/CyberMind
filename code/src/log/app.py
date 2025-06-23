import os
from datetime import datetime
import toml
from flask import Flask, request, redirect, url_for, jsonify, make_response, current_app
from flask_cors import CORS
from flask_restful import Api, Resource

from .secure_log_manager import SecureLogManager
from resources.dbmodel.database_classes import Log
from resources.dbmodel.database_engine import db

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
CORS(app, allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:3300", "http://localhost:3030", "http://localhost:3003"], supports_credentials=True)
api = Api(app)


REGISTRY_FILE = app.config.get("REGISTRY_FILE", "registry.log")

# Crear instancia del log manager
registry_manager = SecureLogManager(log_name="secure_registry", log_file=REGISTRY_FILE, debug_mode=0)

# Inicializar el log
first_log = registry_manager.initialize_log()

if first_log:
    print(f"Log inicializado con el primer registro: '{first_log}'", flush=True)

    with app.app_context():
        # Guardar el primer log en la base de datos
        log_db = Log(
            details=first_log
        )
        db.session.add(log_db)
        db.session.commit()

# Verificar la cadena de hashes al inicio
if registry_manager.verify_hash_chain():
    print(f"El log del fichero '{REGISTRY_FILE}' está intacto.", flush=True)
else:
    print(f"El log del fichero '{REGISTRY_FILE}' ha sido modificado o está corrupto.", flush=True)


class AddLog(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({"error": "Invalid input"}), 400

            message = data['message']
            user = data.get('user', 'anonymous')
            level = data.get('level', 'INFO').upper()

            # Log the message
            registry_manager.log(level, user, message)

            log_entry = registry_manager.get_last_log()

            log_db = Log(
                details=log_entry
            )
            db.session.add(log_db)
            db.session.commit()

        except Exception as e:
            print(f"Error adding log: {str(e)}", flush=True)


api.add_resource(AddLog, '/log')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
