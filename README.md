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

As dependências estão listadas no arquivo requirements.txt.

* requests
* lxml
* pymongo
* bottle
* nosetests
* webtest
* correios-api-py

Rodando testes
----------------
Executar o comando:

	nosetests

na raiz do projeto.

Rodando a aplicação localmente na porta 9876
--------------------------------

	$ ipython -i PostmonServer.py
	>> _standalone()

Caso queira rodar em outra porta, basta passá-la como parametro no chamado do _standalone
