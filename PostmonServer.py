#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bottle
import json
import logging
import xmltodict
from bottle import route, run, response, template, HTTPResponse
from CepTracker import CepTracker
import requests
from packtrack import Correios, Royal
from database import MongoDb as Database


logger = logging.getLogger(__name__)

app_v1 = bottle.Bottle()
jsonp_query_key = 'callback'


def expired(record_date):
    if 'v_date' not in record_date:
        return True

    from datetime import datetime, timedelta

    # 6 months
    WEEKS = 26

    now = datetime.now()

    return (now - record_date['v_date'] >= timedelta(weeks=WEEKS))


def _get_info_from_source(cep):
    tracker = CepTracker()
    info = tracker.track(cep)
    if len(info) == 0:
        raise ValueError('CEP %s nao encontrado' % cep)
    return info


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


def make_error(message):
    formats = {
        'json': 'application/json',
        'xml': 'application/xml',
        'jsonp': 'application/javascript',
    }
    format_ = bottle.request.query.get('format', 'json')
    return HTTPResponse(status=message, content_type=formats[format_])


def _get_estado_info(db, sigla):
    sigla = sigla.upper()
    return db.get_one_uf(sigla, fields={'_id': False, 'sigla': False})


def _get_cidade_info(db, sigla_uf, nome_cidade):
    sigla_uf = sigla_uf.upper()
    sigla_uf_nome_cidade = '%s_%s' % (sigla_uf, nome_cidade)
    fields = {
        '_id': False,
        'sigla_uf': False,
        'codigo_ibge_uf': False,
        'sigla_uf_nome_cidade': False,
        'nome': False
    }
    return db.get_one_cidade(sigla_uf_nome_cidade, fields=fields)


@route('/cep/<cep:re:\d{5}-?\d{3}>')
@app_v1.route('/cep/<cep:re:\d{5}-?\d{3}>')
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
        except ValueError:
            message = '404 CEP %s nao encontrado' % cep
            logger.exception(message)
        except requests.exceptions.RequestException:
            message = '503 Servico Temporariamente Indisponivel'
            logger.exception(message)
        else:
            for item in info:
                db.insert_or_update(item)
            result = db.get_one(cep, fields={'_id': False, 'v_date': False})

        if not result:
            if not message:
                message = '404 CEP %s nao encontrado' % cep
                logger.warning(message)
            return make_error(message)

    result.pop('v_date', None)
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
    db = Database()
    result = _get_cidade_info(db, sigla_uf, nome)
    if result:
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return format_result(result)
    else:
        message = '404 Cidade %s-%s nao encontrada' % (nome, sigla_uf)
        logger.warning(message)
        return make_error(message)


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
            message = "404 Pacote %s nao encontrado" % track
            logger.exception(message)
    else:
        message = '404 Servico %s nao encontrado' % provider
        logger.warning(message)
    return make_error(message)

bottle.mount('/v1', app_v1)


@route('/crossdomain.xml')
def crossdomain():
    response.content_type = 'application/xml'
    return template('crossdomain')


def _standalone(port=9876):
    run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    _standalone()
