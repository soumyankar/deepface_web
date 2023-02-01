# Settings common to all environments (development|staging|production)
# Place environment specific settings in env_settings.py
# An example file (env_settings_example.py) can be used as a starting point

import os

# Application settings
BANNER_APP_NAME ="DeepFace Web API"
APP_NAME = "DeepFace Web API"
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

# Flask settings
CSRF_ENABLED = True

# Flask-SQLAlchemy settings
SQLALCHEMY_TRACK_MODIFICATIONS = False

# FlaskWTF settings and Password Salts
SECRET_KEY = "supersecretkey"
SECURITY_PASSWORD_SALT = 'super_duper_secret_key'
BCRYPT_LOG_ROUNDS = 13
WTF_CSRF_ENABLED = True

# Debugging
FLASK_DEBUG=1