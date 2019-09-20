#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

from database import MongoDb as Database
from utils import slug


class IbgeTracker():

    def __init__(self):
        base_url = 'https://raw.githubusercontent.com/PostmonAPI/ibge-parser/master/data/postmon'
        self.url_ufs = base_url + '/ufs.json'
        self.url_cidades = base_url + '/cidades.json'

    def _request(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def _get_info_ufs(self, siglas):
        return self._request(self.url_ufs)

    def _get_info_cidades(self):
        return self._request(self.url_cidades)

    def _track_ufs(self, db, siglas):
        infos = self._get_info_ufs(siglas)
        for info in infos:
            db.insert_or_update_uf(info)

    def _track_cidades(self, db):
        infos = self._get_info_cidades()
        siglas = {}
        for info in infos:
            codigo_ibge_uf = info['codigo_ibge_uf']
            sigla_uf = info['sigla_uf']
            nome = info['nome']
            if codigo_ibge_uf not in siglas:
                siglas[codigo_ibge_uf] = sigla_uf

            # a chave única de uma cidade não
            # pode ser só o nome, pois
            # existem cidades com mesmo nome
            # em estados diferentes
            info['sigla_uf_nome_cidade'] = slug('%s_%s' % (sigla_uf, nome))

            db.insert_or_update_cidade(info)

        return siglas

    def track(self, db):
        """
        Atualiza as bases internas do mongo
        com os dados mais recentes do IBGE
        referente a ufs e cidades
        """
        siglas = self._track_cidades(db)
        # siglas é um dict cod_ibge -> sigla:
        # { '35': 'SP', '35': 'RJ', ... }
        self._track_ufs(db, siglas)


def _standalone():
    db = Database()
    ibge = IbgeTracker()
    ibge.track(db)


if __name__ == "__main__":
    _standalone()
