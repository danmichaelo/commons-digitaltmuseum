#!/usr/bin/env python
## -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import os
import mwclient
import sqlite3
import time, datetime
from mwtemplates import TemplateEditor
import logging
import logging.handlers
import time
import oursql

debug = True
runstart = datetime.datetime.now()

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

sql = sqlite3.connect('storage/oslobilder.db')
sql.row_factory = sqlite3.Row
cur = sql.cursor()

db = oursql.connect(db='commonswiki_p',
    host='commonswiki-p.rrdb.toolserver.org',
    read_default_file=os.path.expanduser('~/.my.cnf'),
    charset=None,
    use_unicode=False
)
ccur = db.cursor()

on_commons = []
ccur.execute('SELECT page.page_title, max(revision.rev_id) FROM page, templatelinks LEFT JOIN revision ON templatelinks.tl_from=revision.rev_page WHERE templatelinks.tl_namespace=10 AND templatelinks.tl_title=? AND templatelinks.tl_from=page.page_id AND page.page_namespace=6 GROUP BY revision.rev_page', [page.page_title.encode('utf-8')])
for crow in ccur:

    filename = crow[0].replace('_', ' ').decode('utf-8')
    on_commons.append(filename)
    lastrev = crow[1]

    rows = cur.execute(u'SELECT * FROM files WHERE revision=?', [lastrev]).fetchall()
    if rows:
        continue

    #print filename
    img = commons.images[filename]

    width = img.imageinfo['width']
    height = img.imageinfo['height']
    size = img.imageinfo['size']
    revid = img.revision
    
    txt = img.edit(readonly=True)
    te = TemplateEditor(txt)

    tpl = te.templates['oslobilder'][0]
    if 1 in tpl.parameters:
        institution = tpl.parameters[1].value
    else:
        logger.warning('[[File:%s]] %s', filename, 'Too few parameters given!')
        continue
    if 2 in tpl.parameters:
        imageid = tpl.parameters[2].value
    else:
        logger.warning('[[File:%s]] %s', filename, 'Too few parameters given!')
        continue
    collection = ''
    if 'collection' in tpl.parameters:
        collection = tpl.parameters['collection'].value
    elif 3 in tpl.parameters:
        collection = tpl.parameters[3].value

    if 'information' in te.templates:
        tpl = te.templates['information'][0]
    elif 'artwork' in te.templates:
        tpl = te.templates['artwork'][0]
    elif 'photograph' in te.templates:
        tpl = te.templates['photograph'][0]
    else:
        logger.warning('[[File:%s]] %s', filename, 'Did not find any of the following templates: {{information}}, {{artwork}}, {{photograph}}')
        continue
    
    if 'description' in tpl.parameters:
        desc = tpl.parameters['description'].value
    elif 'Description' in tpl.parameters:
        desc = tpl.parameters['Description'].value
    else:
        desc = ''
        #logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |description=')
        continue

    if 'date' in tpl.parameters:
        date = tpl.parameters['date'].value
    elif 'Date' in tpl.parameters:
        date = tpl.parameters['Date'].value
    else:
        date = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |date=')
        continue
    
    if 'source' in tpl.parameters:
        source = tpl.parameters['source'].value
    elif 'Source' in tpl.parameters:
        source = tpl.parameters['Source'].value
    else:
        source = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |source=')
        continue

    if 'author' in tpl.parameters:
        author = tpl.parameters['author'].value
    elif 'Author' in tpl.parameters:
        author = tpl.parameters['Author'].value
    elif 'photographer' in tpl.parameters:
        author = tpl.parameters['photographer'].value
    elif 'Photographer' in tpl.parameters:
        author = tpl.parameters['Photographer'].value
    elif 'artist' in tpl.parameters:
        author = tpl.parameters['artist'].value
    elif 'Artist' in tpl.parameters:
        author = tpl.parameters['Artist'].value
    else:
        author = ''
        logger.warning('[[File:%s]] %s', filename, '{{information}} does not contain |author= or |artist= or |photographer=')
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
                    logger.info('UPDATED [[File:%s]]', filename)
                    para = []
                    val = []
                    for k,v in data.iteritems():
                        if v != row[k]:
                            oldval = row[k]
                            if type(oldval) == unicode and len(oldval) > 20:
                                oldval = oldval[:18] + '...'
                            newval = v
                            if type(newval) == unicode and len(newval) > 20:
                                newval = newval[:18] + '...'
                            logger.info('    %s: %s -> %s', k, oldval, newval)
                            para.append('%s=?' % k)
                            val.append(v)
                    val.append(institution)
                    val.append(imageid)
                    query = u'UPDATE files SET %s WHERE institution=? AND imageid=?' % ', '.join(para)
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
            logger.info('ADDED [[File:%s]]: identified as %s/%s', filename, institution, imageid)

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
            logger.warning('REMOVED [[%s]]: no longer identified as %s/%s', filename, institution, imageid)
            cur.execute(u'DELETE FROM files WHERE filename=?', [filename])
            sql.commit()


f = open('last_update', 'w')
f.write('%.4f' % time.time())
f.close()

runend = datetime.datetime.now()
runtime = (runend - runstart).total_seconds()
logger.info('Updater completed. Runtime was %.f seconds.', runtime)
