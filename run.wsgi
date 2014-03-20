import logging.config
import sys, os, bottle

import yaml


sys.path = ['/var/www/'] + sys.path
os.chdir(os.path.dirname(__file__))


def _config_log(config_file='log.yaml'):
    with open(config_file, 'rt') as f:
        config = yaml.load(f.read())
    logging.config.dictConfig(config)


_config_log()

import PostmonServer

application = bottle.default_app()
