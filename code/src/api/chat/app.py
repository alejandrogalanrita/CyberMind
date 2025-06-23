"""
This module defines the main Flask API application for CyberMind's chat and report generation services.

It provides RESTful endpoints for chat interactions and SBOM-based report generation, handling user authentication
via JWT tokens (with cookie support) using Flask-Praetorian. The application uses Flask extensions such as
Flask-Bcrypt for password hashing, Flask-CORS for cross-origin resource sharing, and Flask-RESTful for API routing.
Configuration is loaded from a TOML file and environment variables.

Database interactions are managed via SQLAlchemy models and a custom database engine. The module also integrates
with external AI and notification services for chat responses, report generation, and user notifications.
FAISS is used for similarity search on CVE embeddings.

Endpoints:
    - /chat/send-message: Send a chat message and receive an AI-generated response (POST, auth required)
    - /chat/generate-report: Generate a report from SBOM data and CVE analysis (POST, auth required)

Key Features:
    - JWT authentication with support for cookies
    - Password hashing with Flask-Bcrypt
    - Cross-origin resource sharing (CORS)
    - AI-powered chat and report generation via external services
    - CVE embedding and similarity search using FAISS
    - Notification integration for report delivery

Dependencies:
    - Flask, Flask-Bcrypt, Flask-CORS, Flask-Praetorian, Flask-RESTful, SQLAlchemy, mariadb, toml, faiss, numpy, requests
"""

import json
import os
import re

from datetime import datetime
from typing import Any, Optional, Final
from urllib.parse import urlparse, urljoin

import faiss
import mariadb
import numpy as np
import requests
import toml

from flask import Flask, request, g, jsonify
from flask_bcrypt import Bcrypt, check_password_hash
from flask_cors import CORS
from flask_praetorian import Praetorian, auth_required
from flask_restful import Api, Resource

from resources.dbmodel.database_classes import Users, Projects, ChatHistory, CVE
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

# Initialize Flask app
CORS(app, allow_origins=[app.config.get("WEB_URI"), "http://localhost:11434"], supports_credentials=True)

# Initialize Flask RESTful API
api = Api(app)

_CHAT_PROMPT: Final = app.config["CHAT_PROMPT"]
_PROMPT: Final = app.config["PROMPT"]

_AI_RUNNER_URL: Final = app.config.get("AI_RUNNER_URL")
_AI_RUNNER_MODEL: Final = app.config.get("AI_RUNNER_MODEL")
_EMBEDDING_URL: Final = app.config.get("EMBEDDING_URL")
_EMBEDDING: Final = app.config.get("EMBEDDING")
_NOTIFICATION_URL: Final = app.config.get("NOTIFICATION_URL", "http://host.docker.internal:3003")

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


class SendMessage(Resource):
    """Handles sending a message in the chat"""

    @auth_required
    def post(self) -> tuple[dict[str, Any], int]:
        """Handles sending a message in the chat"""
        # Get the message from the request
        data = request.json
        message = data.get("message")
        user_email = data.get("user_email")
        received_message = ChatHistory(user_email=user_email, message=message)

        db.session.add(received_message)
        db.session.commit()

        headers = {"Content-Type": "application/json"}
        data = {"model": _AI_RUNNER_MODEL, "messages": [{"role": "system", "content": _CHAT_PROMPT}]}

        previous_messages = (
            ChatHistory.query.filter_by(
                user_email=user_email,
            )
            .order_by(ChatHistory.timestamp.desc())
            .limit(2)
            .all()
        )

        if len(previous_messages) >= 2:
            previous_question = previous_messages[1]
            previous_answer = previous_messages[0]

            data["messages"].append({"role": "user", "content": previous_question.message})
            data["messages"].append({"role": "assistant", "content": previous_answer.message})

        data["messages"].append({"role": "user", "content": message})

        try:
            # Send the message to the AI API
            response = requests.post(_AI_RUNNER_URL, headers=headers, json=data)
            response = json.loads(str(response.content.decode("utf-8")))
            chat_reasoning = response["choices"][0]["message"]["reasoning_content"]
            chat_response = response["choices"][0]["message"]["content"]

            chat_entry = ChatHistory(user_email=user_email, message=chat_response)

            db.session.add(chat_entry)
            db.session.commit()

        except Exception as e:
            return {"ok": False, "response": "An error ocurred"}, 500

        send_log(
            level="INFO",
            user=user_email,
            message=f"User sent the message {{{message}}} and received the response {{{chat_response}}}",
        )

        return {"ok": True, "reasoning": chat_reasoning, "response": chat_response}, 200


api.add_resource(SendMessage, "/chat/send-message")


