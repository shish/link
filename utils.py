#!/usr/bin/env python

import logging

from sqlalchemy.orm import scoped_session, sessionmaker

from models import engine


class SiteError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = message


def load_sqla(handler):
    web.ctx.orm = scoped_session(sessionmaker(bind=engine))
    try:
        return handler()
    except web.HTTPError:
        web.ctx.orm.commit()
        raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()
        # If the above alone doesn't work, uncomment
        # the following line:
        # web.ctx.orm.expunge_all()


def override_method(handler):
    web.ctx.method = web.input().get("_method", web.ctx.method)
    return handler()


def if_logged_in(func):
    def splitter(*args):
        if session.username:
            return func(*args)
        else:
            web.seeother("/#login")

    return splitter
