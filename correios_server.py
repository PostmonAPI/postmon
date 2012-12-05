####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.1.1
####################################################################

from bottle import route, run, error
from correios import CepTracker

import pymongo, json, re


@route('/cep/<cep>')
def verifica_cep(cep):

	if re.match("[0-9]{8}", cep):
		con = pymongo.MongoClient("localhost")
		db = con.postmon
		ceps = db.ceps
		result = ceps.find_one({"cep":cep}, fields={'_id':False})

		if not result:
			tracker = CepTracker()
			info = tracker.track(cep)

			cep_id = ceps.insert(info)

			result = ceps.find_one({"cep":cep}, fields={'_id':False})

		resultado = result
	else:
		result_error = json.dumps({'error':'404'})

		resultado = result_error

	return resultado


@error(404)
def error404(code):
	result_error = json.dumps({'error':'404'})

	return result_error


@error(500)
def error500(code):
	result_error = json.dumps({'error':'500'})

	return result_error
