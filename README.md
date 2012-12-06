Postmon
==========
API para consulta de CEP's


Requisitos do ambiente de desenvolvimento
---------------------------------------------
* MongoDB
* Python 2.7
* iPython (recomendado)

Requisitos do ambiente Python
-----------------------
* requests
* lxml
* pymongo
* bottle

Rodando a aplicação localmente na porta 9876
--------------------------------

	$ ipython -i correios_server.py
	>> _standalone()

Caso queira rodar em outra porta, basta passá-la como parametro no chamado do _standalone
