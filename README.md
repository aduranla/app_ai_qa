# Agente QA con Gemini

Este proyecto implementa un agente de calidad (QA) automatizado que utiliza la API de Google Gemini para generar planes de pruebas basados en historias de usuario.

## Descripción

El agente lee un archivo CSV que contiene historias de usuario con sus criterios de aceptación, y utiliza el modelo de lenguaje Gemini para generar un plan de pruebas completo y estructurado. El plan incluye casos de prueba funcionales, de accesibilidad y de rendimiento, cubriendo escenarios positivos ("Happy Path") y negativos.

## Requisitos

- Python 3.8+
- Clave de API de Google Gemini (configurada como variable de entorno `GOOGLE_API_KEY`)
- Bibliotecas: `pydantic`, `google-genai`

## Instalación

1. Instala las dependencias:
   ```bash
   pip install pydantic google-genai
   ```

2. Configura la variable de entorno:
   ```bash
   set GOOGLE_API_KEY=AIzaSyChrcCrBtonN5OlbV4EJt4mE6BkClNPyDI
   ```

## Uso

1. Prepara un archivo CSV de entrada con las historias de usuario. El formato esperado es:
   - `ID`: Identificador de la historia de usuario
   - `Historia de usuario`: Descripción de la HU
   - `Criterios de aceptación`: Criterios para aceptar la HU

2. Ejecuta el script:
   ```bash
   python agente_qa.py
   ```

3. El script generará un archivo `Plan_de_Pruebas_Generado.csv` con el plan de pruebas.

## Estructura del Plan de Pruebas

Cada caso de prueba incluye:
- **ID Test**: Identificador único
- **Título**: Título descriptivo
- **Descripción**: Detalles del caso
- **Resultado Esperado**: Lo que se espera obtener
- **Precondiciones**: Condiciones previas
- **HUs afectadas**: Historias de usuario relacionadas
- **Categoría**: Funcional, Accesibilidad, Rendimiento
- **Tipo de Flujo**: Happy Path, Negativo

## Funcionalidades

- **Lectura de CSV**: Procesa historias de usuario desde un archivo CSV.
- **Generación con IA**: Utiliza Gemini para crear planes de pruebas exhaustivos.
- **Exportación estructurada**: Guarda los resultados en formato CSV compatible con herramientas de gestión de pruebas.

## Notas

- Asegúrate de que el archivo de entrada esté en el mismo directorio que el script o ajusta la ruta en el código.
- La temperatura del modelo está configurada en 0.2 para obtener resultados deterministas y profesionales.

## Licencia

[Especifica la licencia si aplica]