import { useMutation, useQuery } from "@apollo/client/react";
import React from "react";
import { graphql } from "../gql";
import { useFragment as fragCast } from "../gql/fragment-masking";
import { UserLoginFragment } from "../gql/graphql";

export const ME_FRAGMENT = graphql(`
    fragment UserLogin on User {
        id
        username
        email
    }
`);

export const GET_ME = graphql(`
    query getMe {
        me: user {
            ...UserLogin
        }
    }
`);

export const CREATE_USER = graphql(`
    mutation createUser(
        $username: String!
        $password1: String!
        $password2: String!
        $email: String!
    ) {
        createUser(
            username: $username
            password1: $password1
            password2: $password2
            email: $email
        ) {
            ...UserLogin
        }
    }
`);

export const LOGIN = graphql(`
    mutation login($username: String!, $password: String!) {
        login(username: $username, password: $password) {
            ...UserLogin
        }
    }
`);
export const LOGOUT = graphql(`
    mutation logout {
        logout
    }
`);

type UserContextType = {
    me: UserLoginFragment | null;
    createUserMutation: any;
    loginMutation: any;
    logoutMutation: any;
};

export const UserContext = React.createContext<UserContextType>({
    me: null,
    createUserMutation: null,
    loginMutation: null,
    logoutMutation: null,
});

export function LoginProvider(props: any) {
    const q = useQuery(GET_ME); //, { pollInterval: 10 * 1000 });
    const [createUserMutation, _createQ] = useMutation(CREATE_USER, {
        update: (cache, { data }) => {
            cache.writeQuery({
                query: GET_ME,
                data: { me: fragCast(ME_FRAGMENT, data?.createUser) },
            });
        },
    });
    const [loginMutation, _loginQ] = useMutation(LOGIN, {
        update: (cache, { data }) => {
            cache.writeQuery({
                query: GET_ME,
                data: { me: fragCast(ME_FRAGMENT, data?.login) },
            });
        },
    });
    const [logoutMutation, _logoutQ] = useMutation(LOGOUT, {
        update: (cache) => {
            cache.writeQuery({
                query: GET_ME,
                data: { me: null },
            });
        },
    });

    if (q.loading) {
        // LoadingPage only works inside a Route
        return <div>Login Loading</div>; // <LoadingPage />;
    }
    if (q.error) {
        // ErrorPage only works inside a Route
        return <div>Login Error</div>; // <ErrorPage error={q.error} />;
    }
    const me = fragCast(ME_FRAGMENT, q.data!.me!);

    return (
        <UserContext.Provider
            value={{ me, createUserMutation, loginMutation, logoutMutation }}
        >
            {props.children}
        </UserContext.Provider>
    );
}
