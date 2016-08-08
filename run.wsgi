try:
    import newrelic.agent
except ImportError:
    pass
else:
    newrelic.agent.initialize()

import logging.config
import sys, os, bottle

import yaml

sys.path = ['/var/www/'] + sys.path
os.chdir(os.path.dirname(__file__))


def _config_log(config_file):
    with open(config_file, 'rt') as f:
        config = yaml.load(f.read())
    logging.config.dictConfig(config)


log_file = os.getenv('POSTMON_LOGGING', 'log.yaml')
_config_log(log_file)

import PostmonServer

application = bottle.default_app()
