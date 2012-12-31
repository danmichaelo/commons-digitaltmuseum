#!/usr/bin/env python
## -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import mwclient
import sqlite3
import time, datetime
from danmicholoparser import TemplateEditor
import logging
import logging.handlers
import time

debug = True

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

file_handler = logging.handlers.RotatingFileHandler('updater.log', maxBytes=100000, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

warn_handler = logging.FileHandler('warnings.log')
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(formatter)
logger.addHandler(warn_handler)

if debug:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


logger.info('This is updater.py')

commons = mwclient.Site('commons.wikimedia.org')
page = commons.pages['Template:Oslobilder']

sql = sqlite3.connect('oslobilder.db')
sql.row_factory = sqlite3.Row
cur = sql.cursor()

on_commons = []
for img in page.embeddedin(namespace=6):
    filename = img.page_title
    on_commons.append(filename)
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
    elif 3 in tpl.parameters:
        collection = tpl.parameters[3]

    if 'information' in te.templates:
        tpl = te.templates['information'][0]
    elif 'artwork' in te.templates:
        tpl = te.templates['artwork'][0]
    elif 'photograph' in te.templates:
        tpl = te.templates['photograph'][0]
    else:
        logger.warning('[[File:%s]] %s', filename, 'Did not find {{information}} or {{artwork}}-templates!')
        continue
    
    if 'description' in tpl.parameters:
        desc = tpl.parameters['description']
    elif 'Description' in tpl.parameters:
        desc = tpl.parameters['Description']
    else:
        desc = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |description=')
        continue

    if 'date' in tpl.parameters:
        date = tpl.parameters['date']
    elif 'Date' in tpl.parameters:
        date = tpl.parameters['Date']
    else:
        date = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |date=')
        continue
    
    if 'source' in tpl.parameters:
        source = tpl.parameters['source']
    elif 'Source' in tpl.parameters:
        source = tpl.parameters['Source']
    else:
        source = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |source=')
        continue

    if 'author' in tpl.parameters:
        author = tpl.parameters['author']
    elif 'Author' in tpl.parameters:
        author = tpl.parameters['Author']
    elif 'photographer' in tpl.parameters:
        author = tpl.parameters['photographer']
    elif 'Photographer' in tpl.parameters:
        author = tpl.parameters['Photographer']
    elif 'artist' in tpl.parameters:
        author = tpl.parameters['artist']
    elif 'Artist' in tpl.parameters:
        author = tpl.parameters['Artist']
    else:
        author = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |author=')
        continue

    data = { 'filename': filename, 'width': width, 'height': height, 'size': size, 
             'institution': institution, 'imageid': imageid, 'collection': collection, 
             'author': author, 'source': source, 'date': date, 'description': desc, 
             'revision': revid }
    
    firstrev = img.revisions(limit=1, dir='newer').next()

    rows = cur.execute(u'SELECT * FROM files WHERE NOT(institution=? AND imageid=?) AND first_revision=?', [institution, imageid, firstrev['revid']]).fetchall()
    if rows:
        row = rows[0]
        logger.info('[[File:%s]] Identification changed from %s/%s to %s/%s' % (filename, row['institution'], row['imageid'], institution, imageid))
        try:
            cur.execute(u'UPDATE files SET institution=?, imageid=? WHERE first_revision=?', [institution, imageid, firstrev['revid']])
            sql.commit()
        except sqlite3.integrityerror as e:
            logger.error('[[File:%s]] was not saved. error: %s. query: %s', filename, e.message, query)

    rows = cur.execute(u'SELECT * FROM files ' + \
            'WHERE institution=? AND imageid=?', (institution, imageid)).fetchall()
    if rows:
        found = False
        for row in rows:
            if row['revision'] == revid:
                found = True
            else:
                if firstrev['revid'] == row['first_revision']:
                    found = True
                    logger.info('Image was updated: %s/%s', institution, imageid)
                    para = []
                    val = []
                    for k,v in data.iteritems():
                        if v != row[k]:
                            logger.info('    %s: %s -> %s', k, row[k], v)
                            para.append('%s=?' % k)
                            val.append(v)
                    val.append(institution)
                    val.append(imageid)
                    query = u'UPDATE files SET %s WHERE institution=? AND imageid=?' % ', '.join(para)
                    logger.info(query)
                    #cur.execute(query, val)
                    try:
                        cur.execute(query, val)
                    except sqlite3.IntegrityError as e:
                        logger.error('[[File:%s]] was not saved. Error: %s. Query: %s', filename, e.message, query)
                    sql.commit()
    

        if not found:
            logger.warning('[[File:%s]] shares the identification %s/%s with [[File:%s]]', filename, institution, imageid, row['filename'])

            data['upload_date'] = time.mktime(firstrev['timestamp'])
            data['first_revision'] = firstrev['revid']
            data['uploader'] = firstrev['user']

            para = [ ','.join(data.keys()), ','.join(['?' for q in range(len(data))]) ]
            val = data.values()
            query = u'INSERT INTO files (%s) VALUES (%s)' % tuple(para)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[File:%s]] was not saved. Error: %s. Query: %s', filename, e.message, query)
            sql.commit()

    else:
        firstrev = img.revisions(limit=1, dir='newer').next()

        row2 = cur.execute(u'SELECT * FROM files ' + \
                            'WHERE first_revision=?', [firstrev['revid']]).fetchone()
        if row2:
            logger.info('[[File:%s]] changed identification from %s/%s to %s/%s', \
                        filename, row2['institution'], row2['imageid'], institution, imageid)
            para = []
            val = []
            for k,v in data.iteritems():
                if v != row2[k]:
                    para.append('%s=?' % k)
                    val.append(v)
            val.append(firstrev['revid'])
            query = u'UPDATE files SET %s WHERE first_revision=?' % ', '.join(para)
            logger.info(query)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[File:%s]] was not saved. Error: %s. Query: %s', filename, e.message, query)
            sql.commit()

        else:
            logger.info('[[File:%s]] is identified as %s/%s', filename, institution, imageid)

            data['upload_date'] = time.mktime(firstrev['timestamp'])
            data['first_revision'] = firstrev['revid']
            data['uploader'] = firstrev['user']

            para = [ ','.join(data.keys()), ','.join(['?' for q in range(len(data))]) ]
            val = data.values()
            query = u'INSERT INTO files (%s) VALUES (%s)' % tuple(para)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[%s]] was not saved. Error: %s. Query: %s', filename, e.message, query)
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

