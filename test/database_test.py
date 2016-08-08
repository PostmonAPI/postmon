#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from database import MongoDb


class MongoDbTest(unittest.TestCase):

    def setUp(self):
        self.db = MongoDb()

        self.db.insert_or_update({
            'cep': 'UNIQUE_KEY',
            'logradouro': 'A',
            'bairro': 'A',
            'cidade': 'A',
            'estado': 'A'
        })

    def test_remove_empty_fields(self):

        '''
        Quando um registro é atualizado no banco de dados,
        as chaves inexistentes devem ser removidas.
        '''

        self.db.insert_or_update({
            'cep': 'UNIQUE_KEY',
            'estado': 'B'
        })

        result = self.db.get_one('UNIQUE_KEY')

        self.assertEqual(result['estado'], 'B')
        self.assertNotIn('logradouro', result)
        self.assertNotIn('bairro', result)
        self.assertNotIn('cidade', result)

    def tearDown(self):
        self.db.remove('UNIQUE_KEY')


class UFTest(unittest.TestCase):
    uf_sp = {
        'sigla': 'SP',
        'codigo_ibge': '35',
        'nome': u'São Paulo',
    }

    def setUp(self):
        self.db = MongoDb()
        self.db.insert_or_update_uf(self.uf_sp)

    def tearDown(self):
        self.db._db.ufs.remove()

    def test_get(self):
        result = self.db.get_one_uf_by_nome(u'São Paulo')
        for key, expected in self.uf_sp.items():
            self.assertEqual(expected, result[key])

    def test_update(self):
        self.db.insert_or_update_uf({
            'sigla': u'SP',
            'codigo_ibge': '36'
        })

        result = self.db.get_one_uf_by_nome(u'São Paulo')
        self.assertEqual('36', result['codigo_ibge'])
        self.assertEqual('SP', result['sigla'])


class CidadeTest(unittest.TestCase):
    cidade_sp = {
        'sigla_uf_nome_cidade': u'SP/São Paulo',
        'area_km2': '1099',
    }

    def setUp(self):
        self.db = MongoDb()
        self.db.insert_or_update_cidade(self.cidade_sp)

    def tearDown(self):
        self.db._db.ufs.remove()

    def test_get(self):
        result = self.db.get_one_cidade(u'SP/São Paulo')
        for key, expected in self.cidade_sp.items():
            self.assertEqual(expected, result[key])

    def test_update(self):
        self.db.insert_or_update_cidade({
            'sigla_uf_nome_cidade': u'SP/São Paulo',
            'area_km2': '2000',
        })

        result = self.db.get_one_cidade(u'SP/São Paulo')
        self.assertEqual('2000', result['area_km2'])
