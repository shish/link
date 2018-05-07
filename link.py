#!/usr/bin/env python

import web
web.config.debug = False

import logging.handlers

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import func, or_, not_, and_
from models import Friendship, User, Survey, Question, Heading, Response, Answer, engine
from time import time

urls = (
    '/?', 'surveys',

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
    '/static/(script.js|style.css)', 'static',
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


def handle_exceptions(handler):
    try:
        return handler()
    except LinkError as e:
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

render = render_mako(
    directories=["./templates/"],
    input_encoding='utf-8',
    output_encoding='utf-8',
    default_filters=['unicode', 'h'],
)
app = web.application(urls, globals())
app.add_processor(load_sqla)
app.add_processor(override_method)
app.add_processor(handle_exceptions)


import os, urlparse
db_info = urlparse.urlparse(os.environ['DB_DSN'])
session = web.session.Session(
    app,
    web.session.DBStore(
        web.database(
            dbn=db_info.scheme,
            host=db_info.hostname,
            port=db_info.port,
            db=db_info.path.strip("/"),
            user=db_info.username,
            pw=db_info.password),
        'sessions'
    ),
    initializer={'username': None}
)


def _get_user(username):
    u = web.ctx.orm.query(User).filter(func.lower(User.username)==func.lower(username)).first()
    if not u:
        raise LinkError("404", "User '%s' not found" % username)
    return u


class surveys:
    def GET(self):
        """
        Display a list of all surveys
        """
        orm = web.ctx.orm
        user = orm.query(User).filter(User.username==session.username).first()
        responses = orm.query(Response).filter(Response.user==user).all()
        surveys = orm.query(Survey)

        return render.standard(user, "List of Lists", render.surveys(user, surveys, responses))


class survey:
    @if_logged_in
    def GET(self, id):
        """
        Display a single survey
        """
        orm = web.ctx.orm
        data = web.input()
        user = _get_user(session.username)

        survey = orm.query(Survey).get(id)
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()
        if response:

            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(Response).filter(Response.survey==survey, Response.user_id.in_(friend_ids), or_(Response.privacy=="public", Response.privacy=="friends"))
            other_responses = orm.query(Response).filter(Response.survey==survey, Response.user!=user, not_(Response.user_id.in_(friend_ids)), Response.privacy=="public")
            nav = render.others(survey, friend_responses, other_responses)

            return render.standard(user, survey.name, render.survey(user, survey, response, nav=nav))
        else:
            return render.standard(user, survey.name, render.survey(user, survey, None, compare=data.get("compare")))

    @if_logged_in
    def POST(self, id):
        """
        Re-distribute sorting IDs for entries in a survey
        """
        orm = web.ctx.orm
        data = web.input()
        user = _get_user(session.username)
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
    @if_logged_in
    def POST(self):
        """
        Add a new question (assigned to a survey)
        """
        orm = web.ctx.orm
        post = web.input()
        user = _get_user(session.username)
        survey = orm.query(Survey).get(post["survey"])

        order = time()
        if int(post["heading"]) > 0:
            heading = orm.query(Heading).get(post["heading"])
            order = heading.order + (order - int(order))

        if post["heading"] == "-2":
            h = Heading()
            h.survey_id = survey.id
            h.order = order
            h.text = post["q1"]
            survey.headings.append(h)

        else:
            q1 = Question(post["q1"])
            q1.order = order
            if post.get("q1extra"):
                q1.extra = post.get("q1extra")
            survey.questions.append(q1)
            if post.get("q2"):
                q2 = Question(post["q2"])
                q2.order = order + 0.001
                if post.get("q2extra"):
                    q1.extra = post.get("q2extra")
                survey.questions.append(q2)
                q1.flip = q2
                q2.flip = q1

        web.seeother("/survey/%d" % survey.id)


class question:
    @if_logged_in
    def GET(self, id, action):
        orm = web.ctx.orm
        user = _get_user(session.username)

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
    @if_logged_in
    def POST(self):
        orm = web.ctx.orm
        post = web.input()
        user = _get_user(session.username)
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
    @if_logged_in
    def GET(self, id):
        orm = web.ctx.orm
        data = web.input()
        user = _get_user(session.username)

        theirs = orm.query(Response).get(id)
        if not theirs:
            raise LinkError("Not Found", "No response~")
        them = theirs.user
        survey = theirs.survey
        response = orm.query(Response).filter(Response.survey==survey, Response.user==user).first()

        if response:
            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(Response).filter(Response.survey==survey, Response.user_id.in_(friend_ids), or_(Response.privacy=="public", Response.privacy=="friends"))
            other_responses = orm.query(Response).filter(Response.survey==survey, Response.user!=user, not_(Response.user_id.in_(friend_ids)), Response.privacy=="public")
            nav = render.others(survey, friend_responses, other_responses)

            if (
                (theirs.privacy == "public") or
                (theirs.privacy == "hidden") or
                (theirs.privacy == "friends" and user in them.all_friends)
            ):
                return render.standard(user, survey.name, render.response(survey, response, theirs, nav))
            else:
                raise LinkError("Not Found", "No response~")
        else:
            web.seeother("/survey/%d?compare=%s" % (survey.id, theirs.id))

    @if_logged_in
    def DELETE(self, id):
        orm = web.ctx.orm
        post = web.input()
        user = _get_user(session.username)

        response = orm.query(Response).get(id)
        if response and response.user == user:
            orm.delete(response)
        web.seeother("/survey/%d" % response.survey.id)


class user:
    @if_logged_in
    def GET(self):
        orm = web.ctx.orm
        user = _get_user(session.username)
        return render.standard(user, "User Settings", render.user(user))

    @if_logged_in
    def POST(self):
        orm = web.ctx.orm
        form = web.input()
        old_password = str(form.old_password)
        new_username = str(form.new_username)
        new_password_1 = str(form.new_password_1)
        new_password_2 = str(form.new_password_2)
        new_email = str(form.new_email)

        user = _get_user(session.username)
        if user.token != str(form.csrf_token):
            raise LinkError("Error", "Token error")

        if not user.check_password(old_password):
            raise LinkError("Error", "Current password incorrect")

        if new_username and new_username != user.username:
            check_user = web.ctx.orm.query(User).filter(User.username.ilike(new_username)).first()
            if check_user:
                raise LinkError("Error", "That username is already taken")
            else:
                user.username = new_username
                session.username = new_username
                web.setcookie("username", new_username)

        if new_password_1 or new_password_2:
            if new_password_1 == new_password_2:
                user.set_password(new_password_1)
            else:
                raise LinkError("Error", "New passwords don't match")

        if new_email:
            user.email = new_email
        else:
            user.email = None

        web.seeother("/user")


class login:
    def POST(self):
        form = web.input()
        username = str(form.username)
        password = str(form.password)

        user = _get_user(username)
        if user and user.check_password(password):
            session.username = username
            web.setcookie("username", username)
            log_info("logged in from %s" % (web.ctx.ip))
            web.seeother("/")
        else:
            raise LinkError("Error", "User not found")


class logout:
    def GET(self):
        log_info("logged out")
        session.kill()
        web.seeother("/")


class create:
    def POST(self):
        form = web.input()
        username = form.username
        password1 = form.password1
        password2 = form.password2
        if len(form.email) > 0:
            email = form.email
        else:
            email = None

        user = web.ctx.orm.query(User).filter(User.username.ilike(username)).first()
        if user is None:
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
    def GET(self):
        orm = web.ctx.orm
        data = web.input()
        user = _get_user(session.username)

        return render.standard(user, "Friends", render.friends(user))

    def POST(self):
        orm = web.ctx.orm
        data = web.input()
        their_name = data["their_name"]
        user = _get_user(session.username)
        try:
            them = _get_user(their_name)
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

    def DELETE(self):
        orm = web.ctx.orm
        data = web.input()
        their_name = data["their_name"]
        user = _get_user(session.username)
        try:
            them = _get_user(their_name)
        except Exception:
            raise LinkError("Not found", "User %s not found" % their_name)

        orm.query(Friendship).filter(or_(
            and_(Friendship.friend_a==user, Friendship.friend_b==them),
            and_(Friendship.friend_a==them, Friendship.friend_b==user),
        )).delete()

        web.seeother("/friends")


class static:
    def GET(self, filename):
        try:
            return file("static/"+filename).read()
        except:
            return "not found"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename="../logs/app.log"
    )
    #smtp = logging.handlers.SMTPHandler(
    #    "localhost", "noreply@shishnet.org",
    #    ["shish+link@shishnet.org", ], "link error report"
    #)
    #smtp.setLevel(logging.WARNING)
    #logging.getLogger('').addHandler(smtp)

    logging.info("App starts...")
    app.run()
