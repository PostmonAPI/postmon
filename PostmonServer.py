import bottle
import json
from bottle import route, run, response
from CepTracker import CepTracker
import requests
from correios import Correios
from database import MongoDb as Database

app_v1 = bottle.Bottle()
jsonp_query_key = 'callback'

def expired(record_date):
	from datetime import datetime, timedelta

	WEEKS = 26 #6 months

	now = datetime.now()

	return ( now - record_date['v_date'] >= timedelta(weeks=WEEKS))


def _get_info_from_source(cep):
	tracker = CepTracker()
	info = tracker.track(cep)
	if len(info) == 0:
		raise ValueError()
	return info


def format_result(result):
	# checa se foi solicitada resposta em JSONP
	js_func_name = bottle.request.query.get(jsonp_query_key)

	if js_func_name:
		# se a resposta vai ser JSONP, o content type deve ser js e seu
		# conteudo deve ser JSON
		response.content_type = 'application/javascript'
		result = json.dumps(result)

		result = '%s(%s);' % (js_func_name, result)
	return result


@route('/cep/<cep:re:\d{5}-?\d{3}>')
@app_v1.route('/cep/<cep:re:\d{5}-?\d{3}>')
def verifica_cep(cep):
	cep = cep.replace('-','')
	db = Database()
	response.headers['Access-Control-Allow-Origin'] = '*'

	result = db.get_one(cep, fields={ '_id': False })
	if result and result.has_key('v_date') and not expired(result):
		result.pop('v_date')
	else:
		try:
			info = _get_info_from_source(cep)
		except ValueError:
			response.status = '404 O CEP %s informado nao pode ser localizado' % cep
			return
		except requests.exceptions.RequestException:
			response.status = '503 Servico Temporariamente Indisponivel'
			return
		for item in info:
			db.insert_or_update(item)
		result = db.get_one(cep, fields={ '_id': False, 'v_date': False })

	if result:

		response.headers['Cache-Control'] = 'public, max-age=2592000'
		return format_result(result)
	else:
		response.status = '404 O CEP %s informado nao pode ser localizado' % cep
		return


@app_v1.route('/rastreio/<provider>/<track>')
def track_pack(provider, track):
	if provider == 'ect':
		try:
			encomenda = Correios.encomenda(track)

			resposta = dict()
			result = []

			for status in encomenda.status:
				historico = dict()
				
				historico['data'] = status.data
				historico['local'] = status.local
				historico['situacao'] = status.situacao
				historico['detalhes'] = status.detalhes

				result.append(historico)

			resposta['servico'] = provider
			resposta['codigo'] = track
			resposta['historico'] = result

			return format_result(resposta)

		except AttributeError:
			response.status = '404 O pacote %s informado nao pode ser localizado' %track
	else:
		response.status = '404 O Servico %s nao pode ser encontrado' %provider

bottle.mount('/v1', app_v1)

def _standalone(port=9876):
    run(host='localhost', port=port)
