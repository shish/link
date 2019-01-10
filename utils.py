#!/usr/bin/env python

import web
from sqlalchemy.orm import scoped_session, sessionmaker
from models import engine
import logging


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
        #web.ctx.orm.expunge_all()


def override_method(handler):
    web.ctx.method = web.input().get("_method", web.ctx.method)
    return handler()


def handle_exceptions(handler):
    try:
        return handler()
    except SiteError as e:
        orm = web.ctx.orm
        user = orm.query(User).filter(User.username==session.username).first()
        return render.standard(user, e.title, """
<div id="body" class="container">
    <div class="row">
        <div class="col-md-12">%s</div>
    </div>
</div>""" % e.message)
    except Exception:
        logging.exception("Unhandled exception:")
        #return render.standard("Error", str(e), "", str(e))
        raise


def if_logged_in(func):
    def splitter(*args):
        if session.username:
            return func(*args)
        else:
            web.seeother("/#login")
    return splitter


class render_mako:
    """copied from web.contrib.templates, with t.render_unicode"""
    def __init__(self, *a, **kwargs):
        from mako.lookup import TemplateLookup
        self._lookup = TemplateLookup(*a, **kwargs)

    def __getattr__(self, name):
        # Assuming all templates are html
        path = name + ".html"
        t = self._lookup.get_template(path)
        return t.render_unicode


def setup_sessions(app, initializer):
    import os, urlparse
    db_info = urlparse.urlparse(os.environ['DB_DSN'])
    if db_info.scheme == "sqlite":
        db = web.database(
            dbn=db_info.scheme,
            db=db_info.path.strip("/")
        )
    else:
        db = web.database(
            dbn=db_info.scheme,
            host=db_info.hostname,
            port=db_info.port,
            db=db_info.path.strip("/"),
            user=db_info.username,
            pw=db_info.password
        )
    session_store = web.session.DBStore(db, 'sessions')
    return web.session.Session(app, session_store, initializer=initializer)
