import { useContext } from "react";
import { Link } from "react-router-dom";
import { UserContext } from "../providers/LoginProvider";
import { sectionMaker } from "./Section";

export const UserInfo = sectionMaker(function () {
    const { me, logoutMutation } = useContext(UserContext);

    function logoutHandler(e: React.MouseEvent<HTMLAnchorElement, MouseEvent>) {
        e.preventDefault();
        logoutMutation().catch((e: Error) => {
            alert(e);
        });
    }

    return (
        <>
            <h3>Logged in as {me?.username}</h3>
            <ul>
                <li>
                    <Link to="/friends">Friends</Link>
                </li>
                <li>
                    <Link to="/user">Settings</Link>
                </li>
                <li>
                    <Link to="/" onClick={logoutHandler}>
                        Log Out
                    </Link>
                </li>
            </ul>
        </>
    );
});
