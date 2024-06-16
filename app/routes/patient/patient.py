""" This file is used to create a blueprint for the patient routes. """

import base64
from io import BytesIO
from PIL import Image
from flask import Blueprint, current_app, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.decorators.decorators import token_required
from app.models import (
    create_new_patient,
    get_patient_by_id,
    get_photo_by_id,
    create_new_photo,
    search_patients_nickname,
    update_patient_information,
    update_patient_profile_photo,
    delete_patient_information,
    patient_belong_to_user,
)
from app.models.auth.db_queries import get_user_by_email, get_user_by_id
from app.models.patient.db_queries import (
    create_new_owner,
    get_owner_by_email,
    get_owner_by_id,
    update_photo_information,
)
from app.utils.utils import (
    email_is_valid,
    phone_number_is_valid,
    text_is_valid,
    validate_and_resize_image,
    validate_input,
)
from app.routes.resnet_model.resnet_model import get_model
from app.utils.transformation import get_prediction

patient = Blueprint("patient", __name__)


@patient.route("/register", methods=["POST"])
@token_required
def register_patient(current_user):
    """Register a patient
    Example of data required:
    {
        "nickname": "Dog",
        "age": 5,
        "weight": 10,
        "profile_photo": "base64 encoded image",
        "owner_id": 1
    }"""
    data = request.form
    required_fields = ["nickname", "age", "weight", "owner_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"{field} is required"}), 400

    if "profile_photo" not in request.files:
        return jsonify({"message": "Profile photo is required"}), 400
    profile_photo = request.files["profile_photo"]

    profile_photo, error = validate_and_resize_image(profile_photo)
    if error:
        return jsonify({"message": error}), 400

    if profile_photo:
        profile_photo = base64.b64encode(profile_photo).decode("utf-8")
        patient_data = {
            "nickname": data.get("nickname"),
            "age": data.get("age"),
            "weight": data.get("weight"),
            "user_id": current_user.id,
            "owner_id": data.get("owner_id"),
            "profile_photo": profile_photo,
        }
    else:
        return jsonify({"message": "Profile photo is required"}), 400

    try:
        new_patient = create_new_patient(patient_data)
        return jsonify({"message": "Patient created successfully", "patient": new_patient.get_information_json()}), 201
    except Exception as e:
        return jsonify({"message": "Could not create patient", "error": str(e)}), 500


@patient.route("/profile_photo/<int:patient_id>", methods=["GET"])
def serve_profile_photo(patient_id):
    """Serve the profile photo of a patient"""
    patient_info = get_patient_by_id(patient_id)
    if not patient_info:
        return jsonify({"message": "Patient not found"}), 404
    profile_photo = patient_info.profile_photo
    if not profile_photo:
        return jsonify({"message": "Patient does not have a profile photo"}), 404
    return send_file(BytesIO(base64.b64decode(profile_photo)), mimetype="image/jpeg")


@patient.route("/collection/photos/add", methods=["POST"])
@token_required
def add_photo(current_user):
    """Add a photo to a patient, and using the resnetmodel to save the information
    Example of data required:
    {
        "photo": "base64 encoded image",
        "patient_id": 1,
        "description": "Dog is playing" @optional
    }"""

    data = request.form
    required_fields = ["patient_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"{field} is required"}), 400

    if "photo" not in request.files:
        return jsonify({"message": "Photo is required"}), 400
    photo_file = request.files["photo"]
    filename = secure_filename(photo_file.filename)

    photo_file, error = validate_and_resize_image(photo_file)
    if error:
        return jsonify({"message": error}), 400

    photo_data = {
        "photo": base64.b64encode(photo_file).decode("utf-8"),
        "filename": filename,
        "patient_id": data.get("patient_id"),
        "user_id": current_user.id,
        "description": data.get("description", None),
    }
    # Check if the patient belong to the user
    patient_info = get_patient_by_id(photo_data["patient_id"])
    if not patient_info or not patient_belong_to_user(patient_info, current_user):
        return jsonify({"message": "Patient not found"}), 404
    try:
        new_photo = create_new_photo(photo_data)
        # Calling to resnet/predict/photo/<int:photo_id> , to update their predictec class and probability
        resnet_model = get_model()
        image = Image.open(BytesIO(photo_file))
        DEVICE = "cpu"
        probability, predicted_class = get_prediction(image_path=image, model=resnet_model, device=DEVICE)
        prediction = {"predicted_class": predicted_class, "probability": str(probability)}
        update_photo_information(new_photo, prediction)
        return jsonify({"message": "Photo added successfully", "photo": new_photo.get_information_json()}), 201
    except Exception as e:
        return jsonify({"message": "Could not add photo", "error": str(e)}), 500


@patient.route("/collection/photos/<int:photo_id>", methods=["GET"])
def serve_photo(photo_id):
    """Serve the photo of a patient"""
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({"message": "Photo not found"}), 404
    return send_file(BytesIO(base64.b64decode(photo.photo)), mimetype="image/jpeg")


@patient.route("/information/<int:patient_id>", methods=["GET"])
@token_required
def get_patient_information(current_user, patient_id):
    """Get the information of a patient"""
    patient_info = get_patient_by_id(patient_id)
    if not patient_info or not patient_belong_to_user(patient_info, current_user):
        return jsonify({"message": "Patient not found"}), 404
    return jsonify(patient_info.get_information_json())


@patient.route("/search", methods=["GET"])
@token_required
def search_patients(current_user):
    """Search for patients"""
    data = request.args
    search_query = data.get("s")
    if not search_query:
        return jsonify({"message": "Query is required"}), 400

    try:
        patients = search_patients_nickname(current_user, search_query)
        if patients:
            return jsonify(patients)
        return jsonify({"message": "No patients found"}), 404
    except Exception as e:
        return jsonify({"message": "Could not search patients", "error": str(e)}), 404


@patient.route("/update/information/<int:patient_id>", methods=["PUT"])
@token_required
def update_information(current_user, patient_id):
    """Update the information of a patient
    Example of data required:
    {
        "nickname": "Dog",
        "age": 5,
        "weight": 10
    }
    """
    data = request.get_json()
    required_fields = ["nickname", "age", "weight"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"The field {field} is required"}), 400

    patient_data = {
        "nickname": data.get("nickname"),
        "age": data.get("age"),
        "weight": data.get("weight"),
    }
    try:
        update_patient = get_patient_by_id(patient_id)
        if not update_patient or not patient_belong_to_user(update_patient, current_user):
            return jsonify({"message": "Patient not found"}), 404
        updated_patient = update_patient_information(update_patient, patient_data)
        return jsonify({"message": "Patient updated successfully", "patient": updated_patient.get_information_json()})
    except Exception as e:
        return jsonify({"message": "Could not update patient", "error": str(e)}), 500


@patient.route("/update/profile_photo/<int:patient_id>", methods=["PUT"])
@token_required
def update_profile_photo(current_user, patient_id):
    """Update the profile photo of a patient
    Example of data required:
    {
        "profile_photo": "base64 encoded image"
    }
    """
    if "profile_photo" not in request.files:
        return jsonify({"message": "Profile photo is required"}), 400
    profile_photo = request.files["profile_photo"]
    profile_photo, error = validate_and_resize_image(profile_photo)
    if error:
        return jsonify({"message": error}), 400

    profile_photo = base64.b64encode(profile_photo).decode("utf-8")
    try:
        update_patient = get_patient_by_id(patient_id)
        if not update_patient or not patient_belong_to_user(update_patient, current_user):
            return jsonify({"message": "Patient not found"}), 404
        updated_patient = update_patient_profile_photo(update_patient, profile_photo)
        return (
            jsonify(
                {"message": "Profile photo updated successfully", "patient": updated_patient.get_information_json()}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"message": "Could not update profile photo", "error": str(e)}), 500


@patient.route("/delete/<int:patient_id>", methods=["DELETE"])
@token_required
def delete_patient(current_user, patient_id):
    """Delete a patient"""
    try:
        patient_info = get_patient_by_id(patient_id)
        if not patient_info or not patient_belong_to_user(patient_info, current_user):
            return jsonify({"message": "Patient not found"}), 404
        delete_patient_information(patient_info)
        return jsonify({"message": "Patient deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Could not delete patient", "error": str(e)}), 500


# Additional routes
@patient.route("/generate", methods=["POST"])
@token_required
def generate_patient(current_user):
    """Generate a patient first creating an owner
    Required data:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "",
        "phone_number": "",
        "document": "",

        "nickname": "Dog",
        "age": 5,
        "weight": 10,
        "profile_photo": "base64 encoded image", # of the patient

        # Class Photo
        "analyzed_photo": "base64 encoded image",
        "description": "Dog is playing" @optional
        "class_name: "Dog" @hide
        "probability": "0.99" @hide
    }
    """

    data = request.form
    required_fields = ["first_name", "last_name", "email", "phone_number", "document", "nickname", "age", "weight"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"{field} is required to generate patient"}), 400

    if "profile_photo" not in request.files:
        return jsonify({"message": "Profile photo is required"}), 400
    if "analyzed_photo" not in request.files:
        return jsonify({"message": "Analyzed photo is required"}), 400

    profile_photo = request.files["profile_photo"]
    analyzed_photo = request.files["analyzed_photo"]
    filename_analyzed = secure_filename(analyzed_photo.filename)

    profile_photo, error = validate_and_resize_image(profile_photo)
    if error:
        return jsonify({"message": error}), 400
    analyzed_photo, error = validate_and_resize_image(analyzed_photo)
    if error:
        return jsonify({"message": error}), 400

    # Create the owner
    owner_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "phone_number": data.get("phone_number"),
        "document": data.get("document"),
        "user_id": current_user.id,  # The veterinarian id
    }
    validation_checks_owner = [
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

    for data_owner, validation_func, error_message in validation_checks_owner:
        response = validate_input(data_owner, validation_func, error_message)
        if response:
            return response

    # Check if email is already registered
    owner_check = get_owner_by_email(owner_data["email"])
    if owner_check:
        return jsonify({"message": "Email already registered"}), 400
    user_check = get_user_by_email(owner_data["email"])
    if user_check:
        return jsonify({"message": "Email already registered"}), 400

    # Saving the owner
    try:
        new_owner = create_new_owner(owner_data)
    except Exception as e:
        return jsonify({"message": "Could not create owner", "error": str(e)}), 500

    # Generate the patient

    patient_data = {
        "nickname": data.get("nickname"),
        "age": data.get("age"),
        "weight": data.get("weight"),
        "user_id": current_user.id,
        "owner_id": new_owner.id,
        "profile_photo": base64.b64encode(profile_photo).decode("utf-8"),
        "description": data.get("description"),
    }
    try:
        new_patient = create_new_patient(patient_data)
    except Exception as e:
        return jsonify({"message": "Could not create patient", "error": str(e)}), 500

    # Save the analyzed photo
    photo_data = {
        "photo": base64.b64encode(analyzed_photo).decode("utf-8"),
        "filename": filename_analyzed,
        "patient_id": new_patient.id,
        "user_id": current_user.id,
        "description": patient_data.get("description", None),
        "predicted_class": data.get("class_name"),
        "probability": data.get("probability"),
    }
    try:
        _ = create_new_photo(photo_data)
    except Exception as e:
        return jsonify({"message": "Could not add photo", "error": str(e)}), 500

    return (
        jsonify({"message": "Patient created successfully", "patient": new_patient.get_information_json()}),
        201,
    )


@patient.route("/generate/pdf/<int:patient_id>", methods=["GET"])
@token_required
def generate_pdf(current_user, patient_id):
    """Generate the PDF of the patient"""
    patient_info = get_patient_by_id(patient_id)
    if not patient_info or not patient_belong_to_user(patient_info, current_user):
        return jsonify({"message": "Patient not found"}), 404
    # Generate the PDF information
    try:
        user_info = get_user_by_id(current_user.id)
        user_json_info = user_info.get_json_pdf()

        patient_json_info = patient_info.get_information_json()

        owner_info = get_owner_by_id(patient_info.owner_id)
        owner_json_info = owner_info.get_json_pdf()

        pdf_info = {
            "user": user_json_info,
            "patient": patient_json_info,
            "owner": owner_json_info,
        }
        return jsonify(pdf_info), 200
    except Exception as e:
        return jsonify({"message": "Could not get information", "error": str(e)}), 500
