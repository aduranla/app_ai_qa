import io
import zipfile

def convertir_a_csv(df):
    """Convierte un DataFrame de Pandas a CSV en memoria para descargar."""
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

def crear_zip_automatizacion(tests_generados):
    """Genera un archivo ZIP en memoria RAM con la estructura de Cypress."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for test in tests_generados:
            # Añadir al archivo ZIP con su estructura de carpetas
            zf.writestr(f"cypress/e2e/features/{test.nombre_archivo}.feature", test.codigo_gherkin)
            zf.writestr(f"cypress/support/step_definitions/{test.nombre_archivo}.cy.js", test.codigo_cypress)
    return zip_buffer.getvalue()