####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.3.0
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
	info = tracker.track(cep)

	if len(info) == 0:
		raise ValueError()

	return info



@route('/cep/<cep>')
def verifica_cep(cep):
	cep = cep.replace('-','')

	try:
		if re.match('[0-9]{8}', cep):
			con = pymongo.MongoClient('localhost')
			db = con.postmon
			ceps = db.ceps
			result = ceps.find_one({'cep':cep}, fields={'_id':False})

			from datetime import date

			info = None
			
			if not result or not result.has_key('v_date'):
				info = _get_info_from_correios(cep)
				map(lambda x: ceps.save(x), info)
				result = ceps.find_one({'cep':cep}, fields={'_id':False, 'v_date':False})

			elif expired(result):
				info = _get_info_from_correios(cep)
				map(lambda x: ceps.update({'cep': x['cep']}, {'$set':x}), info)
				result = ceps.find_one({'cep':cep}, fields={'_id':False,'v_date':False})
			else:
				result = ceps.find_one({'cep':cep}, fields={'_id':False,'v_date':False})
		else:
			raise ValueError()

	except ValueError:
		result = dict(status='error',
	        	      message='O Cep %s informado nao pode ser localizado' %cep)		


	if not result.has_key('status'):
		tmp = {'status': 'ok',
		       'data' : result}

		result = tmp

	return result


def __return_error(code):
	print('error: %s' %code)


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
    	
