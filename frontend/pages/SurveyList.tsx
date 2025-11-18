import { useContext } from "react";
import { About } from "../components/About";
import { LogIn } from "../components/Login";
import { Page } from "../components/Page";
import { SurveyItems } from "../components/SurveyItems";
import { UserInfo } from "../components/UserInfo";
import { UserContext } from "../providers/LoginProvider";
import css from "./SurveyList.module.scss";

export function SurveyList() {
    const { me } = useContext(UserContext);

    return (
        <Page className={css.page}>
            {me ? <UserInfo /> : <LogIn />}
            <SurveyItems />
            <About />
        </Page>
    );
}
