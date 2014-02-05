Postmon [<img src="https://api.travis-ci.org/CodingForChange/postmon.png" />](http://travis-ci.org/CodingForChange/postmon)
==========
API para consulta de CEP's e relacionados

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
* celery

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

Para rodar o [Scheduler](#scheduler):

	$ celery worker -B -A PostmonTaskScheduler -l info

Recomenda-se a utilização do [Supervisord](http://supervisord.org/) para manter o Celery rodando. Exemplo de configuração para o _supervisord.conf_:

	[program:celeryd]
	command=celery worker -B -A PostmonTaskScheduler -l info 
	directory=POSTMON_HOME/repositorio
	stdout_logfile=POSTMON_LOG_DIR/celeryd.log
	stderr_logfile=POSTMON_LOG_DIR/celeryd_err.log
	autostart=true
	autorestart=true
	startsecs=10
	stopwaitsecs=600

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

Scheduler
---------

O Postmon conta com um scheduler baseado na ferramenta [Celery](http://www.celeryproject.org/). Até o momento, a única funcionalidade implementada nessa estrutura é a rotina de coleta de dados do [IBGE](#ibge).

O Celery usa, como Broker, a mesma instância do MongoDB utilizada no módulo de CEP.

O comando apresentado na seção [rodando a aplicação](#rodando-a-aplicação-localmente-na-porta-9876) pode ser quebrado em dois caso seja necessário rodar o Celery Worker separado do Celery Beat. Para mais informações sobre essa questão leia a [documentação do Celery](http://docs.celeryproject.org/en/latest/).

Além do Broker, o Celery Beat depende internamente de uma base de dados, criada automaticamente na primeira execução, onde são armazenadas informações sobre os schedules. Por padrão essa base fica em um arquivo chamado _celerybeat_schedule_, criado no diretório onde o Celery Beat foi executado. Esse local pode ser alterado através do switch -s, conforme exemplo abaixo:

	$ celery worker -B -A PostmonTaskScheduler -l info -s /novo/caminho/para/arquivo/celerybeat_schedule

IBGE
-------------

O Postmon fornece as seguintes informações extraídas do site do IBGE:

* Código do município/UF
* Área territorial (em km²)

Essas informações estão presentes nos atributos *estado_info* e *cidade_info* da rota de busca de _cep_, bem como nas seguintes rotas:

* /uf/{sigla-uf}
* /cidade/{sigla-uf}/{nome-cidade}

Exemplos:

* /uf/SP
* /cidade/SP/São Paulo
* /cidade/SP/Araraquara
* /cidade/RJ/Macaé

A rotina de atualização desses dados está configurada para rodar diariamente.

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/CodingForChange/postmon/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

