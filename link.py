#!/usr/bin/env python

import logging.handlers
import os
import random
import sys
from time import time

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
            return {
                "user": user,
                "heading": survey.name,
                "survey": survey,
                "response": response,
                "friends": friend_responses,
                "others": other_responses,
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

        entries = list(survey.questions) + list(survey.headings)
        offset = 0
        for n, entry in enumerate(sorted(entries)):
            if entry.entry_type == "heading":
                offset += 10
            entry.order = n + offset

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

        order = time()
        if int(form["heading"]) > 0:
            heading = orm.query(db.Heading).get(form["heading"])
            order = heading.order + (order - int(order))

        if form["heading"] == "-2":
            h = db.Heading()
            h.survey_id = survey.id
            h.order = order
            h.text = form["q1"]
            survey.headings.append(h)

        else:
            q1 = db.Question(form["q1"])
            q1.order = order
            if form.get("q1extra"):
                q1.extra = form.get("q1extra")
            survey.questions.append(q1)
            if form.get("q2"):
                q2 = db.Question(form["q2"])
                q2.order = order + 0.001
                if form.get("q2extra"):
                    q1.extra = form.get("q2extra")
                survey.questions.append(q2)
                q1.flip = q2
                q2.flip = q1

        raise web.HTTPFound("/survey/%d" % survey.id)


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

        question = orm.query(db.Question).get(self.request.match_info["id"])
        action = self.request.match_info["action"]
        if question.survey.user != user:
            raise web.HTTPForbidden()

        if action == "remove":
            orm.delete(question)
        elif action == "up":
            qs = list(question.survey.questions)
            idx = qs.index(question)
            if idx == 1:
                question.order = qs[idx - 1].order - 1
            if idx > 1:
                question.order = (qs[idx - 1].order + qs[idx - 2].order) / 2
        elif action == "down":
            qs = list(question.survey.questions)
            idx = qs.index(question)
            if idx == len(qs) - 1:
                question.order = qs[idx + 1].order + 1
            if idx < len(qs) - 1:
                question.order = (qs[idx + 1].order + qs[idx + 2].order) / 2

        raise web.HTTPFound("/survey/%d" % question.survey.id)


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
        if form.get("public") == "on":
            response.privacy = "public"
        else:
            response.privacy = "private"

        if form.get("privacy"):
            response.privacy = form.get("privacy")

        for q in survey.questions:
            db.Answer(response=response, question=q, value=int(form["q%d" % q.id]))

        if form.get("compare"):
            raise web.HTTPFound("/response/%s" % form.get("compare"))
        else:
            raise web.HTTPFound("/survey/%d" % survey.id)


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
                    "friends": friend_responses,
                    "others": other_responses,
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
            logging.info(
                f"{session['username']}: logged in from {self.request.transport.get_extra_info('peername')[0]}"
            )
            raise web.HTTPFound("/")
        else:
            raise web.HTTPUnauthorized()


@routes.view("/user/logout")
class Logout(web.View):
    async def get(self):
        session = await get_session(self.request)
        if "username" in session:
            logging.info(f"{session['username']}: logged out")
            del session["username"]
        raise web.HTTPFound("/")


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
                raise web.HTTPFound("/")
            else:
                raise SiteError(
                    "Password Error",
                    "The password and confirmation password don't match D:",
                )
        else:
            raise SiteError(
                "Name Taken", "That username has already been taken, sorry D:"
            )


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


def populate_data(session_factory):
    orm = session_factory()

    alice = orm.query(db.User).filter(db.User.username == "Alice").first()
    if not alice:
        alice = db.User("Alice", "alicepass")
        orm.add(alice)

    bob = orm.query(db.User).filter(db.User.username == "Bob").first()
    if not bob:
        bob = db.User("Bob", "bobpass")
        orm.add(bob)

    pets = orm.query(db.Survey).filter(db.Survey.name == "Pets").first()
    if not pets:
        pets = db.Survey(
            name="Pets",
            user=alice,
            description="What type of pet should we get?",
            long_description="",
        )
        orm.add(pets)

        pets.set_questions(
            [
                db.Question("Cats"),
                db.Question("Dogs"),
                db.Question("Rabbits"),
                db.Question("Human (I am the owner)", "Human (I am the pet)"),
                db.Question("Humans", extra="As in children"),
                db.Question("Birds"),
                db.Question("Lizards"),
            ]
        )

        r = db.Response(survey=pets, user=alice)
        for q in pets.questions:
            db.Answer(response=r, question=q, value=random.choice([-2, -1, 0, 1, 2]))
        orm.add(r)

        r = db.Response(survey=pets, user=bob)
        for q in pets.questions:
            db.Answer(response=r, question=q, value=random.choice([-2, -1, 0, 1, 2]))
        orm.add(r)

    orm.commit()


def main(argv):
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s"
    )

    for arg in argv:
        k, _, v = arg.partition("=")
        os.environ[k] = v

    logging.info("App starts...")
    app = web.Application()

    # Database
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
    populate_data(session_factory)

    # Templates
    aiohttp_mako.setup(
        app,
        directories=["./templates/"],
        input_encoding="utf-8",
        output_encoding="utf-8",
        default_filters=["unicode", "h"],
    )

    # Sessions
    import base64
    from cryptography import fernet
    from aiohttp_session import setup
    from aiohttp_session.cookie_storage import EncryptedCookieStorage

    if os.environ.get("SECRET"):
        fernet_key = os.environ["SECRET"].encode()
    else:
        fernet_key = fernet.Fernet.generate_key()
        print("SECRET=" + fernet_key.decode())
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))

    # Reloader
    try:
        import aiohttp_autoreload

        aiohttp_autoreload.start()
    except ImportError:
        pass

    # Setup Routes
    app.add_routes(routes)
    app.router.add_static("/static/", path="./static/", name="static")

    # Go!
    web.run_app(app, port=8000)


if __name__ == "__main__":
    main(sys.argv)
