from link import setup_db, setup_templates, setup_routes
import os
import pytest
from aiohttp import ClientSession
from aiohttp import web

from aiohttp_session import AbstractStorage, Session


class FakeStorage(AbstractStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}

    async def load_session(self, request):
        return Session(None, data=self.data, new=False, max_age=600)

    async def save_session(self, request, response, session):
        self.data = self._get_session_data(session)


@pytest.fixture
def cli(loop, aiohttp_client):
    # temporary in-memory DB
    os.environ['DB_DSN'] = 'sqlite://'
    os.environ['SECRET'] = 'Tdv6rISUff4OwkXJKLJ1ZU_8epuSvRrhvy0-DlOYgh8='
    app = web.Application()
    setup_db(app)
    setup_templates(app)
    from aiohttp_session import setup
    setup(app, FakeStorage())
    setup_routes(app)
    return loop.run_until_complete(aiohttp_client(app))


async def login(cli: ClientSession):
    resp = await cli.post('/user/login', data={"username": 'alice', "password": 'alicepass'}, allow_redirects=False)
    assert resp.status == 302


async def test_get_surveys(cli: ClientSession):
    resp = await cli.get('/')
    assert resp.status == 200
    assert "List of Lists" in await resp.text()


async def test_get_survey(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/survey/1')
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_post_survey(cli: ClientSession):
    await login(cli)
    resp = await cli.post('/survey/1')
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_post_question(cli: ClientSession):
    await login(cli)
    resp = await cli.post('/question', data={
        "survey": 1,
        "section": "Test",
        "q1": "Do you like eating pie?",
        "q1extra": "Pie is covered on 5 sides",
        "q2": "Do you like baking pie?",
        "q2extra": "For other people",
    })
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_get_question(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/question/1/up')
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_get_response(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/response/2')
    assert resp.status == 200
    assert "Pets" in await resp.text()


async def test_get_user(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/user', allow_redirects=False)
    assert resp.status == 200
    assert "User Settings" in await resp.text()


async def test_get_friends(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/friends')
    assert resp.status == 200
    assert "Friends" in await resp.text()


async def test_get_logout(cli: ClientSession):
    await login(cli)
    resp = await cli.get('/user/logout', allow_redirects=False)
    assert resp.status == 302
