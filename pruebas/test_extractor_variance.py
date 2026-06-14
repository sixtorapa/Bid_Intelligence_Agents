"""
Script de prueba: ejecuta el extractor_agent sobre el PDF de ejemplo y vuelca
el detalle (requisitos brutos por fragmento + consolidado final) a un JSON,
para poder comparar entre ejecuciones y diagnosticar la varianza en el
número de requisitos extraídos.
"""
import json
import sys
from dotenv import load_dotenv

load_dotenv()

from state import BidState, Requisito
from extractor import _leer_paginas, _agrupar_en_fragmentos, SYSTEM_PROMPT, CONSOLIDACION_PROMPT, RequisitosExtraidos
from langchain_openai import ChatOpenAI

PDF = "pruebas/Memoria Justificativa Concesion de Obras.pdf"


def run(tag: str):
    paginas = _leer_paginas(PDF)
    fragmentos = _agrupar_en_fragmentos(paginas)
    print(f"[{tag}] {len(fragmentos)} fragmentos")

    llm = ChatOpenAI(model="gpt-4o", temperature=0, seed=42)
    structured_llm = llm.with_structured_output(RequisitosExtraidos)

    requisitos_brutos = []
    por_fragmento = []
    for idx, fragmento in enumerate(fragmentos, start=1):
        resultado = structured_llm.invoke([
            ("system", SYSTEM_PROMPT),
            ("human", f"[Fragmento {idx}/{len(fragmentos)} del pliego]\n\n{fragmento}"),
        ])
        print(f"  [{tag}] Fragmento {idx}/{len(fragmentos)}: {len(resultado.requisitos)} requisitos")
        por_fragmento.append(len(resultado.requisitos))
        requisitos_brutos.extend(resultado.requisitos)

    print(f"[{tag}] Total bruto: {len(requisitos_brutos)}")

    contexto = RequisitosExtraidos(requisitos=requisitos_brutos)
    consolidado = structured_llm.invoke([
        ("system", CONSOLIDACION_PROMPT),
        ("human", contexto.model_dump_json()),
    ])

    print(f"[{tag}] Total consolidado: {len(consolidado.requisitos)}")

    out = {
        "por_fragmento": por_fragmento,
        "total_bruto": len(requisitos_brutos),
        "total_consolidado": len(consolidado.requisitos),
        "brutos": [r.model_dump() for r in requisitos_brutos],
        "consolidados": [r.model_dump() for r in consolidado.requisitos],
    }
    with open(f"pruebas/extraccion_{tag}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "run"
    run(tag)
