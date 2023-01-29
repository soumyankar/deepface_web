from flask import Flask, request, redirect, url_for, Blueprint, render_template, flash
# from werkzeug.utils import secure_filename
from app.forms.input_form import userInputForm
from os.path import join, dirname, realpath
# from app import app
import base64
import uuid
import json
import requests
import jsonpickle

UPLOADS_PATH = join(dirname(realpath(__file__)), '../static/uploads/')
homepage = Blueprint("homepage", __name__, static_folder="static", template_folder="templates")
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@homepage.route("/", methods=['GET', 'POST'])
def index():
	form = userInputForm()
	if request.method == 'POST' and form.validate():
		name = form.inputName.data
		face = form.inputImage.data
		face_filename_extension = face.filename.split('.')[-1]
		uuid_append = str(uuid.uuid4())
		filename = name+"_"+uuid_append+"."+face_filename_extension
		face.save((UPLOADS_PATH + filename))
		with open(UPLOADS_PATH+filename, "rb") as image_file:
			face_base64 = base64.b64encode(image_file.read())
			# data:image/jpeg;base64,
		face_base64 = "data:image/jpeg;base64,"+str(face_base64) # adding data type and converting the base64 to string
		face_base64 = list(face_base64)
		json_request = {"img": face_base64}
		headers = {'Content-Type': 'application/json'}
		resp_obj = requests.post(url=url_for('api.analyze', _external=True), data=json.dumps(json_request), headers=headers)
		# print(resp_obj)
		return redirect(url_for('homepage.output', name=resp_obj))
	return render_template('index.html', form = form)

@homepage.route("/output", methods=['GET', 'POST'])
def output():
	name = request.args['name']
	# name = json.dumps(name)
	name = json.loads(name)
	print(name)
	return render_template('output.html', name=str(name))
