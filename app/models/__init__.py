""" This file is used to initialize the database object. """

from .auth.auth_model import User, db
from .patient.patient_model import Patient, Photo, Owner
from .auth.db_queries import *
from .user.db_queries import *
from .patient.db_queries import *
