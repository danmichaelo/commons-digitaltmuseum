# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

import sqlite3

from controller import Controller

class Transfer(Controller):

    def __init__(self, config):
        Controller.__init__(self)
        self.config = config

    def get(self, request, args):

        return self.render_template('transfer.html')
