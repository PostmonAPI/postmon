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
