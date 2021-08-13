#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import bottle
import json
import logging
import xmltodict
from bottle import run, request, response, template, HTTPResponse
from bottle.ext.healthcheck import HealthCheck
from raven import Client
from raven.contrib.bottle import Sentry

from CepTracker import CepTracker, _notfound_key
import PackTracker
import requests
from database import MongoDb as Database
from utils import EnableCORS

logger = logging.getLogger(__name__)
HealthCheck(bottle, "/__health__")

app = bottle.default_app()
app.catchall = False
app_v1 = bottle.Bottle()
app_v1.catchall = False
jsonp_query_key = 'callback'

db = Database()
db.create_indexes()


def validate_format(callback):
    def wrapper(*args, **kwargs):
        output_format = request.query.format
        if output_format and output_format not in {'json', 'jsonp', 'xml'}:
            message = "400 Parametro format='%s' invalido." % output_format
            return make_error(message, output_format='json')
        return callback(*args, **kwargs)
    return wrapper


def _notfound(record):
    _meta = record.get('_meta', {})
    return _notfound_key in _meta or _notfound_key in record


def expired(record_date):
    _meta = record_date.get('_meta', {})
    v_date = _meta.get('v_date') or record_date.get('v_date')
    if not v_date:
        return True

    if _notfound(record_date):
        # 1 week
        WEEKS = 1
    else:
        # 6 months
        WEEKS = 26

    now = datetime.now()
    return (now - v_date >= timedelta(weeks=WEEKS))


def _get_info_from_source(cep):
    tracker = CepTracker()
    return tracker.track(cep)


def format_result(result):
    # checa se foi solicitada resposta em JSONP
    js_func_name = bottle.request.query.get(jsonp_query_key)

    # checa se foi solicitado xml
    format = bottle.request.query.get('format')
    if format == 'xml':
        response.content_type = 'application/xml'
        return xmltodict.unparse({'result': result})

    if js_func_name:
        # se a resposta vai ser JSONP, o content type deve ser js e seu
        # conteudo deve ser JSON
        response.content_type = 'application/javascript'
        result = json.dumps(result)

        result = '%s(%s);' % (js_func_name, result)
    return result


def make_error(message, output_format=None):
    formats = {
        'json': 'application/json',
        'xml': 'application/xml',
        'jsonp': 'application/javascript',
    }
    format_ = output_format or bottle.request.query.get('format', 'json')
    response = HTTPResponse(status=message, content_type=formats[format_])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def _get_estado_info(db, sigla):
    sigla = sigla.upper()
    return db.get_one_uf(sigla, fields={'_id': False, 'sigla': False})


def _get_cidade_info(db, sigla_uf, nome_cidade):
    fields = {
        '_id': False,
        'sigla_uf': False,
        'codigo_ibge_uf': False,
        'sigla_uf_nome_cidade': False,
        'nome': False
    }
    return db.get_one_cidade(sigla_uf, nome_cidade, fields=fields)


@app.route('/cep/<cep:re:'r'\d{5}-?'r'\d{3}>')
@app_v1.route('/cep/<cep:re:'r'\d{5}-?'r'\d{3}>')
def verifica_cep(cep):
    cep = cep.replace('-', '')
    db = Database()
    response.headers['Access-Control-Allow-Origin'] = '*'
    message = None
    result = db.get_one(cep, fields={'_id': False})
    if not result or expired(result):
        result = None
        try:
            info = _get_info_from_source(cep)
        except requests.exceptions.RequestException:
            message = '503 Servico Temporariamente Indisponivel'
            logger.exception(message)
            return make_error(message)
        else:
            for item in info:
                db.insert_or_update(item)
            result = db.get_one(cep, fields={
                '_id': False, 'v_date': False})

    if result:
        notfound = _notfound(result)
    else:
        notfound = True

    if notfound:
        message = '404 CEP %s nao encontrado' % cep
        return make_error(message)

    result.pop('v_date', None)
    result.pop('_meta', None)

    response.headers['Cache-Control'] = 'public, max-age=2592000'
    sigla_uf = result['estado']
    estado_info = _get_estado_info(db, sigla_uf)
    if estado_info:
        result['estado_info'] = estado_info
    nome_cidade = result['cidade']
    cidade_info = _get_cidade_info(db, sigla_uf, nome_cidade)
    if cidade_info:
        result['cidade_info'] = cidade_info
    return format_result(result)


@app_v1.route('/uf/<sigla>')
def uf(sigla):
    response.headers['Access-Control-Allow-Origin'] = '*'
    db = Database()
    result = _get_estado_info(db, sigla)
    if result:
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return format_result(result)
    else:
        message = '404 Estado %s nao encontrado' % sigla
        logger.warning(message)
        return make_error(message)


@app_v1.route('/cidade/<sigla_uf>/<nome>')
def cidade(sigla_uf, nome):
    response.headers['Access-Control-Allow-Origin'] = '*'
    db = Database()
    result = _get_cidade_info(db, sigla_uf, nome.decode('utf-8'))
    if result:
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return format_result(result)
    else:
        message = '404 Cidade %s-%s nao encontrada' % (nome, sigla_uf)
        logger.warning(message)
        return make_error(message)


@app_v1.route('/rastreio/<provider>/<track>')
def track_pack(provider, track):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if provider == 'ect':
        auth = (
            request.headers.get('x-correios-usuario'),
            request.headers.get('x-correios-senha'),
        )
        if auth == (None, None):
            auth = None

        try:
            historico = PackTracker.correios(track, auth=auth)
        except (AttributeError, ValueError):
            message = "404 Pacote %s nao encontrado" % track
            logger.exception(message)
        else:
            return format_result({
                'servico': provider,
                'codigo': track,
                'historico': historico,
            })
    else:
        message = '404 Servico %s nao encontrado' % provider
        logger.warning(message)
    return make_error(message)


@app_v1.route('/rastreio/<token>')
def track_pack_token(token):
    return make_error('404 NOT IMPLEMENTED')


@app_v1.route('/rastreio/<provider>/<track>', method='POST')
def track_pack_register(provider, track):
    """
    Registra o rastreamento do pacote. O `callback` é parâmetro obrigatório,
    qualquer outra informação passada será devolvida quando o `callback` for
    chamado.

    {
        "callback": "http://httpbin.org/post",
        "myid": 1,
        "other": "thing"
    }
    """
    if "callback" not in request.json:
        message = "400 callback obrigatorio"
        return make_error(message)

    try:
        result = PackTracker.register(provider, track, request.json)
    except (AttributeError, ValueError):
        message = "400 Falha no registro do %s/%s" % (provider, track)
        logger.exception(message)
        return make_error(message)
    else:
        return format_result({
            'token': result,
        })


@app.route('/crossdomain.xml')
def crossdomain():
    response.content_type = 'application/xml'
    return template('crossdomain')


app.install(validate_format)
app_v1.install(validate_format)
app.install(EnableCORS())
app_v1.install(EnableCORS())
app.mount('/v1', app_v1)

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_client = Client(SENTRY_DSN)
    app = Sentry(app, sentry_client)
    app_v1 = Sentry(app_v1, sentry_client)


def _standalone(port=9876):
    run(app=app, host='0.0.0.0', port=port)


if __name__ == "__main__":
    _standalone()
