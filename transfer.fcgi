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
from config import fieldnames

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])
    
    mylookup = TemplateLookup(directories=['.'], input_encoding='utf-8', output_encoding='utf-8')
    tpl = Template(filename='transfer.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    #yield tpl.render(active_page="dups.fcgi", main=html.decode('utf-8'))
    yield tpl.render_unicode(active_page="transfer.fcgi").encode('utf-8')

WSGIServer(app).run()

