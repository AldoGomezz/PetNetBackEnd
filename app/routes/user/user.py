"""This module contains the user routes"""

import base64
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from app.models import (
    User,
    get_user_information,
    get_user_by_id,
    update_user_info,
    update_user_password,
    get_user_by_email,
    delete_user,
)
from app.decorators.decorators import token_required
from app.utils.utils import (
    email_is_valid,
    send_restore_password_mail,
    send_confirmation_mail,
    text_is_valid,
    address_is_valid,
    validate_input,
    college_number_is_valid,
)

user = Blueprint("user", __name__)


@user.route("/information", methods=["GET"])
@token_required
def get_user(current_user):
    """Get a user information by id"""
    try:
        user_info = get_user_by_id(current_user.id)
        user_json_info = get_user_information(user_info)
        return jsonify(user_json_info), 200
    except Exception as e:
        return jsonify({"message": "There was an error getting user information", "error": str(e)}), 400


@user.route("/profile_photo/<int:user_id>", methods=["GET"])
@token_required
def serve_profile_picture(_, user_id):
    """Serve the profile photo of a user"""
    try:
        user_info = get_user_by_id(user_id)
        if not user_info:
            return jsonify({"message": "User not found"}), 404
        profile_picture = user_info.profile_picture
        if not profile_picture:
            return jsonify({"message": "Profile photo not found"}), 404
        return send_file(BytesIO(base64.b64decode(profile_picture)), mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"message": "There was an error getting the profile photo", "error": str(e)}), 400


@user.route("/update/information", methods=["PUT"])
@token_required
def update_user(current_user):
    """Update user information
    Example of data received:
    {
        "first_name": "John",
        "last_name": "Doe",
        "clinic": "Clinic name",
        "address": "Address",
        "college_number": "123456",
        "username": "john_doe"
    }
    """
    data = request.get_json()
    # Dont update username
    user_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "clinic": data.get("clinic"),
        "address": data.get("address"),
        "college_number": data.get("college_number"),
    }
    validation_checks = [
        (
            user_data["first_name"],
            text_is_valid,
            "Invalid first name, it only can contains alphabetic values and spaces",
        ),
        (user_data["last_name"], text_is_valid, "Invalid last name, it only can contains alphabetic values and spaces"),
        (user_data["clinic"], text_is_valid, "Invalid clinic, it only can contains alphabetic values and spaces"),
        (user_data["address"], address_is_valid, "Invalid address, it only can contains alphabetic values and spaces"),
        (
            user_data["college_number"],
            college_number_is_valid,
            "Invalid college number, it only can contains alphabetic values and spaces",
        ),
    ]
    for data_us, validation_func, error_message in validation_checks:
        response = validate_input(data_us, validation_func, error_message)
        if response:
            return response

    try:
        user_info = get_user_by_id(current_user.id)
        _ = update_user_info(user_info, data)
        return jsonify({"message": "User information updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error updating user information", "error": str(e)}), 400


@user.route("/update/password", methods=["PUT"])
@token_required
def update_password(current_user):
    """Update user password
    Example of data received:
    {
        "actual_password": "old_password",
        "new_password": "new_password",
        "confirm_password": "new_password"
    }
    """
    data = request.get_json()
    try:
        user_info = get_user_by_id(current_user.id)
        if not user_info.check_password(data["actual_password"]):
            return jsonify({"message": "The password is incorrect"}), 400

        if not User.check_passwords_equal(data["new_password"], data["confirm_password"]):
            return jsonify({"message": "Passwords do not match"}), 400

        _ = update_user_password(user_info, data)
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error updating the password", "error": str(e)}), 400


@user.route("/restore/password", methods=["POST"])
def restore_password():
    """Allow the user to restore the password using the email, while sending a code to the user email."""
    data = request.get_json()
    email = data.get("email")
    try:
        valid = email_is_valid(email)
        if not valid:
            return jsonify({"message": "Invalid email"}), 400
    except Exception as e:
        return jsonify({"message": "Invalid email", "error": str(e)}), 400

    user_info = get_user_by_email(email)
    if not user_info:
        return jsonify({"message": "User not found"}), 404

    try:
        return send_restore_password_mail(user_info)
    except Exception as e:
        return jsonify({"message": "There was an error sending the email", "error": str(e)}), 500


@user.route("/restore/password/verify", methods=["POST"])
def restore_password_verify():
    """Restore the password using the code sent to the user email."""
    data = request.get_json()
    code = data.get("code")
    token = data.get("token")
    if not code or not token:
        return jsonify({"message": "Invalid code or token"}), 400
    try:
        code, user_id = User.validate_code_verification(token)
        if not code or not user_id:
            return jsonify({"message": "Invalid code or token"}), 400
    except Exception as e:
        return jsonify({"message": "Token is invalid", "error": str(e)}), 400

    user_info = get_user_by_id(user_id)
    if not user_info:
        return jsonify({"message": "User not found"}), 404

    if code != data.get("code"):
        return jsonify({"message": "Invalid code"}), 400
    # ! Check if user_id is ok to send it back to the user
    return jsonify({"message": "Code verified successfully", "user_id": user_id}), 200


@user.route("/restore/password/update", methods=["POST"])
def restore_password_update():
    """Update the password using the code sent to the user email.
    Example of data received:
    {
        "user_id": 1,
        "new_password": "new_password",
        "confirm_password": "new_password"
    }
    """
    data = request.get_json()
    user_id = data.get("user_id")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    user_info = get_user_by_id(user_id)

    if not user_info:
        return jsonify({"message": "User not found"}), 404

    if not User.check_passwords_equal(new_password, confirm_password):
        return jsonify({"message": "Passwords do not match"}), 400

    try:
        _ = update_user_password(user_info, data)
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error updating the password", "error": str(e)}), 400


@user.route("/update/email", methods=["POST"])
@token_required
def update_email(current_user):
    """Update user email
    Example of data received:
    {
        "new_email": "example@gmail.com"
    }
    """
    data = request.get_json()
    new_email = data.get("new_email")
    try:
        valid = email_is_valid(new_email)
        if not valid:
            return jsonify({"message": "Invalid email"}), 400
    except Exception as e:
        return jsonify({"message": "Invalid email", "error": str(e)}), 400

    # Check if email is already in use
    user_info = get_user_by_email(new_email)
    if user_info:
        return jsonify({"message": "Email already in use"}), 400

    user_info = get_user_by_id(current_user.id)
    if not user_info:
        return jsonify({"message": "User not found"}), 404

    try:
        send_confirmation_mail(user_info, new_email)
        return jsonify({"message": "Please check your new email to confirm updated"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error updating the email", "error": str(e)}), 400


@user.route("/delete", methods=["DELETE"])
@token_required
def delete_user_db(current_user):
    """Delete a user by id"""
    try:
        user_info = get_user_by_id(current_user.id)
        delete_user(user_info)
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error deleting the user", "error": str(e)}), 500
