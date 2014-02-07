#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

import requests
import re
import logging
import os

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
        })
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.exception('Erro no site dos Correios')
            raise ex
        return response.text

    def _get_infos_(self, cep):
        from lxml.html import fromstring
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

        for item in itens:

            data = dict()
            data["v_date"] = datetime.now()

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
                else:
                    data[label] = value

            result.append(data)

        return result
