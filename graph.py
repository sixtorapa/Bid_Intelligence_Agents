"""
graph.py — Definición del grafo LangGraph

Aquí vive la arquitectura real del sistema:
- Los 5 nodos (agentes)
- Las edges condicionales (lógica de routing)
- El loop de revisión Writer → Reviewer → Writer
- El nodo de descarte (cuando scoring es NO-GO)

Es el fichero más importante del proyecto desde el punto de vista
de LangGraph. Todo lo demás son agentes que este grafo orquesta.
"""

from langgraph.graph import StateGraph, END

from state import BidState
from extractor import extractor_agent
from eligibility import eligibility_agent
from research import research_agent
from writer import writer_agent
from reviewer import reviewer_agent


MAX_ITERACIONES = 3


# ---------------------------------------------------------------------------
# Nodos auxiliares
# ---------------------------------------------------------------------------

def descarte_node(state: BidState) -> dict:
    """
    Nodo de descarte: se activa cuando Eligibility devuelve NO-GO.
    Genera un informe de descarte y termina el flujo.
    """
    scoring = state["scoring"]
    motivo = (
        f"Licitación descartada. Score: {scoring.score_global}/100. "
        f"Recomendación: {scoring.recommendation}. "
        f"Gaps críticos: {'; '.join(scoring.gaps_criticos) or 'ninguno especificado'}."
    )
    print(f"\n[Descarte] {motivo}")
    return {"descartado": True, "motivo_descarte": motivo}


def output_node(state: BidState) -> dict:
    """
    Nodo de output final: propuesta aprobada lista para exportar.
    FASE 2: aquí se conectará Notion MCP y Git MCP.
    """
    propuesta = state["propuesta"]
    print(f"\n[Output] ✅ Propuesta final exportada.")
    print(f"  Título: {propuesta.titulo}")
    print(f"  Versión: {propuesta.version}")
    print(f"  Score calidad: {state['review_feedback'].score_calidad}/100")
    print(f"  [FASE 2] → Notion MCP: pendiente")
    print(f"  [FASE 2] → Git MCP: pendiente")
    return {}


# ---------------------------------------------------------------------------
# Edges condicionales — aquí está la lógica de routing del grafo
# ---------------------------------------------------------------------------

def route_after_eligibility(state: BidState) -> str:
    """
    Después del Eligibility Agent:
    - NO-GO → nodo de descarte
    - GO / GO con reservas → Research Agent
    """
    recommendation = state["scoring"].recommendation
    if recommendation == "NO-GO":
        return "descarte"
    return "research"


def route_after_reviewer(state: BidState) -> str:
    """
    Después del Reviewer Agent:
    - Aprobado → output final
    - No aprobado + iteraciones < MAX → vuelve al Writer
    - No aprobado + iteraciones >= MAX → output con warnings
    """
    approved = state["review_feedback"].approved
    iteration_count = state["iteration_count"]

    if approved:
        return "output"
    elif iteration_count >= MAX_ITERACIONES:
        print(f"\n⚠️  Máximo de iteraciones ({MAX_ITERACIONES}) alcanzado. Exportando con warnings.")
        return "output"
    else:
        return "writer"


# ---------------------------------------------------------------------------
# Construcción del grafo
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Construye y compila el grafo LangGraph del Bid Intelligence Agent.

    Estructura:
        START → extractor → eligibility → [condicional] → descarte | research
        research → writer → reviewer → [condicional] → output | writer (loop)
        output → END
        descarte → END
    """
    graph = StateGraph(BidState)

    # Registrar nodos
    graph.add_node("extractor", extractor_agent)
    graph.add_node("eligibility", eligibility_agent)
    graph.add_node("research", research_agent)
    graph.add_node("writer", writer_agent)
    graph.add_node("reviewer", reviewer_agent)
    graph.add_node("descarte", descarte_node)
    graph.add_node("output", output_node)

    # Edges lineales
    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "eligibility")
    graph.add_edge("research", "writer")
    graph.add_edge("writer", "reviewer")

    # Edges condicionales
    graph.add_conditional_edges(
        "eligibility",
        route_after_eligibility,
        {
            "descarte": "descarte",
            "research": "research",
        }
    )

    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "output": "output",
            "writer": "writer",   # loop de revisión
        }
    )

    # Nodos terminales
    graph.add_edge("descarte", END)
    graph.add_edge("output", END)

    return graph.compile()


# Instancia global del grafo compilado
bid_graph = build_graph()
