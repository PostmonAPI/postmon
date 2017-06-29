# coding: utf-8
import json
import os

import packtrack
import requests

from database import MongoDb as Database


def correios(track, backend=None, auth=None):
    if backend is None:
        backend = os.getenv('ECT_BACKEND')
    encomenda = packtrack.Correios.track(track, backend=backend, auth=auth)

    if not encomenda:
        raise ValueError(u"Encomenda nao encontrada.")
    if not encomenda.status:
        raise ValueError(u"A encomenda ainda nao tem historico.")

    result = []
    for status in encomenda.status:
        historico = {
            'data': status.data,
            'local': status.local,
            'situacao': status.situacao,
            'detalhes': status.detalhes,
        }
        result.append(historico)
    return result


def register(provider, track, callback):
    """
    Registra o pacote para acompanhamento.
    """
    db = Database()
    return db.packtrack.register(provider, track, callback)


def run(provider, track):
    db = Database()
    obj = db.packtrack.get_one(provider, track)

    if provider != 'ect':
        raise ValueError(u"Unexpected provider: %s" % provider)

    try:
        data = correios(track)
    except ValueError:
        return False

    changed = obj.get('historico') != data
    db.packtrack.update(provider, track, data, changed=changed)
    return changed


def report(provider, track):
    db = Database()
    obj = db.packtrack.get_one(provider, track)

    _meta = obj.pop('_meta')
    callbacks = _meta.pop('callbacks')

    for callback in callbacks:
        data = obj.copy()
        url = callback['callback']
        data['input'] = callback
        headers = {'Content-Type': 'application/json'}
        requests.post(
            url,
            headers=headers,
            data=json.dumps(data))
