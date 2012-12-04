####################################################################
# A simple Correios API to get the CEP informations 
#
# author: Alexandre Borba
#         Igor Hercowitz
#
# v 1.0
####################################################################

from bottle import route, run, template
from correios import CepTracker

@route('/cep/<cep:int>')
def cep(cep):

	tracker = CepTracker()
	info = tracker.track(cep)

	return info

run(host="localhost", port=8080)