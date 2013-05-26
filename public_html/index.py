#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import re, sys, os

import cgi
from cgi import escape
from flup.server.fcgi import WSGIServer
import urllib

# enable debugging (for now)
import cgitb
cgitb.enable()

import sqlite3
from mako.template import Template
from mako.lookup import TemplateLookup
import yaml

config = yaml.load(open('../config.yml', 'r'))
#from config import default_limit, default_sort, default_sortorder, institutions, columns

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])
    
    f = open('last_update', 'r')
    last_update = f.read()
    f.close()

    sql = sqlite3.connect('storage/oslobilder.db')
    cur = sql.cursor()
    rows = []
    row = cur.execute(u'SELECT count(filename) FROM files').fetchone()
    total = row[0]
    rows = cur.execute(u'SELECT 1 FROM files GROUP BY institution,imageid').fetchall()
    unique = len(rows)
    totals = {}
    for row in cur.execute(u'SELECT institution, count(institution) FROM files GROUP BY institution'):
        totals[row[0]] = row[1]

    mylookup = TemplateLookup(directories=['../templates/'], input_encoding='utf-8', output_encoding='utf-8')
    tpl = Template(filename='../templates/index.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    yield tpl.render_unicode(
            active_page='./', 
            rows=[], 
            total=total, 
            unique=unique, 
            totals=totals, 
            institutions=config['institutions'], 
            columns=config['columns'], 
            last_update=last_update,
            default_limit=config['default_limit'],
            default_sort=config['default_sort'],
            default_sortorder=config['default_sortorder']
            ).encode('utf-8')

WSGIServer(app).run()

