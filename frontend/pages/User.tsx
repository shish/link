import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { Page } from "../components/Page";
import { Settings } from "../components/Settings";
import { UserContext } from "../providers/LoginProvider";
import css from "./User.module.scss";

export function User() {
    const { me } = useContext(UserContext);
    if (!me) {
        return <Navigate to="/" />;
    }

    return (
        <Page title={"Settings"} className={css.page}>
            <Settings />
        </Page>
    );
}
