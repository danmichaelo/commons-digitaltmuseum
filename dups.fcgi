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
import mwclient
from danmicholoparser import TemplateEditor
from config import institutions
from common import get_thumb_url

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])
    
    sql = sqlite3.connect('oslobilder.db')
    cur = sql.cursor()
    dups = []
    for row in cur.execute(u'SELECT institution,imageid,count(*) FROM files GROUP BY institution,imageid'):
        if row[2] > 1:
            dups.append([row[0], row[1]])

    html = u'<ul>'
    for dup in dups:
        html += '<li>%s/%s er oppgitt som kilde for:\n<ul class="dups">\n' % tuple(dup)
        #yield(type(html).__name__)
        for row in cur.execute(u'SELECT filename, width, height FROM files WHERE institution=? AND imageid=?', dup):
            name = row[0].replace(' ', '_')
            name_enc = urllib.quote(name.encode('utf-8'))
            thumbmax = 120
            if row[1] > row[2]:
                thumbw = thumbmax
                thumbh = round(float(row[2])/row[1]*thumbmax)
            else:
                thumbh = thumbmax
                thumbw = round(float(row[1])/row[2]*thumbmax)

            thumb_url = get_thumb_url(name, thumbw)
            thumb = '<img src="%s" border="0" alt="%s" width="%d" height="%d"/>' % (thumb_url, name, thumbw, thumbh)
            html += '<li><a href="http://commons.wikimedia.org/wiki/File:%s">%s<br />%s</a></li>\n' % (name_enc, thumb, row[0])
        html += '</ul>\n'
    html += '</ul>\n'

    mylookup = TemplateLookup(directories=['.'], input_encoding='utf-8', output_encoding='utf-8')
    tpl = Template(filename='dups.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    #yield tpl.render(active_page="dups.fcgi", main=html.decode('utf-8'))
    yield tpl.render_unicode(active_page="dups.fcgi", main=html).encode('utf-8')

WSGIServer(app).run()

