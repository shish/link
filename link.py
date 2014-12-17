#!/usr/bin/env python

import web
web.config.debug = False

import cgi
import logging
import logging.handlers
import hashlib

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import func, or_, not_, and_
from models import *
from time import time

urls = (
    '/?', 'surveys',
    #'/r/(\d+)', 'response',

    '/survey', 'surveys',
    '/survey/(\d+)', 'survey',

    '/response', 'responses',
    '/response/(\d+)', 'response',

    '/question', 'questions',
    '/question/(\d+)/(up|down|remove)', 'question',

    '/user', 'user',
    '/user/login', 'login',
    '/user/logout', 'logout',
    '/user/create', 'create',

    '/friends', 'friends',

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
        if response:

            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(Response).filter(Response.survey==survey, Response.user_id.in_(friend_ids), or_(Response.privacy=="public", Response.privacy=="friends"))
            other_responses = orm.query(Response).filter(Response.survey==survey, Response.user!=user, not_(Response.user_id.in_(friend_ids)), Response.privacy=="public")
            nav = nav + render.others(survey, friend_responses, other_responses)

            return render.standard("Interest Link", survey.name, nav, render.survey(user, survey, response))
        else:
            return render.standard("Interest Link", survey.name, nav, render.survey(user, survey, None, compare=data.get("compare")))

    @handle_exceptions
    @if_logged_in
    def POST(self, id):
        orm = web.ctx.orm
        data = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        survey = orm.query(Survey).get(id)

        if survey.user != user:
            raise LinkError("Permission denied", "That is not your survey")

        entries = list(survey.questions) + list(survey.headings)
        offset = 0
        for n, entry in enumerate(sorted(entries)):
            if entry.entry_type == "heading":
                offset += 10
            entry.order = n + offset

        web.seeother("/survey/%d" % survey.id)


class questions:
    @handle_exceptions
    @if_logged_in
    def POST(self):
        orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()

        survey = orm.query(Survey).get(post["survey"])
        q1 = Question(post["q1"])
        q1.order = time()
        if post.get("q1extra"):
            q1.extra = post.get("q1extra")
        survey.questions.append(q1)
        if post.get("q2"):
            q2 = Question(post["q2"])
            q2.order = time()
            if post.get("q2extra"):
                q1.extra = post.get("q2extra")
            survey.questions.append(q2)
            q1.flip = q2
            q2.flip = q1
        web.seeother("/survey/%d" % survey.id)


class question:
    @handle_exceptions
    @if_logged_in
    def GET(self, id, action):
        orm = web.ctx.orm
        user = orm.query(User).filter(User.username==session.username).one()

        question = orm.query(Question).get(id)
        if question.survey.user != user:
            raise LinkError("Can't modify questions of other people's surveys")

        if action == "remove":
            orm.delete(question)
        elif action == "up":
            qs = list(question.survey.questions)
            idx = qs.index(question)
            if idx == 1:
                question.order = qs[idx-1].order - 1
            if idx > 1:
                question.order = (qs[idx-1].order + qs[idx-2].order) / 2
        elif action == "down":
            qs = list(question.survey.questions)
            idx = qs.index(question)
            if idx == len(qs) - 1:
                question.order = qs[idx+1].order + 1
            if idx < len(qs) - 1:
                question.order = (qs[idx+1].order + qs[idx+2].order) / 2

        web.seeother("/survey/%d" % question.survey.id)


class responses:
    @handle_exceptions
    @if_logged_in
    def POST(self):
        orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        id = post["survey"]

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

        if post.get("compare"):
            web.seeother("/response/%s" % post.get("compare"))
        else:
            web.seeother("/survey/%d" % survey.id)


class response:
    @handle_exceptions
    @if_logged_in
    def GET(self, id):
        orm = web.ctx.orm
        data = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        nav = render.control(user)

        theirs = orm.query(Response).get(id)
        them = theirs.user
        survey = theirs.survey
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()

        if response:

            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(Response).filter(Response.survey==survey, Response.user_id.in_(friend_ids), or_(Response.privacy=="public", Response.privacy=="friends"))
            other_responses = orm.query(Response).filter(Response.survey==survey, Response.user!=user, not_(Response.user_id.in_(friend_ids)), Response.privacy=="public")
            nav = nav + render.others(survey, friend_responses, other_responses)

            if (
                (theirs.privacy == "public") or
                (theirs.privacy == "friends" and user in them.all_friends)
            ):
                return render.standard("Interest Link", survey.name, nav, render.response(survey, response, theirs))
            else:
                raise LinkError("Permission denied", "This response is either friends-only or passworded")
        else:
            web.seeother("/survey/%d?compare=%s" % (survey.id, theirs.id))

    @handle_exceptions
    @if_logged_in
    def DELETE(self, id):
        orm = web.ctx.orm
        post = web.input()
        user = orm.query(User).filter(User.username==session.username).one()

        response = orm.query(Response).get(id)
        if response and response.user == user:
            orm.delete(response)
        web.seeother("/survey/%d" % response.survey.id)


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


class friends:
    @handle_exceptions
    def GET(self):
        orm = web.ctx.orm
        data = web.input()
        user = orm.query(User).filter(User.username==session.username).one()
        nav = render.control(user)

        return render.standard("Interest Link", "Friends", nav, render.friends(user))

    @handle_exceptions
    def POST(self):
        orm = web.ctx.orm
        data = web.input()
        their_name = data["their_name"]
        user = orm.query(User).filter(User.username==session.username).one()
        try:
            them = orm.query(User).filter(User.username.ilike(their_name)).one()
        except Exception:
            raise LinkError("Not found", "User %s not found" % their_name)

        incoming = orm.query(Friendship).filter(Friendship.friend_b==user, Friendship.confirmed==False).all()
        for req in incoming:
            if req.friend_a == them:
                req.confirmed = True
                break
        else:
            orm.add(Friendship(friend_a=user, friend_b=them))

        web.seeother("/friends")

    @handle_exceptions
    def DELETE(self):
        orm = web.ctx.orm
        data = web.input()
        their_name = data["their_name"]
        user = orm.query(User).filter(User.username==session.username).one()
        try:
            them = orm.query(User).filter(User.username==their_name).one()
        except Exception:
            raise LinkError("Not found", "User %s not found (note that names are case-sensitive at the moment)" % their_name)

        orm.query(Friendship).filter(or_(
            and_(Friendship.friend_a==user, Friendship.friend_b==them),
            and_(Friendship.friend_a==them, Friendship.friend_b==user),
        )).delete()

        web.seeother("/friends")



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
