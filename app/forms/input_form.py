from app import db
# from flask_uploads import UploadSet, IMAGES
try:
    from flask_wtf import FlaskForm             # Try Flask-WTF v0.13+
except ImportError:
    from flask_wtf import Form as FlaskForm     # Fallback to Flask-WTF v0.12 or older
from wtforms import StringField, SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import validators, ValidationError
from wtforms.validators import InputRequired, Email, Length
# from app.models.models import User
from datetime import date, datetime

# images = UploadSet('images', IMAGES)
today = date.today()
current_time = datetime.now().time()

class userInputForm(FlaskForm):
    inputImage = FileField('Input Image', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])
    inputName = StringField('Full Name', validators=[InputRequired()])
    submit = SubmitField(('Analyze'))