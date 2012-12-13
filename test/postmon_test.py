# encoding: utf-8
import unittest

import CepTracker


class CepTrackerTest(unittest.TestCase):

	def setUp(self):
		self.tracker = CepTracker.CepTracker()

	def test_cep_com_rua(self):

		'''
		Logradouro: Rua Rocha 
		Bairro: Bela Vista
		Localidade / UF: São Paulo /SP 
		CEP: 01330000
		'''

		result = self.tracker.track('01330000')

		self.assertTrue(len(result) == 1)
		self.assertEqual(result[0]['cep'], '01330000')
		self.assertEqual(result[0]['logradouro'], 'Rua Rocha')
		self.assertEqual(result[0]['cidade'], u'São Paulo')
		self.assertEqual(result[0]['estado'], 'SP')
		self.assertIsNotNone(result[0]['v_date'])

	def test_cep_sem_rua(self):

		'''
		Localidade / UF: Jordão (Guarapuava) /PR  -  - Povoado 
		CEP: 85100000
		'''

		result = self.tracker.track('85100000')

		self.assertTrue(len(result) == 1)
		self.assertEqual(result[0]['cep'], '85100000')
		self.assertEqual(result[0]['cidade'], u'Jordão (Guarapuava)')
		self.assertEqual(result[0]['estado'], 'PR')
		self.assertIsNotNone(result[0]['v_date'])

	def test_cep_inexistente(self):

		'''
		CEP: 99999999
		'''

		result = self.tracker.track('99999999')

		self.assertTrue(len(result) == 0)

	def test_cep_com_mais_de_um_resultado(self):

		'''
		A busca pelo CEP 75064590 retorna dois resultados

		Logradouro: Rua A 
		Bairro: Vila Jaiara
		Localidade / UF: Anápolis /GO 
		CEP: 75064590

		Logradouro: Rua A 
		Bairro: Vila Jaiara Setor Leste
		Localidade / UF: Anápolis /GO 
		CEP: 75064379
		'''

		result = self.tracker.track('75064590')

		self.assertTrue(len(result) == 2)
		self.assertEqual(result[0]['cep'], '75064590')
		self.assertEqual(result[0]['logradouro'], 'Rua A')
		self.assertEqual(result[0]['bairro'], 'Vila Jaiara')
		self.assertEqual(result[0]['cidade'], u'Anápolis')
		self.assertEqual(result[0]['estado'], 'GO')
		self.assertIsNotNone(result[0]['v_date'])

		self.assertEqual(result[1]['cep'], '75064379')
		self.assertEqual(result[1]['logradouro'], 'Rua A')
		self.assertEqual(result[1]['bairro'], 'Vila Jaiara Setor Leste')
		self.assertEqual(result[1]['cidade'], u'Anápolis')
		self.assertEqual(result[1]['estado'], 'GO')
		self.assertIsNotNone(result[1]['v_date'])


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
