"""This module is responsible for handling the routes for the owner of the pet."""

from flask import Blueprint, request, jsonify
from app.decorators.decorators import token_required
from app.models import (
    create_new_owner,
    get_user_by_email,
    get_owner_by_email,
    update_owner_info,
    get_owner_by_id,
    delete_owner_information,
    search_owners_name,
)
from app.utils.utils import email_is_valid, text_is_valid, validate_input, phone_number_is_valid

owner = Blueprint("owner", __name__)


# Create owner routes
@owner.route("/register", methods=["POST"])
@token_required
def register_owner(current_user):
    """Register an owner
    Example of data required:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "example@gmail.com",
        "phone_number": "1234567890",
        "document": "123456789"
    }
    """
    data = request.get_json()
    owner_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "phone_number": data.get("phone_number"),
        "document": data.get("document"),
        "user_id": current_user.id,
    }
    validation_checks = [
        (
            owner_data["first_name"],
            text_is_valid,
            "Invalid first name, it only can contains alphabetic values and spaces",
        ),
        (
            owner_data["last_name"],
            text_is_valid,
            "Invalid last name, it only can contains alphabetic values and spaces",
        ),
        (owner_data["email"], email_is_valid, "Invalid email"),
        (
            owner_data["phone_number"],
            phone_number_is_valid,
            "Invalid phone number it should start with 9 and have 9 digits",
        ),
    ]
    for data, validation_func, error_message in validation_checks:
        response = validate_input(data, validation_func, error_message)
        if response:
            return response

    # Check if email is already registered
    owner_check = get_owner_by_email(owner_data["email"])
    if owner_check:
        return jsonify({"message": "Email already registered"}), 400
    user_check = get_user_by_email(owner_data["email"])
    if user_check:
        return jsonify({"message": "Email already registered"}), 400

    try:
        owner_info = create_new_owner(owner_data)
        return jsonify(owner_info.get_information_json()), 201
    except Exception as e:
        return jsonify({"message": "There was an error registering an owner", "error": str(e)}), 400


@owner.route("/update/information/<int:owner_id>", methods=["PUT"])
@token_required
def update_owner_information(current_user, owner_id):
    """Update owner information
    Example of data received:
    {
        "first_name": "John",
        "last_name": "Do",
        "email": "",
        "phone_number": "1234567890",
        "document": "123456789"
    }
    """
    data = request.get_json()
    owner_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "phone_number": data.get("phone_number"),
        "document": data.get("document"),
    }
    validation_checks = [
        (
            owner_data["first_name"],
            text_is_valid,
            "Invalid first name, it only can contains alphabetic values and spaces",
        ),
        (
            owner_data["last_name"],
            text_is_valid,
            "Invalid last name, it only can contains alphabetic values and spaces",
        ),
        (owner_data["email"], email_is_valid, "Invalid email"),
        (owner_data["phone_number"], phone_number_is_valid, "Invalid phone number"),
    ]
    for data, validation_func, error_message in validation_checks:
        response = validate_input(data, validation_func, error_message)
        if response:
            return response
    # Check if email is already registered
    # TODO add a function to check for email in the database and check if exists more than one owner with the same email.
    user_check = get_user_by_email(owner_data["email"])
    if user_check:
        return jsonify({"message": "Email already registered"}), 400

    owner_info = get_owner_by_id(owner_id)
    # Get the owner information
    if not owner_info or (owner_info.user_id != current_user.id):
        return jsonify({"message": "Owner not found"}), 404
    try:
        owner_info = update_owner_info(owner_info, owner_data)
        return (
            jsonify({"message": "Owner information updated successfully", "owner": owner_info.get_information_json()}),
            200,
        )
    except Exception as e:
        return jsonify({"message": "There was an error updating owner information", "error": str(e)}), 400


@owner.route("/delete/<int:owner_id>", methods=["DELETE"])
@token_required
def delete_owner(current_user, owner_id):
    """Delete an owner"""
    try:
        owner_info = get_owner_by_id(owner_id)
        if not owner_info or (owner_info.user_id != current_user.id):
            return jsonify({"message": "Owner not found"}), 404
        delete_owner_information(owner_info)
        return jsonify({"message": "Owner deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "There was an error deleting the owner", "error": str(e)}), 400


@owner.route("/search", methods=["GET"])
@token_required
def search_owners(current_user):
    """Search for owners"""
    data = request.args
    search_query = data.get("s")
    if not search_query:
        return jsonify({"message": "Query is required"}), 400
    try:
        owners = search_owners_name(current_user, search_query)
        if owners:
            return jsonify(owners)
        return jsonify({"message": "No owners found"}), 404
    except Exception as e:
        return jsonify({"message": "Could not search owners", "error": str(e)}), 404


@owner.route("/get/information/<int:owner_id>", methods=["GET"])
@token_required
def get_owner_information(current_user, owner_id):
    """Get owner information"""
    try:
        owner_info = get_owner_by_id(owner_id)
        if not owner_info or (owner_info.user_id != current_user.id):
            return jsonify({"message": "Owner not found"}), 404
        return jsonify(owner_info.get_information_json()), 200
    except Exception as e:
        return jsonify({"message": "There was an error getting owner information", "error": str(e)}), 400
