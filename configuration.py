""" This file contains the configuration classes for the application. Each class contains the configuration variables that are specific to the environment. The Config class contains the configuration variables that are common to all environments. The Development, Testing, and Production classes inherit from the Config class and contain the configuration variables that are specific to the development, testing, and production environments, respectively. The config dictionary contains the configuration classes for each environment. """

from os import getenv


class Config:
    """Base configuration class. Contains all the configuration variables that are common to all environments."""

    SECRET_KEY = getenv("SECRET_KEY", "secret_key")
    # ------- MAIL SERVER CONFIGURATION -------
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # -----------------------------------------
    TOKEN_EXPIRATION_TIME = 3600  # 1 hour
    BASE_URL = getenv("BASE_URL", "http://localhost:5000")


class Development(Config):
    """Development configuration class. Contains all the configuration variables that are specific to the development environment."""

    DEBUG = True
    # Database URI
    SQLALCHEMY_DATABASE_URI = getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/db_petnet_test")
    # ------- MAIL SERVER ACCESS -------------
    MAIL_USERNAME = getenv("MAIL_USERNAME", None)
    MAIL_PASSWORD = getenv("MAIL_PASSWORD", None)
    # -----------------------------------------


class Testing(Config):
    """Testing configuration class. Contains all the configuration variables that are specific to the testing environment."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/db_petnet_test")


class Production(Config):
    """Production configuration class. Contains all the configuration variables that are specific to the production environment."""

    DEBUG = False
    # Database URI
    DATABASE_NAME = getenv("DATABASE_URL", "")
    SQLALCHEMY_DATABASE_URI = DATABASE_NAME.replace("postgres", "postgresql")
    # ------- MAIL SERVER ACCESS -------------
    MAIL_USERNAME = getenv("MAIL_USERNAME")
    MAIL_PASSWORD = getenv("MAIL_PASSWORD")
    # -----------------------------------------


config = {"development": Development, "testing": Testing, "production": Production, "default": Development}
