import { SurveyViewFragment } from "../gql/graphql";
import { SurveyDescription } from "./SurveyDescription";

describe("test", () => {
    it("playground", () => {
        const s: SurveyViewFragment = {
            id: 1,
            name: "Test Name",
            description: "Test Description",
            longDescription: "Test Long Description",
            owner: { username: "Shish" },
            questions: [],
            myResponse: {},
        };
        cy.mount(<SurveyDescription survey={s} />);
        cy.contains("Created by Shish").should("exist");
    });
});
