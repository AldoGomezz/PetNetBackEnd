""" This module contains helper functions for database queries with User objects"""

from werkzeug.security import generate_password_hash
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


def update_user_info(user: User, data: dict) -> User:
    """Update user information"""
    try:
        user.update_user(data)
        return db_commit_and_save(user)
    except Exception as e:
        raise e


def update_user_password(user: User, data: dict) -> User:
    """Update user password"""
    try:
        user.password = generate_password_hash(data["confirm_password"])
        return db_commit_and_save(user)
    except Exception as e:
        raise e


def delete_user(user: User) -> None:
    """Delete a user"""
    try:
        db.session.delete(user)
        db.session.commit()
        return None
    except Exception as e:
        db.session.rollback()
        raise e
