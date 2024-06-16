"""This module contains the User class which is used to store user information in the database"""

from datetime import datetime, timedelta
from pytz import timezone
import jwt
from flask import current_app as app
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer


db = SQLAlchemy()


def get_serializer():
    """Get the serializer"""
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


class User(db.Model):
    """User class to store user information"""

    id = db.Column(db.Integer, primary_key=True)
    profile_picture = db.Column(db.Text, nullable=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    clinic = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=True)
    college_number = db.Column(db.String(120), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    patients = db.relationship("Patient", backref="user", lazy=True)
    owners = db.relationship("Owner", backref="owner", lazy=True)

    def __init__(self, **kwargs) -> None:
        """Initialize the user object"""
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.email = kwargs.get("email")
        self.clinic = kwargs.get("clinic")
        self.address = kwargs.get("address")
        self.college_number = kwargs.get("college_number")
        self.username = kwargs.get("username")
        self.password = generate_password_hash(kwargs.get("password"))

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @staticmethod
    def check_passwords_equal(password, confirm_password) -> bool:
        """Check if the password is correct"""
        return password == confirm_password

    @staticmethod
    def generate_confirmation_token(user_id, new_mail=None) -> str:
        """Generate a confirmation token"""
        serializer = get_serializer()
        payload = {"user_id": user_id, "new_mail": new_mail}
        return serializer.dumps(payload, salt="email-confirm")

    @staticmethod
    def confirm_token(token: str, expiration=3600) -> str:
        """Confirm the token"""
        try:
            serializer = get_serializer()
            payload = serializer.loads(token, salt="email-confirm", max_age=expiration)
            user_id = payload.get("user_id")
            new_mail = payload.get("new_mail")
        except Exception as _:
            return None
        return user_id, new_mail

    @staticmethod
    def generate_code_verification(code, user_id, expiration_minutes=10) -> str:
        """Generate a confirmation token"""
        local_tz = timezone("Etc/GMT+5")
        expiration = datetime.now(local_tz) + timedelta(minutes=expiration_minutes)
        payload = {"code": code, "user_id": user_id, "exp": expiration}
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        return token

    @staticmethod
    def validate_code_verification(token):
        """Confirm the token"""
        try:
            local_tz = timezone("Etc/GMT+5")
            # b64encode
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            code = payload.get("code")
            user_id = payload.get("user_id")
            expiration = payload.get("exp")
            expiration_datetime = datetime.fromtimestamp(expiration, tz=local_tz)
            if expiration_datetime < datetime.now(local_tz):
                return None
            return code, user_id
        except jwt.ExpiredSignatureError:
            # The token is expired
            return None
        except (jwt.InvalidTokenError, KeyError):
            # The token is invalid
            return None

    def update_user(self, data: dict) -> None:
        """Update the user information"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: {key} is not an attribute of User")

    def check_password(self, password: str) -> bool:
        """Check if the password is correct"""
        return check_password_hash(self.password, password)

    def validate_confirmed(self) -> bool:
        """Check if the user is confirmed"""
        return self.confirmed

    def get_json_information(self) -> dict:
        """Get the user information as a dictionary"""
        return {
            "user_id": self.id,
            "profile_picture": (
                url_for("user.serve_profile_picture", user_id=self.id, _external=True) if self.profile_picture else None
            ),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "clinic": self.clinic,
            "address": self.address,
            "college_number": self.college_number,
            "username": self.username,
            "confirmed": self.confirmed,
            "patients": [patient.get_information_json() for patient in self.patients],
        }

    def get_json_pdf(self) -> dict:
        """Get the user information as a dictionary"""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "clinic": self.clinic,
            "address": self.address,
            "college_number": self.college_number,
        }
