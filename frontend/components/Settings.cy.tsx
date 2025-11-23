import { Settings } from "./Settings";

describe("test", () => {
    it("playground", () => {
        cy.mount(<Settings />);
        cy.contains("Settings").should("exist");
    });
});
