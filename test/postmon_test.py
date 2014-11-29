#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import unittest
import mock

import webtest
import bottle
from requests import RequestException

import CepTracker
import PostmonServer

bottle.DEBUG = True


class PostmonBaseTest(object):

    expected = {
        '01330000': [{
            'logradouro': 'Rua Rocha',
            'bairro': 'Bela Vista',
            'cidade': u'São Paulo',
            'estado': 'SP'
        }],
        '85100000': [{
            'cidade': u'Jordão (Guarapuava)',
            'estado': 'PR'
        }],
        '75064590': [{
            'logradouro': 'Rua A',
            'bairro': 'Vila Jaiara',
            'cidade': u'Anápolis',
            'estado': 'GO'
        }, {
            'logradouro': 'Rua A',
            'bairro': 'Vila Jaiara Setor Leste',
            'cidade': u'Anápolis',
            'estado': 'GO'
        }],
        '12245230': [{
            'logradouro': u'Avenida Tivoli',
            'complemento': u'lado ímpar',
            'bairro': u'Vila Betânia',
            'cidade': u'São José dos Campos',
            'estado': 'SP'
        }],
        '69908768': [{
            'logradouro': 'Rodovia BR-364 (Rio Branco-Porto Velho)',
            'complemento': u'até 5014 - lado par',
            'bairro': 'Loteamento Santa Helena',
            'cidade': 'Rio Branco',
            'estado': 'AC'
        }]
    }

    def test_cep_com_rua(self):
        self.assertCep('01330000')

    def test_cep_sem_rua(self):
        self.assertCep('85100000')

    def test_cep_inexistente(self):
        self.assertCep('99999999')

    def test_cep_com_mais_de_um_resultado(self):
        self.assertCep('75064590')

    def test_ceps_com_complemento(self):
        self.assertCep('12245230')
        self.assertCep('69908768')


class CepTrackerTest(unittest.TestCase, PostmonBaseTest):

    def setUp(self):
        self.tracker = CepTracker.CepTracker()

    def get_cep(self, cep):
        return self.tracker.track(cep)

    def assertCep(self, cep):

        result = self.get_cep(cep)
        expected = self.expected.get(cep, [])

        self.assertEqual(len(expected), len(result))

        for e, r in zip(expected, result):
            for key, value in e.items():
                self.assertIn(key, r)
                self.assertEqual(value, r[key])

            self.assertIn('v_date', r)


class CepTrackerMockTest(CepTrackerTest):

    '''
    O CepTrackerMockTest usa arquivos locais com os resultados
    obtidos nos Correios. Assim é possível saber se os testes do
    CepTrackerTest quebraram por problemas no código ou por alteração
    nos Correios.
    '''

    def setUp(self):
        self.tracker = CepTracker.CepTracker()
        self.tracker._request = self._request_mock

    def _request_mock(self, cep):
        with open('test/assets/' + cep + '.html') as f:
            return f.read().decode('latin-1')


class PostmonWebTest(unittest.TestCase, PostmonBaseTest):

    '''
    Teste do servidor do Postmon
    '''

    def setUp(self):
        self.app = webtest.TestApp(bottle.app())

    def get_cep(self, cep):
        response = self.app.get('/cep/' + cep)
        return response.json

    def assertCep(self, cep):
        expected = self.expected.get(cep, None)
        try:
            result = self.get_cep(cep)
        except webtest.AppError as ex:
            if not expected and '404' in ex.message and cep in ex.message:
                return
            raise ex

        for k, v in expected[0].items():
            self.assertEqual(v, result[k])

        self.assertNotIn('v_date', result)


class PostmonWebJSONPTest(PostmonWebTest):
    '''
    Teste de requisições JSONP no servidor do Postmon
    '''

    def setUp(self):
        self.jsonp_query_key = PostmonServer.jsonp_query_key
        self.jsonp_func_name = 'func_name'
        super(PostmonWebJSONPTest, self).setUp()

    def get_cep(self, cep):
        response = self.app.get(
            '/cep/%s?%s=%s' % (cep,
                               self.jsonp_query_key,
                               self.jsonp_func_name))

        regexp = re.compile('^%s\((.*)\);$' % self.jsonp_func_name)
        json_data = re.findall(regexp, response.body)[0]

        return json.loads(json_data)


class PostmonV1WebTest(PostmonWebTest):

    '''
    Teste do servidor do Postmon no /v1
    '''

    def get_cep(self, cep):
        response = self.app.get('/v1/cep/' + cep)
        return response.json


class PostmonXMLTest(unittest.TestCase):
    """ testa requisições XML """

    def setUp(self):
        self.app = webtest.TestApp(bottle.app())

    def get_cep(self, cep):
        response = self.app.get(
            '/cep/%s?format=xml' % cep
        )
        return response

    def test_xml_return(self):
        import xmltodict
        response = self.get_cep('06708070')
        parsed = xmltodict.parse(response.body)
        result = parsed.get('result')
        self.assertEqual(result['bairro'], u'Parque S\xe3o George')
        self.assertEqual(result['cidade'], u'Cotia')
        self.assertEqual(result['cep'], u'06708070')
        self.assertEqual(result['estado'], u'SP')
        self.assertEqual(result['logradouro'], u'Avenida Eid Mansur')


class PostmonErrors(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(bottle.app())

    def get_cep(self, cep, format='json', expect_errors=False):
        endpoint = '/cep/%s' % cep
        if format == 'xml':
            endpoint += '?format=xml'
        response = self.app.get(endpoint, expect_errors=expect_errors)
        return response

    @mock.patch('PostmonServer._get_info_from_source')
    def test_404_status(self, _mock):
        _mock.return_value = []
        response = self.get_cep('99999999', expect_errors=True)
        self.assertEqual("404 CEP 99999999 nao encontrado", response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_404_status_with_xml_format(self, _mock):
        _mock.return_value = []
        response = self.get_cep('99999999', format='xml', expect_errors=True)
        self.assertEqual("404 CEP 99999999 nao encontrado", response.status)
        self.assertEqual('application/xml', response.headers['Content-Type'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_503_status(self, _mock):
        _mock.side_effect = RequestException
        response = self.get_cep('99999999', expect_errors=True)
        self.assertEqual("503 Servico Temporariamente Indisponivel",
                         response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_503_status_with_xml_format(self, _mock):
        _mock.side_effect = RequestException
        response = self.get_cep('99999999', format='xml', expect_errors=True)
        self.assertEqual("503 Servico Temporariamente Indisponivel",
                         response.status)
        self.assertEqual('application/xml', response.headers['Content-Type'])
        self.assertEqual('', response.body)
