#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import sys
sys.stderr = sys.stdout
sys.path.insert(0, '/data/project/digimus/ENV/lib/python2.7/site-packages')


import cgitb
cgitb.enable()

import logging
import logging.handlers
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

fh = logging.FileHandler('main.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info('Hello world')

import re
import sys

#sys.path.insert(0, '/data/project/digimus')

from werkzeug.wrappers import Request
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect, HTTPException
from werkzeug.utils import redirect
from wsgiref.handlers import CGIHandler

import yaml


import controllers  # relative import

config = yaml.load(open('../config.yml', 'r'))
url_map = Map([
              Rule('/', endpoint='index'),
              Rule('/backend', endpoint='backend'),
              Rule('/dups', endpoint='duplicates'),
              Rule('/stats', endpoint='stats'),
              Rule('/transfer', endpoint='transfer'),
              Rule('/transferbg', endpoint='transferbg')
              ], default_subdomain='tools')

def application(environ, start_response):
    #logger.info(environ)
    environ['SCRIPT_NAME'] = '/digimus'

    try:

        #print "Content-Type: text/plain"
        #print
        #print "Hello"
        #print environ['wsgi.url_scheme']
        #sys.exit(0)

        urls = url_map.bind_to_environ(environ, server_name='wmflabs.org', subdomain='tools')
        endpoint, args = urls.match()

        request = Request(environ)


        logger.info('Endpoint: ' + endpoint)
        logger.info(args)

        controller_name = getattr(getattr(controllers, endpoint), endpoint.capitalize())
        controller = controller_name(config)
        response = controller.get(request, args)
        return response(environ, start_response)

    except NotFound, e:
        c = controllers.controller.Controller()
        import sys
        sys.stderr = sys.stdout
        response = c.not_found()
        return response(environ, start_response)

    except RequestRedirect, e:
        logger.info('Redir to: %s' % e.new_url)
        response = redirect(e.new_url)
        return response(environ, start_response)

    except HTTPException, e:
        logger.error(e)
        return e(environ, start_response)
    #logger.info(args)


try:
    CGIHandler().run(application)
except Exception as e:
    logger.exception('Unhandled Exception')
