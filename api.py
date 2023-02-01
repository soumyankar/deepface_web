import warnings
warnings.filterwarnings("ignore")

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
#------------------------------
# Stuff I need for the templates
from forms.input_form import userInputForm

#-------------------------------
# stuff I need for other essential things
import requests
from json2html import *
from urllib.parse import unquote
from os.path import join, dirname, realpath
UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/uploads/')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#------------------------------
# Enconding a base64 and returning as ascii
import base64
from base64 import b64encode
from json import dumps
ENCODING = 'utf-8'
def b64EncodeString(msg):
    msg_bytes = msg.encode('ascii')
    base64_bytes = base64.b64encode(msg_bytes)
    return base64_bytes.decode('ascii')
#------------------------------

from flask import Flask, jsonify, request, make_response, render_template, redirect, url_for
import argparse
import uuid
import json
import time
from tqdm import tqdm

#------------------------------

import tensorflow as tf
tf_version = int(tf.__version__.split(".")[0])

#------------------------------

if tf_version == 2:
	import logging
	tf.get_logger().setLevel(logging.ERROR)

#------------------------------

from deepface import DeepFace

#------------------------------

app = Flask(__name__)
# Load common settings
app.config.from_object('settings')

#------------------------------

if tf_version == 1:
	graph = tf.get_default_graph()

#------------------------------
#Service API Interface

@app.route('/', methods=['GET', 'POST'])
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
			# third: decode these bytes to text
			# result: string (in utf-8)
			face_base64_string = face_base64.decode(ENCODING)
			face_base64 = "data:image/jpeg;base64,"+ face_base64_string# adding data type and converting the base64 to string
			face_base64 = [face_base64]
			json_request = {"img": face_base64}

		json_data = dumps(json_request, indent=2)
		headers = {'Content-Type': 'application/json'}

		resp_obj = requests.post(url=url_for('analyze', _external=True), data=json_data, headers=headers)
		resp_obj = json.loads(resp_obj.text) # this is a json object, like a dict
		# converting to pretty print json
		resp_obj = json.dumps(resp_obj, indent=4)
		return redirect(url_for('output', name=name, resp_obj=resp_obj, filename=filename))
	return render_template('index.html', form = form)

@app.route("/output", methods=['GET', 'POST'])
def output():
	name = request.args['name']
	json_obj = request.args['resp_obj']
	image_filename = 'uploads/'+request.args['filename']
	resp_obj = json.loads(json_obj)

	# just to take a good look at the response object from deepface.
	print(json.dumps(resp_obj, indent=4))
	
	age = resp_obj['demographies']['img_1'][0]['age']
	dominant_emotion = resp_obj['demographies']['img_1'][0]['dominant_emotion']
	dominant_gender = resp_obj['demographies']['img_1'][0]['dominant_gender']
	dominant_race = resp_obj['demographies']['img_1'][0]['dominant_race']
	emotions_keys = (resp_obj['demographies']['img_1'][0]['emotion']).keys()
	emotions_values = (resp_obj['demographies']['img_1'][0]['emotion']).values()
	race = (resp_obj['demographies']['img_1'][0]['race']).items()
	race_keys = (resp_obj['demographies']['img_1'][0]['race']).keys()
	race_values = (resp_obj['demographies']['img_1'][0]['race']).values()
	gender_keys = (resp_obj['demographies']['img_1'][0]['gender']).keys()
	gender_values = (resp_obj['demographies']['img_1'][0]['gender']).values()

	resp_obj = json2html.convert(
		json = resp_obj, 
		clubbing = False, 
		table_attributes="id=\"info-table\" class=\"table table-bordered table-hover\"")

	return render_template('output.html', 
	name=name, 
	resp_obj=resp_obj, 
	image_filename=image_filename,
	age=age,
	dominant_emotion=dominant_emotion,
	dominant_gender=dominant_gender,
	dominant_race=dominant_race,
	emotions_keys=emotions_keys,
	emotions_values=emotions_values,
	race_keys=race_keys,
	race_values=race_values,
	gender_keys=gender_keys,
	gender_values=gender_values,
	race=race)

#-----------------------------
#-----------------------------
@app.route('/analyze', methods=['POST'])
def analyze():

	global graph

	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()

	#---------------------------

	if tf_version == 1:
		with graph.as_default():
			resp_obj = analyzeWrapper(req, trx_id)
	elif tf_version == 2:
		resp_obj = analyzeWrapper(req, trx_id)

	#---------------------------

	toc = time.time()

	resp_obj["trx_id"] = trx_id
	resp_obj["seconds"] = toc-tic

	return resp_obj, 200

def analyzeWrapper(req, trx_id = 0):
	resp_obj = {}

	instances = []
	if "img" in list(req.keys()):
		raw_content = req["img"] #list

		for item in raw_content: #item is in type of dict
			instances.append(item)

	if len(instances) == 0:
		return {'success': False, 'error': 'you must pass at least one img object in your request'}

	print("Analyzing ", len(instances)," instances")

	#---------------------------

	detector_backend = 'opencv'
	actions= ['emotion', 'age', 'gender', 'race']
	align = True
	enforce_detection = True

	if "actions" in list(req.keys()):
		actions = req["actions"]

	if "detector_backend" in list(req.keys()):
		detector_backend = req["detector_backend"]
	
	if "align" in list(req.keys()):
		align = req["align"]
	
	if "enforce_detection" in list(req.keys()):
		enforce_detection = req["enforce_detection"]

	#---------------------------

	try:
		resp_obj["demographies"] = {}
		for idx, instance in enumerate(instances):

			demographies = DeepFace.analyze(img_path = instance, 
										detector_backend = detector_backend, 
										actions = actions, align = align, 
										enforce_detection = enforce_detection)
			resp_obj["demographies"][f"img_{idx+1}"] = demographies

	except Exception as err:
		print("Exception: ", str(err))
		return jsonify({'success': False, 'error': str(err)}), 205

	#---------------
	return resp_obj

