import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
import io

# Importaciones de los módulos propios
from schemas import *
from export_utils import convertir_a_csv, crear_zip_automatizacion
from ai_client import QA_AI_Client

# ==========================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Pipeline QA IA", page_icon="🧪", layout="wide")
st.title("🧪 Agente QA Automático con Gemini")
st.markdown("Sube tu archivo de Historias de Usuario (.csv) para generar un Plan de Pruebas exhaustivo dividido por categorías.")

# ==========================================
# INICIALIZACIÓN DEL CLIENTE IA
# ==========================================
load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ ERROR: No se encontró la API Key en el archivo .env. Por favor, configúrala.")
    st.stop()

# Instanciamos nuestra clase propia
ai_client = QA_AI_Client(api_key=api_key)

# ==========================================
# VALIDACIÓN Y SANITIZACIÓN DE ENTRADA (SEGURIDAD)
# ==========================================
def validar_csv_seguridad(df):
    """
    Analiza el DataFrame en busca de anomalías estructurales o de seguridad 
    antes de enviarlo al motor LLM.
    """
    # 1. Validación Estructural: Comprobar columnas obligatorias
    columnas_esperadas = ['id', 'historia de usuario', 'criterios de aceptación']
    columnas_presentes = [str(col).lower().strip() for col in df.columns]
    
    for col_esperada in columnas_esperadas:
        # Hacemos una búsqueda flexible por si hay mayúsculas o espacios extra
        if not any(col_esperada in col_pres for col_pres in columnas_presentes):
            return False, f"Error estructural: El CSV no contiene la columna obligatoria '{col_esperada.title()}'."

    # 2. Validación de Contenido y Seguridad
    palabras_prohibidas = [
        "ignora las instrucciones", "ignora todas las instrucciones", 
        "olvida tu rol", "system prompt", "bypass", "comportate como"
    ]
    
    for index, row in df.iterrows():
        # Juntamos todo el texto de la fila para analizarlo
        texto_fila = " ".join([str(val) for val in row.values]).lower()
        
        # 2A. Límite de caracteres (Prevención de ataques DoS por saturación de contexto)
        if len(texto_fila) > 4000:
            return False, f"Error de longitud: La fila {index+1} excede el límite máximo de caracteres permitido (Posible intento de desbordamiento de contexto)."
            
        # 2B. Filtro Heurístico Básico (Prevención de Prompt Injection)
        for palabra in palabras_prohibidas:
            if palabra in texto_fila:
                return False, f"Alerta de Seguridad: Posible intento de 'Prompt Injection' detectado en la fila {index+1} (Patrón prohibido: '{palabra}')."

    return True, "Validación exitosa"

# ==========================================
# INTERFAZ DE USUARIO (UI)
# ==========================================
tab_fase1, tab_fase2 = st.tabs(["Fase 1: Plan de Pruebas", "Fase 2: BDD & Cypress (E2E)"])

