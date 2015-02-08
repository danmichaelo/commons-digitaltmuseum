#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import logging.handlers

import re
import sys
import os
from werkzeug.wrappers import Response

import urllib2
from bs4 import BeautifulSoup
import json
import cgi
from cgi import escape
import mwclient
import sqlite3
import StringIO, gzip
import yaml

from flask import request, url_for, make_response

from .controller import Controller

import logging
logger = logging.getLogger()


class Transferbg(Controller):

    def __init__(self, config):
        Controller.__init__(self)
        self.config = config

    def check_url(self, url, hostname):
        logger = logging.getLogger()

        #yield url
        req = urllib2.Request(url, headers={
            'User-Agent': 'Oslobilder@Commons (+http://toolserver.org/~danmichaelo/oslobilder)',
            'Referer': 'http://toolserver.org/~danmichaelo/oslobilder',
            'Accept-Encoding': 'gzip'
        })
        f = urllib2.urlopen(req)
        headers = f.info()
        if headers.get('Content-Encoding') in ('gzip', 'x-gzip'):
            data = gzip.GzipFile(fileobj=StringIO.StringIO(f.read())).read()
        else:
            data = f.read()

        soup = BeautifulSoup(data)
        commons = mwclient.Site('commons.wikimedia.org')

        # Find license info:

        cp = soup.find_all('p', 'copyright-info')
        if len(cp) == 0:
            cp = soup.find_all('p', 'copyright')
        if len(cp) == 0:
            logger.warn('No license info (URL: %s)', url)
            return { 'error': 'Bildet inneholder ingen lisensinformasjon' }
        else:
            try:
                tag = cp[0].find('a').get('href')
            except AttributeError:
                logger.warn('No license info (URL: %s)', url)
                return { 'error': 'Bildet inneholder ingen lisensinformasjon' }
        license = 'unknown'
        if tag.find('licenses/by-sa/') != -1:
            license = 'by-sa'
        elif tag.find('licenses/by-nc-nd/') != -1:
            license = 'by-nc-nd'
        elif tag.find('/publicdomain/') != -1:
            license = 'pd'
        else:
            logger.warn('Found unknown license: "%s" (URL: %s)', tag, url)

        # Find other metadata:

        year = ''
        fields = {}
        cats = []

        date_re = [
            [re.compile(r'([0-9]{4}) - ([0-9]{4}) \(ca(\.)?\)', re.I), r'{{Other date|~|\1|\2}}'],
            [re.compile(r'([0-9]{4}) \(ca(\.)?\)', re.I), r'{{Other date|~|\1}}'],
            [re.compile(r'([0-9]{4}) - ([0-9]{4})'), r'{{Other date|-|\1|\2}}'],
            [re.compile(r'([0-9]{4}) \(([0-9]{2})\.([0-9]{2})\.\)'), r'\1-\3-\2'],
            [re.compile(r'^([0-9]{4}) \(ANT\)$'), r'\1 (assumed)'],
            [re.compile(r'^([0-9]{4})$'), r'\1']
            ]

        r3 = re.compile(r'^([^,]), (.*)$')
        r4 = re.compile(r'ukjent( person)?', re.I)
        fieldnames_re = [re.compile(q) for q in self.config['fieldnames']]

        for tag in soup.find_all('dt'):
            name = tag.text
            matched = None
            for f in fieldnames_re:
                if f.search(name):
                    matched = f.pattern
                    break
            if not matched:
                logger.warn('Found unknown field: "%s" (URL: %s)', name, url)

        for fn, fn_re in zip(self.config['fieldnames'], fieldnames_re):
            tag = soup.find('dt', text=fn_re)
            if not tag:
                fields[fn] = 'NOTFOUND'
                #yield "Fant ikke feltet %s" % fn
                #return
            else:
                val = tag.findNext('dd')
                if val == None:
                    fields[fn] = 'NOTFOUND'
                    continue

                if val.find('div') != None:
                    val = val.find('div')

                val = val.text.strip().rstrip('.')
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
                elif fn == 'Fotograf' or fn == 'Kunstner':
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

        # Find image source URL

        src = soup.find('li', id='downloadpicture')
        if src != None:
            src = 'http://' + hostname + '.no' + src.find('a').get('href')
        else:
            src = soup.find('div','image').findChild('img').get('src')

        # Find institution and image identification

        # DEBUG:
        # return { 'error': 'schwoing', 'metadata': fields }

        if fields['Permalenke'] != 'NOTFOUND':
            institution, imageid = fields['Permalenke'].split('/',4)[3:]
        elif fields['Eier'] != 'NOTFOUND' and fields['Inventarnr.'] != 'NOTFOUND':
            institution = fields['Eier']
            imageid = fields['Inventarnr.']
        else:
            return { 'error': 'unknown_institution', 'metadata': fields }

        # Check if image has already been transferred

        sql = sqlite3.connect('/data/project/digitaltmuseum/storage/oslobilder.db')
        sql.row_factory = sqlite3.Row
        cur = sql.cursor()
        rows = cur.execute(u'SELECT filename FROM files ' + \
                'WHERE institution=? AND imageid=?', (institution, imageid)).fetchall()
        if len(rows) > 0:
            return { 'error': 'duplicate', 'institution': institution, 'imageid': imageid, 'filename': rows[0][0] }
        else:
            return { 'license': license, 'src': src, 'metadata': fields, 'cats': cats, 'year': year, 'hostname': hostname }

        cur.close()
        sql.close()
        #yield "hello"

        #yield '<table>'
        #for k, v in sorted(environ.items()):
             #yield '<tr><th>%s</th><td>%s</td></tr>' % (escape(k), escape(v))
        #yield '</table>'

    def get(self):

        url = request.args.get('url')

        import sys
        sys.stderr = sys.stdout

        hostname = re.match(r'http(s)?://(www\.)?([a-z]*?)\.no', url)
        if hostname == None:
            print "Content-Type: text/plain"
            print
            print "Invalid url!"
            sys.exit(0)

        hostname = hostname.group(3)
        if hostname != 'oslobilder' and hostname != 'digitaltmuseum':
            print "Content-Type: text/plain"
            print
            print "Invalid url!"
            sys.exit(0)

        data = json.dumps(self.check_url(url, hostname))
        resp = make_response(data)
        resp.headers['Content-Type'] = 'application/json'
        return resp

