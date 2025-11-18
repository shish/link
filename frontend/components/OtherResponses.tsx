import { useQuery } from "@apollo/client/react";
import { useContext } from "react";
import { Link } from "react-router-dom";
import { graphql } from "../gql";
import { UserContext } from "../providers/LoginProvider";
import css from "./OtherResponses.module.scss";
import { sectionMaker } from "./Section";

export const OTHER_RESPONSES = graphql(`
    query getOtherResponses($surveyId: Int!) {
        survey(surveyId: $surveyId) {
            id
            responses {
                id
                owner {
                    username
                    isFriend
                }
            }
        }
    }
`);

export const OtherResponses = sectionMaker(function ({
    survey_id,
}: {
    survey_id: number;
}): React.ReactElement {
    const { me } = useContext(UserContext);
    const q = useQuery(OTHER_RESPONSES, {
        variables: { surveyId: survey_id },
    });

    if (q.loading) {
        return <h3>Loading...</h3>;
    }
    if (q.error) {
        return <h3>Error: {q.error.message}</h3>;
    }
    const responses =
        q.data?.survey?.responses?.filter(
            (r) => r.owner?.username !== me?.username,
        ) || [];
    const friend_responses = responses.filter((r) => r.owner?.isFriend);
    const other_responses = responses.filter((r) => !r.owner?.isFriend);

    return (
        <>
            <h3>Friends</h3>
            <ul>
                {friend_responses.length === 0 && (
                    <li>No friends responded!</li>
                )}
                {friend_responses.map((r) => (
                    <li key={r.id}>
                        <Link to={"/response/" + r.id}>
                            {r.owner?.username}
                        </Link>
                    </li>
                ))}
            </ul>
            <h3>Others</h3>
            <ul>
                {other_responses.length === 0 && <li>No others responded!</li>}
                {other_responses.map((r) => (
                    <li key={r.id}>
                        <Link to={"/response/" + r.id}>
                            {r.owner?.username}
                        </Link>
                    </li>
                ))}
            </ul>
        </>
    );
}, css.others);
