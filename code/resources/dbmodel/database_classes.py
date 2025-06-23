from .database_engine import db
from datetime import datetime


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, unique=True)
    email = db.Column(db.String(255), primary_key=True, unique=True, nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_surname = db.Column(db.String(255), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False, default="usuario")
    active = db.Column(db.Boolean, nullable=False, default=True)

    refresh_token = db.Column(db.String(512))
    refresh_token_expires_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def lookup(cls, entry_email: str) -> "Users":
        return cls.query.filter_by(email=entry_email).one_or_none()

    @classmethod
    def identify(cls, entry_email: str) -> "Users":
        return cls.query.filter_by(email=entry_email).one_or_none()

    @property
    def password(self) -> str:
        return self.user_password

    @property
    def identity(self) -> str:
        return self.email

    @property
    def rolenames(self) -> list[str]:
        return [self.role]

    def get_id(self) -> str:
        return self.email

    @property
    def is_authenticated(self) -> bool:
        print("Checking if user is authenticated")
        return True

    @property
    def is_active(self) -> bool:
        return self.active

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def is_anonymous(self) -> bool:
        return False

    def to_dict(self) -> dict[str, any]:
        return {
            "email": self.email,
            "user_name": self.user_name,
            "user_surname": self.user_surname,
            "role": self.role,
            "active": self.active,
            "refresh_token": self.refresh_token,
            "refresh_token_expires_at": (
                self.refresh_token_expires_at.isoformat() if self.refresh_token_expires_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Projects(db.Model):
    __tablename__ = "projects"

    email = db.Column(
        db.String(255),
        nullable=False,
        primary_key=True,
    )
    project_name = db.Column(db.String(255), nullable=False, primary_key=True)

    about = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)
    report_name = db.Column(db.String(255))
    report_data = db.Column(db.LargeBinary)
    report_reasoning = db.Column(db.LargeBinary)
    creation_date = db.Column(db.DateTime, nullable=False)
    modification_date = db.Column(db.DateTime, nullable=False)
    in_process = db.Column(db.Boolean, default=False)
    max_total_vulns = db.Column(db.Float)
    min_fixable_ratio = db.Column(db.Float)
    max_severity_level = db.Column(db.Float)
    composite_score = db.Column(db.Float)

    def to_dict(self) -> dict[str, any]:
        project_dict = {
            "email": self.email,
            "project_name": self.project_name,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "modification_date": self.modification_date.isoformat() if self.modification_date else None,
        }
        if self.about:
            project_dict["about"] = self.about
        if self.file_name:
            project_dict["file_name"] = self.file_name
        if self.file_data:
            # decode safely, ignoring errors
            try:
                project_dict["file_data"] = self.file_data.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["file_data"] = None
        if self.report_name:
            project_dict["report_name"] = self.report_name
        if self.report_data:
            try:
                project_dict["report_data"] = self.report_data.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["report_data"] = None
        if self.report_reasoning:
            try:
                project_dict["report_reasoning"] = self.report_reasoning.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["report_reasoning"] = None
        if self.creation_date:
            project_dict["creation_date"] = self.creation_date.strftime("%Y-%m-%d %H:%M:%S")
        if self.modification_date:
            project_dict["modification_date"] = self.modification_date.strftime("%Y-%m-%d %H:%M:%S")
        if self.in_process:
            project_dict["in_process"] = self.in_process
        if self.max_severity_level:
            project_dict["max_severity_level"] = self.max_severity_level
        if self.min_fixable_ratio:
            project_dict["self.min_fixable_ratio"] = self.min_fixable_ratio
        if self.max_total_vulns:
            project_dict["self.max_total_vulns"] = self.max_total_vulns
        if self.composite_score:
            project_dict["self.composite_score"] = self.composite_score

        return project_dict


class DeletedProjects(db.Model):
    __tablename__ = "deleted_projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False)
    project_name = db.Column(db.String(255), nullable=False)

    about = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)
    report_name = db.Column(db.String(255))
    report_data = db.Column(db.LargeBinary)
    report_reasoning = db.Column(db.LargeBinary)
    creation_date = db.Column(db.DateTime, nullable=False)
    deletion_date = db.Column(db.DateTime, nullable=False)
    max_total_vulns = db.Column(db.Float)
    min_fixable_ratio = db.Column(db.Float)
    max_severity_level = db.Column(db.Float)
    composite_score = db.Column(db.Float)

    def to_dict(self) -> dict[str, any]:
        project_dict = {
            "id": self.id,
            "email": self.email,
            "project_name": self.project_name,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "deletion_date": self.deletion_date.isoformat() if self.deletion_date else None,
        }
        if self.about:
            project_dict["about"] = self.about
        if self.file_name:
            project_dict["file_name"] = self.file_name
        if self.file_data:
            try:
                project_dict["file_data"] = self.file_data.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["file_data"] = None
        if self.report_name:
            project_dict["report_name"] = self.report_name
        if self.report_data:
            try:
                project_dict["report_data"] = self.report_data.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["report_data"] = None
        if self.report_reasoning:
            try:
                project_dict["report_reasoning"] = self.report_reasoning.decode("utf-8", errors="ignore")
            except Exception:
                project_dict["report_reasoning"] = None
        if self.max_severity_level:
            project_dict["max_severity_level"] = self.max_severity_level
        if self.min_fixable_ratio:
            project_dict["self.min_fixable_ratio"] = self.min_fixable_ratio
        if self.max_total_vulns:
            project_dict["self.max_total_vulns"] = self.max_total_vulns
        if self.composite_score:
            project_dict["self.composite_score"] = self.composite_score

        return project_dict


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False)

    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict[str, any]:
        return {
            "id": self.id,
            "project_email": self.project_email,
            "project_name": self.project_name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class CVE(db.Model):
    __tablename__ = "cves"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cve_id = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    published_date = db.Column(db.DateTime)
    last_modified_date = db.Column(db.DateTime)
    cvss_score = db.Column(db.Float)
    vector_string = db.Column(db.String(100))
    severity = db.Column(db.String(20))
    cwe_id = db.Column(db.String(20))
    embedding = db.Column(db.LargeBinary)

    def to_dict(self) -> dict[str, any]:
        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "last_modified_date": self.last_modified_date.isoformat() if self.last_modified_date else None,
            "cvss_score": self.cvss_score,
            "vector_string": self.vector_string,
            "severity": self.severity,
            "cwe_id": self.cwe_id,
        }


class AlertPermits(db.Model):
    __tablename__ = "alert_permits"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False)
    alert_method = db.Column(db.String(50), nullable=False)
    alert_frequency = db.Column(db.String(50), nullable=False, default="daily")
    alert_enabled = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict[str, any]:
        return {
            "id": self.id,
            "user_email": self.user_email,
            "alert_method": self.alert_method,
            "alert_frequency": self.alert_frequency,
            "alert_enabled": self.alert_enabled,
        }


class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    details = db.Column(db.Text, nullable=False)

    def to_dict(self) -> dict[str, any]:
        return {"id": self.id, "details": self.details}


class Notifications(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False)
    notification_title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    project_name = db.Column(db.String(255), nullable=True)

    def to_dict(self) -> dict[str, any]:
        return {
            "id": self.id,
            "user_email": self.user_email,
            "notification_title": self.notification_title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_read": self.is_read,
            "project_name": self.project_name if hasattr(self, 'project_name') else None,
        }
