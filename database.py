#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import os

import pymongo

from utils import slug


class MongoDb(object):

    _fields = [
        'logradouro',
        'bairro',
        'cidade',
        'estado',
        'complemento'
    ]

    def __init__(self, address='localhost'):
        self._client = pymongo.MongoClient(address)
        USERNAME = os.environ.get('POSTMON_DB_USER')
        PASSWORD = os.environ.get('POSTMON_DB_PASSWORD')
        if all((USERNAME, PASSWORD)):
            self._client.postmon.authenticate(USERNAME, PASSWORD)
        self._db = self._client.postmon
        self.packtrack = PackTrack(self._db.packtrack)

    def create_indexes(self):
        self._db.ceps.ensure_index('cep')

    def get_one(self, cep, **kwargs):
        r = self._db.ceps.find_one({'cep': cep}, **kwargs)
        if r and u'endereço' in r and 'endereco' not in r:
            # Garante que o cache também tem a key `endereco`. #92
            # Novos resultados já são adicionados corretamente.
            r['endereco'] = r[u'endereço']
        return r

    def get_one_uf(self, sigla, **kwargs):
        return self._db.ufs.find_one({'sigla': sigla}, **kwargs)

    def get_one_cidade(self, sigla_uf, nome_cidade, **kwargs):
        sigla_uf = slug(sigla_uf)
        nome_cidade = slug(nome_cidade)
        sigla_uf_nome_cidade = u'{}_{}'.format(sigla_uf, nome_cidade)
        spec = {'sigla_uf_nome_cidade': sigla_uf_nome_cidade}
        return self._db.cidades.find_one(spec, **kwargs)

    def get_one_uf_by_nome(self, nome, **kwargs):
        return self._db.ufs.find_one({'nome': nome}, **kwargs)

    def insert_or_update(self, obj, **kwargs):

        update = {'$set': obj}
        empty_fields = set(self._fields) - set(obj)
        if empty_fields:
            update['$unset'] = dict((x, 1) for x in empty_fields)

        self._db.ceps.update({'cep': obj['cep']}, update, upsert=True)

    def insert_or_update_uf(self, obj, **kwargs):
        update = {'$set': obj}
        self._db.ufs.update({'sigla': obj['sigla']}, update, upsert=True)

    def insert_or_update_cidade(self, obj, **kwargs):
        update = {'$set': obj}
        chave = 'sigla_uf_nome_cidade'
        self._db.cidades.update({chave: obj[chave]}, update, upsert=True)

    def remove(self, cep):
        self._db.ceps.remove({'cep': cep})


class PackTrack(object):

    def __init__(self, collection):
        self._collection = collection

    def _patch(self, obj):
        try:
            _id = obj.pop('_id')
        except KeyError:
            return
        else:
            obj['token'] = str(_id)

    def get_one(self, provider, track):
        spec = {'servico': provider, 'codigo': track}
        obj = self._collection.find_one(spec)
        self._patch(obj)
        return obj

    def get_all(self):
        objs = list(self._collection.find())
        for obj in objs:
            self._patch(obj)
        return objs

    def register(self, provider, track, callback):
        key = {'servico': provider, 'codigo': track}
        data = {
            '$addToSet': {
                '_meta.callbacks': callback,
            },
            '$setOnInsert': {
                '_meta.created_at': datetime.utcnow(),
                '_meta.changed_at': None,
                '_meta.checked_at': None,
            },
        }
        self._collection.find_and_modify(key, data, upsert=True)
        obj = self._collection.find_one(key)
        self._patch(obj)
        return obj['token']

    def update(self, provider, track, data, changed):
        key = {'servico': provider, 'codigo': track}
        now = datetime.utcnow()

        set_ = {
            "_meta.checked_at": now
        }
        if changed:
            set_.update({
                '_meta.changed_at': now,
                'historico': data,
            })

        query = {"$set": set_}
        self._collection.update(key, query)
