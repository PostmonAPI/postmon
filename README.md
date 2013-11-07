Postmon [<img src="https://api.travis-ci.org/CodingForChange/postmon.png" />](http://travis-ci.org/CodingForChange/postmon)
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
* packtrack

Rodando testes
----------------
Executar o comando:

	make test

na raiz do projeto.

Rodando a aplicação localmente na porta 9876
--------------------------------

	$ python PostmonServer.py

ou

	$ ipython -i PostmonServer.py
	>> _standalone()

Caso queira rodar em outra porta, basta passá-la como parametro no chamado do _standalone


MongoDB com autenticação
------------------------

Se o seu MongoDB possui autenticação habilitada você deverá configurar o banco do postmon
e também exportar duas variavéis de ambiente.

```javascript
mongo
> use postmon
> db.addUser('admin', '123456')
```

Agora que seu Mongo está com password exporte as variaveis de ambiente.

```bash
export POSTMON_DB_USER=admin
export POSTMON_DB_PASSWORD=123456
```
