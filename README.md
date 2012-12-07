Postmon
==========
API para consulta de CEP's

	Stable - Branch master
	Unstable - Branch dev

Caso queira ajudar no desenvolvimento do projeto, utilize sempre o branch dev, a não ser que seja um Bugfix! o/


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
* nosetests

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
