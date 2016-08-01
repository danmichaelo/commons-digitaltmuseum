# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import json
import re
from werkzeug.wrappers import Response
from time import time
import urllib
from .controller import Controller

import logging
logger = logging.getLogger()


class SearchController(Controller):

    def __init__(self, app, config):
        Controller.__init__(self, app)
        self.config = config

    def get(self, request):

        start_time = time()

        f = self.read('last_update')
        last_update = f.read()
        f.close()

        plimit = self.config['default_limit']
        psort = self.config['default_sort']
        porder = self.config['default_sortorder']
        where = []
        where_data = []

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
                            where_data.append('%' + val.decode('utf-8')[1:-1] + '%')
                        elif val[-1] == '*':
                            where.append('%s LIKE ?' % knownkey)
                            where_data.append(val.decode('utf-8')[:-1]+'%')
                        elif val[0] == '*':
                            where.append('%s LIKE ?' % knownkey)
                            where_data.append('%' + val.decode('utf-8')[1:])
                        else:
                            where.append('%s=?' % knownkey)
                            where_data.append(val.decode('utf-8'))

        if len(req_inst) > 0 and len(req_inst) < len(self.config['institutions']):
            where.append('institution IN (%s)' % ','.join(["?" for q in range(len(req_inst))]))
            where_data.extend(req_inst)

        if len(where) == 0:
            where = ''
        else:
            where = ' WHERE ' + ' AND '.join(where)

        sql = self.open_db()
        cur = sql.cursor()
        rows = []
        query = u'SELECT filename, width, height, size, institution, imageid, ' + \
                 'collection, author, date, description, upload_date ' + \
                 'FROM files' + where + ' ORDER BY %s %s LIMIT %s' % (psort, porder, plimit)

        logger.info(query)
        logger.info(where_data)

        for row in cur.execute(query, where_data):

            name = row[0].replace(' ', '_')
            name_enc = urllib.quote(name.encode('utf-8'))

            url = 'https://commons.wikimedia.org/wiki/File:' + name_enc
            thumbmax = 120
            if row[1] > row[2]:
                thumbw = thumbmax
                thumbh = round(float(row[2])/row[1]*thumbmax)
            else:
                thumbh = thumbmax
                thumbw = round(float(row[1])/row[2]*thumbmax)

            thumb_url = self.get_thumb_url(name, thumbw)
            thumb = '<a href="%s"><img src="%s" border="0" alt="%s" width="%d" height="%d"/></a>' % (url, thumb_url, row[0], thumbw, thumbh)

            url = '<a href="%s">%s</a>' % (url, row[0])

            row2 = {'thumb': thumb, 'filename': url, 'width': row[1], 'height': row[2], 
                    'size': '%.f' % (row[3]/1024), 'institution': row[4], 'imageid': row[5], 
                    'collection': row[6], 'author': row[7], 'date': row[8], 'description': row[9], 
                    'upload_date': row[10] }
            rows.append(row2)

        end_time = time()
        time_spent = int((end_time - start_time)*1000)

        data = json.dumps({
            'where': where, 'data': where_data, 'rows': rows, 'query': query, 'time': time_spent, 'last_update': last_update
        })
        return Response(data, mimetype='application/json')
