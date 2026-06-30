import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import zipfile

# ==========================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Pipeline QA IA", page_icon="🧪", layout="wide")
st.title("🧪 Agente QA Automático con Gemini")
st.markdown("Sube tu archivo de Historias de Usuario (.csv) para generar un Plan de Pruebas exhaustivo dividido por categorías.")

# ==========================================
# CARGA DE API KEY
# ==========================================
load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ ERROR: No se encontró la API Key en el archivo .env. Por favor, configúrala.")
    st.stop()

client = genai.Client(api_key=api_key)

# ==========================================
# ESQUEMAS PYDANTIC
# ==========================================
class CasoPrueba(BaseModel):
    id_test: str
    titulo: str
    ac_que_valida: str
    descripcion: str
    resultado_esperado: str
    precondiciones: str
    hus_afectadas: str
    categoria: str
    tipo_flujo: str

class PlanPruebas(BaseModel):
    casos: list[CasoPrueba]
    
class CasoE2E(BaseModel):
    titulo_flujo: str
    pasos_criticos: str
    justificacion_negocio: str # Para que Gemini nos explique por qué cree que es E2E

class ListaCasosE2E(BaseModel):
    flujos: list[CasoE2E]

class AutomatizacionTest(BaseModel):
    nombre_archivo: str # ej: 'solicitud_muestra_gratis'
    codigo_gherkin: str
    codigo_cypress: str

class CodigoAutomatizacion(BaseModel):
    tests: list[AutomatizacionTest] # Obligamos a la IA a devolver una lista, no uno solo
    
# ==========================================
# INTERFAZ DE USUARIO (UI)
# ==========================================
# Creamos dos pestañas maestras para la aplicación
tab_fase1, tab_fase2 = st.tabs(["Fase 1: Plan de Pruebas", "Fase 2: BDD & Cypress (E2E)"])

