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
import pymysql.cursors

debug = True
runstart = datetime.datetime.now()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

# file_handler = logging.handlers.RotatingFileHandler('updater.log', maxBytes=100000, backupCount=3)
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)

# warn_handler = logging.FileHandler('warnings.log')
# warn_handler.setLevel(logging.WARNING)
# warn_handler.setFormatter(formatter)
# logger.addHandler(warn_handler)

if debug:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_commons_metadata(img):
    pagename = img.page_title
    width = img.imageinfo['width']
    height = img.imageinfo['height']
    size = img.imageinfo['size']
    revid = img.revision
    txt = img.text()
    te = TemplateEditor(txt)

    tpl = te.templates['oslobilder'][0]
    if 1 in tpl.parameters:
        institution = tpl.parameters[1].value
    else:
        logger.warning('[[File:%s]] %s', pagename, 'Too few parameters given!')
        return
    if 2 in tpl.parameters:
        imageid = tpl.parameters[2].value
    else:
        logger.warning('[[File:%s]] %s', pagename, 'Too few parameters given!')
        return
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
    elif 'painting' in te.templates:
        tpl = te.templates['painting'][0]
    else:
        logger.warning('[[File:%s]] %s', pagename,
                       'Did not find any of the following templates: {{information}}, {{artwork}}, {{photograph}}, {{painting}}')
        return

    if 'description' in tpl.parameters:
        desc = tpl.parameters['description'].value
    elif 'Description' in tpl.parameters:
        desc = tpl.parameters['Description'].value
    else:
        desc = ''
        logger.warning('[[File:%s]] %s', pagename, '{{information}} does not contain |description=')

    if 'date' in tpl.parameters:
        date = tpl.parameters['date'].value
    elif 'Date' in tpl.parameters:
        date = tpl.parameters['Date'].value
    else:
        logger.warning('[[File:%s]] %s', pagename, '{{information}} does not contain |date=')
        return

    if 'source' in tpl.parameters:
        source = tpl.parameters['source'].value
    elif 'Source' in tpl.parameters:
        source = tpl.parameters['Source'].value
    else:
        logger.warning('[[File:%s]] %s', pagename, '{{information}} does not contain |source=')
        return

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
        logger.warning('[[File:%s]] %s', pagename,
                       '{{information}} does not contain |author= or |artist= or |photographer=')
        return

    return {'filename': pagename, 'width': width, 'height': height, 'size': size,
            'institution': institution, 'imageid': imageid, 'collection': collection,
            'author': author, 'source': source, 'date': date, 'description': desc,
            'revision': revid}

logger.info('This is updater.py')

commons = mwclient.Site('commons.wikimedia.org')
template = commons.pages['Template:Oslobilder']

sql = sqlite3.connect('instance/oslobilder.db')
sql.row_factory = sqlite3.Row
cur = sql.cursor()

db = pymysql.connect(db='commonswiki_p',
                    host='commonswiki.labsdb',
                    read_default_file=os.path.expanduser('~/replica.my.cnf'))
ccur = db.cursor()

on_commons = []

