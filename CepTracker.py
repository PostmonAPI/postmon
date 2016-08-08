#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import re

from lxml.html import fromstring
import requests

logger = logging.getLogger(__name__)


class CepTracker():

    def __init__(self):
        self.url = 'http://m.correios.com.br/movel/buscaCepConfirma.do'

    def _request(self, cep):
        response = requests.post(self.url, data={
            'cepEntrada': cep,
            'tipoCep': '',
            'cepTemp': '',
            'metodo': 'buscarCep'
        }, timeout=10)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.exception('Erro no site dos Correios')
            raise ex
        return response.text

    def _get_infos_(self, cep):
        response = self._request(cep)
        html = fromstring(response)
        registro_csspattern = '.caixacampobranco, .caixacampoazul'
        registros = html.cssselect(registro_csspattern)

        resultado = []
        for item in registros:
            item_csspattern = '.resposta, .respostadestaque'
            resultado.append([a.text for a in item.cssselect(item_csspattern)])

        return resultado

    def track(self, cep):
        itens = self._get_infos_(cep)
        result = []

        found = False
        now = datetime.now()

        for item in itens:
            data = {
                "_meta": {
                    "v_date": now,
                }
            }

            for label, value in zip(item[0::2], item[1::2]):

                label = label.lower().strip(' :')
                value = re.sub('\s+', ' ', value.strip())

                if 'localidade' in label:
                    cidade, estado = value.split('/', 1)
                    data['cidade'] = cidade.strip()
                    data['estado'] = estado.split('-')[0].strip()
                elif 'logradouro' in label and ' - ' in value:
                    logradouro, complemento = value.split(' - ', 1)
                    data['logradouro'] = logradouro.strip()
                    data['complemento'] = complemento.strip(' -')
                elif label == u'endereço':
                    # Use sempre a key `endereco`. O `endereço` existe para não
                    # quebrar clientes existentes. #92
                    data['endereco'] = data[label] = value
                else:
                    if label == 'cep' and value == cep:
                        found = True
                    data[label] = value

            result.append(data)

        if not found:
            result.append({
                'cep': cep,
                '_meta': {
                    "v_date": now,
                    '__notfound__': True,
                },
            })
        return result


class CepTracker2(object):

    def __init__(self):
        self.url = "http://www.buscacep.correios.com.br/sistemas/buscacep/resultadoBuscaCepEndereco.cfm?t"  # NOQA

    def _request(self, cep):
        response = requests.post(self.url, data={
            "relaxation": cep,
            "Metodo": "listaLogradouro",
            "TipoConsulta": "relaxation",
            "StartRow": 1,
            "EndRow": 10,
        }, timeout=10)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.exception('Erro no site dos Correios')
            raise ex
        return response.text

    def _get_infos_(self, cep):
        response = self._request(cep)
        html = fromstring(response)
        registros = html.cssselect('.tmptabela tr')

        if not registros:
            return None, []

        header = [h.text.strip(':') for h in registros[0].cssselect('th')]
        registros = registros[1:]
        resultado = []
        for item in registros:
            resultado.append([a.text for a in item.cssselect('td')])

        return header, resultado

    def track(self, cep):
        header, resultado = self._get_infos_(cep)
        result = []

        found = False
        now = datetime.now()

        for item in resultado:
            data = {
                "_meta": {
                    "v_date": now,
                }
            }

            for label, value in zip(header, item):

                label = label.lower().strip()
                value = re.sub('\s+', ' ', value.strip())

                if 'localidade' in label:
                    cidade, estado = value.split('/', 1)
                    data['cidade'] = cidade.strip()
                    data['estado'] = estado.split('-')[0].strip()
                elif 'logradouro' in label:
                    if ' - ' in value:
                        logradouro, complemento = value.split(' - ', 1)
                        data['complemento'] = complemento.strip(' -')
                    else:
                        logradouro = value
                    logradouro = logradouro.strip()
                    if logradouro:
                        data['logradouro'] = logradouro
                elif label == u'endereço':
                    # Use sempre a key `endereco`. O `endereço` existe para não
                    # quebrar clientes existentes. #92
                    data['endereco'] = data[label] = value
                elif 'bairro' in label:
                    data['bairro'] = value
                elif 'cep' in label:
                    _cep = value.replace('-', '')
                    if _cep == cep:
                        found = True
                    data['cep'] = _cep
                else:
                    data[label] = value

            result.append(data)

        if not found:
            result.append({
                'cep': cep,
                '_meta': {
                    "v_date": now,
                    '__notfound__': True,
                },
            })
        return result