in_db = []
for row in cur.execute('SELECT filename FROM files'):
    in_db.append(row['filename'])
in_db_set = set(in_db)
on_commons_set = set(on_commons)
logger.info("%d files in DB, %d files on Commons", len(in_db_set), len(on_commons_set))
if len(in_db) != len(in_db_set):
    logger.error("Data integrity error! len(in_db) = %d != len(in_db_set) = %d", len(in_db), len(in_db_set))
elif len(on_commons) != len(on_commons_set):
    logger.error("Data integrity error! len(on_commons) = %d != len(on_commons_set) = %d", len(on_commons), len(on_commons_set))
elif on_commons_set.difference(in_db_set):
    logger.error("Data integrity error! The following images on commons was not found in the DB: %s", ', '.join(list(on_commons_set.difference(in_db_set))))
    print type(in_db[0]), type(on_commons[0])
else:
    for filename in list(in_db_set.difference(on_commons_set)):
        rows = cur.execute(u'SELECT institution, imageid FROM files WHERE filename=?', [filename]).fetchall()
        if len(rows) != 1:
            logger.error("Data integrity error! More than one database entry for File:%s", filename)
        else:
            institution = rows[0]['institution']
            imageid = rows[0]['imageid']
            logger.warning('[[%s]] is no longer identified as %s/%s', filename, institution, imageid)
            cur.execute(u'DELETE FROM files WHERE filename=?', [filename])
            sql.commit()


f = open('last_update', 'w')
f.write('%.4f' % time.time())
f.close()


