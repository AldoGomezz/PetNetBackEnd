"""Utility functions for the app"""

import re
import secrets
import string
import io
from PIL import Image
from flask import jsonify, url_for, render_template_string
from flask_mail import Mail, Message
from app.models import User

mail = Mail()


def generate_code_alphanumeric(longitud=6):
    """Generate a random alphanumeric code"""
    caracteres = string.ascii_letters + string.digits
    return "".join(secrets.choice(caracteres) for _ in range(longitud))


def send_confirmation_mail(user, new_mail=None):
    """Send a confirmation email to the user"""
    token = User.generate_confirmation_token(user.id, new_mail)
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    if new_mail:
        msg = Message("Welcome to Pet Net", sender="cristopherelvism@gmail.com", recipients=[new_mail])
    else:
        msg = Message("Welcome to Pet Net", sender="cristopherelvism@gmail.com", recipients=[user.email])
    # msg.body = f"Please click the link to confirm your email {confirm_url}"
    # Load the html template
    with open("app/templates/html/email_confirmation.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    # Render the html template
    msg.html = render_template_string(html_template, confirm_url=confirm_url)
    mail.send(msg)


def send_restore_password_mail(user):
    """Send a confirmation email to the user"""
    code = generate_code_alphanumeric()
    token = User.generate_code_verification(code, user.id)
    msg = Message("Restore your password Pet Net", sender="cristopherelvism@gmai.com", recipients=[user.email])

    with open("app/templates/html/email_restore_password.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    # Render the html template
    msg.html = render_template_string(html_template, code_password=code, username=user.username)
    mail.send(msg)

    return jsonify({"message": "Code sended succesfully", "token": token}), 200


def text_is_valid(name: str):
    """Sanitize the name"""
    # Only allow alphabetic characters and spaces, removing extra spaces.
    valid_text = False
    name = name.strip()
    if not re.match(r"^[a-zA-Z ]+$", name):
        allowed_text = re.sub(r"[^a-zA-Z ]+", "", name)
        return valid_text, allowed_text
    valid_text = True
    return valid_text, name


def address_is_valid(address: str):
    """Validate the address. It should have at least 5 characters."""
    valid_address = False
    if len(address) < 5:
        return valid_address, None
    valid_address = True
    return valid_address, None


def college_number_is_valid(college_number: str):
    """Validate the college number. Only containes numbers and letters."""
    valid_college_number = False
    if not re.match(r"^[a-zA-Z0-9]+$", college_number):
        return valid_college_number, None
    valid_college_number = True
    return valid_college_number, None


def email_is_valid(email: str):
    """Validate email it should start with one or more alphanumeric characters, hyphens, or periods, followed by the '@' symbol.
    After the '@' symbol, it should have one or more sequences of alphanumeric characters or hyphens, each followed by a period.
    Finally, it should end with 2 to 4 alphanumeric characters or hyphens after the last period. For example: example@domain.com.
    """
    # Check if the email is valid
    valid_email = False
    if not re.match(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$", email):
        return valid_email, None
    valid_email = True
    return valid_email, None


def phone_number_is_valid(phone_number: str):
    """Validate the phone number. It should have 9 digits."""
    valid_phone_number = False
    if not re.match(r"^[9]\d{0,8}$", phone_number):
        return valid_phone_number, None
    valid_phone_number = True
    return valid_phone_number, None


def validate_and_resize_image(image_file):
    """Validate the image file and resize it to 512x512 pixels"""
    try:
        image = Image.open(image_file)
        if image.format not in ["JPEG", "JPG", "PNG"]:
            return None, "Invalid image format. Only JPG, JPEG, and PNG are allowed."
        # Convert RGBA images to RGB
        if image.mode == "RGBA":
            image = image.convert("RGB")
        resized_image = image.resize((512, 512))
        byte_array = io.BytesIO()
        resized_image.save(byte_array, format="JPEG")
        return byte_array.getvalue(), None
    except Exception as e:
        return None, str(e)


def validate_input(data, validation_func, error_message, suggestion=None):
    """Validate the input data using the validation function provided. If the input is invalid, return a response with the error message and suggestion."""
    is_valid, suggestion_name = validation_func(data)
    if not is_valid:
        response = {"message": error_message, "suggestion": suggestion_name if suggestion_name else suggestion}
        return jsonify(response), 400
    return None  # Input is valid
