# -*- coding: utf-8 -*-

from pycouchdb import Server


def dump():
    server = Server("http://admin:admin@localhost:5984/")
    return server.info()


def restore():
    pass
