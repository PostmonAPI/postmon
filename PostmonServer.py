#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bottle
import json
import xmltodict
from bottle import route, run, response
from CepTracker import CepTracker
import requests
from correios import Correios
from database import MongoDb as Database


app_v1 = bottle.Bottle()
jsonp_query_key = 'callback'


def expired(record_date):
    from datetime import datetime, timedelta

    # 6 months
    WEEKS = 26

    now = datetime.now()

    return (now - record_date['v_date'] >= timedelta(weeks=WEEKS))


def _get_info_from_source(cep):
    tracker = CepTracker()
    info = tracker.track(cep)
    if len(info) == 0:
        raise ValueError()
    return info


def format_result(result):
    # checa se foi solicitada resposta em JSONP
    js_func_name = bottle.request.query.get(jsonp_query_key)

    #checa se foi solicitado xml
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

    result = db.get_one(cep, fields={'_id': False})
    if result and 'v_date' in result and not expired(result):
        result.pop('v_date')
    else:
        try:
            info = _get_info_from_source(cep)
        except ValueError:
            response.status = "404 O CEP {0} informado nao pode ser "
            "localizado".format(cep)
            return
        except requests.exceptions.RequestException:
            response.status = '503 Servico Temporariamente Indisponivel'
            return
        for item in info:
            db.insert_or_update(item)
        result = db.get_one(cep, fields={'_id': False, 'v_date': False})

    if result:
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
    else:
        response.status = '404 O CEP %s informado nao pode ser '
        'localizado' % cep
        return


@app_v1.route('/uf/<sigla>')
def uf(sigla):
    db = Database()
    result = _get_estado_info(db, sigla)
    if result:
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return format_result(result)
    else:
        message = '404 A sigla %s informada ' \
                  'nao pode ser localizada'
        response.status = message % sigla
        print response.status
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
            response.status = "404 O pacote {0} informado nao pode ser "
            "localizado".format(track)
    else:
        response.status = '404 O Servico %s nao pode ser encontrado' % provider

bottle.mount('/v1', app_v1)


def _standalone(port=9876):
    run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    _standalone()
