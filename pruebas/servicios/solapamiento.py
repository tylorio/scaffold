"""Alarma de solapamiento entre la prueba y el material de refuerzo (D21).

Si un ejercicio del refuerzo se parece demasiado a un ítem de las formas A o B, la
mejora en el postest puede ser memoria y no aprendizaje. Esto no decide nada: lista
pares sospechosos para que el investigador y los jueces los revisen a mano.
"""
from __future__ import annotations

import ast
import io
import keyword
import re
import tokenize
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .banco import Banco

# Calibrado con el primer banco real (2026-11-23), como pidió el asesor en P10: los
# tres solapamientos que él identificó entre la prueba y las plantillas del
# prototipo dan entre 0,20 y 0,29 de parecido de enunciado, y el resto de los pares,
# 0,15 como máximo. Con 0,5 no se detectaba ninguno. Queda bajo a propósito: marca
# de más y la decisión la toman los jueces. Revisarlo con los bloques de recursión
# y excepciones.
UMBRAL_ENUNCIADO = 0.2  # confirmado por el asesor en D22, como filtro y no como veredicto
# Segunda alarma (D22): si la solución de un bloque, cambiando nombres, sirve para un
# ítem. Calibrada como la primera: los tres solapamientos conocidos del prototipo dan
# entre 0,32 y 0,57, y el umbral queda un poco por debajo del menor. Coincide con el
# valor provisional del asesor. Marca también pares sin solapamiento (hasta 0,39):
# los decide el juez.
UMBRAL_SOLUCION = 0.3


@dataclass(frozen=True)
class MaterialRefuerzo:
    id: str
    enunciado: str
    codigo: str | None = None  # el del ejemplo, o la solución de referencia del ejercicio


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


_SIN_PESO = {
    tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
    tokenize.ENCODING, tokenize.ENDMARKER,
}


def _tokens(codigo: str) -> list[str]:
    """Tokens con los nombres como ID y los literales como LIT: un isomorfo da lo mismo."""
    salida = []
    for token in tokenize.generate_tokens(io.StringIO(codigo).readline):
        if token.type in _SIN_PESO:
            continue
        if token.type == tokenize.NAME:
            salida.append(token.string if keyword.iskeyword(token.string) else "ID")
        elif token.type in (tokenize.NUMBER, tokenize.STRING):
            salida.append("LIT")
        else:
            salida.append(token.string)
    return salida


def _trigramas(codigo: str) -> set[tuple[str, ...]]:
    tokens = _tokens(codigo)
    return {tuple(tokens[i:i + 3]) for i in range(len(tokens) - 2)}


def similitud_soluciones(a: str, b: str) -> float:
    """Jaccard sobre trigramas de tokens normalizados (D22). 0 si alguno no es Python."""
    try:
        ast.parse(a)
        ast.parse(b)
        ta, tb = _trigramas(a), _trigramas(b)
    except (SyntaxError, ValueError, RecursionError, tokenize.TokenError):
        return 0.0
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


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


def soluciones_de_carpeta(carpeta: Path) -> dict[str, str]:
    """Código de cada función y clase de los archivos de soluciones, por su nombre."""
    soluciones = {}
    for ruta in sorted(Path(carpeta).glob("*.py")):
        codigo = ruta.read_text(encoding="utf-8")
        for nodo in ast.parse(codigo).body:
            if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)):
                soluciones[nodo.name] = ast.get_source_segment(codigo, nodo)
    return soluciones


def material_de_refuerzo(
    bloques: list[dict] | None = None, soluciones: dict[str, str] | None = None,
) -> list[MaterialRefuerzo]:
    """Ejemplos resueltos y ejercicios de los bloques de refuerzo (D20).

    Sin bloques, usa los de ejemplo. Cada pieza se nombra `bloque/ejemplo-n` o
    `bloque/ejercicio`. Con `soluciones` (nombre de función → código), cada
    ejercicio lleva su solución de referencia para la alarma de soluciones.
    """
    soluciones = soluciones or {}
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
                soluciones.get(ejercicio["funcion"]),
            ))
    return material


# Respuestas posibles de cada juez para cada par (D23). Basta con que un juez diga
# "misma tarea" para reemplazar el ejercicio del bloque.
RESPUESTAS_JUECES = ("misma_tarea", "misma_habilidad", "sin_relacion")


def ficha_para_jueces(pares: list[ParSospechoso], n_jueces: int = 3) -> str:
    """CSV con un par por fila y una columna por juez, para responder con D23."""
    import csv

    salida = io.StringIO(newline="")
    columnas = ["item_prueba", "material", "motivo", "similitud"] + [
        f"juez_{n}" for n in range(1, n_jueces + 1)
    ]
    escritor = csv.writer(salida)
    escritor.writerow(columnas)
    for par in pares:
        escritor.writerow([par.item_prueba, par.material, par.motivo, par.similitud]
                          + [""] * n_jueces)
    escritor.writerow([])
    escritor.writerow([f"Respuestas: {', '.join(RESPUESTAS_JUECES)}. Con un solo "
                       "'misma_tarea' se reemplaza el ejercicio del bloque (D23)."])
    return salida.getvalue()
