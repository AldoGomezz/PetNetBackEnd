"""This file contains the routes for the authentication blueprint"""

from datetime import datetime, timezone, timedelta
from jwt import encode
from flask import Blueprint, request, jsonify, current_app, render_template_string
from app.decorators.decorators import token_required
from app.models import (
    User,
    get_user_by_username,
    create_user,
    get_user_by_id,
    db_commit_and_save,
    get_user_information,
    get_user_by_email,
)
from app.utils.utils import (
    text_is_valid,
    email_is_valid,
    validate_input,
    send_confirmation_mail,
)

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()
    user_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "clinic": data.get("clinic"),
        "address": data.get("address"),
        "college_number": data.get("college_number"),
        "username": data.get("username"),
        "password": data.get("password"),
        "confirm_password": data.get("confirm_password"),
    }
    # Required fields
    required_fields = [
        "first_name",
        "last_name",
        "email",
        "clinic",
        "address",
        "college_number",
        "username",
        "password",
        "confirm_password",
    ]
    for field in required_fields:
        if not user_data.get(field):
            return jsonify({"message": f"{field} is required"}), 400

    # Validate the user data
    validation_checks = [
        (
            user_data["first_name"],
            text_is_valid,
            "Invalid first name, it only can contains alphabetic values and spaces",
        ),
        (user_data["last_name"], text_is_valid, "Invalid last name, it only can contains alphabetic values and spaces"),
        (user_data["email"], email_is_valid, "Invalid email"),
        (user_data["clinic"], text_is_valid, "Invalid clinic, it only can contains alphabetic values and spaces"),
        (user_data["username"], text_is_valid, "Invalid username, it only can contains alphabetic values and spaces"),
    ]
    for data, validation_func, error_message in validation_checks:
        response = validate_input(data, validation_func, error_message)
        if response:
            return response

    username = user_data.get("username")
    password = user_data.get("password")
    confirm_password = user_data.get("confirm_password")

    if not User.check_passwords_equal(password, confirm_password):
        return jsonify({"message": "Passwords do not match", "suggestion": ""}), 400

    # Check if the user exists
    user = get_user_by_username(username)
    if user:
        return jsonify({"message": "User already exists", "suggestion": ""}), 400

    # Check if the email exists
    email = user_data.get("email")
    user = get_user_by_email(email)
    if user:
        return jsonify({"message": "Email already exists", "suggestion": ""}), 400

    # Create a new user
    try:
        new_user = create_user(user_data)
        new_user_username = new_user.username
        send_confirmation_mail(new_user)
        return (
            jsonify({"message": f"User {new_user_username} created successfully,please check you email to confirm"}),
            201,
        )
    except Exception as e:
        return jsonify({"message": "An error occur while creating user", "error": str(e)}), 500


@auth.route("/confirm_email/<token>", methods=["GET"])
def confirm_email(token):
    """Confirm the user email"""
    user_id, new_mail = User.confirm_token(token)
    if user_id:
        try:
            user = get_user_by_id(user_id)
            user.confirmed = True
            message = "Email confirmed successfully"
            if new_mail:
                user.email = new_mail
                message = "Email updated successfully"
            _ = db_commit_and_save(user)
            with open("app/templates/html/confirmation_success.html", "r", encoding="utf-8") as f:
                html_template = f.read()
            return render_template_string(html_template, message=message)
        except Exception as e:
            return (
                jsonify({"message": "An error occurred while confirming email", "error": str(e)}),
                500,
            )
    return jsonify({"message": "Invalid token to confirm email"}), 401


@auth.route("/login", methods=["POST"])
def login():
    """Login a user"""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    # Validate the user data
    valid_username, _ = text_is_valid(username)
    if not valid_username:
        return (
            jsonify(
                {
                    "message": "Invalid username, it only can contains alphabetic values and spaces",
                }
            ),
            400,
        )
    user = get_user_by_username(username)
    if user:
        if user.validate_confirmed():
            if user.check_password(password):
                # Generate JWT token
                user_information = get_user_information(user)
                exp_time = datetime.now(timezone.utc) + timedelta(seconds=current_app.config["TOKEN_EXPIRATION_TIME"])
                user_information["exp"] = exp_time
                token = encode(user_information, current_app.config["SECRET_KEY"], algorithm="HS256")
                return jsonify({"token": token})
            return jsonify({"message": "Invalid credentials, username or password is incorrect"}), 401
        send_confirmation_mail(user)
        return jsonify({"message": "Please check your email to confirm your account"}), 401
    return jsonify({"message": "User does not exist"}), 404


@auth.route("/logout", methods=["POST"])
def logout():
    """Logout a user"""
    return jsonify({"message": "User logged out successfully"}), 204


@auth.route("/renew_token", methods=["GET"])
@token_required
def renew_token(current_user):
    """Renew the token"""
    user_information = get_user_information(current_user)
    user_information["iat"] = datetime.now(timezone.utc)
    token = encode(user_information, current_app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": token}), 200
