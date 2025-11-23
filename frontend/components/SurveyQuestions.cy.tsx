import { Privacy, SurveyViewFragment } from "../gql/graphql";
import { SurveyQuestions } from "./SurveyQuestions";

describe("test", () => {
    it("playground", () => {
        const s: SurveyViewFragment = {
            id: 1,
            name: "Test Name",
            description: "Test Description",
            longDescription: "Test Long Description",
            owner: { username: "Shish" },
            questions: [
                {
                    id: 1,
                    section: "Sweet",
                    order: 1,
                    text: "Cake Baking",
                    flip: "Cake Eating",
                },
                {
                    id: 2,
                    section: "Sweet",
                    order: 2,
                    text: "Chocolate",
                },
                {
                    id: 3,
                    section: "Savory",
                    order: 1,
                    text: "Pizza Cooking",
                    flip: "Pizza Eating",
                },
                {
                    id: 4,
                    section: "Savory",
                    order: 2,
                    text: "Pasta",
                },
            ],
        };
        const r = {
            id: 1,
            privacy: Privacy.Friends,
            answers: [],
        };
        cy.mount(<SurveyQuestions survey={s} response={r} />);
        cy.contains("Savory").should("exist");
        cy.contains("Page 1/2").should("exist");
    });
});
