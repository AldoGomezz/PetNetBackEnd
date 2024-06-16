"""This module contains the database queries for the patient model."""

from sqlalchemy import or_
from app.models.auth.auth_model import db, User
from app.models.patient.patient_model import Owner, Patient, Photo


def db_commit_and_save(obj):
    """Commit and save an object to the database"""
    try:
        db.session.add(obj)
        db.session.commit()
        return obj
    except Exception as e:
        db.session.rollback()
        raise e


def create_new_patient(data: dict) -> Patient:
    """Create a new patient"""
    try:
        patient = Patient(**data)
        return db_commit_and_save(patient)
    except Exception as e:
        raise e


def get_patient_by_id(patient_id: int) -> Patient:
    """Get a patient by id"""
    try:
        return Patient.query.filter_by(id=patient_id).first()
    except Exception as e:
        raise e


def update_patient_information(patient: Patient, data: dict) -> Patient:
    """Update the patient information"""
    try:
        for key, value in data.items():
            setattr(patient, key, value)
        return db_commit_and_save(patient)
    except Exception as e:
        raise e


def update_patient_profile_photo(patient: Patient, profile_photo: str) -> Patient:
    """Update the patient profile photo"""
    try:
        patient.profile_photo = profile_photo
        return db_commit_and_save(patient)
    except Exception as e:
        raise e


def delete_patient_information(patient: Patient) -> None:
    """Delete the patient information"""
    try:
        db.session.delete(patient)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def patient_belong_to_user(patient: Patient, user: User) -> bool:
    """Check if the patient belongs to the user"""
    try:
        if patient.user_id != user.id:
            return False
        return True
    except Exception as e:
        raise e


def create_new_owner(data: dict) -> Owner:
    """Create a new owner"""
    try:
        owner = Owner(**data)
        return db_commit_and_save(owner)
    except Exception as e:
        raise e


def update_owner_info(owner: Owner, data: dict) -> Owner:
    """Update the owner information"""
    try:
        for key, value in data.items():
            setattr(owner, key, value)
        return db_commit_and_save(owner)
    except Exception as e:
        raise e


def delete_owner_information(owner: Owner) -> None:
    """Delete the owner information"""
    try:
        db.session.delete(owner)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def get_owner_by_email(email: str) -> Owner:
    """Get an owner by email"""
    try:
        return Owner.query.filter_by(email=email).first()
    except Exception as e:
        raise e


def get_owner_by_id(owner_id: int) -> Owner:
    """Get an owner by id"""
    try:
        return Owner.query.filter_by(id=owner_id).first()
    except Exception as e:
        raise e


def create_new_photo(data: dict) -> Photo:
    """Create a new photo"""
    try:
        photo = Photo(**data)
        return db_commit_and_save(photo)
    except Exception as e:
        raise e


def get_photo_by_id(photo_id: int) -> Photo:
    """Get a photo by id"""
    try:
        return Photo.query.filter_by(id=photo_id).first()
    except Exception as e:
        raise e


def update_photo_information(photo: Photo, data: dict) -> Photo:
    """Update the photo information"""
    try:
        for key, value in data.items():
            setattr(photo, key, value)
        return db_commit_and_save(photo)
    except Exception as e:
        raise e


def photo_belong_to_user(photo: Photo, user: User) -> bool:
    """Check if the photo belongs to the user"""
    try:
        patients = (patient for patient in user.patients)
        photos = (photo for patient in patients for photo in patient.photos)
        photos_id = [photo.patient_id for photo in photos]

        if photo.id not in photos_id:
            return False
        return True
    except Exception as e:
        raise e


def search_patients_nickname(user: User, search_query: str) -> list:
    """Search for patients"""
    try:
        if search_query == "*":
            return [patient.get_information_json() for patient in user.patients]

        patients = [patient for patient in user.patients if search_query.lower() in patient.nickname.lower()]
        return [patient.get_information_json() for patient in patients]
    except Exception as e:
        raise e


def search_owners_name(user: User, search_query: str) -> list:
    """Search for owners, the search is done by first name and last name"""
    try:
        if search_query == "*":
            return [owner.get_information_json() for owner in user.owners]

        owners = [
            owner
            for owner in user.owners
            if search_query.lower() in owner.first_name.lower() or search_query.lower() in owner.last_name.lower()
        ]

        return [owner.get_information_json() for owner in owners]
    except Exception as e:
        raise e
