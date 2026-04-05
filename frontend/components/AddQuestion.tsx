import { useMutation } from "@apollo/client/react";
import { useState } from "react";
import { graphql } from "../gql";
import type { SurveyViewFragment } from "../gql/graphql";
import { GET_SURVEY } from "../pages/SurveyView";

const ADD_QUESTION = graphql(`
    mutation addQuestion($surveyId: Int!, $question: QuestionInput!) {
        addQuestion(surveyId: $surveyId, question: $question) {
            section
            text
            flip
        }
    }
`);

//export const AddQuestion = sectionMaker(function({ survey_id }: { survey_id: number; }) {
export const AddQuestion = ({ survey }: { survey: SurveyViewFragment }) => {
    const sections = Array.from(
        new Set(survey.questions.map((q) => q.section)),
    ).sort();
    const [section, setSection] = useState(sections[0]);
    const [addQuestionMutation, addQuestionQ] = useMutation(ADD_QUESTION, {
        refetchQueries: [GET_SURVEY],
    });

    return (
        <section style={{ gridArea: "addq" }}>
            <h3>Add Question</h3>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    const form = e.currentTarget;
                    const section = form.section.value;
                    const text = form.text.value;
                    const flip = form.flip.value;
                    addQuestionMutation({
                        variables: {
                            surveyId: survey.id,
                            question: { section, text, flip },
                        },
                    })
                        .then(() => {
                            form.text.value = "";
                            form.flip.value = "";
                        })
                        .catch((err) => {
                            console.error(err);
                        });
                }}
            >
                <label>
                    Section:
                    {sections.includes(section) ? (
                        <select
                            name="section"
                            onChange={(e) => setSection(e.target.value)}
                            value={section}
                            disabled={addQuestionQ.loading}
                        >
                            {sections.map((s) => (
                                <option key={s} value={s}>
                                    {s || "Unsorted"}
                                </option>
                            ))}
                            <option key={-1} value={""}>
                                {"Create New Section"}
                            </option>
                        </select>
                    ) : (
                        <input
                            type="text"
                            name="section"
                            onChange={(e) => setSection(e.target.value)}
                            required={true}
                            disabled={addQuestionQ.loading}
                        />
                    )}
                </label>
                <label>
                    Question:
                    <input
                        type="text"
                        name="text"
                        required={true}
                        disabled={addQuestionQ.loading}
                    />
                </label>
                <label>
                    Opposite pair (optional):
                    <input
                        type="text"
                        name="flip"
                        disabled={addQuestionQ.loading}
                    />
                </label>
                <button type="submit" disabled={addQuestionQ.loading}>
                    Add Question
                </button>
            </form>
        </section>
    );
}; //, css.intro);
