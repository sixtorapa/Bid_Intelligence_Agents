"""
agents/research.py — Research Agent

FASE 1: Stub con contexto hardcodeado.
FASE 2: Se conectará a Web MCP (Brave Search) y ChromaDB (RAG).

Responsabilidad: Investigar mercado, competidores y licitaciones
similares para dar contexto al Writer Agent.
"""

from state import BidState


def research_agent(state: BidState) -> dict:
    """
    Nodo 3 del grafo.

    En producción: usa Web MCP para búsqueda real + ChromaDB para RAG
    de propuestas ganadoras anteriores.
    """
    print("\n[Research Agent] Investigando mercado y competidores...")

    scoring = state["scoring"]

    # --- STUB: contexto hardcodeado ---
    research_context = """
    CONTEXTO DE MERCADO (stub):

    Licitaciones similares adjudicadas (PLACE/BOE):
    - Proyecto rehabilitación edificio público, Ayuntamiento de Valladolid: 820.000€
      Adjudicatario: Estudio Arquitectura XYZ. Baja: 3.5%.
    - Proyecto similar, Diputación de Burgos: 790.000€. Baja media del sector: 4-6%.

    Precio de mercado estimado para este tipo de proyecto:
    - Rango: 800.000€ - 870.000€
    - Estrategia recomendada: baja del 4-5% sobre presupuesto base (≈ 808.000€ - 816.000€)

    Competidores habituales en este segmento:
    - Estudio XYZ: fuerte en técnica, precio medio.
    - Constructora ABC: agresiva en precio, menor score técnico históricamente.

    Propuestas ganadoras propias recuperadas por RAG:
    - Propuesta para rehabilitación Palacio Municipal (2022): ganada con baja del 4.2%.
      Puntos fuertes valorados: equipo técnico senior, metodología BIM, plazo reducido.
    """
    # --- FIN STUB ---

    print(f"[Research Agent] Contexto de mercado recopilado.")
    if scoring:
        print(f"  (Gaps a considerar: {scoring.gaps_criticos})")

    return {"research_context": research_context}