with tab_fase1:
    archivo_subido = st.file_uploader("📂 Sube tu archivo CSV de Historias de Usuario", type=["csv"])

    if archivo_subido is not None:
        try:
            # 1. Leemos los bytes crudos en memoria
            bytes_data = archivo_subido.getvalue()
            
            # 2. Decodificación adaptativa (Estrategia de Fallback)
            try:
                texto_csv = bytes_data.decode('utf-8-sig') # Estándar de Excel moderno
            except UnicodeDecodeError:
                try:
                    texto_csv = bytes_data.decode('utf-8') # Estándar web
                except UnicodeDecodeError:
                    texto_csv = bytes_data.decode('latin-1') # Windows antiguo o ISO
                    
            # 3. Ingesta resiliente: sep=None obliga a Pandas a detectar si es ',' o ';' o '\t'
            df_input = pd.read_csv(io.StringIO(texto_csv), sep=None, engine='python')
            
            # --- Lógica de validación ---
            es_valido, mensaje_validacion = validar_csv_seguridad(df_input)
            
            if not es_valido:
                st.error(f"🛑 ARCHIVO RECHAZADO: {mensaje_validacion}")
                st.stop() 
            # ----------------------------------------------------------------
            
            st.success(f"Archivo cargado y validado correctamente con {len(df_input)} historias de usuario.")
            
            with st.expander("👀 Previsualizar Historias de Usuario cargadas"):
                st.dataframe(df_input)
                
        except Exception as e:
            st.error(f"❌ Error crítico al leer el archivo CSV. Estructura no reconocida. Detalle: {e}")
            st.stop()

        # Gestión del Estado
        if 'df_funcional' not in st.session_state:
            st.session_state.df_funcional = None
            st.session_state.df_acc = None
            st.session_state.df_rend = None
            st.session_state.df_seguridad = None

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
                
                # Bloque robusto de gestión de errores en la interfaz
                try:
                    plan_generado = ai_client.generar_plan_pruebas_por_hu(texto_hu)
                    plan_completo.extend(plan_generado.casos)
                except Exception as e:
                    if "429" in str(e):
                        st.error(f"🛑 Límite de cuota de API excedido en HU {id_hu}. Por favor, espera unos minutos.")
                        break # Rompemos el bucle si nos cortan el grifo
                    else:
                        st.warning(f"⚠️ Error de validación o red en HU {id_hu}. Saltando a la siguiente... Detalle: {e}")
                
                barra_progreso.progress(numero_actual / total_hus)
                
            texto_estado.success("✅ ¡Análisis completado!")
            
            if plan_completo:
                df_resultados = pd.DataFrame([caso.model_dump() for caso in plan_completo])
                
                # Limpieza de datos (eliminamos columnas de soporte interno de Pydantic)
                if 'ac_que_valida' in df_resultados.columns:
                    df_resultados.drop(columns=['ac_que_valida'], inplace=True)
                    
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
                
                df_func = df_resultados[df_resultados['Categoría'].str.contains('funcional', case=False, na=False)].copy()
                df_acceso = df_resultados[df_resultados['Categoría'].str.contains('accesibilidad', case=False, na=False)].copy()
                df_rendi = df_resultados[df_resultados['Categoría'].str.contains('rendimiento', case=False, na=False)].copy()
                df_segu = df_resultados[df_resultados['Categoría'].str.contains('seguridad', case=False, na=False)].copy()
                
                def asignar_ids_secuenciales(df):
                    nuevos_ids = [f"TC-{i:03d}" for i in range(1, len(df) + 1)]
                    df['ID Test'] = nuevos_ids
                    return df
                    
                st.session_state.df_funcional = asignar_ids_secuenciales(df_func)
                st.session_state.df_acc = asignar_ids_secuenciales(df_acceso)
                st.session_state.df_rend = asignar_ids_secuenciales(df_rendi)
                st.session_state.df_seguridad = asignar_ids_secuenciales(df_segu)
            else:
                st.error("No se pudo generar ningún caso de prueba. Revisa la conexión con la API.")

        # Renderizado
        if st.session_state.df_funcional is not None:
            st.divider()
            st.subheader("📊 Resultados del Plan de Pruebas")
            tab1, tab2, tab3, tab4 = st.tabs(["Funcional", "Accesibilidad", "Rendimiento", "Seguridad"])
            fecha_str = datetime.now().strftime('%Y%m%d')

            with tab1:
                st.dataframe(st.session_state.df_funcional, use_container_width=True)
                st.download_button("📥 Descargar CSV Funcional", data=convertir_a_csv(st.session_state.df_funcional), file_name=f"Plan_Funcional_{fecha_str}.csv", mime="text/csv")
                
            with tab2:
                st.dataframe(st.session_state.df_acc, use_container_width=True)
                st.download_button("📥 Descargar CSV Accesibilidad", data=convertir_a_csv(st.session_state.df_acc), file_name=f"Plan_Accesibilidad_{fecha_str}.csv", mime="text/csv")
                
            with tab3:
                st.dataframe(st.session_state.df_rend, use_container_width=True)
                st.download_button("📥 Descargar CSV Rendimiento", data=convertir_a_csv(st.session_state.df_rend), file_name=f"Plan_Rendimiento_{fecha_str}.csv", mime="text/csv")
                
            with tab4:
                if not st.session_state.df_seguridad.empty:
                    st.dataframe(st.session_state.df_seguridad, use_container_width=True)
                    st.download_button("📥 Descargar CSV Seguridad", data=convertir_a_csv(st.session_state.df_seguridad), file_name=f"Plan_Seguridad_{fecha_str}.csv", mime="text/csv")
                else:
                    st.info("No se generaron pruebas de seguridad para estas Historias de Usuario.")

with tab_fase2:
    st.header("🤖 Automatización de Flujos Críticos (E2E)")
    
    if 'df_funcional' not in st.session_state or st.session_state.df_funcional is None:
        st.warning("⚠️ Primero debes generar el Plan de Pruebas en la 'Fase 1'.")
    else:
        st.info(f"Se han detectado {len(st.session_state.df_funcional)} casos funcionales.")
        
        if st.button("🔍 Identificar Flujos E2E", type="primary"):
            with st.spinner("Analizando casos funcionales y diseñando flujos E2E..."):
                casos_texto = st.session_state.df_funcional[['ID Test', 'Título', 'Descripción']].to_string()
                
                try:
                    respuesta = ai_client.identificar_flujos_e2e(casos_texto)
                    df_propuesta = pd.DataFrame([f.model_dump() for f in respuesta.flujos])
                    st.session_state.df_e2e_editar = df_propuesta
                except Exception as e:
                    st.error(f"❌ Fallo al conectar con Gemini: {e}")

        if 'df_e2e_editar' in st.session_state:
            st.markdown("### ✍️ Paso 2: Revisa y edita los flujos propuestos")
            st.caption("Haz doble clic en cualquier celda para editar el texto.")
            
            df_editado_por_usuario = st.data_editor(
                st.session_state.df_e2e_editar, 
                num_rows="dynamic",
                use_container_width=True
            )
            st.divider()
            
        if st.button("⚡ Aprobar y Generar Gherkin/Cypress", type="primary"):
            if 'df_e2e_editar' in st.session_state:
                with st.spinner("Escribiendo código de automatización para TODOS los flujos..."):
                    flujos_aprobados_texto = df_editado_por_usuario.to_string()
                    try:
                        respuesta_codigo = ai_client.generar_codigo_automatizacion(flujos_aprobados_texto)
                        st.session_state.codigo_generado = respuesta_codigo.tests
                    except Exception as e:
                         st.error(f"❌ Fallo en la generación de código: {e}")

    if 'codigo_generado' in st.session_state:
        st.success(f"✅ ¡Código generado para {len(st.session_state.codigo_generado)} flujos E2E!")
        
        for test in st.session_state.codigo_generado:
            with st.expander(f"📁 Archivos para: {test.nombre_archivo}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**`{test.nombre_archivo}.feature`**")
                    st.code(test.codigo_gherkin, language="gherkin")
                with col2:
                    st.markdown(f"**`{test.nombre_archivo}.cy.js`**")
                    st.code(test.codigo_cypress, language="javascript")
        
        st.divider()
        
        datos_zip = crear_zip_automatizacion(st.session_state.codigo_generado)
        
        st.download_button(
            label="📦 Descargar TODO en formato .ZIP (Listo para Cypress)",
            data=datos_zip,
            file_name=f"Automatizacion_E2E_{datetime.now().strftime('%Y%m%d')}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )