"""
agents/writer.py — Writer Agent

FASE 1: Stub con propuesta hardcodeada.
FASE 1+: Se conectará a GPT-4o con el contexto del Research Agent.

Responsabilidad: Redactar la memoria técnica y propuesta económica.
En cada iteración del loop incorpora el feedback del Reviewer Agent.
"""

from state import BidState, TechnicalProposal


def writer_agent(state: BidState) -> dict:
    """
    Nodo 4 del grafo.

    Puede ejecutarse varias veces (loop de revisión).
    Cada ejecución incrementa la versión de la propuesta e
    incorpora el feedback del Reviewer si existe.
    """
    iteration = state["iteration_count"]
    feedback = state.get("review_feedback")
    propuesta_anterior = state.get("propuesta")

    version = (propuesta_anterior.version + 1) if propuesta_anterior else 1

    print(f"\n[Writer Agent] Redactando propuesta v{version} (iteración {iteration + 1})...")

    if feedback and feedback.gaps_detectados:
        print(f"  Incorporando feedback del Reviewer:")
        for gap in feedback.gaps_detectados:
            print(f"    → {gap}")

    # --- STUB: propuesta hardcodeada ---
    # En producción: GPT-4o con research_context + RAG de propuestas anteriores

    memoria_tecnica = f"""
    MEMORIA TÉCNICA — v{version}

    1. PRESENTACIÓN DEL EQUIPO
    Nuestro estudio aporta {state['empresa_profile'].años_experiencia} años de experiencia
    en proyectos de arquitectura pública. El equipo designado para este proyecto incluye
    arquitecto director con más de 10 años en rehabilitación de edificios singulares.

    2. METODOLOGÍA
    Aplicamos metodología BIM Level 2 para coordinación y control del proyecto,
    garantizando trazabilidad completa de todas las decisiones técnicas.

    3. PLAZO DE EJECUCIÓN
    Proponemos un plazo de 16 meses (2 meses menos que el máximo), con hitos
    mensuales de control claramente definidos.

    {'4. RESPUESTA A REVISIÓN: Se han incorporado las observaciones del revisor.' if version > 1 else ''}
    """

    propuesta_economica = f"""
    PROPUESTA ECONÓMICA — v{version}

    Presupuesto base de licitación: 850.000,00 € (IVA excluido)
    Baja ofertada: 4,5% (estrategia basada en análisis de mercado)
    Precio ofertado: 811.750,00 € (IVA excluido)

    Desglose por capítulos disponible en Anexo I.
    """
    # --- FIN STUB ---

    propuesta = TechnicalProposal(
        titulo=f"Propuesta Técnica y Económica — {state['empresa_profile'].nombre}",
        memoria_tecnica=memoria_tecnica.strip(),
        propuesta_economica=propuesta_economica.strip(),
        documentacion_adjunta=["ISO 9001 vigente", "Declaración responsable", "Títulos acreditativos"],
        version=version
    )

    print(f"[Writer Agent] Propuesta v{version} generada.")

    return {
        "propuesta": propuesta,
        "iteration_count": iteration + 1
    }
