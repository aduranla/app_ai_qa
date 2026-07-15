from pydantic import BaseModel

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
    justificacion_negocio: str

class ListaCasosE2E(BaseModel):
    flujos: list[CasoE2E]

class AutomatizacionTest(BaseModel):
    nombre_archivo: str 
    codigo_gherkin: str
    codigo_cypress: str

class CodigoAutomatizacion(BaseModel):
    tests: list[AutomatizacionTest]