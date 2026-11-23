"""Banco de refuerzo en bloques (D20): 8 por concepto, 2 por semana durante 4 semanas.

Cada bloque trae una explicación breve, un ejemplo resuelto y ejercicios graduados con
casos de prueba. Se escribe en archivos JSON (uno por bloque) que se cargan al portal;
no se edita en línea. Cambiar el contenido exige subir la versión, y la versión nueva
debe validarse otra vez (RF-22).

El material de `contenido.PLANTILLAS` sirve como banco de ejemplo: un bloque por
concepto, en la semana 1.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from analisis.servicios.conceptos import CONCEPTOS, NOMBRES_CONCEPTOS

from .contenido import PLANTILLAS, CasoPrueba, Ejemplo, Ejercicio

SEMANAS = 4
BLOQUES_POR_SEMANA = 2


class BloqueInvalido(Exception):
    pass


# Los bloques de ejemplo salen de las plantillas del prototipo, y varios de sus
# ejercicios se solapan con la prueba real. Sirven para desarrollo y pruebas, nunca
# para los estudiantes (orientación del asesor, 2026-11-22).
SUFIJO_EJEMPLO = "-ejemplo"


def es_de_ejemplo(bloque_id: str) -> bool:
    return bloque_id.endswith(SUFIJO_EJEMPLO)


def introduccion(concepto: str) -> str:
    """Igual para todos: no cita el análisis ni el IDC del estudiante (D11)."""
    return (
        f"Este material te ayuda a practicar {NOMBRES_CONCEPTOS[concepto].lower()} por tu "
        f"cuenta. Cada semana se abren {BLOQUES_POR_SEMANA} bloques nuevos, cada uno con una "
        "explicación, un ejemplo resuelto y ejercicios que se corrigen solos."
    )


def semana_de(hoy: date, inicio: date | None) -> int:
    """Semana de la intervención en curso: 0 antes de empezar, 1 el primer día.

    No se detiene en 4: pasada la intervención, todo lo liberado sigue abierto.
    """
    if inicio is None or hoy < inicio:
        return 0
    return (hoy - inicio).days // 7 + 1


def inicio_de_semana(inicio: date, semana: int) -> date:
    return inicio + timedelta(weeks=semana - 1)


def ranuras_faltantes(bloques: list[tuple[str, int, int]]) -> dict[str, list[tuple[int, int]]]:
    """Por concepto, las (semana, orden) del plan de D20 que no tienen bloque."""
    presentes = set(bloques)
    return {
        concepto: [
            (semana, orden)
            for semana in range(1, SEMANAS + 1)
            for orden in range(1, BLOQUES_POR_SEMANA + 1)
            if (concepto, semana, orden) not in presentes
        ]
        for concepto in CONCEPTOS
    }


@dataclass(frozen=True)
class Bloque:
    id: str
    concepto: str
    semana: int
    orden: int
    version: int
    titulo: str
    explicacion: tuple[str, ...]
    ejemplos: tuple[Ejemplo, ...]
    ejercicios: tuple[Ejercicio, ...]

    @property
    def nombre_concepto(self) -> str:
        return NOMBRES_CONCEPTOS[self.concepto]

    def ejercicio(self, ejercicio_id: str) -> Ejercicio | None:
        return next((e for e in self.ejercicios if e.id == ejercicio_id), None)


def huella(contenido: dict) -> str:
    return hashlib.sha256(
        json.dumps(contenido, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# Nivel de cada ejercicio, en el orden en que deben aparecer (D20).
NIVELES = ("Fácil", "Medio", "Difícil")
_NIVEL = {"facil": "Fácil", "fácil": "Fácil", "medio": "Medio", "dificil": "Difícil",
          "difícil": "Difícil"}
EJERCICIOS_POR_BLOQUE = 3


def normalizar(contenido: Any, id_archivo: str | None = None) -> Any:
    """Lleva un bloque al formato interno. Acepta también el formato de autoría.

    En el formato de autoría (el de los bloques del asesor) el `id` sale del nombre
    del archivo, la explicación es un texto con párrafos separados por una línea en
    blanco, hay un solo `ejemplo` con `comentario`, y los ejercicios no tienen
    título. El contenido no cambia: solo su forma.
    """
    if not isinstance(contenido, dict):
        return contenido
    bloque = dict(contenido)
    if "id" not in bloque and id_archivo:
        bloque["id"] = id_archivo
    if isinstance(bloque.get("explicacion"), str):
        bloque["explicacion"] = [
            p.strip() for p in bloque["explicacion"].split("\n\n") if p.strip()
        ]
    if "ejemplos" not in bloque and isinstance(bloque.get("ejemplo"), dict):
        bloque["ejemplos"] = [bloque.pop("ejemplo")]
    if isinstance(bloque.get("ejemplos"), list):
        bloque["ejemplos"] = [
            {
                "titulo": e.get("titulo", ""), "enunciado": e.get("enunciado", ""),
                "codigo": e.get("codigo", ""), "salida": e.get("salida", ""),
                "explicacion": e.get("explicacion", e.get("comentario", "")),
            } if isinstance(e, dict) else e
            for e in bloque["ejemplos"]
        ]
    if isinstance(bloque.get("ejercicios"), list):
        bloque["ejercicios"] = [
            {
                **e, "titulo": e.get("titulo", ""),
                "nivel": _NIVEL.get(str(e.get("nivel", "")).strip().lower(), e.get("nivel")),
            } if isinstance(e, dict) else e
            for e in bloque["ejercicios"]
        ]
    return bloque


def validar(contenido: Any) -> list[str]:
    if not isinstance(contenido, dict):
        return ["El bloque debe ser un objeto JSON."]
    errores = []
    ident = contenido.get("id", "?")
    faltan = {"id", "concepto", "semana", "orden", "version", "titulo", "explicacion",
              "ejemplos", "ejercicios"} - contenido.keys()
    if faltan:
        return [f"{ident}: faltan {', '.join(sorted(faltan))}."]
    if contenido["concepto"] not in CONCEPTOS:
        errores.append(f"{ident}: concepto desconocido.")
    if contenido["semana"] not in range(1, SEMANAS + 1):
        errores.append(f"{ident}: la semana debe estar entre 1 y {SEMANAS}.")
    if contenido["orden"] not in range(1, BLOQUES_POR_SEMANA + 1):
        errores.append(f"{ident}: el orden debe ser 1 o 2.")
    if not isinstance(contenido["version"], int) or contenido["version"] < 1:
        errores.append(f"{ident}: la versión debe ser un entero positivo.")
    if not contenido["ejemplos"]:
        errores.append(f"{ident}: falta el ejemplo resuelto.")
    ejercicios = contenido["ejercicios"]
    if len(ejercicios) != EJERCICIOS_POR_BLOQUE:
        errores.append(f"{ident}: debe tener {EJERCICIOS_POR_BLOQUE} ejercicios (D20).")
    ids = [e.get("id") for e in ejercicios if isinstance(e, dict)]
    if len(ids) != len(set(ids)) or len(ids) != len(ejercicios):
        errores.append(f"{ident}: los ejercicios deben tener id distintos.")
    elif [e.get("nivel") for e in ejercicios] != list(NIVELES)[:len(ejercicios)]:
        errores.append(f"{ident}: los niveles van en orden: fácil, medio y difícil.")
    for e in ejercicios:
        if not isinstance(e, dict):
            continue
        ruta = f"{ident}/{e.get('id')}"
        sin = {"id", "nivel", "enunciado", "funcion", "plantilla", "casos"} - e.keys()
        if sin:
            errores.append(f"{ruta}: faltan {', '.join(sorted(sin))}.")
            continue
        if not str(e["id"]) or len(str(e["id"])) > 20:
            errores.append(f"{ruta}: el id debe tener entre 1 y 20 caracteres.")
        if not str(e["funcion"]).isidentifier():
            errores.append(f"{ruta}: el nombre de la función no es válido.")
        if not e["casos"]:
            errores.append(f"{ruta}: sin casos de prueba.")
        for n, caso in enumerate(e["casos"], 1):
            if not isinstance(caso, dict) or not isinstance(caso.get("args"), list):
                errores.append(f"{ruta}, caso {n}: args debe ser una lista.")
            elif "esperado" not in caso and not caso.get("lanza"):
                errores.append(f"{ruta}, caso {n}: falta esperado o lanza.")
    return errores


def desde_json(contenido: dict) -> Bloque:
    return Bloque(
        id=contenido["id"],
        concepto=contenido["concepto"],
        semana=contenido["semana"],
        orden=contenido["orden"],
        version=contenido["version"],
        titulo=contenido["titulo"],
        explicacion=tuple(contenido["explicacion"]),
        ejemplos=tuple(Ejemplo(**e) for e in contenido["ejemplos"]),
        ejercicios=tuple(
            Ejercicio(
                id=e["id"], nivel=e["nivel"], titulo=e.get("titulo", ""),
                enunciado=e["enunciado"],
                plantilla=e["plantilla"], funcion=e["funcion"],
                casos=tuple(
                    CasoPrueba(tuple(c["args"]), c.get("esperado"), c.get("lanza"))
                    for c in e["casos"]
                ),
            )
            for e in contenido["ejercicios"]
        ),
    )


def cargar_carpeta(carpeta: Path) -> list[dict]:
    """Lee y valida todos los bloques `*.json` de una carpeta (y sus subcarpetas)."""
    bloques, errores = [], []
    for ruta in sorted(Path(carpeta).rglob("*.json")):
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except ValueError as error:
            errores.append(f"{ruta.name}: no es JSON válido ({error}).")
            continue
        contenido = normalizar(contenido, ruta.stem)
        errores.extend(validar(contenido))
        bloques.append(contenido)
    ids = [b.get("id") for b in bloques if isinstance(b, dict)]
    if len(ids) != len(set(ids)):
        errores.append("Hay bloques con el mismo id.")
    if errores:
        raise BloqueInvalido(" ".join(errores))
    return bloques


def bloques_de_ejemplo() -> list[dict]:
    """El material de las plantillas como un bloque por concepto, en la semana 1."""
    bloques = []
    for concepto, plantilla in PLANTILLAS.items():
        bloques.append({
            "id": f"{concepto}{SUFIJO_EJEMPLO}",
            "concepto": concepto,
            "semana": 1,
            "orden": 1,
            "version": 1,
            "titulo": f"{NOMBRES_CONCEPTOS[concepto]}: bloque de ejemplo",
            "explicacion": list(plantilla.explicacion),
            "ejemplos": [vars(e) for e in plantilla.ejemplos],
            "ejercicios": [
                {
                    "id": e.id, "nivel": e.nivel, "titulo": e.titulo, "enunciado": e.enunciado,
                    "plantilla": e.plantilla, "funcion": e.funcion,
                    "casos": [
                        {"args": list(c.args), "esperado": c.esperado, "lanza": c.lanza}
                        for c in e.casos
                    ],
                }
                for e in plantilla.ejercicios
            ],
        })
    return bloques
