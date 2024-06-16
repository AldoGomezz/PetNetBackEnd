""" This file contains the API for the ResNet model. """

import io
import os
import base64
import requests
from cachetools import cached, TTLCache
from PIL import Image
from flask import Blueprint, jsonify, request
from app.decorators.decorators import token_required
from app.utils.transformation import get_prediction, load_model
from app.models import get_photo_by_id, update_photo_information, photo_belong_to_user

resnet = Blueprint("resnet", __name__)

MODEL_PATH = "./model_petnet_50_new.pth"
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DEVICE = "cpu"

if not os.path.exists(MODEL_PATH):
    response = requests.get(
        "https://onedrive.live.com/download?resid=E1236C32112E61C0%213983&authkey=!ADtKWzTvdvuJkpo", timeout=10
    )
    # https://onedrive.live.com/download?resid=E1236C32112E61C0%213935&authkey=!AE2FFtjkWzjLN_E
    with open(MODEL_PATH, "wb") as f:
        f.write(response.content)

# Cache for the model with max size of 1 and TTL of 60 seconds
cache = TTLCache(maxsize=1, ttl=60)


@cached(cache)
def get_model():
    """Load the model from the cache or load it if it's not in the cache"""
    return load_model(model_path=MODEL_PATH, device_name=DEVICE)


@resnet.route("/predict", methods=["POST"])
@token_required
def predict(_):
    """Simple API to predict the class of an image"""
    if request.method == "POST":
        # Get the image from the POST request
        image = request.files["file"]
        image = Image.open(io.BytesIO(image.read()))
        # Get the model from cache or load it if it's not in the cache
        resnet_model = get_model()

        # Make a prediction
        probability, predicted_class = get_prediction(image_path=image, model=resnet_model, device=DEVICE)
        # Return the prediction in JSON format
        return jsonify({"class_name": predicted_class, "probability": probability})

    return jsonify({"message": "This was not a POST request"})


@resnet.route("/predict/save/photo/<int:photo_id>", methods=["POST"])
@token_required
def predict_save_photo(current_user, photo_id):
    """Saving the prediction in the database
    {
        "predicted_class": "class_name",
        "probability": "0.0"
    }
    """
    if request.method == "POST":
        photo = get_photo_by_id(photo_id)
        if not photo or not photo_belong_to_user(photo, current_user):
            return jsonify({"message": "Photo not found"}), 404

        data = request.json

        try:
            prediction = {
                "predicted_class": data.get("predicted_class", None),
                "probability": data.get("probability", None),
            }
            update_photo_information(photo, prediction)
            return jsonify(prediction)
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"}), 400

    return jsonify({"message": "This was not a POST request"})


@resnet.route("/predict/photo/<int:photo_id>", methods=["GET"])
@token_required
def predict_photo(current_user, photo_id):
    """Simple API to predict the class of an image"""
    if request.method == "GET":
        photo = get_photo_by_id(photo_id)
        if not photo or not photo_belong_to_user(photo, current_user):
            return jsonify({"message": "Photo not found"}), 404
        try:
            # If photo.photo is a string representing the image data
            image_data = base64.b64decode(photo.photo)
            image = Image.open(io.BytesIO(image_data))
            # Get the model from cache or load it if it's not in the cache
            resnet_model = get_model()

            probability, predicted_class = get_prediction(image_path=image, model=resnet_model, device=DEVICE)
            prediction = {"predicted_class": predicted_class, "probability": str(probability)}
            update_photo_information(photo, prediction)
            return jsonify(prediction)
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"}), 400

    return jsonify({"message": "This was not a GET request"})
