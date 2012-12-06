import sys, os, bottle

sys.path = ['/var/www/'] + sys.path
os.chdir(os.path.dirname(__file__))

import PostmonServer

application = bottle.default_app()
