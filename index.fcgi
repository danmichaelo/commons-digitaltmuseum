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

institutions = {
    'OMU': 'Oslo Museum',
    'BAR': 'Oslo byarkiv',
    'NF': 'Norsk folkemuseum',
    'ARB': 'Arbeiderbevegelsens arkiv og bibliotek',
    'TELE': 'Telemuseet',
    'NTM': 'Norsk Teknisk Museum',
    'UBB': 'Universitetsbiblioteket i Bergen'
    }

columns = [
    ['filename', 'Filnavn', True],
    ['width', 'Bredde (px)', True],
    ['height', u'Høyde (px)', True],
    ['size', u'Størrelse (kB)', True],
    ['institution', u'Institusjon', True],
    ['imageid', u'Bilde-ID', True],
    ['collection', u'Samling', True],
    ['author', u'Fotograf', True],
    ['sourcedate', u'Dato', True],
    ['description', u'Beskrivelse', False]
]

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])

    sql = sqlite3.connect('oslobilder.db')
    cur = sql.cursor()
    rows = []
    row = cur.execute(u'SELECT count(filename) FROM files').fetchone()
    total = row[0]
    totals = {}
    for row in cur.execute(u'SELECT institution, count(institution) FROM files GROUP BY institution'):
        totals[row[0]] = row[1]

    mylookup = TemplateLookup(directories=['.'], input_encoding='utf-8', output_encoding='utf-8')
    tpl = Template(filename='template.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    yield tpl.render_unicode(rows=[], total=total, totals=totals, institutions=institutions, columns=columns).encode('utf-8')

WSGIServer(app).run()

