####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.0
####################################################################

from bottle import route, run, template
from correios import CepTracker

import pymongo

@route('/cep/<cep>')
def verifica_cep(cep):

	con = pymongo.MongoClient("localhost")

	db = con.postmon

	ceps = db.ceps
	result = ceps.find_one({"cep":cep}, fields={'_id':False})

	if result:
		retorno = result

	else:
		tracker = CepTracker()
		info = tracker.track(cep)

		cep_id = ceps.insert(info)

		retorno = ceps.find_one({"cep":cep}, fields={'_id':False})

	return retorno
