Feature: Filtrado combinado de tareas de empleados
  Como Propietario de Evento, quiero poder aplicar múltiples filtros en la lista de tareas de empleados
  para poder encontrar rápidamente la información que necesito y gestionar eficientemente los procesos.

  Scenario: Filtrar tareas por nombre de evento y estado
    Given un propietario de evento ha iniciado sesión y está en la vista de tareas de empleados con una lista cargada
    When el usuario aplica un filtro por el nombre de evento "Proceso de Onboarding Q1"
    And aplica un filtro adicional por el estado "Pendiente"
    Then la lista de tareas se actualiza mostrando solo las tareas que pertenecen al evento "Proceso de Onboarding Q1" y tienen el estado "Pendiente"