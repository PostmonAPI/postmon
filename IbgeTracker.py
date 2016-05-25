#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

from lxml.html import fromstring
from database import MongoDb as Database


class IbgeTracker():

    def __init__(self):
        self.url_ufs = 'http://www.ibge.gov.br/home/geociencias' + \
                       '/areaterritorial/principal.shtm'
        self.url_cidades = 'http://www.ibge.gov.br/home/geociencias' + \
                           '/areaterritorial/area.php?nome=%'

    def _request(self, url):
        response = requests.post(url)
        response.raise_for_status()
        return response.text

    def _get_info_ufs(self, siglas):
        texto = self._request(self.url_ufs)
        html = fromstring(texto)
        seletorcss_linhas = "div#miolo_interno > table > tr"
        linhas = html.cssselect(seletorcss_linhas)
        linhas.pop()  # a primeira é o cabeçalho
        infos = []
        for linha in linhas:
            seletorcss_celulas = "td"
            celulas = linha.cssselect(seletorcss_celulas)
            codigo_ibge = celulas[0].text_content()
            if codigo_ibge in siglas:
                sigla = siglas[codigo_ibge]
                infos.append({
                    'sigla': sigla,
                    'codigo_ibge': codigo_ibge,
                    'nome': celulas[1].text_content().strip(' (*)'),
                    'area_km2': celulas[2].text_content()
                })

        #  neste ponto, após a carga
        #  das cidades, a lista
        #  'infos' deve estar populada

        return infos

    def _get_info_cidades(self):
        texto = self._request(self.url_cidades)
        html = fromstring(texto)
        seletorcss_linhas = "div#miolo_interno > table > tr"
        linhas = html.cssselect(seletorcss_linhas)
        try:
            linhas.pop(0)  # a primeira é o cabeçalho
        except IndexError:
            pass
        infos = []
        for linha in linhas:
            seletorcss_celulas = "td"
            celulas = linha.cssselect(seletorcss_celulas)
            infos.append({
                'codigo_ibge_uf': celulas[0].text_content(),
                'sigla_uf': celulas[1].text_content(),
                'codigo_ibge': celulas[2].text_content(),
                'nome': celulas[3].text_content(),
                'area_km2': celulas[4].text_content()
            })
        return infos

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
            info['sigla_uf_nome_cidade'] = '%s_%s' % (sigla_uf, nome)

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
