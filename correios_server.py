####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.1.0
####################################################################

from bottle import route, run, error
from correios import CepTracker

import pymongo
import json

@route('/cep/<cep>')
def verifica_cep(cep):

	con = pymongo.MongoClient("192.168.122.43")
	db = con.postmon
	ceps = db.ceps
	result = ceps.find_one({"cep":cep}, fields={'_id':False})

	if not result:
		tracker = CepTracker()
		info = tracker.track(cep)

		cep_id = ceps.insert(info)

		result = ceps.find_one({"cep":cep}, fields={'_id':False})

	return result

@error(404)
def error(code):
	result_error = json.dumps({'error':"404"})

	return result_error

run(host="localhost", port=8080)