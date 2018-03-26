import atexit
import cf_deployment_tracker
import os
import json
from datetime import datetime
from cloudant import Cloudant
from cloudant.result import Result, ResultByKey
from flask import Flask, render_template, request, jsonify

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

#cloudant
db_name = 'rastreador'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
        user = '<cloudant-user>'
        password = '<cloudant-pass>'
        url = '<cloudant-URL>'
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])

@app.route('/listarjson')
def get_listarmapa():
	if client:
		totalDocs = db.doc_count()
        #view = db.all_docs()
		result_collection = Result(db.all_docs, include_docs=True)
		result = result_collection[totalDocs-1]
        #resultjson = json.loads(result[0])
	    #return type(resultjson).__name__
	return jsonify(result[0])

@app.route('/list')
def get_list():
    if client:
        lat_gra = 0
        lat_min = 0
        lat_sec = 0
        lat_mul = 1
        latitude = ''
        lat = 0

        lon_gra = 0
        lon_min = 0
        lon_sec = 0
        lon_mul = 1
        longitude = ''
        long = 0

        totalDocs = db.doc_count()
        result_collection = Result(db.all_docs, include_docs=True)
        result = result_collection[totalDocs-1]

        #conversao degree para decimal (Latitude)
        latitude = str(result[0]['doc']['payload']['d']['col3'])
        lat_gra = float(latitude[0:2])
        lat_min = float(latitude[2:4])/60
        lat_sec = float(latitude[4:])/3600
        if ( str(result[0]['doc']['payload']['d']['col4']) == 'S' ):
            lat_mul = -1
        else:
            lat_mul = 1
        lat = lat_mul * (lat_gra + lat_min + lat_sec)

        #conversao degree para decimal (Longitude)
        longitude = str(result[0]['doc']['payload']['d']['col5'])
        lon_gra = float(longitude[0:2])
        lon_min = float(longitude[2:4])/60
        lon_sec = float(longitude[4:])/3600
        if ( str(result[0]['doc']['payload']['d']['col6']) == 'W' ):
            lon_mul = -1
        else:
            lon_mul = 1
        lon = lon_mul * (lon_gra + lon_min + lon_sec)
    #resultjson = json.loads(result[0])
	#return type(resultjson).__name__
	#return jsonify(result[0]['doc']['payload']['d'])
    #return str(lon_mul*(lon_gra+lon_min+lon_sec))
    return render_template('mapa_itiro.html',lat=lat, lon=lon)

@app.route('/fruit')
def fruits():
    array = '{"fruits": ["apple", "banana", "orange"]}'
    data  = json.loads(array)
    fruits_list = data['fruits']
    return fruits_list[0]

@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    if client:
        data = {'name':user}
        db.create_document(data)
        return 'Hello %s! I added you to the database.' % user
    else:
        print('No database')
        return 'Hello %s!' % user

@app.route('/maps')
def maps():
	return render_template('maps.html')

@atexit.register
def shutdown():
    if client:
        client.disconnect()

port = int(os.getenv('PORT', 5000))
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port, debug=True)
