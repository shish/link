# mypy: disable-error-code="index"

import pytest

from .conftest import Login, Query


@pytest.mark.asyncio
async def test_addFriend_anon(query: Query):
    # anon can't add a friend
    result = await query(
        'mutation m { addFriend(username: "Frank") { id } }',
        error="Anonymous users can't add friends",
    )
    assert result.data is None


@pytest.mark.asyncio
async def test_addFriend_self(query: Query, login: Login):
    # log in as alice and add herself as a friend
    await login("Alice")
    result = await query(
        'mutation m { addFriend(username: "Alice") { id } }',
        error="You can't add yourself",
    )
    assert result.data is None


@pytest.mark.asyncio
async def test_addFriend_dupe(query: Query, login: Login):
    # log in as alice and add frank as a friend
    await login("Alice")
    result = await query('mutation m { addFriend(username: "Frank") { id } }')

    # try to add frank again
    result = await query(
        'mutation m { addFriend(username: "Frank") { id } }',
        error="Friend request already sent",
    )
    assert result.data is None


@pytest.mark.asyncio
async def test_addFriend_notfound(query: Query, login: Login):
    # log in as alice and add a non-existent user
    await login("Alice")
    result = await query(
        'mutation m { addFriend(username: "NotAUser") { id } }',
        error="User not found",
    )
    assert result.data is None


@pytest.mark.asyncio
async def test_removeFriend_notfound(query: Query, login: Login):
    # log in as alice and remove a non-existent user
    await login("Alice")
    result = await query(
        'mutation m { removeFriend(username: "NotAUser") { id } }',
        error="User not found",
    )
    assert result.data is None


@pytest.mark.asyncio
async def test_addFriend_e2e(query: Query, login: Login):
    # log in as alice and add frank as a friend, check outgoing request
    await login("Alice")
    result = await query(
        """
        mutation m {
            addFriend(username: "Frank") {
                id
                friendsOutgoing { username }
            }
        }
    """
    )
    assert "Frank" in [
        user["username"] for user in result.data["addFriend"]["friendsOutgoing"]
    ]

    # log in as frank and check from his end
    await login("Frank")
    result = await query("query q { user { friendsIncoming { username } } }")
    assert "Alice" in [
        user["username"] for user in result.data["user"]["friendsIncoming"]
    ]

    # accept the request, check that alice is now a friend
    result = await query(
        """
        mutation m {
            addFriend(username: "Alice") {
                id
                friends { username }
            }
        }
    """
    )
    assert "Alice" in [user["username"] for user in result.data["addFriend"]["friends"]]

    # check alice's friends list
    await login("Alice")
    result = await query("query q { user { friends { username } } }")
    assert "Frank" in [user["username"] for user in result.data["user"]["friends"]]

    # remove the friend, check result
    result = await query(
        """
        mutation m {
            removeFriend(username: "Frank") {
                id
                friends { username }
            }
        }
    """
    )
    assert "Frank" not in [
        user["username"] for user in result.data["removeFriend"]["friends"]
    ]

    # check frank's friends list
    await login("Frank")
    result = await query("query q { user { friends { username } } }")
    assert "Alice" not in [user["username"] for user in result.data["user"]["friends"]]
