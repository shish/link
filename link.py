#!/usr/bin/env python

import logging.handlers
import os
import sys
from time import time
import json

import aiohttp_mako
from aiohttp import web
from aiohttp_session import get_session
from sqlalchemy import and_, func, not_, or_

import models as db

routes = web.RouteTableDef()


def if_logged_in(func):
    async def splitter(self, *args):
        session = await get_session(self.request)
        if "username" in session:
            return await func(self, *args)
        else:
            raise web.HTTPFound("/#login")

    return splitter


class SiteError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = message


def _get_user(orm, username):
    u = (
        orm.query(db.User)
        .filter(func.lower(db.User.username) == func.lower(username))
        .first()
    )
    if not u:
        raise web.HTTPNotFound()
    return u


@routes.view("/")
@routes.view("/survey")
@aiohttp_mako.template("surveys.mako")
class Surveys(web.View):
    async def get(self):
        """
        Display a list of all surveys
        """
        session = await get_session(self.request)
        orm = self.request["orm"]
        user = (
            orm.query(db.User)
            .filter(db.User.username == session.get("username"))
            .first()
        )
        responses = orm.query(db.Response).filter(db.Response.user == user).all()
        surveys = orm.query(db.Survey)

        return {
            "user": user,
            "heading": "List of Lists",
            "surveys": surveys,
            "responses": responses,
        }


@routes.view(r"/survey/{survey_id:\d+}")
@aiohttp_mako.template("survey.mako")
class Survey(web.View):
    @if_logged_in
    async def get(self):
        """
        Display a single survey
        """
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        survey = orm.query(db.Survey).get(self.request.match_info["survey_id"])
        response = (
            orm.query(db.Response)
            .filter(db.Response.survey == survey, db.Response.user == user)
            .first()
        )
        if response:
            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(db.Response).filter(
                db.Response.survey == survey,
                db.Response.user_id.in_(friend_ids),
                or_(db.Response.privacy == "public", db.Response.privacy == "friends"),
            )
            other_responses = orm.query(db.Response).filter(
                db.Response.survey == survey,
                db.Response.user != user,
                not_(db.Response.user_id.in_(friend_ids)),
                db.Response.privacy == "public",
            )
            link = f"https://{self.request.host}/response/{response.id}"
            return {
                "user": user,
                "heading": survey.name,
                "survey": survey,
                "response": response,
                "friends": list(friend_responses),
                "others": list(other_responses),
                "link": link,
            }
        else:
            return {
                "user": user,
                "heading": survey.name,
                "survey": survey,
                "response": None,
                "friends": None,
                "others": None,
                "compare": form.get("compare"),
            }

    @if_logged_in
    async def post(self):
        """
        Re-distribute sorting IDs for entries in a survey
        """
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        survey = orm.query(db.Survey).get(self.request.match_info["survey_id"])

        if survey.user != user:
            raise SiteError("Permission denied", "That is not your survey")

        entries = list(survey.questions)
        for n, entry in enumerate(sorted(entries)):
            entry.order = n

        raise web.HTTPFound("/survey/%d" % survey.id)


@routes.view("/question")
class Questions(web.View):
    @if_logged_in
    async def post(self):
        """
        Add a new question (assigned to a survey)
        """
        orm = self.request["orm"]
        form = await self.request.post()

        survey = orm.query(db.Survey).get(form["survey"])

        section = form["section"]
        order = time()

        q1 = db.Question(section, form["q1"])
        q1.order = order
        if form.get("q1extra"):
            q1.extra = form.get("q1extra")
        survey.questions.append(q1)
        if form.get("q2"):
            q2 = db.Question(section, form["q2"])
            q2.order = order + 0.001
            if form.get("q2extra"):
                q1.extra = form.get("q2extra")
            survey.questions.append(q2)
            q1.flip = q2
            q2.flip = q1

        return web.HTTPFound("/survey/%d" % survey.id)


@routes.view(r"/question/{question_id:\d+}/{action:(remove|up|down)}")
class Question(web.View):
    @if_logged_in
    async def get(self):
        """
        Update a question's location, or remove it
        """
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        question = orm.query(db.Question).get(self.request.match_info["question_id"])
        action = self.request.match_info["action"]
        if question.survey.user != user:
            raise web.HTTPForbidden()

        if action == "remove":
            orm.delete(question)
        elif action == "up" or action == "down":
            # Swap the sort-order IDs of two things
            qs = list(question.survey.contents)
            idx = qs.index(question)
            if action == "up":
                # swap the selected thing, and the thing above it
                oth = idx - 1
                # if the thing above us is our pair, go two above
                if qs[idx].is_second_of_pair:
                    oth = idx - 2
            else:
                # swap the selected thing, and the thing below it
                oth = idx + 1
                # if the thing below us is our pair, go two below
                if qs[idx].is_first_of_pair:
                    oth = idx + 2

            # make sure "the other thing" exists
            if 0 <= oth < len(qs):
                # if either of the selected things are part of a pair, make
                # sure we are operating on the main entry, not the sub-entry
                q1 = qs[idx].flip if qs[idx].is_second_of_pair else qs[idx]
                q2 = qs[oth].flip if qs[oth].is_second_of_pair else qs[oth]
                q1.order, q2.order = q2.order, q1.order

        return web.HTTPFound("/survey/%d" % question.survey.id)


