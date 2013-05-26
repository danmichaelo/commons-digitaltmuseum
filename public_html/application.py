#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import cgitb
cgitb.enable()

import logging
import logging.handlers
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

fh = logging.FileHandler('main.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

import os
import sys

sys.path.insert(0, '/data/project/digimus/env-py2.7/lib/python2.7/site-packages')
#sys.path.insert(0, '/data/project/digimus')

from jinja2 import Environment, FileSystemLoader
template_path = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = Environment(loader=FileSystemLoader(template_path), autoescape=True)

from werkzeug.wrappers import Response
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect, HTTPException
from werkzeug.utils import redirect
from wsgiref.handlers import CGIHandler

import sqlite3
import yaml

config = yaml.load(open('../config.yml', 'r'))
url_map = Map([
              Rule('/', endpoint='get_index')
              ], default_subdomain='tools')


def render_template(template_name, **context):
    t = jinja_env.get_template('../templates/' + template_name)
    return Response(t.render(context), mimetype='text/html')


def error_404():
    response = render_template('404.html')
    response.status_code = 404
    return response


def get_index(environ, start_response):

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

    return render_template('index.html',
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
                           )


def application(environ, start_response):
    #logger.info(environ)
    environ['SCRIPT_NAME'] = '/ukbot'

    try:
        urls = url_map.bind_to_environ(environ, server_name='wmflabs.org', subdomain='tools')
        endpoint, args = urls.match()
        logger.info(args)
        response = globals()[endpoint](args)
        return response(environ, start_response)

    except NotFound, e:
        response = error_404()
        return response(environ, start_response)

    except RequestRedirect, e:
        logger.info('Redir to: %s' % e.new_url)
        response = redirect(e.new_url)
        return response(environ, start_response)

    except HTTPException, e:
        logger.error(e)
        return e(environ, start_response)
    #logger.info(args)
    #return ['Rule points to %r with arguments %r' % (endpoint, args)]


try:
        CGIHandler().run(application)
except Exception as e:
        logger.exception('Unhandled Exception')
