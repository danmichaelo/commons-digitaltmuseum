# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4
import sqlite3
from flask import render_template
from .controller import Controller


class TransferController(Controller):

    def __init__(self, app, config):
        Controller.__init__(self, app)
        self.config = config

    def get(self):
        return render_template('transfer.html')