@routes.view("/response")
class Responses(web.View):
    @if_logged_in
    async def post(self):
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        id = form["survey"]

        survey = orm.query(db.Survey).get(id)
        response = (
            orm.query(db.Response)
            .filter(db.Response.survey == survey, db.Response.user == user)
            .first()
        )
        if response:
            for answer in response.answers:
                orm.delete(answer)
        else:
            response = db.Response(survey=survey, user=user)

        response.privacy = form.get("privacy", "private")

        for q in survey.questions:
            qn = "q%d" % q.id
            if qn in form:
                db.Answer(response=response, question=q, value=int(form[qn]))

        if form.get("compare"):
            return web.HTTPFound("/response/%s" % form.get("compare"))
        else:
            return web.HTTPFound("/survey/%d" % survey.id)


@routes.view(r"/response/{response_id:\d+}")
@aiohttp_mako.template("response.mako")
class Response(web.View):
    @if_logged_in
    async def get(self):
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        theirs = orm.query(db.Response).get(self.request.match_info["response_id"])
        if not theirs:
            raise web.HTTPNotFound()
        them = theirs.user
        survey = theirs.survey
        response = (
            orm.query(db.Response)
            .filter(db.Response.survey == survey, db.Response.user == user)
            .first()
        )

        if response:
            friend_ids = [friend.id for friend in user.all_friends]
            friend_responses = orm.query(db.Response).filter(
                db.Response.survey == survey,
                db.Response.user_id.in_(friend_ids),
                or_(db.Response.privacy == "public", db.Response.privacy == "friends"),
            )
            other_responses = orm.query(db.Response).filter(
                db.Response.survey == survey,
                db.Response.user != user,
                not_(db.Response.user_id.in_(friend_ids)),
                db.Response.privacy == "public",
            )

            if (
                (theirs.privacy == "public")
                or (theirs.privacy == "hidden")
                or (theirs.privacy == "friends" and user in them.all_friends)
            ):
                return {
                    "user": user,
                    "heading": survey.name,
                    "survey": survey,
                    "response": response,
                    "theirs": theirs,
                    "friends": list(friend_responses),
                    "others": list(other_responses),
                }
            else:
                raise web.HTTPNotFound()
        else:
            raise web.HTTPFound("/survey/%d?compare=%s" % (survey.id, theirs.id))

    async def post(self):
        form = await self.request.post()
        if form.get("_method") == "DELETE":
            return await self.delete()

    @if_logged_in
    async def delete(self):
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        response = orm.query(db.Response).get(self.request.match_info["response_id"])
        if response and response.user == user:
            orm.delete(response)
        raise web.HTTPFound("/survey/%d" % response.survey.id)


@routes.view("/user")
@aiohttp_mako.template("user.mako")
class User(web.View):
    @if_logged_in
    async def get(self):
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        return {"user": user, "heading": "User Settings"}

    @if_logged_in
    async def post(self):
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)

        old_password = str(form["old_password"])
        new_username = str(form["new_username"])
        new_password_1 = str(form["new_password_1"])
        new_password_2 = str(form["new_password_2"])
        new_email = str(form["new_email"])

        user = _get_user(orm, session["username"])
        if user.token != str(form["csrf_token"]):
            raise SiteError("Error", "Token error")

        if not user.check_password(old_password):
            raise SiteError("Error", "Current password incorrect")

        if new_username and new_username != user.username:
            check_user = (
                orm.query(db.User).filter(db.User.username.ilike(new_username)).first()
            )
            if check_user:
                raise SiteError("Error", "That username is already taken")
            else:
                user.username = new_username
                session.username = new_username
                # FIXME: web.setcookie("username", new_username)

        if new_password_1 or new_password_2:
            if new_password_1 == new_password_2:
                user.set_password(new_password_1)
            else:
                raise SiteError("Error", "New passwords don't match")

        if new_email:
            user.email = new_email
        else:
            user.email = None

        raise web.HTTPFound("/user")


@routes.view("/user/login")
class Login(web.View):
    async def post(self):
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)

        username = str(form["username"])
        password = str(form["password"])

        user = _get_user(orm, username)
        if user and user.check_password(password):
            session["username"] = user.username
            # FIXME: web.setcookie("username", username)
            addr = self.request.transport.get_extra_info("peername")[0]
            logging.info(f"{session['username']}: logged in from {addr}")
            return web.HTTPFound("/")
        else:
            raise web.HTTPUnauthorized()


@routes.view("/user/logout")
class Logout(web.View):
    async def get(self):
        session = await get_session(self.request)
        if "username" in session:
            logging.info(f"{session['username']}: logged out")
            del session["username"]
        return web.HTTPFound("/")


