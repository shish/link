import { UserInfo } from "./UserInfo";

describe("test", () => {
    it("playground", () => {
        cy.mount(<UserInfo />);
        cy.contains("Mochael").should("exist");
    });
});
