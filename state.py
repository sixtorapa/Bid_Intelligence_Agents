"""
state.py — Estado compartido del grafo y modelos Pydantic.

Todos los agentes leen y escriben sobre BidState.
Los modelos Pydantic garantizan structured outputs tipados.
"""

from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models — structured outputs de cada agente
# ---------------------------------------------------------------------------

class ClasificacionEmpresarial(BaseModel):
    """Clasificación de contratista (LCSP): grupo, subgrupo y categoría."""
    grupo: str          # p.ej. "C" (Edificaciones), "G" (Viales)
    subgrupo: str       # p.ej. "2" (Estructuras)
    categoria: str      # p.ej. "5" (umbral económico acreditado)


class ProyectoReferencia(BaseModel):
    """Obra/proyecto similar ejecutado, como acreditación de experiencia."""
    nombre: str
    cliente: str
    importe_eur: float
    año: int
    descripcion: str = ""


class EmpresaProfile(BaseModel):
    nombre: str
    años_experiencia: int
    certificaciones: list[str] = Field(default_factory=list)
    facturacion_anual_eur: float
    especialidades: list[str] = Field(default_factory=list)
    clasificacion_empresarial: list[ClasificacionEmpresarial] = Field(default_factory=list)
    proyectos_referencia: list[ProyectoReferencia] = Field(default_factory=list)


class Requisito(BaseModel):
    tipo: str                  # "tecnico" | "economico" | "temporal" | "documental" | "criterio_adjudicacion"
    descripcion: str
    obligatorio: bool = True
    valor: Optional[str] = None   # e.g. "mínimo 3 años", "€500.000", "13.5 puntos"


class ScoringResult(BaseModel):
    score_global: float = Field(ge=0, le=100)
    score_tecnico: float = Field(ge=0, le=100)
    score_economico: float = Field(ge=0, le=100)
    score_temporal: float = Field(ge=0, le=100)
    recommendation: str        # "GO" | "NO-GO" | "GO con reservas"
    gaps_criticos: list[str] = Field(default_factory=list)
    justificacion: str = ""


class TechnicalProposal(BaseModel):
    titulo: str
    memoria_tecnica: str
    propuesta_economica: str
    documentacion_adjunta: list[str] = Field(default_factory=list)
    version: int = 1


class ReviewFeedback(BaseModel):
    approved: bool
    score_calidad: float = Field(ge=0, le=100)
    gaps_detectados: list[str] = Field(default_factory=list)
    sugerencias: list[str] = Field(default_factory=list)
    justificacion: str = ""


# ---------------------------------------------------------------------------
# BidState — el objeto de estado compartido por todos los nodos del grafo
# ---------------------------------------------------------------------------

class BidState(TypedDict):
    # Input
    pliego_pdf: str                          # Path al PDF
    empresa_profile: EmpresaProfile

    # Outputs de cada agente (None hasta que ese agente se ejecute)
    requisitos: Optional[list[Requisito]]
    scoring: Optional[ScoringResult]
    research_context: Optional[str]
    propuesta: Optional[TechnicalProposal]
    review_feedback: Optional[ReviewFeedback]

    # Control del loop
    iteration_count: int
    approved: bool

    # Flag de descarte (cuando scoring es NO-GO)
    descartado: bool
    motivo_descarte: Optional[str]
