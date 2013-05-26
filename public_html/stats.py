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

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])
    
    sql = sqlite3.connect('storage/oslobilder.db')
    cur = sql.cursor()
    html = 'Mest aktive opplastere:<ul>'
    for row in cur.execute(u'SELECT uploader, count(*) as cnt FROM files GROUP BY uploader ORDER BY cnt DESC'):
        html += '<li>%s: %d</li>' % (row[0], row[1])
        #html += '<li><a href="http://commons.wikimedia.org/wiki/File:%s">%s<br />%s</a></li>\n' % (enc, thumb, row[0])
    html += '</ul>\n'

    mylookup = TemplateLookup(directories=['../templates/'], input_encoding='utf-8', output_encoding='utf-8')
    tpl = Template(filename='../templates/dups.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    yield tpl.render_unicode(active_page="stats.py", main=html).encode('utf-8')

WSGIServer(app).run()

