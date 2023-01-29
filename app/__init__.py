from datetime import datetime
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
 
db = SQLAlchemy(session_options={"autoflush": False})

# Instantiate Flask extensions
csrf_protect = CSRFProtect()
# Initialize Flask Application
def create_app(extra_config_settings={}):
    """Create a Flask application.
    """
    # Instantiate Flask
    app = Flask(__name__)

    # Setup Flask-SQLAlchemy
    # db.init_app(app)

    # Load common settings
    app.config.from_object('app.settings')
    # Load environment specific settings
    app.config.from_object('app.local_settings')
    # Register blueprints
    from .views import register_blueprints
    register_blueprints(app)

    return app