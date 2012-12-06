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

Rodando testes
----------------
Precisa ter instalado em seu ambiente o nosetests, depois é só deixa-lo executando na raiz do projeto.

Rodando a aplicação localmente na porta 9876
--------------------------------

	$ ipython -i correios_server.py
	>> _standalone()

Caso queira rodar em outra porta, basta passá-la como parametro no chamado do _standalone
