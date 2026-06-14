"""
extractor.py — Extractor Agent

FASE 1+: Lee el PDF real del pliego con PyMuPDF y usa GPT-4o con
structured output para extraer los requisitos.
FASE 3: Se sustituirá la llamada a GPT-4o por el endpoint Modal con
LLaMA fine-tuneado (mismo contrato de entrada/salida).

Responsabilidad: Analizar el PDF del pliego y extraer toda la
información estructurada relevante como lista de Requisito.

El documento se procesa en fragmentos (varias páginas cada uno) porque
en una sola llamada con el documento completo (~80k caracteres) GPT-4o
es inconsistente entre ejecuciones a la hora de "ser exhaustivo" con los
criterios de adjudicación y otros requisitos — en unas pasadas extrae
~50 requisitos y en otras ~30. Procesando fragmentos más pequeños el
modelo cubre todo el texto de forma fiable, y una pasada final de
consolidación elimina duplicados introducidos por el solape entre
fragmentos.
"""

import fitz
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from state import BidState, Requisito


SYSTEM_PROMPT = """Eres un experto en contratación pública española (LCSP) \
especializado en analizar pliegos y memorias justificativas de licitaciones.

Se te proporciona UN FRAGMENTO (no el documento completo) de un pliego. \
Lee el texto y extrae TODOS los requisitos relevantes que aparezcan en ESTE \
fragmento para que una empresa licitadora pueda evaluar su viabilidad y \
redactar una propuesta. Si el fragmento no contiene ningún requisito \
relevante (p.ej. es portada, índice o texto introductorio), devuelve una \
lista vacía.

Clasifica cada requisito en uno de estos tipos:
- "tecnico": solvencia técnica, clasificación empresarial, experiencia previa, \
certificaciones de calidad y medios personales/materiales EXIGIDOS PARA LICITAR \
o adscritos como condición de solvencia.
- "economico": presupuesto base de licitación, valor estimado, solvencia \
económica/financiera, garantías.
- "temporal": plazos de presentación de ofertas, ejecución, explotación o entrega.
- "documental": documentación obligatoria a presentar (declaraciones, \
certificados, planes, etc.).
- "criterio_adjudicacion": cada criterio (y subcriterio) de valoración de \
ofertas, con su puntuación o ponderación.

NO extraigas como Requisito las frases puramente descriptivas del objeto o \
régimen del contrato que no impongan ninguna condición evaluable sobre el \
licitador o su oferta (p.ej. "la obra se ejecuta a riesgo y ventura del \
contratista", "no se permite la división en lotes", descripción general de las \
actividades que realizará el concesionario). Esas frases son contexto, no \
requisitos.

Para cada requisito indica:
- descripcion: descripción clara y concisa del requisito.
- obligatorio: true si es eliminatorio/obligatorio, false si es valorable.
- valor: el dato concreto asociado (importe, plazo, puntuación...) si existe, \
o null si no aplica.

Sé exhaustivo con los criterios de adjudicación: si un criterio se desglosa en \
varios subcriterios numerados o con puntuación propia, extrae CADA SUBCRITERIO \
como un Requisito independiente — nunca agrupes varios subcriterios en uno solo.

ATENCIÓN — patrón "tabla + desarrollo", muy habitual en los criterios \
"sujetos a juicio de valor": el pliego suele presentar primero una TABLA o \
lista numerada (Nº / Criterio / Puntuación máxima) que define la lista CERRADA \
de criterios con su puntuación, y a continuación una sección de "Desarrollo de \
los criterios" que explica, criterio por criterio, en prosa, QUÉ aspectos \
concretos se valorarán dentro de cada uno (sin asignarles puntuación propia). \
En ese caso:
- Extrae UN Requisito de tipo "criterio_adjudicacion" POR CADA FILA de la \
tabla (ni más ni menos), con su puntuación en `valor`.
- Si en este fragmento aparece también el "Desarrollo" de alguno de esos \
criterios, usa ese texto para AMPLIAR la `descripcion` del MISMO Requisito \
— no crees Requisitos adicionales por cada aspecto o párrafo del desarrollo.
- Si en este fragmento solo aparece el "Desarrollo" de un criterio (p.ej. \
porque la tabla quedó en otro fragmento), genera igualmente UN ÚNICO Requisito \
para ese criterio (nombre del criterio + resumen del desarrollo), con \
`valor=null` si no conoces la puntuación."""


