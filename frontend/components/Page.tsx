import {
    faGears,
    faRightToBracket as faLogin,
    faRightFromBracket as faLogout,
    faUserFriends,
} from "@fortawesome/free-solid-svg-icons";
import { FAIcon } from "@shish2k/react-faicon";
import { useContext } from "react";
import { Link, ScrollRestoration } from "react-router-dom";

import { UserContext } from "../providers/LoginProvider";
import css from "./Page.module.scss";
import "./style.scss";

function Header({ title }: { title?: string }) {
    const { me, logoutMutation } = useContext(UserContext);

    function logoutHandler(e: React.MouseEvent<HTMLAnchorElement, MouseEvent>) {
        e.preventDefault();
        logoutMutation().catch((e: Error) => {
            alert(e);
        });
    }

    return (
        <header className={css.header}>
            <h1>
                <Link to="/">
                    <span className="large_only">Link</span>
                </Link>
                {title ? " - " + title : ""}
            </h1>
            <div className={css.fill}>&nbsp;</div>
            {me ? (
                <>
                    <h1>
                        <Link to="/friends">
                            <FAIcon icon={faUserFriends} data-cy="friends" />
                        </Link>
                    </h1>
                    <h1>
                        <Link to="/user">
                            <FAIcon icon={faGears} data-cy="settings" />
                        </Link>
                    </h1>
                    <h1>
                        <Link to="/" onClick={logoutHandler}>
                            <FAIcon icon={faLogout} data-cy="logout" />
                        </Link>
                    </h1>
                </>
            ) : (
                <h1>
                    <Link to="/">
                        <FAIcon icon={faLogin} data-cy="login" />
                    </Link>
                </h1>
            )}
        </header>
    );
}

export function Page({
    title,
    children,
    className,
}: {
    title?: string;
    children: React.ReactNode;
    className?: string;
}) {
    return (
        <div className={css.page + (className ? " " + className : "")}>
            <ScrollRestoration />
            <Header title={title} />
            <article>{children}</article>
            <footer className={css.footer}>
                <a href="https://github.com/shish/link2">Link software</a>
                {" by "}
                <a href="https://shish.io/">Shish</a>
            </footer>
        </div>
    );
}
