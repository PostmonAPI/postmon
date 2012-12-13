# encoding: utf-8
import unittest

import webtest
import bottle

import CepTracker
import PostmonServer

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

		for k, v in expected[0].items():
			self.assertEqual(v, result[k])

		self.assertNotIn('v_date', result)
