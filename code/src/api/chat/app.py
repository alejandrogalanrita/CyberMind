"""
REST API for SVAIA web application.

Features:
    Creating, editing & deleting both Users and Projects.
    AI Chat functionality via communication with LLM provider.
"""

# Imports
import os
import re
import toml
import json

import mariadb
import requests
from datetime import datetime

import faiss
import numpy as np

from typing import Any, Optional
from flask import Flask, request, g, jsonify, make_response, current_app
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_praetorian import Praetorian, auth_required, roles_required, current_user

# from werkzeug.security import check_password_hash
from flask_bcrypt import Bcrypt, check_password_hash

from urllib.parse import urlparse, urljoin

from resources.dbmodel.database_classes import Users, Projects, ChatHistory, CVE
from resources.dbmodel.database_engine import db

import base64

from resources.utils import send_log

app = Flask(__name__)

# Load configuration from config.toml
app.config.from_file("resources/config.toml", load=toml.load)

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

uri_template = "mariadb+mariadbconnector://{user}:{password}@mariadb:3306/flask_database"

app.config["SQLALCHEMY_DATABASE_URI"] = uri_template.format(user=db_user, password=db_password)

db.init_app(app)

# Initialize Flask app
CORS(app, allow_origins=["http://localhost:8080", "http://localhost:11434"], supports_credentials=True)
api = Api(app)

ALLOWED_ROLES = app.config.get("ALLOWED_ROLES").split(",")
CHAT_PROMPT = app.config["CHAT_PROMPT"]
PROMPT = app.config["PROMPT"]

AI_RUNNER_URL = app.config.get("AI_RUNNER_URL")
AI_RUNNER_MODEL = app.config.get("AI_RUNNER_MODEL")
EMBEDDING_URL = app.config.get("EMBEDDING_URL")
EMBEDDING = app.config.get("EMBEDDING")
NOTIFICATION_URL = app.config.get("NOTIFICATION_URL", "http://host.docker.internal:3003") #TODO: Change to the correct URL


# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)


class CustomPraetorian(Praetorian):
    """Custom Praetorian to support cookie-based token retrieval and RS256"""

    def read_token_from_header(self) -> Optional[str]:
        # 1. Try cookie first
        token = request.cookies.get("access_token")
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


# Send Message function for displaying basic utility
class SendMessage(Resource):
    """Handles sending a message in the chat"""

    @auth_required
    def post(self) -> dict[str, Any]:
        """Handles sending a message in the chat"""
        # Get the message from the request
        data = request.json
        message = data.get("message")

        user_email = data.get("user_email")

        received_message = ChatHistory(user_email=user_email, message=message)

        db.session.add(received_message)
        db.session.commit()

        headers = {"Content-Type": "application/json"}

        data = {"model": AI_RUNNER_MODEL, "messages": [{"role": "system", "content": CHAT_PROMPT}]}

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
            response = requests.post(AI_RUNNER_URL, headers=headers, json=data)
            response = json.loads(str(response.content.decode("utf-8")))
            chat_reasoning = response["choices"][0]["message"]["reasoning_content"]
            chat_response = response["choices"][0]["message"]["content"]

            chat_entry = ChatHistory(user_email=user_email, message=chat_response)

            db.session.add(chat_entry)
            db.session.commit()

        except Exception as e:
            print(f"Error: {e}", flush=True)
            return jsonify({"ok": False, "response": str(e)}), 500

        send_log(
            level="INFO",
            user=user_email,
            message=f"User sent the message {{{message}}} and received the response {{{chat_response}}}",
        )

        return {"ok": True, "reasoning": chat_reasoning, "response": chat_response}, 200


# Register the SendMessage resource with the API
api.add_resource(SendMessage, "/chat/send-message")


def send_notification(user_email, subject, message, project_name):
    """
    Sends a notificatton to the /alert/send-report endpoint.
    """
    print(f"Sending notification to {user_email} with subject '{subject}'", flush=True)
    url = f"{NOTIFICATION_URL}/alert/send-report"
    payload = {"user_email": user_email, "subject": subject, "body": message, "project_name": project_name}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending message: {str(e)}", flush=True)
        return None


class GenerateReport(Resource):
    """Handles generating a report from the CVE database"""

    @auth_required
    def post(self) -> dict[str, Any]:
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

        # Save the report to the project
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

            send_notification(user_email, f"Reporte generado para el projecto {project_name}", text,  project_name)

            return {"ok": True, "content": payload}, 200
        else:
            return {"ok": False, "message": "Project not found"}, 404


api.add_resource(GenerateReport, "/chat/generate-report")


@app.before_request
def load_jwt_from_cookie() -> None:
    """Load JWT token from cookie before each request"""
    token = request.cookies.get("access_token")
    if token:
        try:
            g.jwt_user = guard.extract_jwt_token(token)
        except Exception:
            g.jwt_user = None


def generate_cve_embedding():
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
        EMBEDDING_URL, json={"input": text, "model": EMBEDDING}, headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def load_faiss_index():
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


def find_similar_cves(query_texts: list[str], top_k=10) -> list[CVE]:
    """Finds top_k similar CVEs per input using FAISS."""
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
    sbom = json.loads(sbom_json_str)
    return [f"{c['name']} {c.get('version', '')}" for c in sbom.get("components", [])]


def generate_sbom_report(sbom_json: str, tags: Optional[str]) -> str:
    if tags:
        prompt = PROMPT + " You should mention if the following requirements are met: " + tags
    else:
        prompt = PROMPT

    components = extract_component_names(sbom_json)
    matched_cves = find_similar_cves(components)

    headers = {"Content-Type": "application/json"}

    data = {
        "model": AI_RUNNER_MODEL,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": sbom_json + str(matched_cves)}],
    }

    response = requests.post(AI_RUNNER_URL, headers=headers, json=data)

    print(f"Response from AI: {response}", flush=True)

    chat_reasoning = response.json()["choices"][0]["message"]["reasoning_content"]
    chat_response = response.json()["choices"][0]["message"]["content"]

    return chat_reasoning, chat_response


if __name__ == "__main__":
    generate_cve_embedding()
    app.run(host="0.0.0.0", port=80, debug=True)
