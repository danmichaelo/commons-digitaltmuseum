#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import re, sys, os

import cgi
from cgi import escape
from flup.server.fcgi import WSGIServer
import urllib
import urlparse
import json

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

def app(environ, start_response):

    start_response('200 OK', [('Content-Type', 'text/html')])

    limit = 200
    where = []
    whereData = []
    post_input = {}
    try:
        length = int(environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        length = 0
    if length != 0:
        body = environ['wsgi.input'].read(length)
        post_input = urlparse.parse_qs(body, True)
        req_inst = []
        for key, v in post_input.items():
            val = v[0].strip()
            if key.split('_')[0] == 'inst':
                req_inst.append(key.split('_')[1].decode('utf-8'))
            #yield key + ' = ' + val[0] + '\n'
            elif key == 'limit':
                limit = int(val)
            else:
                for knownkey in ['collection', 'author', 'filename']:
                    if key == knownkey and len(val) > 0:
                        if val[0] == '*' and val[-1] == '*':
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
                
        if len(req_inst) == 0:
            yield "none"
            return
        elif len(req_inst) < len(institutions):
            where.append('institution IN (%s)' % ','.join( ["?" for q in range(len(req_inst))] ))
            whereData.extend(req_inst)

    if len(where) == 0:
        where = ''
    else:
        where = ' WHERE ' + ' AND '.join(where)

    #yield where
    #return

    sql = sqlite3.connect('oslobilder.db')
    cur = sql.cursor()
    rows = []
    totals = {}
    total = 0
    for row in cur.execute(u'SELECT filename, width, height, size, institution, imageid, ' + \
                            'collection, author, sourcedate, description FROM files' + where + ' LIMIT %d'%limit, whereData):
        url = 'http://commons.wikimedia.org/wiki/File:' + urllib.quote(row[0].encode('utf-8'))
        url = '<a href="%s">%s</a>' % (url, row[0])
        #inst = institutions[row[4]]

        row2 = {'filename': url, 'width': row[1], 'height': row[2], 'size': '%.f' % (row[3]/1024), 'institution': row[4], 'imageid': row[5], 'collection': row[6],
                'author': row[7], 'sourcedate': row[8], 'description': row[9] }
        rows.append(row2)
        #s = '<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n' % (row[4], row[5], row[6])
        #yield s.encode('utf-8')
    
    yield json.dumps({ 'where': where, 'data': whereData, 'rows': rows })
    #yield '</table>\n'
    #yield 'ok\n'


    #mylookup = TemplateLookup(directories=['.'], input_encoding='utf-8', output_encoding='utf-8')
    #tpl = Template(filename='template.html', input_encoding='utf-8', output_encoding='utf-8', lookup=mylookup)
    #t = tpl.render() #data="world")
    #yield tpl.render_unicode(rows=rows, total=total, totals=totals, columns=columns).encode('utf-8')

    #commons = mwclient.Site('commons.wikimedia.org')
    #page = commons.pages['Template:Oslobilder']

    #yield '<table class="wikitable"><tr><th>Institusjon</th></tr>\n'
    ##for img in page.embeddedin(namespace=6):
    #    txt = img.edit(readonly=True)
    #    te = TemplateEditor(txt)
    #    tpl = te.templates['oslobilder'][0]

    

    #form = cgi.FieldStorage(fp = environ['wsgi.input'], environ = environ)
    #yield form.keys()
    #if 'url' not in form:
        #yield '????'
        #return

    #yield '<h1>FastCGI Environment</h1>'
    #yield escape(environ.post('url'))
    #url = form.getfirst('url')
    #if not url.find('http://www.oslobilder.no') == 0:
    #    yield "Invalid url!"
    #    return
    #yield url
    #f = urllib.urlopen(url)
    #txt = f.read()
    #soup = BeautifulSoup(txt)
    #soup.find_all('p', 'copyright-info')
    #tag = soup.find('p', 'copyright-info').find('a').get('href')
    #license = 'unknown'
    #if tag.find('licenses/by-sa/') != -1:
    #    license = 'cc-by-sa-3.0'
    #elif tag.find('licenses/by-nc-nd/') != -1:
    #    license = 'cc-by-nd-3.0'

    #fieldnames = ['Bildetittel', 'Motiv', 'Datering', 'Fotograf', 'Avbildet person', 
    #              'Avbildet sted', 'Utsikt over',
    #              'Emneord', 'Bildenummer', 'Historikk', 
    #              'Permalenke', 'Eierinstitusjon', 'Arkiv/Samling']
    #fields = {}
    #cats = []

    #r1 = re.compile(r'([0-9]{4}) - ([0-9]{4}) \(ca\)')
    #r2 = re.compile(r'([0-9]{4}) \(ca\)')
    #r3 = re.compile(r'^([^,]), (.*)$')
    #for fn in fieldnames:
    #    tag = soup.find('dt', text=re.compile(fn))
    #    if not tag:
    #        fields[fn] = 'NOTFOUND'
    #        #yield "Fant ikke feltet %s" % fn
    #        #return
    #    else:
    #        val = tag.findNext('dd').findChild('div').text.strip()
    #        if fn == 'Datering':
    #            val = r1.sub(r'{{Other date|~|\1|\2}}', val)
    #            val = r2.sub(r'{{Other date|~|\1}}', val)
    #        elif fn == 'Avbildet person':
    #            val = r3.sub(r'\2 \1', val)
    #            cats.append(val)
    #            while tag.find_next('dt').text.strip() == '':
    #                tag = tag.find_next('dt')
    #                tmp = tag.findNext('dd').findChild('div').text.strip()
    #                tmp = r3.sub(r'\2 \1', tmp)
    #                val += '\n' + tmp
    #                cats.append(val)
    #        fields[fn] = val

    #src = soup.find('div','image').findChild('img').get('src')

    #commons = mwclient.Site('commons.wikimedia.org')

    #yield "hello"

    #yield '<table>'
    #for k, v in sorted(environ.items()):
         #yield '<tr><th>%s</th><td>%s</td></tr>' % (escape(k), escape(v))
    #yield '</table>'

WSGIServer(app).run()

