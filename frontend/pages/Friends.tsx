import { useMutation, useQuery } from "@apollo/client/react";
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { ErrorPage } from "../components/ErrorPage";
import { LoadingPage } from "../components/LoadingPage";
import { Page } from "../components/Page";
import { graphql } from "../gql";
import { useFragment as fragCast } from "../gql/fragment-masking";
import css from "./Friends.module.scss";

export const FRIENDS_FRAGMENT = graphql(`
    fragment FriendsFragment on User {
        id
        friends {
            username
        }
        friendsOutgoing {
            username
        }
        friendsIncoming {
            username
        }
    }
`);

export const GET_FRIENDS = graphql(`
    query getFriends {
        me: user {
            id
            ...FriendsFragment
        }
    }
`);

export const ADD_FRIEND = graphql(`
    mutation addFriend($username: String!) {
        addFriend(username: $username) {
            ...FriendsFragment
        }
    }
`);

export const REMOVE_FRIEND = graphql(`
    mutation removeFriend($username: String!) {
        removeFriend(username: $username) {
            ...FriendsFragment
        }
    }
`);

function ConfirmedFriends({ friends }: { friends: { username: string }[] }) {
    const [removeFriendMutation, removeFriendQ] = useMutation(REMOVE_FRIEND);

    return (
        <section className={css.confirmed}>
            <h3>Confirmed</h3>
            {friends.length == 0 ? (
                <p>No friends yet.</p>
            ) : (
                <table className="zebra">
                    <tbody>
                        {friends.map((friend) => (
                            <tr key={friend.username}>
                                <td>{friend.username}</td>
                                <td>
                                    <input
                                        type="button"
                                        value="Remove"
                                        onClick={() => {
                                            removeFriendMutation({
                                                variables: {
                                                    username: friend.username,
                                                },
                                            }).catch((e) => {
                                                alert(e);
                                            });
                                        }}
                                        disabled={removeFriendQ.loading}
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </section>
    );
}

function IncomingFriends({ friends }: { friends: { username: string }[] }) {
    const [addFriendMutation, addFriendQ] = useMutation(ADD_FRIEND);

    return (
        <section className={css.incoming}>
            <h3>Incoming Requests</h3>
            {friends.length == 0 ? (
                <p>No pending invites.</p>
            ) : (
                <table className="zebra">
                    <tbody>
                        {friends.map((friend) => (
                            <tr key={friend.username}>
                                <td>{friend.username}</td>
                                <td>
                                    <input
                                        type="button"
                                        value="Accept"
                                        onClick={() => {
                                            addFriendMutation({
                                                variables: {
                                                    username: friend.username,
                                                },
                                            }).catch((e) => {
                                                alert(e);
                                            });
                                        }}
                                        disabled={addFriendQ.loading}
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </section>
    );
}

function OutgoingFriends({ friends }: { friends: { username: string }[] }) {
    const [friendToAdd, setFriendToAdd] = useState("");
    const [addFriendMutation, addFriendQ] = useMutation(ADD_FRIEND);
    const [removeFriendMutation, removeFriendQ] = useMutation(REMOVE_FRIEND);

    return (
        <section className={css.outgoing}>
            <h3>Outgoing Requests</h3>
            <table className="zebra">
                <tbody>
                    <tr>
                        <td>
                            <input
                                type="text"
                                placeholder="Username"
                                value={friendToAdd}
                                onChange={(e) => setFriendToAdd(e.target.value)}
                                disabled={addFriendQ.loading}
                            />
                        </td>
                        <td>
                            <input
                                type="button"
                                value="Send"
                                onClick={() => {
                                    addFriendMutation({
                                        variables: { username: friendToAdd },
                                    })
                                        .then(() => {
                                            setFriendToAdd("");
                                        })
                                        .catch((e) => {
                                            alert(e);
                                        });
                                }}
                                disabled={addFriendQ.loading}
                            />
                        </td>
                    </tr>
                    {friends.map((friend) => (
                        <tr key={friend.username}>
                            <td>{friend.username}</td>
                            <td>
                                <input
                                    type="button"
                                    value="Cancel"
                                    onClick={() => {
                                        removeFriendMutation({
                                            variables: {
                                                username: friend.username,
                                            },
                                        }).catch((e) => {
                                            alert(e);
                                        });
                                    }}
                                    disabled={removeFriendQ.loading}
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </section>
    );
}

export function Friends() {
    ///////////////////////////////////////////////////////////////////
    // Hooks
    const q = useQuery(GET_FRIENDS);

    ///////////////////////////////////////////////////////////////////
    // Hook edge case handling
    if (q.loading) {
        return <LoadingPage />;
    }
    if (q.error) {
        return <ErrorPage error={q.error} />;
    }
    const me = q.data?.me;
    if (!me) {
        return <Navigate to="/" />;
    }

    ///////////////////////////////////////////////////////////////////
    // Render

    const ff = fragCast(FRIENDS_FRAGMENT, me);
    return (
        <Page title={"Friends"} className={css.page}>
            <IncomingFriends friends={ff.friendsIncoming} />
            <ConfirmedFriends friends={ff.friends} />
            <OutgoingFriends friends={ff.friendsOutgoing} />
        </Page>
    );
}
