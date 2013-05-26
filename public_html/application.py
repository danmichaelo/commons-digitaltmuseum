#!/usr/bin/python
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

import re
import os
import sys
from time import time

sys.path.insert(0, '/data/project/digimus/env-py2.7/lib/python2.7/site-packages')
#sys.path.insert(0, '/data/project/digimus')

from jinja2 import Environment, FileSystemLoader
template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

jinja_env = Environment(loader=FileSystemLoader(template_path), 
                        autoescape=True,
                        trim_blocks=True,
                        lstrip_blocks=True)

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect, HTTPException
from werkzeug.utils import redirect
from wsgiref.handlers import CGIHandler

import sqlite3
import yaml
import json
import urllib


from common import get_thumb_url

config = yaml.load(open('../config.yml', 'r'))
url_map = Map([
              Rule('/', endpoint='get_index'),
              Rule('/backend', endpoint='get_backend')
              ], default_subdomain='tools')


def render_template(template_name, **context):
    t = jinja_env.get_template(template_name)
    return Response(t.render(context), mimetype='text/html')


def error_404():
    response = render_template('404.html')
    response.status_code = 404
    return response


def get_index(request, args):

    f = open('../last_update', 'r')
    last_update = f.read()
    f.close()

    sql = sqlite3.connect('../storage/oslobilder.db')
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


def get_backend(request, args):

    start_time = time()

    f = open('../last_update', 'r')
    last_update = f.read()
    f.close()

    plimit = config['default_limit']
    psort = config['default_sort']
    porder = config['default_sortorder']
    where = []
    whereData = []
    post_input = {}

    logger.info('DO MO SO')

    req_inst = []
    for key, v in request.args.items():
        val = v.strip()
        if key.split('_')[0] == 'inst':
            req_inst.append(key.split('_')[1])

        elif key == 'limit':
            try:
                plimit = int(val)
            except ValueError:
                plimit = config['default_limit']
        elif key == 'sort':
            psort = re.sub(r'[^\w]', '', val)  # leaves A-Za-z0-9_
        elif key == 'order':
            porder = 'DESC' if val == 'desc' else 'ASC'
        else:
            for knownkey in ['collection', 'author', 'filename']:
                if key == knownkey and len(val) > 0:
                    if val == '#':
                        where.append('%s=""' % knownkey)
                    elif val[0] == '*' and val[-1] == '*':
                        where.append('%s LIKE ?' % knownkey)
                        whereData.append('%' + val.decode('utf-8')[1:-1] + '%')
                    elif val[-1] == '*':
                        where.append('%s LIKE ?' % knownkey)
                        whereData.append(val.decode('utf-8')[:-1]+'%')
                    elif val[0] == '*':
                        where.append('%s LIKE ?' % knownkey)
                        whereData.append('%' + val.decode('utf-8')[1:])
                    else:
                        where.append('%s=?' % knownkey)
                        whereData.append(val.decode('utf-8'))

    if len(req_inst) > 0 and len(req_inst) < len(config['institutions']):
        where.append('institution IN (%s)' % ','.join( ["?" for q in range(len(req_inst))] ))
        whereData.extend(req_inst)

    if len(where) == 0:
        where = ''
    else:
        where = ' WHERE ' + ' AND '.join(where)

    #yield where
    #return

    sql = sqlite3.connect('../storage/oslobilder.db')
    #sql.row_factory = sqlite3.Row
    cur = sql.cursor()
    rows = []
    totals = {}
    total = 0
    query = u'SELECT filename, width, height, size, institution, imageid, ' + \
             'collection, author, date, description, upload_date ' + \
             'FROM files' + where + ' ORDER BY %s %s LIMIT %s' % (psort, porder, plimit)

    logger.info(query)
    logger.info(whereData)
    #yield '</table>\n'

    for row in cur.execute(query, whereData):

        name = row[0].replace(' ', '_')
        name_enc = urllib.quote(name.encode('utf-8'))

        url = 'http://commons.wikimedia.org/wiki/File:' + name_enc
        thumbmax = 120
        if row[1] > row[2]:
            thumbw = thumbmax
            thumbh = round(float(row[2])/row[1]*thumbmax)
        else:
            thumbh = thumbmax
            thumbw = round(float(row[1])/row[2]*thumbmax)

        #thumb = '<a href="%s"><img src="/tsthumb/tsthumb?f=%s&domain=commons.wikimedia.org&w=120&h=120" border="0" alt="%s" width="%d" height="%d"/></a>' % (url, enc, row[0], thumbw, thumbh)

        thumb_url = get_thumb_url(name, thumbw)
        thumb = '<a href="%s"><img src="%s" border="0" alt="%s" width="%d" height="%d"/></a>' % (url, thumb_url, row[0], thumbw, thumbh)

        url = '<a href="%s">%s</a>' % (url, row[0])

        row2 = {'thumb': thumb, 'filename': url, 'width': row[1], 'height': row[2], 
                'size': '%.f' % (row[3]/1024), 'institution': row[4], 'imageid': row[5], 
                'collection': row[6], 'author': row[7], 'date': row[8], 'description': row[9], 
                'upload_date': row[10] }
        rows.append(row2)
        #s = '<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n' % (row[4], row[5], row[6])
        #yield s.encode('utf-8')
    
    end_time = time()
    time_spent = int((end_time - start_time)*1000)
    
    f = open('../counter', 'r+')
    cnt = int(f.read()) + 1
    f.seek(0)
    f.write('%d' % cnt)
    f.truncate()
    f.close()

    data = json.dumps({ 'where': where, 'data': whereData, 'rows': rows, 'query': query, 'time': time_spent, 'last_update': last_update })
    return Response(data, mimetype='application/json')


def application(environ, start_response):
    #logger.info(environ)
    environ['SCRIPT_NAME'] = '/digimus'

    try:

        urls = url_map.bind_to_environ(environ, server_name='wmflabs.org', subdomain='tools')
        endpoint, args = urls.match()

        request = Request(environ)

        logger.info(endpoint)
        logger.info(args)
        response = globals()[endpoint](request, args)
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


try:
    CGIHandler().run(application)
except Exception as e:
    logger.exception('Unhandled Exception')