# Find all pages that embeds {{Oslobilder}}
ccur.execute('SELECT page.page_title, max(revision.rev_id) FROM page, templatelinks LEFT JOIN revision ON templatelinks.tl_from=revision.rev_page WHERE templatelinks.tl_namespace=10 AND templatelinks.tl_title=? AND templatelinks.tl_from=page.page_id AND page.page_namespace=6 GROUP BY revision.rev_page', [template.page_title])
for crow in ccur:

    commons_pagename = crow[0].replace('_', ' ').decode('utf-8')
    on_commons.append(commons_pagename)
    lastrev = crow[1]

    rows = cur.execute('SELECT * FROM files WHERE revision=?', [lastrev]).fetchall()
    if rows:
        # Latest revision of the page is already in our local DB
        continue

    # Get some metadata from Commons
    img = commons.images[commons_pagename]
    data = get_commons_metadata(img)

    if data is None:
        # Uh oh, something failed
        continue
    
    firstrev = next(img.revisions(limit=1, dir='newer'))

    # Check if identification has changed
    rows = cur.execute('SELECT * FROM files WHERE NOT(institution=? AND imageid=?) AND first_revision=?', [data['institution'], data['imageid'], firstrev['revid']]).fetchall()
    if rows:
        row = rows[0]
        logger.info('[[File:%s]] Identification changed from %s/%s to %s/%s' % (commons_pagename, row['institution'], row['imageid'], data['institution'], data['imageid']))
        try:
            cur.execute('UPDATE files SET institution=?, imageid=? WHERE first_revision=?', [data['institution'], data['imageid'], firstrev['revid']])
            sql.commit()
        except sqlite3.integrityerror as e:
            logger.error('[[File:%s]] was not saved. error: %s. query: %s', commons_pagename, e, query)

    rows = cur.execute('SELECT * FROM files WHERE institution=? AND imageid=?', (data['institution'], data['imageid'])).fetchall()
    if rows:
        found = False
        for row in rows:
            if row['revision'] == data['revision']:
                found = True  # No need to update
            else:
                if firstrev['revid'] == row['first_revision']:
                    found = True
                    logger.info('UPDATE [[File:%s]]:', commons_pagename)
                    para = []
                    val = []
                    for k, v in data.items():
                        if v != row[k]:
                            oldval = row[k]
                            if type(oldval) == str and len(oldval) > 40:
                                oldval = oldval[:38] + '...'
                            newval = v
                            if type(newval) == str and len(newval) > 40:
                                newval = newval[:38] + '...'
                            logger.info('    %s: %s -> %s', k, oldval, newval)
                            para.append('%s=?' % k)
                            val.append(v)
                    val.append(row['first_revision'])
                    query = 'UPDATE files SET %s WHERE first_revision=?' % ', '.join(para)
                    try:
                        cur.execute(query, val)
                    except sqlite3.IntegrityError as e:
                        logger.error('[[File:%s]] was not saved. Error: %s --- Query: %s --- Params: %s',
                                     commons_pagename, e, query, repr(val))
                    sql.commit()

        if not found:
            logger.info('INSERT [[File:%s]]: identified as %s/%s', commons_pagename, data['institution'], data['imageid'])
            logger.warning('[[File:%s]] shares the identification %s/%s with [[File:%s]]', commons_pagename, data['institution'], data['imageid'], row['filename'])

            data['upload_date'] = time.mktime(firstrev['timestamp'])
            data['first_revision'] = firstrev['revid']
            data['uploader'] = firstrev['user']

            para = [','.join(list(data.keys())), ','.join(['?' for q in range(len(data))])]
            val = list(data.values())
            query = 'INSERT INTO files (%s) VALUES (%s)' % tuple(para)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[File:%s]] was not saved. Error: %s. Query: %s', commons_pagename, e, query)
            sql.commit()

    else:
        firstrev = next(img.revisions(limit=1, dir='newer'))

        row2 = cur.execute('SELECT * FROM files WHERE first_revision=?', [firstrev['revid']]).fetchone()
        if row2:
            logger.info('UPDATE [[File:%s]]: identification changed from %s/%s to %s/%s',
                        commons_pagename, row2['institution'], row2['imageid'], data['institution'], data['imageid'])
            para = []
            val = []
            for k,v in data.items():
                if v != row2[k]:
                    para.append('%s=?' % k)
                    val.append(v)
            val.append(firstrev['revid'])
            query = 'UPDATE files SET %s WHERE first_revision=?' % ', '.join(para)
            logger.info(query)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[File:%s]] was not saved. Error: %s. Query: %s', commons_pagename, e, query)
            sql.commit()

        else:
            logger.info('INSERT [[File:%s]]: identified as %s/%s', commons_pagename, data['institution'], data['imageid'])

            data['upload_date'] = time.mktime(firstrev['timestamp'])
            data['first_revision'] = firstrev['revid']
            data['uploader'] = firstrev['user']

            para = [','.join(list(data.keys())), ','.join(['?' for q in range(len(data))])]
            val = list(data.values())
            query = 'INSERT INTO files (%s) VALUES (%s)' % tuple(para)
            try:
                cur.execute(query, val)
            except sqlite3.IntegrityError as e:
                logger.error('[[%s]] was not saved. Error: %s. Query: %s', commons_pagename, e, query)
            sql.commit()

if __name__ == '__main__':
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
    else:
        for commons_pagename in list(in_db_set.difference(on_commons_set)):
            rows = cur.execute('SELECT institution, imageid FROM files WHERE filename=?', [commons_pagename]).fetchall()
            if len(rows) != 1:
                logger.error("Data integrity error! More than one database entry for File:%s", commons_pagename)
            else:
                logger.warning('REMOVED [[%s]]: no longer identified as %s/%s', commons_pagename, rows[0]['institution'], rows[0]['imageid'])
                cur.execute('DELETE FROM files WHERE filename=?', [commons_pagename])
                sql.commit()

    f = open('instance/last_update', 'w')
    f.write('%.4f' % time.time())
    f.close()

    runend = datetime.datetime.now()
    runtime = (runend - runstart).total_seconds()
    logger.info('Updater completed. Runtime was %.f seconds.', runtime)
