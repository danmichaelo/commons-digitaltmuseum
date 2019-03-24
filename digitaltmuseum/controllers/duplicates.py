# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4
import sqlite3
import urllib.request, urllib.parse, urllib.error
from flask import render_template
from .controller import Controller


class DuplicatesController(Controller):

    def __init__(self, app, config):
        Controller.__init__(self, app)
        self.config = config

    def get(self):

        db = self.open_db()
        cur = db.cursor()
        dups = []
        for row in cur.execute('SELECT institution,imageid,count(*) FROM files GROUP BY institution,imageid'):
            if row[2] > 1:
                dups.append([row[0], row[1]])

        html = '<ul>'
        for dup in dups:
            html += '<li>%s/%s er oppgitt som kilde for:\n<ul class="dups">\n' % tuple(dup)
            # yield(type(html).__name__)
            for row in cur.execute('SELECT filename, width, height FROM files WHERE institution=? AND imageid=?', dup):
                name = row[0].replace(' ', '_')
                name_enc = urllib.parse.quote(name.encode('utf-8'))
                thumbmax = 120
                if row[1] > row[2]:
                    thumbw = thumbmax
                    thumbh = round(float(row[2])/row[1]*thumbmax)
                else:
                    thumbh = thumbmax
                    thumbw = round(float(row[1])/row[2]*thumbmax)

                thumb_url = self.get_thumb_url(name, thumbw)
                thumb = '<img src="%s" border="0" alt="%s" width="%d" height="%d"/>' % (thumb_url, name, thumbw, thumbh)
                html += '<li><a href="https://commons.wikimedia.org/wiki/File:%s">%s<br />%s</a></li>\n' % (name_enc, thumb, row[0])
            html += '</ul>\n'
        html += '</ul>\n'

        return render_template('dups.html', main=html)

