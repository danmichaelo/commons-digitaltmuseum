# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import json
from werkzeug.wrappers import Response
from time import time
import sqlite3
import urllib
from flask import render_template
from .controller import Controller

import logging
logger = logging.getLogger()


class Backend(Controller):

    def __init__(self, config):
        Controller.__init__(self)
        self.config = config

    def __init__(self, config):
        self.config = config

    def get(self, request, args):

        start_time = time()

        f = open('../last_update', 'r')
        last_update = f.read()
        f.close()

        plimit = self.config['default_limit']
        psort = self.config['default_sort']
        porder = self.config['default_sortorder']
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
                    plimit = self.config['default_limit']
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

        if len(req_inst) > 0 and len(req_inst) < len(self.config['institutions']):
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

            thumb_url = self.get_thumb_url(name, thumbw)
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