@routes.view("/user/create")
class Create(web.View):
    async def post(self):
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)

        username = form["username"]
        password1 = form["password1"]
        password2 = form["password2"]
        email = form.get("email") or None  # cast empty string to None

        user = orm.query(db.User).filter(db.User.username.ilike(username)).first()
        if user is None:
            if password1 == password2:
                user = db.User(username, password1, email)
                orm.add(user)

                session["username"] = username
                logging.info(f"{session['username']}: User created")
                return web.HTTPFound("/")
            else:
                raise SiteError(
                    "Password Error",
                    "The password and confirmation password don't match D:",
                )
        else:
            raise SiteError(
                "Name Taken", "That username has already been taken, sorry D:"
            )


@routes.view("/user/delete")
class Delete(web.View):
    @if_logged_in
    async def delete(self):
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])
        # cascade rules for many-many are complicated, deleting
        # by hand for now...
        orm.query(db.Friendship).filter(
            or_(db.Friendship.friend_a == user, db.Friendship.friend_b == user)
        ).delete()
        orm.delete(user)
        logging.info(f"{session['username']}: deleted")
        del session["username"]
        return web.HTTPFound("/")


@routes.view("/friends")
@aiohttp_mako.template("friends.mako")
class Friends(web.View):
    async def get(self):
        orm = self.request["orm"]
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        return {"user": user, "heading": "Friends"}

    async def post(self):
        form = await self.request.post()
        if form.get("_method") == "DELETE":
            return await self.delete()

        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        their_name = form["their_name"]
        try:
            them = _get_user(orm, their_name)
        except Exception:
            raise web.HTTPNotFound()

        incoming = (
            orm.query(db.Friendship)
            .filter(db.Friendship.friend_b == user, db.Friendship.confirmed == False)
            .all()
        )
        for req in incoming:
            if req.friend_a == them:
                req.confirmed = True
                break
        else:
            orm.add(db.Friendship(friend_a=user, friend_b=them))

        raise web.HTTPFound("/friends")

    async def delete(self):
        orm = self.request["orm"]
        form = await self.request.post()
        session = await get_session(self.request)
        user = _get_user(orm, session["username"])

        their_name = form["their_name"]
        try:
            them = _get_user(orm, their_name)
        except Exception:
            raise web.HTTPNotFound()

        orm.query(db.Friendship).filter(
            or_(
                and_(db.Friendship.friend_a == user, db.Friendship.friend_b == them),
                and_(db.Friendship.friend_a == them, db.Friendship.friend_b == user),
            )
        ).delete()

        raise web.HTTPFound("/friends")


@routes.view("/stats")
class Stats(web.View):
    async def get(self):
        addr = self.request.transport.get_extra_info("peername")[0]
        if addr != "127.0.0.1":  # pragma: nocover
            raise web.HTTPForbidden()
        orm = self.request["orm"]
        return web.Response(
            body=json.dumps(
                {
                    "friendships": orm.query(db.Friendship).count(),
                    "users": orm.query(db.User).count(),
                    "surveys": orm.query(db.Survey).count(),
                    "questions": orm.query(db.Question).count(),
                    "responses": orm.query(db.Response).count(),
                    "answers": orm.query(db.Answer).count(),
                }
            )
        )


def setup_db(app: web.Application):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(os.environ["DB_DSN"], echo=False)
    db.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    @web.middleware
    async def add_db(request, handler):
        request["orm"] = session_factory()
        try:
            resp = await handler(request)
        finally:
            request["orm"].commit()
            request["orm"].close()
        return resp

    app.middlewares.append(add_db)
    db.populate_example_data(session_factory)


def setup_templates(app: web.Application):
    aiohttp_mako.setup(
        app,
        directories=["./templates/"],
        input_encoding="utf-8",
        output_encoding="utf-8",
        default_filters=["unicode", "h"],
    )


def setup_sessions(app: web.Application):
    import base64
    from cryptography import fernet
    from aiohttp_session import setup
    from aiohttp_session.cookie_storage import EncryptedCookieStorage

    if os.environ.get("SECRET"):
        fernet_key = os.environ["SECRET"].encode()
    else:  # pragma: nocover
        fernet_key = fernet.Fernet.generate_key()
        print("SECRET=" + fernet_key.decode())
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))


def setup_debug(app: web.Application):  # pragma: nocover
    # Reloader
    try:
        import aiohttp_autoreload

        aiohttp_autoreload.start()
    except ImportError:
        pass


def setup_routes(app: web.Application):
    app.add_routes(routes)
    app.router.add_static("/static/", path="./static/", name="static")


def main(argv):  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s"
    )

    for arg in argv:
        k, _, v = arg.partition("=")
        os.environ[k] = v

    logging.info("App starts...")
    app = web.Application()

    setup_db(app)
    setup_templates(app)
    setup_sessions(app)
    setup_debug(app)
    setup_routes(app)

    web.run_app(app, port=8000)


if __name__ == "__main__":  # pragma: nocover
    main(sys.argv)
