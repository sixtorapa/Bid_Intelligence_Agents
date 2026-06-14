"""
eligibility.py — Eligibility Agent

FASE 1+: Usa GPT-4o con structured output para evaluar la viabilidad
de la empresa frente a la lista completa de requisitos extraídos.

Responsabilidad: Comparar requisitos del pliego con el perfil de la
empresa y generar un ScoringResult con recomendación GO / NO-GO.
"""

import json

from langchain_openai import ChatOpenAI

from state import BidState, ScoringResult


SYSTEM_PROMPT = """Eres un consultor experto en licitaciones públicas españolas \
(LCSP) que evalúa la viabilidad de que una empresa licite a un contrato público.

Se te proporciona:
1. El perfil de la empresa licitadora (experiencia, certificaciones, \
facturación, especialidades, clasificación empresarial y proyectos de \
referencia ejecutados).
2. La lista completa de requisitos extraídos del pliego (técnicos, económicos, \
temporales, documentales y criterios de adjudicación).

Evalúa la viabilidad de la empresa para este contrato y devuelve:
- score_tecnico (0-100): ¿cumple la empresa los requisitos de solvencia \
técnica, clasificación empresarial (grupo/subgrupo/categoría) y experiencia \
acreditada mediante proyectos de referencia y certificaciones? Si el pliego \
exige una clasificación o categoría que la empresa no tiene o que es \
insuficiente, trátalo como un gap crítico.
- score_economico (0-100): ¿puede asumir el presupuesto/valor estimado y las \
garantías exigidas, y cumple la solvencia económica requerida (facturación \
anual y categoría de clasificación acreditan capacidad económica suficiente)?
- score_temporal (0-100): ¿son realistas los plazos exigidos para una empresa \
con este perfil?
- score_global (0-100): media ponderada (técnico 40%, económico 40%, temporal \
20%), ajustada según tu criterio si hay gaps muy críticos.
- recommendation: "GO" si score_global >= 70 y no hay incumplimientos \
eliminatorios, "GO con reservas" si está entre 50 y 70, "NO-GO" si es inferior \
a 50 o hay un requisito obligatorio que la empresa claramente no cumple.
- gaps_criticos: lista de incumplimientos concretos detectados (vacía si no hay).
- justificacion: breve explicación de la recomendación.

Basa la evaluación en los datos del perfil y los requisitos proporcionados, no \
en suposiciones."""


def eligibility_agent(state: BidState) -> dict:
    """
    Nodo 2 del grafo.

    Evalúa la lista completa de requisitos contra el perfil de la
    empresa con GPT-4o. La edge condicional en graph.py usa
    scoring.recommendation para decidir si continuar o descartar.
    """
    print("\n[Eligibility Agent] Evaluando viabilidad...")

    requisitos = state["requisitos"]
    empresa = state["empresa_profile"]

    contexto = {
        "empresa": empresa.model_dump(),
        "requisitos": [r.model_dump() for r in requisitos],
    }

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(ScoringResult)

    scoring = structured_llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", json.dumps(contexto, ensure_ascii=False, indent=2)),
    ])

    print(f"[Eligibility Agent] Score: {scoring.score_global}/100 → {scoring.recommendation}")
    if scoring.gaps_criticos:
        for g in scoring.gaps_criticos:
            print(f"  ⚠️  {g}")

    return {"scoring": scoring}
