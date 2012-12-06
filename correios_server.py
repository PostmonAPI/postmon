####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.2.0
####################################################################

from bottle import route, run, error
from correios import CepTracker

import pymongo, json, re


def expired(record_date):
	from datetime import datetime, timedelta

	WEEKS = 26 #6 months

	now = datetime.now()

	return ( now - record_date['v_date'] >= timedelta(weeks=WEEKS))


def _get_info_from_correios(cep):
	tracker = CepTracker()
	return tracker.track(cep)


@route('/cep/<cep>')
def verifica_cep(cep):

	if re.match("[0-9]{8}", cep):
		con = pymongo.MongoClient("localhost")
		db = con.postmon
		ceps = db.ceps
		result = ceps.find_one({"cep":cep}, fields={"_id":False})

		from datetime import date

		#if not result or expired(date(2012, 4, 1)):
		info = None

		if not result or not result.has_key('v_date'):
			info = _get_info_from_correios(cep)
			map(lambda x: ceps.save(x), info)
			result = ceps.find_one({"cep":cep}, fields={'_id':False, 'v_date':False})

		elif expired(result):
			info = _get_info_from_correios(cep)
			map(lambda x: ceps.update({"cep": x['cep']}, {"$set":x}), info)
			result = ceps.find_one({"cep":cep}, fields={"_id":False,'v_date':False})

		else:
			result = ceps.find_one({"cep":cep}, fields={"_id":False,'v_date':False})

	else:
		result = json.dumps({'error':'404'})

	
	return result


@error(404)
def error404(code):
	result_error = json.dumps({'error':'404'})

	return result_error


@error(500)
def error500(code):
	result_error = json.dumps({'error':'500'})

	return result_error



def _standalone(port=9876):
    run(host='localhost', port=port)    	
