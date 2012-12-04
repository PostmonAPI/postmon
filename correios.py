####################################################################
# A simple Correios site wrapper to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.0
# usage:
# >>> tracker = CepTracker()
# >>> infos = tracker.track(cep)
####################################################################

from lxml.html import fromstring
import requests
import unicodedata
import re

class CepTracker():
	def __init__(self):
		self.url = 'http://m.correios.com.br/movel/buscaCepConfirma.do'
		self.result = dict()
		self.fields = ['logradouro', 'bairro', ['cidade', 'estado'], 'cep']

	def track(self, cep):
		response = requests.post(self.url, 
			                 data={'cepEntrada': cep, 'tipoCep':'', 'cepTemp':'', 'metodo':'buscarCep'})

		html = fromstring(response.text)
		itens = html.cssselect('div .respostadestaque')

		for index, item in enumerate(itens):
			text = re.sub('\s+',' ',item.text.strip())

			if (index == 2):
				for j, text in enumerate(text.split('/')):
					self.result[self.fields[index][j]] = unicodedata.normalize('NFKD', text.strip()).encode('ascii','ignore') if isinstance(text, unicode) else text.strip() 
			else:	
				self.result[self.fields[index]] = unicodedata.normalize('NFKD', text).encode('ascii','ignore') if isinstance(text, unicode) else text 

		return self.result