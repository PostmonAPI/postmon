# encoding: utf-8
from datetime import datetime

import requests
import re

class CepTracker():
	def __init__(self):
		self.url = 'http://m.correios.com.br/movel/buscaCepConfirma.do'
		self.result = []

		self.fields = ['logradouro', 'bairro', ['cidade', 'estado'], 'cep']

	def _get_infos_(self, cep, csspattern='div .respostadestaque'):
		from lxml.html import fromstring
		response = requests.post(self.url, 
			                 data={'cepEntrada': cep, 'tipoCep':'', 'cepTemp':'', 'metodo':'buscarCep'})

		html = fromstring(response.text)
		return html.cssselect(csspattern)

	def track(self, cep):
		itens = self._get_infos_(cep)

		index= 4 - len(itens)
		data = dict()
		for item in itens:

			if index % 4 == 0:
				if index > 0:
					index = 0
					self.result.append(data)
					data = dict()

			# TODO: definir v_date apenas uma vez
			data["v_date"] = datetime.now()

			text = re.sub('\s+',' ',item.text.strip())

			if (index == 2):
				cidade, estado = text.split('/', 1)
				data['cidade'] = cidade.strip()
				data['estado'] = estado.split('-')[0].strip()
			else:
				data[self.fields[index]] = text
				
			index +=1

		if  len(data) > 0:	
			self.result.append(data)

		return self.result
