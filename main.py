"""
main.py — Entry point del Bid Intelligence Agent

Ejecuta el grafo con un pliego de ejemplo y un perfil de empresa.
Uso: python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from graph import bid_graph
from state import BidState, ClasificacionEmpresarial, EmpresaProfile, ProyectoReferencia

PLIEGO_EJEMPLO = "pruebas/Memoria Justificativa Concesion de Obras.pdf"


def run_pipeline(pliego_pdf: str, empresa: EmpresaProfile) -> BidState:
    """
    Ejecuta el grafo completo y devuelve el estado final.
    """
    initial_state: BidState = {
        "pliego_pdf": pliego_pdf,
        "empresa_profile": empresa,
        "requisitos": None,
        "scoring": None,
        "research_context": None,
        "propuesta": None,
        "review_feedback": None,
        "iteration_count": 0,
        "approved": False,
        "descartado": False,
        "motivo_descarte": None,
    }

    print("=" * 60)
    print("  BID INTELLIGENCE AGENT — Fase 1 (stubs)")
    print("=" * 60)

    final_state = bid_graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  RESUMEN FINAL")
    print("=" * 60)

    if final_state.get("descartado"):
        print(f"🚫 DESCARTADO: {final_state['motivo_descarte']}")
    else:
        print(f"✅ APROBADO tras {final_state['iteration_count']} iteración/es")
        print(f"   Propuesta: {final_state['propuesta'].titulo} (v{final_state['propuesta'].version})")
        print(f"   Score calidad final: {final_state['review_feedback'].score_calidad}/100")

    return final_state


if __name__ == "__main__":

    # --- Caso 1: Empresa que pasa el GO ---
    print("\n>>> CASO 1: Empresa cualificada\n")
    empresa_go = EmpresaProfile(
        nombre="Estudio Arquitectura Norte S.L.",
        años_experiencia=8,
        certificaciones=["ISO 9001", "ISO 14001"],
        facturacion_anual_eur=750_000,
        especialidades=["rehabilitación", "obra pública", "BIM"],
        clasificacion_empresarial=[
            ClasificacionEmpresarial(grupo="C", subgrupo="2", categoria="3"),
            ClasificacionEmpresarial(grupo="C", subgrupo="4", categoria="3"),
        ],
        proyectos_referencia=[
            ProyectoReferencia(
                nombre="Rehabilitación Polideportivo Municipal",
                cliente="Ayuntamiento de Tudela",
                importe_eur=1_200_000,
                año=2023,
                descripcion="Rehabilitación integral de cubierta y vestuarios de polideportivo municipal."
            ),
            ProyectoReferencia(
                nombre="Reforma Centro Cívico",
                cliente="Ayuntamiento de Estella",
                importe_eur=650_000,
                año=2022,
                descripcion="Reforma energética y accesibilidad de centro cívico."
            ),
        ]
    )
    run_pipeline(PLIEGO_EJEMPLO, empresa_go)

    # --- Caso 2: Empresa que NO pasa el GO ---
    print("\n\n>>> CASO 2: Empresa que no cumple requisitos\n")
    empresa_nogo = EmpresaProfile(
        nombre="Arquitectos Pequeños S.L.",
        años_experiencia=2,
        certificaciones=[],
        facturacion_anual_eur=150_000,
        especialidades=["residencial"],
        clasificacion_empresarial=[],
        proyectos_referencia=[
            ProyectoReferencia(
                nombre="Vivienda unifamiliar",
                cliente="Cliente privado",
                importe_eur=80_000,
                año=2024,
                descripcion="Proyecto y dirección de obra de vivienda unifamiliar aislada."
            ),
        ]
    )
    run_pipeline(PLIEGO_EJEMPLO, empresa_nogo)
