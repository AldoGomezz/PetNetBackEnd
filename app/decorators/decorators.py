""" This file contains all the decorators used in the application"""

from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app as app
from jwt import decode
from app.models import get_user_by_id


def token_required(f):
    """Decorator to check if a token is provided in the request headers"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            # Decode the token
            data = decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            if not isinstance(data, dict):
                raise ValueError("Token payload is not a dictionary")

            if "exp" in data:
                exp = data.get("exp")
                if exp < int(datetime.now(timezone.utc).timestamp()):
                    raise ValueError("Token has expired")
            if "user_id" in data:
                user_id = data.get("user_id")
                current_user = get_user_by_id(user_id)
            else:
                raise KeyError("user_id not found in token data")
        except Exception as e:
            return jsonify({"message": "Token is invalid!", "error": str(e)}), 400

        try:
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({"message": "An error occurred while processing the request", "error": str(e)}), 500

    return decorated
