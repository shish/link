from link import setup_db, setup_templates, setup_routes, setup_sessions
import os
import pytest
from aiohttp import web, ClientSession
import re
import models

models.security = False


@pytest.fixture
def cli(loop, aiohttp_client):
    # temporary in-memory DB
    os.environ["DB_DSN"] = "sqlite://"
    os.environ["SECRET"] = "Tdv6rISUff4OwkXJKLJ1ZU_8epuSvRrhvy0-DlOYgh8="
    app = web.Application()
    setup_db(app)
    setup_templates(app)
    setup_sessions(app)
    setup_routes(app)
    return loop.run_until_complete(aiohttp_client(app))


async def login(cli: ClientSession, name="alice"):
    resp = await cli.post(
        "/user/login",
        data={"username": name, "password": f"{name}pass"},
        allow_redirects=False,
    )
    assert resp.status == 302


async def test_get_login_fail(cli: ClientSession):
    resp = await cli.post(
        "/user/login",
        data={"username": "asdfasdfa", "password": "asdfasd"},
        allow_redirects=False,
    )
    assert resp.status == 404


async def test_get_logout(cli: ClientSession):
    await login(cli)
    resp = await cli.get("/user/logout", allow_redirects=False)
    assert resp.status == 302


async def test_redirect_to_login(cli: ClientSession):
    resp = await cli.post("/survey/1", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers['Location'] == "/#login"


async def test_create_dupe_username(cli: ClientSession):
    resp = await cli.post(
        "/user/create",
        data={"username": "alice", "password1": "davidpass", "password2": "davidpass"},
        allow_redirects=False,
    )
    assert resp.status == 500


async def test_create_bad_password(cli: ClientSession):
    resp = await cli.post(
        "/user/create",
        data={"username": "David", "password1": "dffgsd", "password2": "davidpass"},
        allow_redirects=False,
    )
    assert resp.status == 500

async def test_list_surveys(cli: ClientSession):
    resp = await cli.get("/", allow_redirects=False)
    assert resp.status == 200
    assert "List of Lists" in await resp.text()


async def test_get_survey_exists(cli: ClientSession):
    await login(cli)
    resp = await cli.get("/survey/1", allow_redirects=False)
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_reorder_survey(cli: ClientSession):
    await login(cli)
    resp = await cli.post("/survey/1", allow_redirects=False)
    assert resp.status == 302
    # TODO: test that survey was reordered

    await login(cli, "bob")
    resp = await cli.post("/survey/1", allow_redirects=False)
    assert resp.status == 500


async def test_post_question(cli: ClientSession):
    await login(cli)
    resp = await cli.post(
        "/question",
        data={
            "survey": 1,
            "section": "Test",
            "q1": "Do you like eating pie?",
            "q1extra": "Pie is covered on 5 sides",
            "q2": "Do you like baking pie?",
            "q2extra": "For other people",
        },
        allow_redirects=False,
    )
    assert resp.status == 302


async def test_move_question(cli: ClientSession):
    await login(cli)

    resp = await cli.get("/question/2/up", allow_redirects=False)
    assert resp.status == 302

    resp = await cli.get("/question/2/down", allow_redirects=False)
    assert resp.status == 302

    resp = await cli.get("/question/2/remove", allow_redirects=False)
    assert resp.status == 302

    await login(cli, "bob")
    resp = await cli.get("/question/2/remove", allow_redirects=False)
    assert resp.status == 500


async def test_get_response(cli: ClientSession):
    await login(cli)
    resp = await cli.get("/response/2", allow_redirects=False)
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_delete_response(cli: ClientSession):
    await login(cli)
    resp = await cli.post("/response/2", data={"_method": "DELETE"}, allow_redirects=False)
    assert resp.status == 302


async def test_get_user(cli: ClientSession):
    await login(cli)
    resp = await cli.get("/user", allow_redirects=False)
    assert resp.status == 200
    assert "User Settings" in await resp.text()


async def test_post_user(cli: ClientSession):
    import hashlib
    await login(cli)
    resp = await cli.post("/user", data={
        "old_password": "alicepass",
        "new_username": "AliceNew",
        "new_password_1": "apass2",
        "new_password_2": "apass2",
        "new_email": "alice@example.com",
        "csrf_token": hashlib.md5("alicepass".encode()).hexdigest(),
    }, allow_redirects=False)
    assert resp.status == 302


async def test_get_friends(cli: ClientSession):
    await login(cli)
    resp = await cli.get("/friends", allow_redirects=False)
    assert resp.status == 200
    assert "Friends" in await resp.text()


async def test_post_delete_friends(cli: ClientSession):
    await login(cli)
    resp = await cli.post(
        "/friends", data={"their_name": "alice"}, allow_redirects=False
    )
    assert resp.status == 302
    resp = await cli.post(
        "/friends",
        data={"_method": "DELETE", "their_name": "alice"},
        allow_redirects=False,
    )
    assert resp.status == 302


async def test_e2e_deletion_cascade(cli: ClientSession):
    # create user
    resp = await cli.post(
        "/user/create",
        data={"username": "David", "password1": "davidpass", "password2": "davidpass"},
        allow_redirects=False,
    )
    assert resp.status == 302

    # TODO: create friendships

    # check empty response
    resp = await cli.get(f"/survey/1", allow_redirects=False)
    assert resp.status == 200

    # respond to survey
    resp = await cli.post(
        "/response",
        data={"survey": 1, "privacy": "public", "q1": 1, "q2": 0, "q3": -1},
        allow_redirects=False,
    )
    assert resp.status == 302

    # look at our response
    resp = await cli.get(f"/survey/1", allow_redirects=False)
    assert resp.status == 200

    # find our response ID
    matches = re.search(r"/response/(\d)", await resp.text()).groups()
    resp_id = matches[0]

    # check response exists
    resp = await cli.get(f"/response/{resp_id}", allow_redirects=False)
    assert resp.status == 200

    # delete user
    resp = await cli.delete("/user/delete", allow_redirects=False)
    assert resp.status == 302

    # check that response is gone
    await login(cli)
    resp = await cli.get(f"/response/{resp_id}", allow_redirects=False)
    assert resp.status == 404

    # TODO: make sure nothing else got deleted by accident


# TODO: more tests
# - privacy settings
# - friendships
