import sys, os, bottle

sys.path = ['/var/www/'] + sys.path
os.chdir(os.path.dirname(__file__))

import correios_server # This loads your application

application = bottle.default_app()
