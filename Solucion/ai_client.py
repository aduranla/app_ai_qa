import os
import time
from google import genai
from google.genai import types
from schemas import PlanPruebas, ListaCasosE2E, CodigoAutomatizacion

class QA_AI_Client:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-pro'

    def generar_plan_pruebas_por_hu(self, historia_texto, max_intentos=3):
        prompt = f"""
        Eres un Analista de Pruebas (QA) Senior experto.
        A continuación, te proporciono una Historia de Usuario con sus Criterios de Aceptación.
        
        Tu tarea es diseñar un Plan de Pruebas completo y exhaustivo basándote en esta historia y donde NINGÚN criterio de aceptación quede sin validar. Analiza la Historia de Usuario y desglosa sus 'Criterios de Aceptación'.
        Debes incluir:
        1. Pruebas Funcionales.
        2. Pruebas de Accesibilidad.
        3. Pruebas de Rendimiento.
        4. Pruebas de Seguridad (si aplican).
        
        Asegúrate de cubrir escenarios ideales ("Happy Path") y escenarios de error o extremos ("Negativo").
        
        HISTORIA DE USUARIO A ANALIZAR:
        {historia_texto}
        """
        
        # Gestión robusta de errores y reintentos (Exponential Backoff)
        for intento in range(max_intentos):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PlanPruebas,
                        temperature=0.2,
                    ),
                )
                return response.parsed
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    time.sleep(2 ** intento) # Espera 1s, luego 2s, luego 4s...
                    continue
                elif intento == max_intentos - 1:
                    raise Exception(f"Fallo definitivo de API tras {max_intentos} intentos: {str(e)}")
                else:
                    time.sleep(1)

    def identificar_flujos_e2e(self, casos_texto, max_intentos=3):
        prompt_e2e = f"""
        Eres un QA Automation Lead. Revisa esta lista de casos funcionales:
        {casos_texto}
        
        Selecciona ÚNICAMENTE los casos que representen un flujo "End-to-End" crítico para el negocio.
        Combina pasos si es necesario para crear un flujo completo de usuario.
        """
        # Implementación de reintentos exponenciales
        for intento in range(max_intentos):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt_e2e,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ListaCasosE2E,
                        temperature=0.2,
                    ),
                )
                return response.parsed
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    time.sleep(2 ** intento) # Espera 1s, luego 2s, luego 4s...
                    continue
                elif intento == max_intentos - 1:
                    raise Exception(f"Fallo definitivo de API al identificar E2E tras {max_intentos} intentos: {str(e)}")
                else:
                    time.sleep(1)

    def generar_codigo_automatizacion(self, flujos_aprobados_texto, max_intentos=3):
        prompt_codigo = f"""
        Eres un SDET experto en Cypress. Basado en los siguientes flujos E2E validados:
        {flujos_aprobados_texto}
        
        Por CADA UNO de los flujos de la tabla, debes generar de forma independiente:
        1. Un 'nombre_archivo' corto en formato snake_case.
        2. El código Gherkin (.feature).
        3. El esqueleto de pruebas en Cypress (.cy.js) con los step definitions.
        
        REGLA DE ORO: Si hay N flujos en la tabla, debes devolver N elementos en la lista. ¡No te dejes ninguno!
        """
        
        # Implementación de reintentos exponenciales
        for intento in range(max_intentos):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt_codigo,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CodigoAutomatizacion,
                        temperature=0.1,
                    ),
                )
                return response.parsed
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    time.sleep(2 ** intento)
                    continue
                elif intento == max_intentos - 1:
                    raise Exception(f"Fallo definitivo de API en generación de código tras {max_intentos} intentos: {str(e)}")
                else:
                    time.sleep(1)