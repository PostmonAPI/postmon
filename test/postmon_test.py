#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import re
import unittest
import mock

import webtest
import bottle
from bson.objectid import ObjectId
from packtrack import correios
from requests import RequestException

import CepTracker
import PackTracker
from PostmonServer import expired, jsonp_query_key
from database import MongoDb

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
        }],
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
        expected = self.expected.get(cep)

        if not expected:
            self.assertTrue(result[0]['_meta'][CepTracker._notfound_key])
            return

        self.assertEqual(len(expected), len(result))

        for e, r in zip(expected, result):
            for key, value in e.items():
                self.assertIn(key, r)
                self.assertEqual(value, r[key])
            self.assertIn('_meta', r)
            self.assertIn('v_date', r['_meta'])


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
        with open('test/assets/buscacep/' + cep + '.html') as f:
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
        expected = self.expected.get(cep)
        try:
            result = self.get_cep(cep)
        except webtest.AppError as ex:
            if not expected and '404' in ex.message and cep in ex.message:
                return
            raise ex

        for k, v in expected[0].items():
            self.assertEqual(v, result[k])

        self.assertNotIn('_meta', result)
        self.assertNotIn('v_date', result)


class PostmonWebJSONPTest(PostmonWebTest):
    '''
    Teste de requisições JSONP no servidor do Postmon
    '''

    def setUp(self):
        self.jsonp_query_key = jsonp_query_key
        self.jsonp_func_name = 'func_name'
        super(PostmonWebJSONPTest, self).setUp()

    def get_cep(self, cep):
        response = self.app.get(
            '/cep/%s?%s=%s' % (cep,
                               self.jsonp_query_key,
                               self.jsonp_func_name))

        regexp = re.compile(r'^%s\((.*)\);$' % self.jsonp_func_name)
        json_data = re.findall(regexp, response.body)[0]

        return json.loads(json_data)


class PostmonV1WebTest(PostmonWebTest):

    '''
    Teste do servidor do Postmon no /v1
    '''
    @classmethod
    def setUpClass(cls):
        cls.db = MongoDb()
        cls.db.insert_or_update_uf({
            'sigla': 'SP',
            'campo': 'valor',
        })
        cls.db.insert_or_update_cidade({
            'sigla_uf_nome_cidade': u'SP_SAO PAULO',
            'area_km2': '1099',
        })

    @classmethod
    def tearDownClass(cls):
        cls.db._db.cidades.remove()
        cls.db._db.ufs.remove()

    def setUp(self):
        super(PostmonV1WebTest, self).setUp()

    def get_cep(self, cep):
        response = self.app.get('/v1/cep/' + cep)
        return response.json

    def test_uf(self):
        response = self.app.get('/v1/uf/sp')
        jr = json.loads(response.body)
        self.assertEqual({'campo': 'valor'}, jr)

    def test_uf_404(self):
        response = self.app.get('/v1/uf/xx', expect_errors=True)
        self.assertEqual('404 Estado xx nao encontrado', response.status)

    def test_cidade(self):
        response = self.app.get('/v1/cidade/SP/S%C3%83O PAULO')
        jr = json.loads(response.body)
        self.assertEqual({'area_km2': '1099'}, jr)

    def test_cidade_404(self):
        response = self.app.get('/v1/cidade/SP/XX', expect_errors=True)
        self.assertEqual('404 Cidade XX-SP nao encontrada', response.status)


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


