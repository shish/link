import { useQuery } from "@apollo/client/react";
import { useContext } from "react";
import { Navigate, useParams } from "react-router-dom";
import { CompareIntro } from "../components/CompareIntro";
import { CompareSection } from "../components/CompareSection";
import { ErrorPage } from "../components/ErrorPage";
import { LoadingPage } from "../components/LoadingPage";
import { OtherResponses } from "../components/OtherResponses";
import { Page } from "../components/Page";
import { Section } from "../components/Section";
import { useFragment as fragCast, graphql } from "../gql";
import { Comparison } from "../gql/graphql";
import { UserContext } from "../providers/LoginProvider";
import css from "./ResponseView.module.scss";

export const RESPONSE_WITH_COMPARISON = graphql(`
    fragment ResponseWithComparison on Response {
        id
        owner {
            username
        }
        survey {
            id
            name
            longDescription
        }
        comparison {
            section
            order
            text
            flip
            mine
            theirs
        }
    }
`);

export const GET_RESPONSE = graphql(`
    query getResponse($responseId: Int!) {
        response(responseId: $responseId) {
            ...ResponseWithComparison
        }
    }
`);

export function ResponseView() {
    ///////////////////////////////////////////////////////////////////
    // Hooks
    const { response_id } = useParams();
    const { me } = useContext(UserContext);
    const q = useQuery(GET_RESPONSE, {
        variables: { responseId: parseInt(response_id!, 10) },
    });
    if (!me) {
        return <Navigate to="/" />;
    }

    ///////////////////////////////////////////////////////////////////
    // Hook edge case handling
    if (q.loading) {
        return <LoadingPage />;
    }
    if (q.error) {
        return <ErrorPage error={q.error} />;
    }
    const response = fragCast(RESPONSE_WITH_COMPARISON, q.data?.response);
    if (!response) {
        return (
            <ErrorPage
                error={{ message: `No response with the ID ${response_id}` }}
            />
        );
    }

    ///////////////////////////////////////////////////////////////////
    // Render
    const sections = response.comparison.map((c) => c.section).sort();
    const section_comparisons: Record<string, Array<Comparison>> = {};
    sections.forEach((s) => {
        section_comparisons[s] = response.comparison.filter(
            (c) => c.section === s,
        );
    });

    return (
        <Page
            title={
                "Compare with " +
                (response.owner ? response.owner.username : "anonymous")
            }
            className={css.page}
        >
            <CompareIntro response={response} />

            <Section className={css.answers}>
                {Object.entries(section_comparisons).map(
                    ([section, comparisons]) => (
                        <CompareSection
                            key={section}
                            section={section}
                            comparisons={comparisons}
                        />
                    ),
                )}
            </Section>

            <OtherResponses survey_id={response.survey.id} />
        </Page>
    );
}
