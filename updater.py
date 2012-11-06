#!/usr/bin/env python
## -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import mwclient
import sqlite3
import time, datetime
from danmicholoparser import TemplateEditor
import logging

debug = True

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

file_handler = logging.FileHandler('updater.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

warn_handler = logging.FileHandler('updater.log')
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(formatter)
logger.addHandler(warn_handler)

if debug:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


logger.info('This is updated.py')

commons = mwclient.Site('commons.wikimedia.org')
page = commons.pages['Template:Oslobilder']

sql = sqlite3.connect('oslobilder.db')
cur = sql.cursor()

for img in page.embeddedin(namespace=6):
    filename = img.page_title
    #print filename
    width = img.imageinfo['width']
    height = img.imageinfo['height']
    size = img.imageinfo['size']
    revid = img.revision
    
    txt = img.edit(readonly=True)
    te = TemplateEditor(txt)

    tpl = te.templates['oslobilder'][0]
    institution = tpl.parameters[1]
    imageid = tpl.parameters[2]
    collection = ''
    if 'collection' in tpl.parameters:
        collection = tpl.parameters['collection']

    if 'information' in te.templates:
        tpl = te.templates['information'][0]
    else:
        logger.warning('[[%s]] %s', (filename, '{{information}}-template not found!'))
        continue
    
    if 'description' in tpl.parameters:
        desc = tpl.parameters['description']
    elif 'Description' in tpl.parameters:
        desc = tpl.parameters['Description']
    else:
        desc = ''
        logger.warning('[[%s]] %s', (filename, '{{information}} does not contain |description='))
        continue

    if 'date' in tpl.parameters:
        date = tpl.parameters['date']
    elif 'Date' in tpl.parameters:
        date = tpl.parameters['Date']
    else:
        date = ''
        logger.warning('[[%s]] %s', (filename, '{{information}} does not contain |date='))
        continue
    
    if 'source' in tpl.parameters:
        source = tpl.parameters['source']
    elif 'Source' in tpl.parameters:
        source = tpl.parameters['Source']
    else:
        source = ''
        logger.warning('[[%s]] %s', (filename, '{{information}} does not contain |source='))
        continue

    if 'author' in tpl.parameters:
        author = tpl.parameters['author']
    elif 'Author' in tpl.parameters:
        author = tpl.parameters['Author']
    else:
        author = ''
        logger.warning('[[%s]] %s', (filename, '{{information}} does not contain |author='))
        continue
    
    row = cur.execute(u'SELECT filename, revision FROM files WHERE institution=? AND imageid=?', (institution, imageid)).fetchone()
    if row:
        if row['revision'] != revid:
            logger.info('[[%s]] was updated - updating DB', [filename])
    else:
        logger.info('[[%s]] is new - saving to DB', [filename])
        firstrev = img.revisions(limit=1, dir='newer').next()
        uploaddate = time.mktime(firstrev['timestamp'])
        data = [filename, width, height, size, institution, imageid, collection, author, source, date, desc, revid, uploaddate]
        cur.execute(u'INSERT INTO files (filename, width, height, size, institution, imageid, ' + \
                     'collection, author, source, sourcedate, description, revision, uploaddate) ' + \
                     'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', data)
        sql.commit()
    #break
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

    #yield json.dumps({ 'license': license, 'src': src, 'metadata': fields, 'cats': cats })
    #yield "hello"

    #yield '<table>'
    #for k, v in sorted(environ.items()):
         #yield '<tr><th>%s</th><td>%s</td></tr>' % (escape(k), escape(v))
    #yield '</table>'
