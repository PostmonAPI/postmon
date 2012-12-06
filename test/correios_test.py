# encoding: utf-8
import unittest

import correios


class CorreiosTest(unittest.TestCase):

	def test_cep_com_rua(self):

		'''
		Logradouro: Rua Rocha 
		Bairro: Bela Vista
		Localidade / UF: São Paulo /SP 
		CEP: 01330000
		'''

		tracker = correios.CepTracker()
		result = tracker.track('01330000')

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

		tracker = correios.CepTracker()
		result = tracker.track('85100000')

		self.assertTrue(len(result) == 1)
		self.assertEqual(result[0]['cep'], '85100000')
		self.assertEqual(result[0]['cidade'], u'Jordão (Guarapuava)')
		self.assertEqual(result[0]['estado'], 'PR')
		self.assertIsNotNone(result[0]['v_date'])

	def test_cep_inexistente(self):

		'''
		CEP: 99999999
		'''

		tracker = correios.CepTracker()
		result = tracker.track('99999999')

		self.assertTrue(len(result) == 0)

	# TODO: existe CEP com mais de um resultado?
