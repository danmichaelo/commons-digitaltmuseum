# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import sqlite3
from flask import render_template
from .controller import Controller

class Stats(Controller):

    def __init__(self, config):
        Controller.__init__(self)
        self.config = config

    def get(self):

        sql = sqlite3.connect('/data/project/digitaltmuseum/storage/oslobilder.db')
        cur = sql.cursor()
        html = 'Mest aktive opplastere:<ul>'
        for row in cur.execute(u'SELECT uploader, count(*) as cnt FROM files GROUP BY uploader ORDER BY cnt DESC'):
            html += '<li>%s: %d</li>' % (row[0], row[1])
            #html += '<li><a href="http://commons.wikimedia.org/wiki/File:%s">%s<br />%s</a></li>\n' % (enc, thumb, row[0])
        html += '</ul>\n'

        return render_template('stats.html', main=html)