with tab_fase1:
    # ==========================================
    # FUNCIONES NÚCLEO
    # ==========================================
    def generar_plan_pruebas_por_hu(historia_texto):
        prompt = f"""
        EEres un Analista de Pruebas (QA) Senior experto.
        A continuación, te proporciono una lista de Historias de Usuario con sus Criterios de Aceptación.
        
        Tu tarea es diseñar un Plan de Pruebas completo y exhaustivo basándote en estas historias y donde NINGÚN criterio de aceptación quede sin validar. Analiza cada Historia de Usuario y desglosa sus 'Criterios de Aceptación'.
        Debes incluir:
        1. Pruebas Funcionales.
        2. Pruebas de Accesibilidad.
        3. Pruebas de Rendimiento.
        4. Pruebas de Seguridad (si aplican).
        
        Asegúrate de cubrir escenarios ideales ("Happy Path") y escenarios de error o extremos ("Negativo") para todas las historias siempre que aplique.
        
        HISTORIA DE USUARIO A ANALIZAR:
        {historia_texto}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlanPruebas,
                temperature=0.2,
            ),
        )
        return response.parsed

    def convertir_a_csv(df):
        """Convierte un DataFrame de Pandas a CSV en memoria para el botón de descarga."""
        return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

    # ==========================================
    # INTERFAZ DE USUARIO (UI)
    # ==========================================
    # 1. Subida del archivo
    archivo_subido = st.file_uploader("📂 Sube tu archivo CSV de Historias de Usuario", type=["csv"])

    if archivo_subido is not None:
        # Leer el CSV forzando explícitamente el punto y coma como separador
        try:
            df_input = pd.read_csv(archivo_subido, encoding='utf-8-sig', sep=';')
            st.success(f"Archivo cargado correctamente con {len(df_input)} historias de usuario.")
            
            with st.expander("👀 Previsualizar Historias de Usuario cargadas"):
                st.dataframe(df_input)
                
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")
            st.stop()

        # ==========================================
        # GESTIÓN DEL ESTADO (SESSION STATE)
        # ==========================================
        # Inicializamos las variables en la memoria de Streamlit si no existen
        if 'df_funcional' not in st.session_state:
            st.session_state.df_funcional = None
            st.session_state.df_acc = None
            st.session_state.df_rend = None
            st.session_state.df_seguridad = None

        # Botón para iniciar el proceso
        if st.button("🚀 Generar Plan de Pruebas", type="primary"):
            
            barra_progreso = st.progress(0)
            texto_estado = st.empty()
            
            plan_completo = []
            total_hus = len(df_input)
            
            for index, row in df_input.iterrows():
                numero_actual = index + 1
                texto_estado.text(f"⏳ Analizando HU {numero_actual} de {total_hus}...")
                
                id_hu = row.get('ID', '')
                historia = row.get('Historia de usuario', '')
                criterios = row.get('Criterios de aceptación', '')
                texto_hu = f"ID: {id_hu} | HU: {historia} | Criterios: {criterios}"
                
                try:
                    plan_generado = generar_plan_pruebas_por_hu(texto_hu)
                    plan_completo.extend(plan_generado.casos)
                except Exception as e:
                    st.error(f"⚠️ Error procesando la HU {id_hu}: {e}")
                
                barra_progreso.progress(numero_actual / total_hus)
                
            texto_estado.success("✅ ¡Análisis completado!")
            
            # 1. Convertir a DataFrame base ANTES de numerar
            df_resultados = pd.DataFrame([caso.model_dump() for caso in plan_completo])
            
            # --- NUEVO: Eliminamos la columna interna para que no salga en el CSV ---
            if 'ac_que_valida' in df_resultados.columns:
                df_resultados.drop(columns=['ac_que_valida'], inplace=True)
                
            # Mapeamos los nombres de las columnas restantes
            df_resultados.rename(columns={
                "id_test": "ID Test", 
                "titulo": "Título", 
                "descripcion": "Descripción", 
                "resultado_esperado": "Resultado Esperado",
                "precondiciones": "Precondiciones", 
                "hus_afectadas": "HUs afectadas",
                "categoria": "Categoría", 
                "tipo_flujo": "Tipo de Flujo"
            }, inplace=True)
            
            # 2. Separar DataFrames por categoría usando .copy()
            df_func = df_resultados[df_resultados['Categoría'].str.contains('funcional', case=False, na=False)].copy()
            df_acceso = df_resultados[df_resultados['Categoría'].str.contains('accesibilidad', case=False, na=False)].copy()
            df_rendi = df_resultados[df_resultados['Categoría'].str.contains('rendimiento', case=False, na=False)].copy()
            df_segu = df_resultados[df_resultados['Categoría'].str.contains('seguridad', case=False, na=False)].copy()
            
            # 3. Función auxiliar para reasignar IDs secuenciales a un DataFrame específico
            def asignar_ids_secuenciales(df):
                # Genera la lista TC-001, TC-002 según el tamaño de este DataFrame
                nuevos_ids = [f"TC-{i:03d}" for i in range(1, len(df) + 1)]
                df['ID Test'] = nuevos_ids
                return df
                
            # 4. Asignamos los IDs y guardamos en la memoria de la sesión
            st.session_state.df_funcional = asignar_ids_secuenciales(df_func)
            st.session_state.df_acc = asignar_ids_secuenciales(df_acceso)
            st.session_state.df_rend = asignar_ids_secuenciales(df_rendi)
            st.session_state.df_seguridad = asignar_ids_secuenciales(df_segu)

        # ==========================================
        # RENDERIZADO DE RESULTADOS (Fuera del botón)
        # ==========================================
        # Si tenemos datos en la memoria de la sesión, mostramos las pestañas
        if st.session_state.df_funcional is not None:
            
            st.divider()
            st.subheader("📊 Resultados del Plan de Pruebas")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Funcional", "Accesibilidad", "Rendimiento", "Seguridad"])
            fecha_str = datetime.now().strftime('%Y%m%d')

            with tab1:
                st.dataframe(st.session_state.df_funcional, use_container_width=True)
                st.download_button(
                    label="📥 Descargar CSV Funcional",
                    data=convertir_a_csv(st.session_state.df_funcional),
                    file_name=f"Plan_Funcional_{fecha_str}.csv",
                    mime="text/csv",
                    key="btn_funcional"
                )
                
            with tab2:
                st.dataframe(st.session_state.df_acc, use_container_width=True)
                st.download_button(
                    label="📥 Descargar CSV Accesibilidad",
                    data=convertir_a_csv(st.session_state.df_acc),
                    file_name=f"Plan_Accesibilidad_{fecha_str}.csv",
                    mime="text/csv",
                    key="btn_acc"
                )
                
            with tab3:
                st.dataframe(st.session_state.df_rend, use_container_width=True)
                st.download_button(
                    label="📥 Descargar CSV Rendimiento",
                    data=convertir_a_csv(st.session_state.df_rend),
                    file_name=f"Plan_Rendimiento_{fecha_str}.csv",
                    mime="text/csv",
                    key="btn_rend"
                )
                
            with tab4:
                if not st.session_state.df_seguridad.empty:
                    st.dataframe(st.session_state.df_seguridad, use_container_width=True)
                    st.download_button(
                        label="📥 Descargar CSV Seguridad",
                        data=convertir_a_csv(st.session_state.df_seguridad),
                        file_name=f"Plan_Seguridad_{fecha_str}.csv",
                        mime="text/csv",
                        key="btn_seguridad"
                    )
                else:
                    st.info("No se generaron pruebas de seguridad para estas Historias de Usuario.")
    pass

    with tab_fase2:
        st.header("🤖 Automatización de Flujos Críticos (E2E)")
        
        # 1. Verificar que la Fase 1 se haya completado
        if 'df_funcional' not in st.session_state or st.session_state.df_funcional is None:
            st.warning("⚠️ Primero debes generar el Plan de Pruebas en la 'Fase 1' para poder extraer los flujos E2E.")
        else:
            st.info(f"Se han detectado {len(st.session_state.df_funcional)} casos funcionales. La IA filtrará los más críticos.")
            
            # Botón PASO 1: Pedir propuesta a Gemini
            if st.button("🔍 1. Identificar Flujos E2E", type="primary"):
                with st.spinner("Analizando casos funcionales y diseñando flujos E2E..."):
                    # Convertimos el DataFrame a texto para dárselo a Gemini
                    casos_texto = st.session_state.df_funcional[['ID Test', 'Título', 'Descripción']].to_string()
                    
                    prompt_e2e = f"""
                    Eres un QA Automation Lead. Revisa esta lista de casos funcionales:
                    {casos_texto}
                    
                    Selecciona ÚNICAMENTE los casos que representen un flujo "End-to-End" crítico para el negocio.
                    Combina pasos si es necesario para crear un flujo completo de usuario.
                    """
                    
                    respuesta = client.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=prompt_e2e,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ListaCasosE2E,
                            temperature=0.2,
                        ),
                    )
                    
                    # Guardamos la propuesta en session_state para que no se borre
                    df_propuesta = pd.DataFrame([f.model_dump() for f in respuesta.parsed.flujos])
                    st.session_state.df_e2e_editar = df_propuesta

            # PASO 2: Validación manual (El "Human in the Loop")
            if 'df_e2e_editar' in st.session_state:
                st.markdown("### ✍️ Paso 2: Revisa y edita los flujos propuestos")
                st.caption("Haz doble clic en cualquier celda para editar el texto. Puedes añadir o eliminar filas usando los controles de la tabla.")
                
                # st.data_editor permite al usuario modificar el DataFrame en vivo
                df_editado_por_usuario = st.data_editor(
                    st.session_state.df_e2e_editar, 
                    num_rows="dynamic", # Permite añadir/borrar filas
                    use_container_width=True
                )
                
                st.divider()
                
            # PASO 3: Generación final de código basada en la tabla EDITADA
            if st.button("⚡ 3. Aprobar y Generar Gherkin/Cypress", type="primary"):
                with st.spinner("Escribiendo código de automatización para TODOS los flujos..."):
                    flujos_aprobados_texto = df_editado_por_usuario.to_string()
                    
                    prompt_codigo = f"""
                    Eres un SDET experto en Cypress. Basado en los siguientes flujos E2E validados:
                    {flujos_aprobados_texto}
                    
                    Por CADA UNO de los flujos de la tabla, debes generar de forma independiente:
                    1. Un 'nombre_archivo' corto en formato snake_case (ej: login_usuario_valido).
                    2. El código Gherkin (.feature).
                    3. El esqueleto de pruebas en Cypress (.cy.js) con los step definitions.
                    
                    REGLA DE ORO: Si hay 3 flujos en la tabla, debes devolver 3 elementos en la lista. ¡No te dejes ninguno!
                    """
                    
                    respuesta_codigo = client.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=prompt_codigo,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=CodigoAutomatizacion,
                            temperature=0.1,
                        ),
                    )
                    
                    st.session_state.codigo_generado = respuesta_codigo.parsed.tests

        # PASO 4: Visualización del Código y Descarga ZIP
        if 'codigo_generado' in st.session_state:
            st.success(f"✅ ¡Código generado para {len(st.session_state.codigo_generado)} flujos E2E!")
            
            # --- CREAR EL ZIP EN MEMORIA ---
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                
                # Iterar sobre cada test generado para pintarlo y meterlo al zip
                for test in st.session_state.codigo_generado:
                    
                    # 1. Pintar en Streamlit dentro de un desplegable (expander)
                    with st.expander(f"📁 Archivos para: {test.nombre_archivo}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**`{test.nombre_archivo}.feature`**")
                            st.code(test.codigo_gherkin, language="gherkin")
                        with col2:
                            st.markdown(f"**`{test.nombre_archivo}.cy.js`**")
                            st.code(test.codigo_cypress, language="javascript")
                    
                    # 2. Añadir al archivo ZIP con su estructura de carpetas
                    zf.writestr(f"cypress/e2e/features/{test.nombre_archivo}.feature", test.codigo_gherkin)
                    zf.writestr(f"cypress/support/step_definitions/{test.nombre_archivo}.cy.js", test.codigo_cypress)
            
            st.divider()
            
            # Botón gigantesco de Descarga del ZIP
            st.download_button(
                label="📦 Descargar TODO en formato .ZIP (Listo para Cypress)",
                data=zip_buffer.getvalue(),
                file_name=f"Automatizacion_E2E_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
