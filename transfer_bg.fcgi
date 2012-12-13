#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import logging.handlers

import re
import sys
import os

import urllib
from bs4 import BeautifulSoup
import json
import cgi
from cgi import escape
from flup.server.fcgi import WSGIServer
import mwclient
import sqlite3

formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
warn_handler = logging.FileHandler('transfer.log')
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(formatter)

# enable debugging
import cgitb
cgitb.enable()

from config import fieldnames

def app(environ, start_response):

    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    logger.addHandler(warn_handler)

    start_response('200 OK', [('Content-Type', 'text/html')])
    form = cgi.FieldStorage(fp = environ['wsgi.input'], environ = environ)
    #yield form.keys()
    if 'url' not in form:
        yield '????'
        return

    #yield '<h1>FastCGI Environment</h1>'
    #yield escape(environ.post('url'))
    url = form.getfirst('url')
    if not re.match(r'http://(www\.)?oslobilder\.no', url):
        yield "Invalid url!"
        return
    #yield url
    f = urllib.urlopen(url)
    txt = f.read()
    soup = BeautifulSoup(txt)
    soup.find_all('p', 'copyright-info')
    tag = soup.find('p', 'copyright-info').find('a').get('href')
    license = 'unknown'
    if tag.find('licenses/by-sa/') != -1:
        license = 'by-sa'
    elif tag.find('licenses/by-nc-nd/') != -1:
        license = 'by-nc-nd'
    elif tag.find('/publicdomain/') != -1:
        license = 'pd'
    else:
        logger.warn('Found unknown license: "%s" (URL: %s)', tag, url)
    year = ''

    fields = {}
    cats = []
    
    commons = mwclient.Site('commons.wikimedia.org')

    date_re = [
        [re.compile(r'([0-9]{4}) - ([0-9]{4}) \(ca\)', re.I), r'{{Other date|~|\1|\2}}'],
        [re.compile(r'([0-9]{4}) \(ca\)', re.I), r'{{Other date|~|\1}}'],
        [re.compile(r'([0-9]{4}) - ([0-9]{4})'), r'{{Other date|-|\1|\2}}'],
        [re.compile(r'^([0-9]{4})$'), r'\1']
        ]

    r3 = re.compile(r'^([^,]), (.*)$')
    r4 = re.compile(r'ukjent( person)?', re.I)
    fieldnames_re = [re.compile(q) for q in fieldnames]

    for tag in soup.find_all('dt'):
        name = tag.text
        matched = None
        for f in fieldnames_re:
            if f.search(name):
                matched = f.pattern
                break
        if not matched:
            logger.warn('Found unknown field: "%s" (URL: %s)', name, url)

    for fn, fn_re in zip(fieldnames, fieldnames_re):
        tag = soup.find('dt', text=fn_re)
        if not tag:
            fields[fn] = 'NOTFOUND'
            #yield "Fant ikke feltet %s" % fn
            #return
        else:
            val = tag.findNext('dd').find('div').text.strip().rstrip('.')
            if fn == 'Datering':
                matched = False
                for pattern, replacement in date_re:
                    match = pattern.match(val)
                    if match:
                        matched = True
                        val = pattern.sub(replacement, val)
                        year = match.groups()[-1]

                if not matched:
                    logger.warn('Found unknown date format: "%s" (URL: %s)', val, url)

            elif fn == 'Avbildet sted' or fn == 'Emneord':
                val = '|'.join([q.text.strip() for q in tag.find_next('dd').find_all('a')])

            elif fn == 'Avbildet person':
                val = r3.sub(r'\2 \1', val)
                cats.append(val)
                while tag.find_next('dt').text.strip() == '':
                    tag = tag.find_next('dt')
                    tmp = tag.findNext('dd').findChild('div').text.strip()
                    tmp = r3.sub(r'\2 \1', tmp)
                    val += '\n' + tmp
                    cats.append(val)
            elif fn == 'Fotograf':
                vals = val.split(',')
                if len(vals) == 2:
                    last = vals[0].strip()
                    first = vals[1].strip()
                    val = first + ' ' + last
                if r4.search(val):
                    val = r4.sub(r'{{Unknown|author}}', val)
                else:
                    creator_template = 'Creator:%s' % val
                    p = commons.pages[creator_template]
                    if p.exists:
                        if p.redirect:
                            creator_template = p.redirects_to().name
                        val = '{{%s}}' % creator_template

                    
            fields[fn] = val

    src = soup.find('div','image').findChild('img').get('src')

    institution, imageid = fields['Permalenke'].split('/',4)[3:]
    sql = sqlite3.connect('oslobilder.db')
    sql.row_factory = sqlite3.Row
    cur = sql.cursor()
    rows = cur.execute(u'SELECT filename FROM files ' + \
            'WHERE institution=? AND imageid=?', (institution, imageid)).fetchall()
    if len(rows) > 0:
        yield json.dumps({ 'error': 'duplicate', 'institution': institution, 'imageid': imageid, 'filename': rows[0][0] });
    else:
        yield json.dumps({ 'license': license, 'src': src, 'metadata': fields, 'cats': cats, 'year': year })
    
    cur.close()
    sql.close()
    #yield "hello"

    #yield '<table>'
    #for k, v in sorted(environ.items()):
         #yield '<tr><th>%s</th><td>%s</td></tr>' % (escape(k), escape(v))
    #yield '</table>'

WSGIServer(app).run()

