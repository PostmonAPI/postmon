# encoding: utf-8
from datetime import datetime

import requests
import re

class EctTracker():

	def __init__(self):
		self.url = 'http://websro.correios.com.br/sro_bin/txect01$.Inexistente?P_LINGUA=001&P_TIPO=002&P_COD_LIS='

	def _get_infos_(self, cod):
		from lxml.html import fromstring

		response = requests.get(self.url+cod)
		html = fromstring(response.text)
		tree = html.iter(tag='table')
		table = tree.next()

		return table.text_content()