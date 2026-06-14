"""
agents/reviewer.py — Reviewer Agent

FASE 1: Stub que aprueba en la segunda iteración (para demostrar el loop).
FASE 1+: Se conectará a GPT-4o para evaluación real contra criterios del pliego.

Responsabilidad: Evaluar la propuesta contra los criterios del pliego
y decidir si aprobar o mandar a revisar (con feedback concreto).
"""

from state import BidState, ReviewFeedback


def reviewer_agent(state: BidState) -> dict:
    """
    Nodo 5 del grafo.

    La edge condicional en graph.py lee review_feedback.approved
    para decidir si volver al Writer o ir al output final.

    STUB: En la primera iteración detecta gaps artificiales para
    demostrar el loop. En la segunda iteración aprueba.
    """
    iteration = state["iteration_count"]
    propuesta = state["propuesta"]

    print(f"\n[Reviewer Agent] Evaluando propuesta v{propuesta.version}...")

    # --- STUB: lógica de aprobación simplificada ---
    if iteration == 1:
        # Primera iteración: detectar gaps para forzar una revisión
        feedback = ReviewFeedback(
            approved=False,
            score_calidad=62.0,
            gaps_detectados=[
                "Falta descripción del equipo técnico auxiliar (delineantes, ingenieros)",
                "La propuesta económica no incluye desglose por capítulos (Anexo I vacío)",
            ],
            sugerencias=[
                "Añadir CV resumidos del equipo técnico completo",
                "Incluir tabla de desglose económico por partidas principales",
            ],
            justificacion="Propuesta con buena base técnica pero incompleta en documentación exigida."
        )
        print(f"[Reviewer Agent] ❌ No aprobada (score: {feedback.score_calidad}). Gaps detectados: {len(feedback.gaps_detectados)}")
    else:
        # Segunda iteración (o más): aprobar
        feedback = ReviewFeedback(
            approved=True,
            score_calidad=88.0,
            gaps_detectados=[],
            sugerencias=[],
            justificacion="Propuesta completa. Cumple todos los criterios de adjudicación del pliego."
        )
        print(f"[Reviewer Agent] ✅ Aprobada (score: {feedback.score_calidad}).")
    # --- FIN STUB ---

    return {
        "review_feedback": feedback,
        "approved": feedback.approved
    }
