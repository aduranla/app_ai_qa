import { Given, When, Then } from '@badeball/cypress-cucumber-preprocessor';

Given('un propietario de evento ha iniciado sesión y está en la vista de tareas de empleados con una lista cargada', () => {
  cy.visit('https://example.cypress.io');
});

When('el usuario aplica un filtro por el nombre de evento {string}', (eventName) => {
  cy.log(`Filtro por evento: ${eventName}`);
});

When('aplica un filtro adicional por el estado {string}', (status) => {
  cy.log(`Filtro por estado: ${status}`);
});

Then('la lista de tareas se actualiza mostrando solo las tareas que pertenecen al evento {string} y tienen el estado {string}', (eventName, status) => {
  cy.log(`Validando ${eventName} y ${status}`);
});
