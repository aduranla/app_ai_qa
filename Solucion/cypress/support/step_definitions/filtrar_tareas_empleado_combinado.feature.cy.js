import { Given, When, Then } from '@badeball/cypress-cucumber-preprocessor';

// Prerrequisito: Se asume que existe un usuario 'propietario de evento'
// y que los datos de prueba (eventos, empleados, tareas) han sido creados mediante fixtures o API calls.

Given('un propietario de evento ha iniciado sesión y está en la vista de tareas de empleados con una lista cargada', () => {
  cy.login('propietario_evento', 'password'); // Comando personalizado para el login
  cy.visit('/events/employee-tasks');
  cy.get('[data-cy="task-list-container"]').should('be.visible');
  cy.get('[data-cy="task-row"]').should('have.length.greaterThan', 0);
});

When('el usuario aplica un filtro por el nombre de evento {string}', (eventName) => {
  cy.get('[data-cy="advanced-filter-button"]').click();
  cy.get('[data-cy="filter-event-name-input"]').type(eventName);
  // Se asume que el filtro se aplica al escribir o al presionar un botón
  cy.get('[data-cy="apply-filters-button"]').click();
  cy.wait(500); // Espera explícita corta para la actualización de la UI, idealmente reemplazar con espera de XHR
});

When('aplica un filtro adicional por el estado {string}', (status) => {
  // El filtro avanzado ya debería estar abierto
  cy.get('[data-cy="filter-status-select"]').select(status);
  cy.get('[data-cy="apply-filters-button"]').click();
  cy.wait(500); // Espera para la actualización
});

Then('la lista de tareas se actualiza mostrando solo las tareas que pertenecen al evento {string} y tienen el estado {string}', (eventName, status) => {
  cy.get('[data-cy="task-row"]').should('be.visible'); // Asegurarse que hay resultados

  cy.get('[data-cy="task-row"]').each(($row) => {
    cy.wrap($row).find('[data-cy="task-event-name-cell"]').should('contain.text', eventName);
    cy.wrap($row).find('[data-cy="task-status-cell"]').should('contain.text', status);
  });
});