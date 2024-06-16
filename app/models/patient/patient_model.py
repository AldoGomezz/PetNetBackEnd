"""Patient class to store patient information."""

from datetime import datetime
from flask import url_for
from pytz import timezone
from app.models.auth.auth_model import db

local_tz = timezone("Etc/GMT+5")


class Patient(db.Model):
    """Patient class to store patient information
    To use this class you need to have a user_id and owner_id
    # may we can set a default owner_id to 1 if the user is not an owner
    """

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    date_of_register = db.Column(db.DateTime, nullable=False, default=datetime.now(local_tz))
    weight = db.Column(db.Float, nullable=False)
    profile_photo = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # this is the id of the veteriniarian
    owner_id = db.Column(db.Integer, db.ForeignKey("owner.id"), nullable=False)  # this is the id of the pet owner
    photos = db.relationship("Photo", backref="patient", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs) -> None:
        self.nickname = kwargs.get("nickname")
        self.age = kwargs.get("age")
        self.weight = kwargs.get("weight")
        self.user_id = kwargs.get("user_id")
        self.owner_id = kwargs.get("owner_id")
        self.profile_photo = kwargs.get("profile_photo")

    def get_information_json(self) -> dict:
        """Return the information of the patient in json format"""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "age": self.age,
            "date_of_register": self.date_of_register.strftime("%Y-%m-%d %H:%M:%S") if self.date_of_register else None,
            "weight": self.weight,
            "profile_photo": (
                url_for("patient.serve_profile_photo", patient_id=self.id, _external=True)
                if self.profile_photo
                else None
            ),
            "user_id": self.user_id,
            "owner_id": self.owner_id,
            "photos": [photo.get_information_json() for photo in self.photos],
        }


class Photo(db.Model):
    """Photo class to store patient photos
    To use this class you need to have a patient_id
    """

    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    date_of_register = db.Column(db.DateTime, nullable=False, default=datetime.now(local_tz))
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)  # this is the id of the pet
    description = db.Column(db.String(255), nullable=True)
    probability = db.Column(db.String(25), nullable=True)
    predicted_class = db.Column(db.String(100), nullable=True)

    def __init__(self, **kwargs) -> None:
        """Initialize the photo object"""
        self.photo = kwargs.get("photo")
        self.filename = kwargs.get("filename")
        self.patient_id = kwargs.get("patient_id")
        self.user_id = kwargs.get("user_id")
        self.description = kwargs.get("description")

        # If probability and predicted_class are not provided, set them to None
        self.probability = kwargs.get("probability", None)
        self.predicted_class = kwargs.get("predicted_class", None)

    def get_information_json(self) -> dict:
        """Return the information of the photo in json format"""
        return {
            "id": self.id,
            "photo": url_for("patient.serve_photo", photo_id=self.id, _external=True),
            "filename": self.filename,
            "date_of_register": self.date_of_register.strftime("%Y-%m-%d %H:%M:%S") if self.date_of_register else None,
            "patient_id": self.patient_id,
            "description": self.description,
            "probability": self.probability,
            "predicted_class": self.predicted_class,
        }


class Owner(db.Model):
    """Owner class to store owner information"""

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(120), nullable=False)
    document = db.Column(db.String(20), nullable=False)  # dni - ruc - passport
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # this is the id of the veterinarian
    patients = db.relationship(
        "Patient", backref="owner", lazy=True, cascade="all, delete-orphan"
    )  # this is the information of the pets he owns.

    def __init__(self, **kwargs) -> None:
        """Initialize the owner object"""
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.email = kwargs.get("email")
        self.phone_number = kwargs.get("phone_number")
        self.document = kwargs.get("document")
        self.user_id = kwargs.get("user_id")

    def get_information_json(self) -> dict:
        """Return the information of the owner in json format"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "document": self.document,
            "patients": [patient.get_information_json() for patient in self.patients],
        }

    def get_json_pdf(self) -> dict:
        """Return the information of the owner in json format"""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "document": self.document,
        }

    def get_email(self) -> str:
        """Return the email of the owner"""
        return self.email
