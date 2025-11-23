import { Page } from "./Page";

describe("test", () => {
    it("playground", () => {
        cy.mount(
            <Page title="Foo">
                <section>
                    <h3>Bar</h3>
                    <p>hello</p>
                </section>
            </Page>,
        );
        cy.contains("- Foo").should("exist");
    });
});