class GenerateReport(Resource):
    """Handles generating a report from the CVE database"""

    @auth_required
    def post(self) -> tuple[dict[str, Any], int]:
        """Generates a report based on CVE data"""
        data = request.json
        user_email = data.get("user_email")
        project_name = data.get("project_name")
        project = Projects.query.filter_by(email=user_email, project_name=project_name).first()

        if not project:
            return {"ok": False, "message": "Project not found"}, 404

        sbom = project.file_data.decode("utf-8")
        project.in_process = True
        db.session.commit()

        tags = f"""
            max_total_vulns: No deben haber más de {project.max_total_vulns} vulnerabilidades,
            min_fixable_ratio: Deben de haber al menos {project.min_fixable_ratio} vulnerabilidades solucionables,
            max_severity_level: No deben haber vulnerabilidades con CVSS > {project.max_severity_level},
            composite_score: = La suma de CVSS debe ser <= {project.composite_score}"""

        reasoning, text = generate_sbom_report(sbom, tags)

        # Clean the project name: replace spaces with underscores and remove invalid characters
        cleaned_project_name = re.sub(r"[^a-zA-Z0-9_\-]", "", project_name.replace(" ", "_"))

        project = Projects.query.filter_by(email=user_email, project_name=project_name).first()

        if project:
            project.report_name = f"{cleaned_project_name}_report.txt"
            project.report_data = text.encode("utf-8")
            project.report_reasoning = reasoning.encode("utf-8")
            project.modification_date = datetime.utcnow()
            project.in_process = False

            db.session.commit()

            payload = {
                "project_name": project_name,
                "report_name": project.report_name,
                "report_reasoning": reasoning,
                "report_data": text,
            }

            send_log(
                level="INFO",
                user=user_email,
                message=f"User generated a report for project '{project_name}' as '{project.report_name}'",
            )

            send_notification(user_email, f"Reporte generado para el projecto {project_name}", text, project_name)

            return {"ok": True, "content": payload}, 200
        else:
            return {"ok": False, "message": "Project not found"}, 404


api.add_resource(GenerateReport, "/chat/generate-report")


def send_notification(user_email: str, subject: str, message: str, project_name: str) -> Optional[dict[str, Any]]:
    """
    Sends a notification message to the user via the notification service.

    Parameters:
        user_email (str): The email of the user to notify.
        subject (str): The subject of the notification.
        message (str): The message content to send.
        project_name (str): The name of the project related to the notification.

    Returns:
        dict: The response from the notification service, or None if an error occurs.
    """

    url = f"{_NOTIFICATION_URL}/alert/send-report"
    payload = {"user_email": user_email, "subject": subject, "body": message, "project_name": project_name}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "message": "Failed to send notification"}


def generate_cve_embedding() -> None:
    """Generates embeddings for all CVEs in the database."""
    cve_entries = CVE.query.all()
    for cve in cve_entries:
        if cve.embedding is None:
            try:
                embedding = generate_embedding(cve.description)
                cve.embedding = json.dumps(embedding).encode("utf-8")
                db.session.commit()
            except Exception as e:
                print(f"Error generating embedding for {cve.cve_id}: {e}", flush=True)


def generate_embedding(text: str) -> list[float]:
    """Generates an embedding using OpenAI-compatible endpoint (local)."""
    response = requests.post(
        _EMBEDDING_URL, json={"input": text, "model": _EMBEDDING}, headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()

    return response.json()["data"][0]["embedding"]


def load_faiss_index() -> tuple[Optional[faiss.IndexFlatL2], list[int]]:
    """Loads the FAISS index from the database."""
    cve_entries = CVE.query.filter(CVE.embedding != None).all()
    vectors = []
    ids = []
    for cve in cve_entries:
        vec = json.loads(cve.embedding.decode("utf-8"))
        vectors.append(vec)
        ids.append(cve.id)

    if not vectors:
        return None, []

    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype("float32"))
    return index, ids


def find_similar_cves(query_texts: list[str], top_k: int = 10) -> list[CVE]:
    """
    Finds top_k similar CVEs per input using FAISS.

    Parameters:
        query_texts (list[str]): List of texts to search for similar CVEs.
        top_k (int): Number of top similar CVEs to return.

    Returns:
        list[CVE]: List of CVE objects that match the query texts.
    """
    query_embeddings = [generate_embedding(txt) for txt in query_texts]
    index, cve_ids = load_faiss_index()

    if not index:
        return []

    _, matches = index.search(np.array(query_embeddings).astype("float32"), top_k)
    matched_ids = set()
    for match_list in matches:
        for idx in match_list:
            matched_ids.add(cve_ids[idx])

    return CVE.query.filter(CVE.id.in_(list(matched_ids))).all()


def extract_component_names(sbom_json_str: str) -> list[str]:
    """
    Extracts component names and versions from the SBOM JSON string.

    Parameters:
        sbom_json_str (str): The SBOM JSON string.

    Returns:
        list[str]: A list of component names and versions.
    """
    sbom = json.loads(sbom_json_str)
    return [f"{c['name']} {c.get('version', '')}" for c in sbom.get("components", [])]


def generate_sbom_report(sbom_json: str, tags: Optional[str]) -> tuple[str, str]:
    """
    Generates a report based on the SBOM JSON and optional tags.

    Parameters:
        sbom_json (str): The SBOM JSON string.
        tags (Optional[str]): Optional tags to include in the prompt.

    Returns:
        tuple: A tuple containing the reasoning and the response from the AI.
    """
    if tags:
        prompt = _PROMPT + " You should mention if the following requirements are met: " + tags
    else:
        prompt = _PROMPT

    components = extract_component_names(sbom_json)
    matched_cves = find_similar_cves(components)

    headers = {"Content-Type": "application/json"}

    data = {
        "model": _AI_RUNNER_MODEL,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": sbom_json + str(matched_cves)}],
    }

    response = requests.post(_AI_RUNNER_URL, headers=headers, json=data)

    chat_reasoning = response.json()["choices"][0]["message"]["reasoning_content"]
    chat_response = response.json()["choices"][0]["message"]["content"]

    return chat_reasoning, chat_response


# Request lifecycle management
@app.before_request
def load_jwt_from_cookie() -> None:
    """Load JWT token from cookie before each request"""
    token = request.cookies.get("access_token")
    if token:
        try:
            g.jwt_user = guard.extract_jwt_token(token)
        except Exception:
            g.jwt_user = None


if __name__ == "__main__":
    generate_cve_embedding()
    app.run(host="0.0.0.0", port=80, debug=True)
