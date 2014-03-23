from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from flask import Flask
from flask import render_template
from time import time

import re
import yaml
import sqlite3
from . import controllers

config = yaml.load(open('/data/project/digitaltmuseum/config.yml', 'r'))

app = Flask(__name__)

def error_404():
    return '404'
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
    return controllers.Index(config).get()

@app.route('/stats')
def show_stats():
    return controllers.Stats(config).get()

@app.route('/dups')
def show_dups():
    return controllers.Duplicates(config).get()

@app.route('/transfer')
def show_transfer():
    return controllers.Transfer(config).get()

@app.route('/transferbg')
def show_transferbg():
    return controllers.Transferbg(config).get()


if __name__ == "__main__":
    app.run()
