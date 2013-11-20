#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta
from celery import Celery
from celery.utils.log import get_task_logger
from IbgeTracker import IbgeTracker
from database import MongoDb as Database
import os

USERNAME = os.environ.get('POSTMON_DB_USER')
PASSWORD = os.environ.get('POSTMON_DB_PASSWORD')
if all((USERNAME, PASSWORD)):
    broker_conn_string = 'mongodb://%s:%s@localhost:27017' \
        % (USERNAME, PASSWORD)
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