CONSOLIDACION_PROMPT = """Eres un experto en contratación pública española (LCSP).

Se te proporciona una lista de requisitos extraídos de un pliego, generada \
procesando el documento por fragmentos. Debido al solape entre fragmentos, \
algunos requisitos pueden estar duplicados o casi duplicados (misma \
información expresada con palabras distintas).

Devuelve la lista consolidada: une los duplicados/casi-duplicados en una sola \
entrada (quedándote con la descripción más completa), pero conserva TODOS los \
requisitos distintos — no elimines ni resumas información que no sea \
estrictamente un duplicado. No inventes requisitos nuevos.

ATENCIÓN — duplicados con redacción distinta: dos requisitos del mismo `tipo` \
que se refieran al MISMO importe, plazo, porcentaje u obligación concreta son \
el MISMO requisito aunque estén redactados de forma muy distinta (uno más \
general/resumido y otro más detallado, o cada uno mencionando solo una parte \
del dato). Fusiónalos en una sola entrada SIEMPRE que compartan el mismo dato \
concreto (mismo importe en €, mismo %, mismo plazo, mismo grupo/subgrupo de \
clasificación, etc.), aunque la descripción textual no coincida. Quédate con la \
versión más completa y, si una de las entradas tiene `valor` y la otra no, \
conserva ese `valor`. Ejemplos típicos a fusionar: varias entradas sobre la \
misma aportación pública (construcción/explotación) citando la misma cifra; \
varias entradas sobre la misma garantía definitiva (mismo % y misma fase); \
varias entradas sobre la misma solvencia económica (mismo importe de referencia); \
varias entradas sobre la misma clasificación empresarial (mismo grupo/subgrupo/ \
categoría).

Presta especial atención a los criterios de adjudicación "sujetos a juicio de \
valor": deben quedar EXACTAMENTE los criterios numerados de su tabla (ni más \
ni menos), cada uno con su puntuación. Si encuentras varias entradas que en \
realidad describen aspectos o párrafos del "desarrollo" de UN MISMO criterio \
numerado (en vez de criterios independientes con puntuación propia), fusiónalas \
en una sola entrada para ese criterio, combinando sus descripciones y \
conservando la puntuación si alguna entrada la tiene."""


class RequisitosExtraidos(BaseModel):
    requisitos: list[Requisito] = Field(
        description="Lista completa de requisitos extraídos del pliego."
    )


def _leer_paginas(path: str) -> list[str]:
    with fitz.open(path) as doc:
        return [page.get_text() for page in doc]


def _agrupar_en_fragmentos(paginas: list[str], max_chars: int = 14000, solape_paginas: int = 2) -> list[str]:
    """
    Agrupa páginas consecutivas en fragmentos de hasta max_chars caracteres,
    solapando `solape_paginas` páginas entre fragmentos consecutivos para no
    perder requisitos que queden justo en el límite de un fragmento.
    """
    fragmentos = []
    n = len(paginas)
    i = 0
    while i < n:
        chunk = []
        total = 0
        j = i
        while j < n and (not chunk or total + len(paginas[j]) <= max_chars):
            chunk.append(paginas[j])
            total += len(paginas[j])
            j += 1
        fragmentos.append("\n".join(chunk))
        if j >= n:
            break
        i = max(j - solape_paginas, i + 1)
    return fragmentos


def extractor_agent(state: BidState) -> dict:
    """
    Nodo 1 del grafo.

    Lee el PDF, lo divide en fragmentos por páginas y extrae con GPT-4o
    una lista tipada de Requisito por fragmento. Al final consolida todos
    los fragmentos en una sola lista, eliminando duplicados del solape.
    """
    print(f"\n[Extractor Agent] Analizando pliego: {state['pliego_pdf']}")

    paginas = _leer_paginas(state["pliego_pdf"])
    texto_total = "".join(paginas)
    fragmentos = _agrupar_en_fragmentos(paginas)
    print(f"[Extractor Agent] PDF leído ({len(texto_total)} caracteres, {len(paginas)} páginas) "
          f"→ {len(fragmentos)} fragmentos. Extrayendo requisitos con GPT-4o...")

    llm = ChatOpenAI(model="gpt-4o", temperature=0, seed=42)
    structured_llm = llm.with_structured_output(RequisitosExtraidos)

    requisitos_brutos: list[Requisito] = []
    for idx, fragmento in enumerate(fragmentos, start=1):
        resultado = structured_llm.invoke([
            ("system", SYSTEM_PROMPT),
            ("human", f"[Fragmento {idx}/{len(fragmentos)} del pliego]\n\n{fragmento}"),
        ])
        print(f"  Fragmento {idx}/{len(fragmentos)}: {len(resultado.requisitos)} requisitos.")
        requisitos_brutos.extend(resultado.requisitos)

    print(f"[Extractor Agent] {len(requisitos_brutos)} requisitos brutos. Consolidando duplicados...")

    contexto = RequisitosExtraidos(requisitos=requisitos_brutos)
    consolidado = structured_llm.invoke([
        ("system", CONSOLIDACION_PROMPT),
        ("human", contexto.model_dump_json()),
    ])

    print(f"[Extractor Agent] Extraídos {len(consolidado.requisitos)} requisitos tras consolidar.")

    return {"requisitos": consolidado.requisitos}
