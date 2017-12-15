#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta
from celery import Celery
from celery.utils.log import get_task_logger
from IbgeTracker import IbgeTracker
import PackTracker
from database import MongoDb as Database
import os

USERNAME = os.environ.get('POSTMON_DB_USER')
PASSWORD = os.environ.get('POSTMON_DB_PASSWORD')
HOST = os.environ.get('POSTMON_DB_HOST', 'localhost')
if all((USERNAME, PASSWORD, HOST)):
    broker_conn_string = 'mongodb://%s:%s@%s:27017' \
        % (USERNAME, PASSWORD, HOST)
else:
    broker_conn_string = 'mongodb://localhost:27017'

print(broker_conn_string)

app = Celery('postmon', broker=broker_conn_string)

app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='America/Sao_Paulo',
    CELERY_ENABLE_UTC=True,
    CELERYBEAT_SCHEDULE={
        'track_ibge_daily': {
            'task': 'PostmonTaskScheduler.track_ibge',
            'schedule': timedelta(days=1)  # útil para
                                           # testes: timedelta(minutes=1)
        },
        'track_packs': {
            'task': 'PostmonTaskScheduler.track_packs',
            'schedule': timedelta(hours=1),
        }

    }
)

logger = get_task_logger(__name__)


@app.task
def track_ibge():
    logger.info('Iniciando tracking do IBGE...')
    db = Database()
    ibge = IbgeTracker()
    ibge.track(db)
    logger.info('Finalizou o tracking do IBGE')


@app.task
def track_packs():
    logger.info('Iniciando tracking de pacotes...')
    db = Database()
    for obj in db.packtrack.get_all():
        provider = obj['servico']
        track = obj['codigo']
        changed = PackTracker.run(provider, track)
        if changed:
            PackTracker.report(provider, track)

    logger.info('Finalizou o tracking de pacotes')
