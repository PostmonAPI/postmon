from datetime import datetime

import requests
import unicodedata
import re

def _normalize_unicode(text):
	return unicodedata.normalize('NFKD', text).encode('ascii','ignore') if isinstance(text, unicode) else text

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

		index=0
		data = dict()
		for item in itens:

			if index % 4 == 0:
				if index > 0:
					index = 0
					self.result.append(data)
					data = dict()
				
				data["v_date"] = datetime.now()

			text = re.sub('\s+',' ',item.text.strip())

			if (index == 2):
				for j, text in enumerate(text.split('/')):
					data[self.fields[index][j]] = _normalize_unicode(text.strip())
			else:
				data[self.fields[index]] = _normalize_unicode(text)
				
			index +=1

		if  len(data) > 0:	
			self.result.append(data)

		return self.result
