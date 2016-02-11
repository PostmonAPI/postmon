
.PHONY: test
test: pep8
	nosetests

.PHONY: pep8
pep8:
	@flake8 * --ignore=F403,F401 --exclude=requirements.txt,*.pyc,*.md,COPYING,Makefile,*.wsgi,*celerybeat-schedule*,*.yaml,*.log,Dockerfile
