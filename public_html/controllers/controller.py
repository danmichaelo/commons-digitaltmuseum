# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import os
from jinja2 import Environment, FileSystemLoader
from werkzeug.wrappers import Response
import hashlib
import urllib

class Controller:

    def __init__(self):
        pass

    def get_thumb_url(self, name, width):
        name = name.encode('utf-8')
        m = hashlib.md5()
        m.update(name)
        md5d = m.hexdigest()
        enc = urllib.quote(name)
        return '//upload.wikimedia.org/wikipedia/commons/thumb/%(h1)s/%(h1)s%(h2)s/%(name)s/%(width)dpx-%(name)s' % {
            'name': enc, 'width': width, 'h1': md5d[0], 'h2': md5d[1]
           }


    def render_template(self, template_name, **context):
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

        jinja_env = Environment(loader=FileSystemLoader(template_path),
                                autoescape=True,
                                trim_blocks=True,
                                lstrip_blocks=True)

        t = jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def not_found(self):

        response = self.render_template('404.html')
        response.status_code = 404
        return response