class PostmonOtherRoutesTest(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(bottle.app())

    def test_crossdomain(self):
        expected = bottle.template('crossdomain')
        response = self.app.get('/crossdomain.xml')
        self.assertMultiLineEqual(expected, response.body)


class PostmonErrors(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(bottle.app())

    def get_cep(self, cep, format='json', expect_errors=False, use_v1=False):
        endpoint = ''
        if use_v1:
            endpoint += '/v1'
        endpoint += '/cep/%s' % cep
        if format != 'json':
            endpoint += '?format=' + format
        response = self.app.get(endpoint, expect_errors=expect_errors)
        return response

    @mock.patch('PostmonServer._get_info_from_source')
    def test_404_status(self, _mock):
        _mock.return_value = []
        response = self.get_cep('99999999', expect_errors=True)
        self.assertEqual("404 CEP 99999999 nao encontrado", response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_404_status_with_xml_format(self, _mock):
        _mock.return_value = []
        response = self.get_cep('99999999', format='xml', expect_errors=True)
        self.assertEqual("404 CEP 99999999 nao encontrado", response.status)
        self.assertEqual('application/xml', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_503_status(self, _mock):
        _mock.side_effect = RequestException
        response = self.get_cep('88888888', expect_errors=True)
        self.assertEqual("503 Servico Temporariamente Indisponivel",
                         response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer._get_info_from_source')
    def test_503_status_with_xml_format(self, _mock):
        _mock.side_effect = RequestException
        response = self.get_cep('88888888', format='xml', expect_errors=True)
        self.assertEqual("503 Servico Temporariamente Indisponivel",
                         response.status)
        self.assertEqual('application/xml', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)

    def test_invalid_format(self):
        response = self.get_cep('99999999', format='xxx', expect_errors=True)
        self.assertEqual("400 Parametro format='xxx' invalido.",
                         response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)

    @mock.patch('PostmonServer.Database')
    def test_404_cache_hit(self, _db):
        cep = '99999999'
        _db_instance = mock.Mock()
        _db.return_value = _db_instance
        _db_instance.get_one.return_value = {
            'cep': cep,
            CepTracker._notfound_key: True,
            'v_date': datetime.now(),
        }
        response = self.get_cep(cep, expect_errors=True)
        self.assertEqual("404 CEP %s nao encontrado" % cep, response.status)
        self.assertEqual('application/json', response.headers['Content-Type'])
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        self.assertEqual('', response.body)
        _db_instance.get_one.assert_called_with(cep, fields={'_id': False})


class PostmonV1Errors(PostmonErrors):

    def get_cep(self, cep, format='json', expect_errors=False, use_v1=True):
        return super(PostmonV1Errors, self).get_cep(cep, format,
                                                    expect_errors, use_v1)


class TestExpired(unittest.TestCase):

    def test_empty(self):
        self.assertTrue(expired({}))

    def test_v_date_backward_compatibility(self):
        dt = datetime.now() - timedelta(weeks=5)
        obj = {'v_date': dt}
        self.assertFalse(expired(obj))

    def test_v_date_expired_backward_compatibility(self):
        dt = datetime.now() - timedelta(weeks=54)
        obj = {'v_date': dt}
        self.assertTrue(expired(obj))

    def test_meta_v_date(self):
        dt = datetime.now() - timedelta(weeks=5)
        obj = {'_meta': {'v_date': dt}}
        self.assertFalse(expired(obj))

    def test_meta_v_date_expired(self):
        dt = datetime.now() - timedelta(weeks=54)
        obj = {'_meta': {'v_date': dt}}
        self.assertTrue(expired(obj))

    def test_notfound(self):
        dt = datetime.now() - timedelta(weeks=2)
        obj = {'_meta': {'v_date': dt, CepTracker._notfound_key: True}}
        self.assertFalse(expired(obj))

    def test_notfound_expired_early(self):
        dt = datetime.now() - timedelta(weeks=5)
        obj = {'_meta': {'v_date': dt, CepTracker._notfound_key: True}}
        self.assertTrue(expired(obj))


class TestDatabase(unittest.TestCase):
    def test_insert_notfound(self):
        db = MongoDb()
        cep = u'11111111'
        db.remove(cep)
        db.insert_or_update({
            u'cep': cep,
            u'_meta': {
                u'v_date': 'v_date',
                CepTracker._notfound_key: True,
            }
        })
        expected = {
            u'cep': cep,
            u'estado': u'SP',
            u'_meta': {
                u'v_date': 'v_date',
            }
        }
        db.insert_or_update(expected)
        result = db.get_one(cep, fields={'_id': False})
        self.assertEqual(expected, result)


class PackTrackTest(unittest.TestCase):

    def setUp(self):
        db = MongoDb()
        self.collection = db.packtrack._collection
        self.app = webtest.TestApp(bottle.app())

    def tearDown(self):
        self.collection.remove()

    def _get(self, track, provider='ect', expect_errors=False):
        url = '/v1/rastreio/{}/{}'.format(provider, track)
        response = self.app.get(url, expect_errors=expect_errors)
        if expect_errors:
            return response

        jr = json.loads(response.body)
        return jr

    def _post(self, track, data):
        url = '/v1/rastreio/ect/' + track
        response = self.app.post(url, json.dumps(data),
                                 headers={'Content-Type': 'application/json'})
        jr = json.loads(response.body)
        return jr

    @mock.patch('PackTracker.correios')
    def test_get(self, _mock):
        data = [{
            "codigo": "test",
            "servico": "ect",
            "historico": [{
                "detalhes": None,
                "local": "AGF SAO PATRICIO - Sao Paulo/SP",
                "data": "19/07/2016 11:37",
                "situacao": "Postado"
            }]
        }]
        _mock.return_value = data[0]["historico"]
        response = self._get("test")
        self.assertEqual(data[0], response)

    @mock.patch('PackTracker.correios')
    def test_get_404(self, _mock):
        _mock.side_effect = AttributeError
        response = self._get("test", expect_errors=True)
        self.assertEqual('404 Pacote test nao encontrado', response.status)

    def test_get_another_provider(self):
        response = self._get("test", provider="google", expect_errors=True)
        self.assertEqual('404 Servico google nao encontrado', response.status)

    def test_register_packtrack(self):
        data = {
            'callback': 'http://example.com',
        }
        response = self._post('test', data)
        self.assertTrue(response['token'])

    def test_register_same_packtrack(self):
        data = [{
            'callback': 'http://example.com',
            'something': 'XXX',
        }, {
            'callback': 'http://example.com',
            'something': 'YYY',
        }]
        response = self._post('test', data[0])
        token = response['token']

        response = self._post('test', data[1])
        self.assertEqual(token, response['token'])

        obj = self.collection.find_one(ObjectId(token))
        self.assertEqual(data, obj['_meta']['callbacks'])

    def test_register_same_callback(self):
        data = {
            'callback': 'http://example.com',
            'something': 'XXX',
        }
        response = self._post('test', data)
        token = response['token']
        response = self._post('test', data)

        obj = self.collection.find_one(ObjectId(token))
        self.assertEqual([data], obj['_meta']['callbacks'])

    @mock.patch('PackTracker.correios')
    def test_run(self, _mock):
        _mock.return_value = [{
            "detalhes": None,
            "local": "AGF SAO PATRICIO - Sao Paulo/SP",
            "data": "19/07/2016 11:37",
            "situacao": "Postado"
        }]
        data = {
            'callback': 'http://example.com',
            'something': 'XXX',
        }
        self._post('test', data)
        changed = PackTracker.run('ect', 'test')
        self.assertTrue(changed)

        self._post('test', data)
        changed = PackTracker.run('ect', 'test')
        self.assertFalse(changed)

        _mock.return_value.append({
            "detalhes": "Encaminhado para UNIDADE DE CORREIOS/BR",
            "local": "AGF SAO PATRICIO - Sao Paulo/SP",
            "data": "20/07/2016 08:46",
            "situacao": "Encaminhado"
        })
        self._post('test', data)
        changed = PackTracker.run('ect', 'test')
        self.assertTrue(changed)

        self._post('test', data)
        changed = PackTracker.run('ect', 'test')
        self.assertFalse(changed)

    @mock.patch('PackTracker.requests.post')
    def test_report(self, _mock_requests):

        input_data = {
            'callback': 'http://example.com',
            'something': 'XXX',
        }
        response = self._post('test', input_data)
        token = response['token']

        encomenda = correios.Encomenda('track')
        status = correios.Status(
            local="AGF SAO PATRICIO - Sao Paulo/SP",
            data="19/07/2016 11:37",
            situacao="Postado",
        )
        encomenda.adicionar_status(status)
        with mock.patch('PackTracker.packtrack') as _mock_correios:
            _mock_correios.Correios.track.return_value = encomenda
            changed = PackTracker.run('ect', 'test')
        self.assertTrue(changed)

        PackTracker.report('ect', 'test')

        call = _mock_requests.call_args
        self.assertEqual(('http://example.com',), call[0])

        data = json.loads(call[1]['data'])

        self.assertEqual(input_data, data['input'])
        self.assertEqual(token, data['token'])
        self.assertEqual([{
            u'detalhes': status.detalhes,
            u'local': status.local,
            u'situacao': status.situacao,
            u'data': status.data,
        }], data['historico'])
