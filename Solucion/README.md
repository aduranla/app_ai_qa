# App QA - Generador de Plan de Pruebas con IA

Este proyecto implementa una aplicación web con Streamlit que utiliza Gemini para transformar Historias de Usuario en un plan de pruebas automatizado.

## Qué hace

El script app_qa.py permite:

- Cargar un archivo CSV con Historias de Usuario.
- Enviar cada historia a un modelo de IA para generar casos de prueba estructurados.
- Clasificar los casos por categoría: funcional, accesibilidad, rendimiento y seguridad.
- Mostrar los resultados en tablas y permitir descargarlos en formato CSV.
- Generar flujos E2E y producir archivos de automatización en Gherkin y Cypress.

## Funcionalidades principales

### Fase 1: Plan de Pruebas
- Recibe un CSV con columnas como:
  - ID
  - Historia de usuario
  - Criterios de aceptación
- Genera casos de prueba con campos como:
  - ID de prueba
  - Título
  - Descripción
  - Resultado esperado
  - Precondiciones
  - HUs afectadas
  - Categoría
  - Tipo de flujo
- Permite descargar los resultados por categoría.

### Fase 2: BDD y Cypress (E2E)
- Identifica flujos críticos a partir de los casos funcionales.
- Permite revisar y editar los flujos propuestos manualmente.
- Genera código en formato:
  - Gherkin (.feature)
  - Cypress (.cy.js)
- Descarga todo en un archivo ZIP listo para usar en un proyecto de automatización.

## Requisitos

Instala las dependencias necesarias:

```bash
pip install streamlit pandas python-dotenv google-genai pydantic
```

## Configuración

Crea un archivo .env en la misma carpeta del proyecto con tu clave de API de Google:

```env
GOOGLE_API_KEY=tu_clave_aqui
```

## Ejecución

Ejecuta la aplicación con:

```bash
streamlit run app_qa.py
```

## Notas importantes

- El archivo CSV debe estar en formato separado por punto y coma (;).
- La IA necesita una conexión válida a Google Gemini para generar los resultados.
- El flujo de automatización E2E requiere haber generado previamente la Fase 1.
