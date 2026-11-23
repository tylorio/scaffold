"""Alarma de solapamiento entre la prueba y el material de refuerzo (D21).

Si un ejercicio del refuerzo se parece demasiado a un ítem de las formas A o B, la
mejora en el postest puede ser memoria y no aprendizaje. Esto no decide nada: lista
pares sospechosos para que el investigador y los jueces los revisen a mano.
"""
from __future__ import annotations

import ast
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from .banco import Banco

# [PENDIENTE] Provisionales: ajustarlos con los primeros bancos reales.
UMBRAL_ENUNCIADO = 0.5
UMBRAL_SOLUCION = 0.8


@dataclass(frozen=True)
class MaterialRefuerzo:
    id: str
    enunciado: str
    codigo: str | None = None  # los ejemplos resueltos traen código; los ejercicios, no


@dataclass(frozen=True)
class ParSospechoso:
    item_prueba: str  # p. ej. "A/T2"
    material: str
    motivo: str  # "enunciado" o "solucion"
    similitud: float


def _palabras(texto: str) -> set[str]:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return {p for p in re.findall(r"[a-z]+", sin_tildes) if len(p) > 3}


def similitud_enunciados(a: str, b: str) -> float:
    """Jaccard sobre las palabras de más de 3 letras, sin tildes ni mayúsculas."""
    pa, pb = _palabras(a), _palabras(b)
    return len(pa & pb) / len(pa | pb) if pa | pb else 0.0


def _estructura(codigo: str) -> list[str]:
    """Secuencia de tipos de nodo: ignora nombres y literales, que cambian en un isomorfo."""
    return [type(nodo).__name__ for nodo in ast.walk(ast.parse(codigo))]


def similitud_soluciones(a: str, b: str) -> float:
    try:
        return SequenceMatcher(None, _estructura(a), _estructura(b), autojunk=False).ratio()
    except (SyntaxError, ValueError, RecursionError):
        return 0.0


def pares_sospechosos(
    bancos: dict[str, Banco],
    material: Iterable[MaterialRefuerzo],
    umbral_enunciado: float = UMBRAL_ENUNCIADO,
    umbral_solucion: float = UMBRAL_SOLUCION,
) -> list[ParSospechoso]:
    material = list(material)
    pares = []
    for forma, banco in sorted(bancos.items()):
        for item in banco.items:
            nombre = f"{forma}/{item.item}"
            for m in material:
                enunciado = similitud_enunciados(item.enunciado, m.enunciado)
                if enunciado >= umbral_enunciado:
                    pares.append(ParSospechoso(nombre, m.id, "enunciado", round(enunciado, 3)))
                if m.codigo:
                    solucion = similitud_soluciones(item.referencia, m.codigo)
                    if solucion >= umbral_solucion:
                        pares.append(ParSospechoso(nombre, m.id, "solucion", round(solucion, 3)))
    return sorted(pares, key=lambda p: -p.similitud)


def material_de_refuerzo(bloques: list[dict] | None = None) -> list[MaterialRefuerzo]:
    """Ejemplos resueltos y ejercicios de los bloques de refuerzo (D20).

    Sin bloques, usa los de ejemplo. Cada pieza se nombra `bloque/ejemplo-n` o
    `bloque/ejercicio`.
    """
    from refuerzo.servicios.banco import bloques_de_ejemplo

    material = []
    for bloque in bloques if bloques is not None else bloques_de_ejemplo():
        for n, ejemplo in enumerate(bloque["ejemplos"], 1):
            material.append(MaterialRefuerzo(
                f"{bloque['id']}/ejemplo-{n}", f"{ejemplo['titulo']}. {ejemplo['enunciado']}",
                ejemplo["codigo"],
            ))
        for ejercicio in bloque["ejercicios"]:
            material.append(MaterialRefuerzo(
                f"{bloque['id']}/{ejercicio['id']}",
                f"{ejercicio['titulo']}. {ejercicio['enunciado']}",
            ))
    return material
