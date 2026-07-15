# App QA - Generador de Plan de Pruebas con IA

Este proyecto implementa una aplicación web con Streamlit que utiliza Gemini para transformar Historias de Usuario en un plan de pruebas automatizado y, posteriormente, generar flujos E2E en Gherkin y Cypress.

## Estructura actual del proyecto

La aplicación ha evolucionado de un único script a una arquitectura modular compuesta por estos archivos principales:

```text
Solucion/
├── app.py                  # Aplicación principal en Streamlit
├── ai_client.py            # Cliente para interactuar con Gemini
├── schemas.py              # Modelos Pydantic para validar respuestas de la IA
├── export_utils.py         # Funciones de exportación a CSV y ZIP
├── cypress/                # Proyecto de automatización generado o compatible con Cypress
├── package.json            # Dependencias de Node/Cypress
├── *.csv                   # Ejemplos de entradas y resultados de prueba
└── README.md               # Documentación del proyecto
```

## Qué hace

La aplicación permite:

- Cargar un archivo CSV con Historias de Usuario.
- Enviar cada historia a un modelo de IA para generar casos de prueba estructurados.
- Clasificar los casos por categoría: funcional, accesibilidad, rendimiento y seguridad.
- Mostrar los resultados en tablas y permitir descargarlos en formato CSV.
- Identificar flujos E2E críticos y generar automatización en Gherkin y Cypress.
- Exportar los artefactos generados en archivos ZIP listos para su uso.

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
- Exporta todo en un archivo ZIP listo para usar en un proyecto de automatización.

## Requisitos

Instala las dependencias necesarias con:

```bash
pip install streamlit pandas python-dotenv google-genai pydantic
```

Si vas a trabajar con la parte de automatización Cypress, también puedes instalar las dependencias de Node desde la carpeta correspondiente:

```bash
cd cypress
npm install
```

## Configuración

Crea un archivo .env en la raíz del proyecto con tu clave de API de Google:

```env
GOOGLE_API_KEY=tu_clave_aqui
```

## Ejecución

Ejecuta la aplicación principal con:

```bash
streamlit run app.py
```

## Notas importantes

- El archivo CSV debe estar en formato adecuado para leer columnas como ID, Historia de usuario y Criterios de aceptación.
- La IA necesita una conexión válida a Google Gemini para generar los resultados.
- El flujo de automatización E2E requiere haber generado previamente la Fase 1.
- La lógica de negocio y los modelos de respuesta están separados en los módulos de la arquitectura actual para facilitar mantenimiento y escalabilidad.
