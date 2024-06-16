""" This file is the entry point of the application. It creates the Flask app instance and returns it. """

from flask import Flask
from app.models import db
from configuration import config
from .utils.utils import mail
from .routes import auth, user, resnet, patient, owner


def create_app(config_name: str):
    """Create a Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    mail.init_app(app)
    with app.app_context():
        db.init_app(app)
        db.create_all()
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(user, url_prefix="/users")
    app.register_blueprint(resnet, url_prefix="/resnet")
    app.register_blueprint(patient, url_prefix="/patients")
    app.register_blueprint(owner, url_prefix="/owners")
    return app
