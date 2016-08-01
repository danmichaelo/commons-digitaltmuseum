from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import requests
from flask import Flask
from flask import render_template
from flask import request, make_response
from time import time
import os

import yaml
from . import controllers
# from . import settings

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

fh = logging.FileHandler('main.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)

app = Flask('app', template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['APPLICATION_ROOT'] = '/digitaltmuseum'
# app.debug = True  # reload on each code change

app.logger.addHandler(fh)
app.logger.addHandler(sh)

# app.logger.info('Flask server started in %s', settings.APP_ROOT)

config_file = os.path.join(app.root_path, 'config.yml')
config = yaml.load(open(config_file, 'r'))

app.logger.info('Root path: %s', app.root_path)
app.logger.info('Instance path: %s', app.instance_path)


def error_404():
    # return '404'
    response = render_template('404.html')
    response.status_code = 404
    return response


def read_status(fname):
    stat = open(fname).read()
    statspl = stat.split()

    if statspl[0] == 'running':
        stat = 'Updating now... started %d secs ago.' % (int(time()) - int(statspl[1])) 
    elif statspl[0] == '0':
        stat = 'Last successful run: ' + ' '.join(statspl[2:]) + '. Runtime was ' + statspl[1] + ' seconds.'
    else:
        stat = '<em>Failed</em>'
    return stat


@app.route('/')
def show_index():
    return controllers.IndexController(app, config).get()


@app.route('/search')
def show_search():
    return controllers.SearchController(app, config).get(request)


@app.route('/stats')
def show_stats():
    return controllers.StatsController(app, config).get()


@app.route('/dups')
def show_dups():
    return controllers.DuplicatesController(app, config).get()


@app.route('/transfer')
def show_transfer():
    return controllers.TransferController(app, config).get()


@app.route('/url')
def show_url():
    return controllers.UrlController(app, config).get()


@app.route('/proxy/index.php')
def proxy_index_php():
    response = requests.get('https://commons.wikimedia.org/w/index.php', params=request.args)
    return make_response(response.text)


@app.route('/proxy/api.php')
def proxy_api_php():
    response = requests.get('https://commons.wikimedia.org/w/api.php', params=request.args)
    return make_response(response.text)


if __name__ == "__main__":
    app.run()
