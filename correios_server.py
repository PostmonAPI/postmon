from bottle import route, run, error, response
from correios import CepTracker

import pymongo, json, re

def expired(record_date):
	from datetime import datetime, timedelta

	WEEKS = 26 #6 months

	now = datetime.now()

	return ( now - record_date['v_date'] >= timedelta(weeks=WEEKS))


def _get_info_from_correios(cep):
	tracker = CepTracker()
	info = tracker.track(cep)

	if len(info) == 0:
		raise ValueError()

	return info

@route('/cep/<cep:re:\d{5}-?\d{3}>')
def verifica_cep(cep):
	cep = cep.replace('-','')

	response.headers['Access-Control-Allow-Origin'] = '*'
	
	try:
		con = pymongo.MongoClient('localhost')
		db = con.postmon
		ceps = db.ceps
		result = ceps.find_one({'cep':cep}, fields={'_id':False})

		if not result or not result.has_key('v_date'):
			info = _get_info_from_correios(cep)
			map(lambda x: ceps.save(x), info)

		elif expired(result):
			info = _get_info_from_correios(cep)
			map(lambda x: ceps.update({'cep': x['cep']}, {'$set':x}), info)

		result = ceps.find_one({'cep':cep}, fields={'_id':False,'v_date':False})

	except ValueError:
		result = dict(status='404',
	        	      message='O CEP %s informado nao pode ser localizado' %cep)		


	if not result.has_key('status'):
		tmp = {'status': '200',
		       'data' : result}

		result = tmp

	return result


def __return_error(code):
	print('error: %s' %code)


@error(404)
def error404(code):
	result_error = json.dumps({'status':'404', 'message': 'Not Found'})
	return result_error

@error(500)
def error500(code):
	result_error = json.dumps({'status':'500', 'message': 'Internal Server Error'})
	return result_error

def _standalone(port=9876):
    run(host='localhost', port=port)
