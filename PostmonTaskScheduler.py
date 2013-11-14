#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta
from celery import Celery
from celery.utils.log import get_task_logger
from IbgeTracker import IbgeTracker
from database import MongoDb as Database

app = Celery('postmon', broker='mongodb://localhost:27017')

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
