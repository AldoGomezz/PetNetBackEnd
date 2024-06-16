"""This module contains database queries for the authentication model"""

from app.models.auth.auth_model import User, db


def db_commit_and_save(obj):
    """Commit and save an object to the database"""
    try:
        db.session.add(obj)
        db.session.commit()
        return obj
    except Exception as e:
        db.session.rollback()
        raise e


def create_user(user_data) -> User:
    """Create a new user"""
    user = User(**user_data)
    return db_commit_and_save(user)


def get_user_by_id(user_id: int) -> User:
    """Get a user by id"""
    try:
        return User.query.filter_by(id=user_id).first()
    except Exception as e:
        raise e


def get_user_by_username(username: str) -> User:
    """Get a user by username"""
    try:
        return User.query.filter_by(username=username).first()
    except Exception as e:
        raise e


def get_user_by_email(email: str) -> User:
    """Get a user by email"""
    try:
        return User.query.filter_by(email=email).first()
    except Exception as e:
        raise e


def get_user_information(user: User) -> dict:
    """Get the user information"""
    try:
        return User.get_json_information(user)
    except Exception as e:
        raise e
