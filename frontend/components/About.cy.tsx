import { About } from "./About";

describe("test", () => {
    it("playground", () => {
        cy.mount(<About />);
        cy.contains("About").should("exist");
    });
});
