# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4
import sqlite3
import os
from flask import render_template
from .controller import Controller


class StatsController(Controller):

    def __init__(self, app, config):
        Controller.__init__(self, app)
        self.config = config

    def get(self):

        db = self.open_db()
        cur = db.cursor()
        html = 'Mest aktive opplastere:<ul>'
        for row in cur.execute('SELECT uploader, count(*) as cnt FROM files GROUP BY uploader ORDER BY cnt DESC'):
            html += '<li>%s: %d</li>' % (row[0], row[1])
            # html += '<li><a href="http://commons.wikimedia.org/wiki/File:%s">%s<br />%s</a></li>\n' % (enc, thumb, row[0])
        html += '</ul>\n'

        return render_template('stats.html', main=html)
