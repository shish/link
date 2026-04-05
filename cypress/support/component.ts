// ***********************************************************
// This example support/component.ts is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import "./commands";

// Alternatively you can use CommonJS syntax:
// require('./commands')

import { type MountOptions, type MountReturn, mount } from "cypress/react";
import React from "react";
import { DevApp } from "../../frontend/App";
import { GET_ME } from "../../frontend/providers/LoginProvider";

// Augment the Cypress namespace to include type definitions for
// your custom command.
// Alternatively, can be defined in cypress/support/component.d.ts
// with a <reference path="./component" /> at the top of your spec.
declare global {
    namespace Cypress {
        interface Chainable<Subject> {
            mount(
                component: React.ReactNode,
                options?: MountOptions & { mocks?: any[] },
            ): Cypress.Chainable<MountReturn>;
        }
    }
}

//Cypress.Commands.add('mount', mount)
Cypress.Commands.add("mount", (component, options: any = {}) => {
    const mocks = options.mocks ?? [];
    // DevApp includes LoginProvider which does this
    mocks.unshift({
        request: {
            query: GET_ME,
            variables: {},
        },
        result: {
            data: {
                me: {
                    __typename: "User",
                    username: "Mochael",
                    email: "mock@example.com",
                },
            },
        },
    });
    const provider = React.createElement(DevApp, { component, mocks });
    return mount(provider, options);
});