@app.route('/verify', methods=['POST'])
def verify():

	global graph

	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()

	resp_obj = jsonify({'success': False})

	if tf_version == 1:
		with graph.as_default():
			resp_obj = verifyWrapper(req, trx_id)
	elif tf_version == 2:
		resp_obj = verifyWrapper(req, trx_id)

	#--------------------------

	toc =  time.time()

	resp_obj["trx_id"] = trx_id
	resp_obj["seconds"] = toc-tic

	return resp_obj, 200

def verifyWrapper(req, trx_id = 0):

	resp_obj = {}

	model_name = "VGG-Face"; distance_metric = "cosine"; detector_backend = "opencv"
	align = True; enforce_detection = True
	if "model_name" in list(req.keys()):
		model_name = req["model_name"]
	if "distance_metric" in list(req.keys()):
		distance_metric = req["distance_metric"]
	if "detector_backend" in list(req.keys()):
		detector_backend = req["detector_backend"]
	if "align" in list(req.keys()):
		align = req["align"]
	if "enforce_detection" in list(req.keys()):
		enforce_detection = req["enforce_detection"]
	#----------------------
	try:
		if "img" in list(req.keys()):
			raw_content = req["img"] #list

			if len(raw_content) == 0:
				return jsonify({'success': False, 'error': 'you must pass at least one img object in your request'}), 205
			
			print("Input request of ", trx_id, " has ",len(raw_content)," pairs to verify")

			results = []
			for idx, item in enumerate(raw_content): #item is in type of dict
				img1 = item["img1"]; img2 = item["img2"]

				validate_img1 = False
				if len(img1) > 11 and img1[0:11] == "data:image/":
					validate_img1 = True

				validate_img2 = False
				if len(img2) > 11 and img2[0:11] == "data:image/":
					validate_img2 = True

				if validate_img1 != True or validate_img2 != True:
					return jsonify({'success': False, 'error': 'you must pass both img1 and img2 as base64 encoded string'}), 205
				
				result = DeepFace.verify(img1_path=img1, 
								img2_path=img2, 
								model_name=model_name, 
								detector_backend=detector_backend, 
								distance_metric=distance_metric,
								align=align,
								enforce_detection=enforce_detection,
								)
				results.append(result)
				
			resp_obj[f"pairs"] = results
	except Exception as err:
		resp_obj = jsonify({'success': False, 'error': str(err)}), 205		

	return resp_obj

@app.route('/represent', methods=['POST'])
def represent():

	global graph

	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()

	resp_obj = jsonify({'success': False})

	if tf_version == 1:
		with graph.as_default():
			resp_obj = representWrapper(req, trx_id)
	elif tf_version == 2:
		resp_obj = representWrapper(req, trx_id)

	#--------------------------

	toc =  time.time()

	resp_obj["trx_id"] = trx_id
	resp_obj["seconds"] = toc-tic

	return resp_obj, 200

def representWrapper(req, trx_id = 0):

	resp_obj = jsonify({'success': False})

	#-------------------------------------
	#find out model

	model_name = "VGG-Face"; detector_backend = 'opencv'

	if "model_name" in list(req.keys()):
		model_name = req["model_name"]

	if "detector_backend" in list(req.keys()):
		detector_backend = req["detector_backend"]

	#-------------------------------------
	#retrieve images from request

	img = ""
	if "img" in list(req.keys()):
		img = req["img"] #list
		#print("img: ", img)

	validate_img = False
	if len(img) > 11 and img[0:11] == "data:image/":
		validate_img = True

	if validate_img != True:
		print("invalid image passed!")
		return jsonify({'success': False, 'error': 'you must pass img as base64 encoded string'}), 205

	#-------------------------------------
	#call represent function from the interface

	try:

		embedding_objs = DeepFace.represent(img
			, model_name = model_name
			, detector_backend = detector_backend
		)

	except Exception as err:
		print("Exception: ",str(err))
		resp_obj = jsonify({'success': False, 'error': str(err)}), 205

	#-------------------------------------

	#print("embedding is ", len(embedding)," dimensional vector")
	resp_obj = {}
	faces = []
	for embedding_obj in embedding_objs:
		face = {}
		face["embedding"] = embedding_obj["embedding"]
		face["facial_area"] = embedding_obj["facial_area"]
		face["model_name"] = model_name
		face["detector_backend"] = detector_backend
		faces.append(face)

	resp_obj["embeddings"] = faces

	#-------------------------------------

	return resp_obj

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-p', '--port',
		type=int,
		default=5000,
		help='Port of serving api')
	args = parser.parse_args()
	app.run(host='0.0.0.0', port=args.port, debug=True)