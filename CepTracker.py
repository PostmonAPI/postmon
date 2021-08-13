#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import os
import re

import requests

logger = logging.getLogger(__name__)
_notfound_key = '__notfound__'


class CepTracker(object):
    url = os.getenv(
        "CORREIOS_CEP_URL",
        "https://buscacepinter.correios.com.br/app/endereco/carrega-cep-endereco.php",  # NOQA
    )

    def _request(self, cep):
        response = requests.post(self.url, data={
            "pagina": "/app/endereco/index.php",
            "cepaux": "",
            "mensagem_alerta": "",
            "endereco": cep,
            "tipoCEP": "ALL",
        }, timeout=10)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.exception('Erro no site dos Correios')
            raise ex
        return response.json()

    def track(self, cep):
        data = self._request(cep)
        result = []

        found = False
        now = datetime.now()

        for item in data["dados"]:
            if item['cep'] == cep:
                found = True

            data = {
                "_meta": {
                    "v_date": now,
                },
                "cep": item['cep'],
                "bairro": item['bairro'],
                "cidade": item['localidade'],
                "estado": item['uf'],
            }
            logradouro = item["logradouroDNEC"]
            if ' - ' in logradouro:
                logradouro, complemento = logradouro.split(' - ', 1)
                data['complemento'] = complemento.strip(' -')
            data['logradouro'] = logradouro

            result.append(data)

        if not found:
            result.append({
                'cep': cep,
                '_meta': {
                    "v_date": now,
                    _notfound_key: True,
                },
            })
        return result
