# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import sqlite3
from controller import Controller

class Index(Controller):

    def __init__(self, config):
        Controller.__init__(self)
        self.config = config


    def get(self, request, args):

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

        return self.render_template('index.html',
                               active_page='./',
                               rows=[],
                               total=total,
                               unique=unique,
                               totals=totals,
                               institutions=self.config['institutions'],
                               columns=self.config['columns'],
                               last_update=last_update,
                               default_limit=self.config['default_limit'],
                               default_sort=self.config['default_sort'],
                               default_sortorder=self.config['default_sortorder']
                               )
