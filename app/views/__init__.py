from .homepage import homepage
from .api import api
def register_blueprints(app):
    app.register_blueprint(homepage)
    app.register_blueprint(api)