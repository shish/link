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
from time import time

urls = (
    '/?', 'surveys',
    '/survey', 'surveys',
    '/survey/(\d+)', 'survey',
    '/question/(\d+)', 'question',
    '/compare/(\d+)/(.*)', 'compare',
    '/user', 'user',
    '/login', 'login',
    '/logout', 'logout',
    '/create', 'create',
    '/(favicon.ico)', 'static',
)
site = "http://link.shishnet.org"


def log_info(text):
    if session.username:
        logging.info("%s: %s" % (session.username, text))
    else:
        logging.info("<anon>: %s" % text)


class LinkError(Exception):
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


def if_logged_in(func):
    def splitter(*args):
        if session.username:
            return func(*args)
        else:
            web.seeother("/")
    return splitter


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

render = render_mako(
    directories=["./templates/"],
    input_encoding='utf-8',
    output_encoding='utf-8',
    default_filters=['unicode', 'h'],
)
app = web.application(urls, globals())
app.add_processor(load_sqla)
app.add_processor(override_method)

import rediswebpy
session = web.session.Session(
    app, rediswebpy.RedisStore(),  # prefix='session:quotes:'),
    initializer={'username': None})


class surveys:
    @handle_exceptions
    def GET(self):
    	orm = web.ctx.orm
        user = orm.query(User).filter(User.username==session.username).first()
        responses = orm.query(Response).filter(Response.user==user).all()
        surveys = orm.query(Survey)

        if user:
            nav = render.control(user)
        else:
            nav = render.login()
        return render.standard("Interest Link", "List of Lists", nav, render.surveys(surveys, responses))


class survey:
    @handle_exceptions
    @if_logged_in
    def GET(self, id):
    	orm = web.ctx.orm
        data = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        nav = render.control(user)

        survey = orm.query(Survey).get(id)
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()
        compare = data.get("compareto")
        if response:
            others = orm.query(Response).filter(Response.survey==survey, Response.user!=user, Response.privacy=="public").all()
            users = []
            for other in others:
                users.append(other.user)
            nav = nav + render.others(survey, users)

            if compare:
                them = orm.query(User).filter(User.username==compare).one()
                theirs = orm.query(Response).filter(Response.survey==survey, Response.user==them).first()
                return render.standard("Survey", survey.name, nav, render.compare(survey, response, theirs))
            else:
                return render.standard("Survey", survey.name, nav, render.survey(survey, response))
        else:
            return render.standard("Survey", survey.name, nav, render.survey(survey, None, compareto=compare))

    @handle_exceptions
    @if_logged_in
    def POST(self, id):
    	orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()

        survey = orm.query(Survey).get(id)
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()
        if response:
            for answer in response.answers:
                orm.delete(answer)
	else:
            response = Response(survey=survey, user=user)
        if post.get("public") == "on":
            response.privacy = "public"
        else:
            response.privacy = "private"

        if post.get("privacy"):
            response.privacy = post.get("privacy")

        for q in survey.questions:
            Answer(response=response, question=q, value=post["q%d" % q.id])

        if post.get("compareto"):
            web.seeother("/compare/%d/%s" % (survey.id, post.get("compareto")))
        else:
            web.seeother("/survey/%d" % survey.id)

    @handle_exceptions
    @if_logged_in
    def DELETE(self, id):
    	orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()

        survey = orm.query(Survey).get(id)
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()
        if response:
            orm.delete(response)
        web.seeother("/survey/%d" % survey.id)


class question:
    @handle_exceptions
    @if_logged_in
    def POST(self, id):
    	orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()

        survey = orm.query(Survey).get(id)
        q1 = Question(post["q1"])
        q1.order = time()
        survey.questions.append(q1)
        if post.get("q2"):
            q2 = Question(post["q2"])
            q2.order = time()
            survey.questions.append(q2)
            q1.flip = q2
            q2.flip = q1
        web.seeother("/survey/%d" % survey.id)


class compare:
    @handle_exceptions
    @if_logged_in
    def GET(self, id, compare):
    	orm = web.ctx.orm
        data = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        nav = render.control(user)

        survey = orm.query(Survey).get(id)
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()
        if response:
            others = orm.query(Response).filter(Response.survey==survey, Response.user!=user, Response.privacy=="public").all()
            users = []
            for other in others:
                users.append(other.user)
            nav = nav + render.others(survey, users)

            if compare.isnumeric():
                theirs = orm.query(Response).get(compare)
            else:
                them = orm.query(User).filter(User.username==compare).one()
                theirs = orm.query(Response).filter(Response.survey==survey, Response.user==them).one()
                if theirs.privacy != "public":
                    theirs = None
            return render.standard("Survey", survey.name, nav, render.compare(survey, response, theirs))
        else:
            web.seeother("/survey/%d?compareto=%s" % (survey.id, compare))


class login:
    @handle_exceptions
    def POST(self):
        form = web.input()
        username = str(form.username)
        password = str(form.password)

        user = web.ctx.orm.query(User).filter(User.username==username).first()
        if user and user.check_password(password):
            session.username = username
            web.setcookie("username", username)
            log_info("logged in from %s" % (web.ctx.ip))
            web.seeother("/")
        else:
            raise LinkError("Error", "User not found")


class logout:
    @handle_exceptions
    def GET(self):
        log_info("logged out")
        session.kill()
        web.seeother("/")


class create:
    @handle_exceptions
    def POST(self):
        form = web.input()
        username = form.username
        password1 = form.password1
        password2 = form.password2
        if len(form.email) > 0:
            email = form.email
        else:
            email = None

        user = web.ctx.orm.query(User).filter(User.username==username).first()
        if user == None:
            if password1 == password2:
                user = User(username, password1, email)
                web.ctx.orm.add(user)
                web.ctx.orm.commit()

                session.username = username
                log_info("User created")
                web.seeother("/")
            else:
                raise LinkError("Password Error", "The password and confirmation password don't match D:")
        else:
            raise LinkError("Name Taken", "That username has already been taken, sorry D:")


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
