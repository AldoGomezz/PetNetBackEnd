""" This file is used to run the application. It imports the create_app function from the app package and runs the application."""

from os import getenv
from dotenv import load_dotenv
from app import create_app

load_dotenv()  # Loading environment variables from .env file

application = create_app(getenv("CONFIGURATION", "default"))

if __name__ == "__main__":
    application.run(debug=True)
