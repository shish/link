#!/usr/bin/env python

import web
web.config.debug = False

import cgi
import logging
import logging.handlers
import hashlib

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import func
from models import *

urls = (
    '/?', 'surveys',
    '/survey', 'surveys',
    '/survey/(\d+)', 'survey',
    '/user', 'user',
    '/(favicon.ico)', 'static',
)
site = "http://link.shishnet.org"

app = web.application(urls, globals())


class LinkError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = message


def handle_exceptions(func):
    def logger(*args):
        try:
            return func(*args)
        except LinkError, e:
            return render.standard("Error", e.title, "", e.message)
        except Exception, e:
            logging.exception("Unhandled exception:")
            #return render.standard("Error", str(e), "", str(e))
            raise
    return logger


class surveys:
    @handle_exceptions
    def GET(self):
        return "surveys"


class survey:
    @handle_exceptions
    def GET(self, id):
        return "survey %s" % id


class user:
    @handle_exceptions
    def GET(self):
        return "user"


class static:
    @handle_exceptions
    def GET(self, filename):
        try:
            return file("static/"+filename).read()
        except:
            return "not found"


if __name__ == "__main__":
    logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)-8s %(message)s',
            filename="../logs/app.log")
    smtp = logging.handlers.SMTPHandler(
            "localhost", "noreply@shishnet.org",
            ["shish+link@shishnet.org", ], "link error report")
    smtp.setLevel(logging.WARNING)
    logging.getLogger('').addHandler(smtp)

    logging.info("App starts...")
    app.run()
