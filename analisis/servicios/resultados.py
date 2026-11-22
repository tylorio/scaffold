"""Archivo `resultados-v1`: lo único que viaja del núcleo local al portal (05 §3.6).

Lleva códigos anónimos, IDC agregados y la asignación congelada. Nunca código,
rutas, URLs, correos ni hashes de commit (ESC-06). Dos filtros independientes lo
garantizan: una lista cerrada de claves (`validar_documento`) y una revisión de
cada texto (`validar_sin_datos_prohibidos`). El exportador y el importador aplican
los dos.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from .conceptos import CONCEPTOS
from .idc import CASO_A, CASO_B, CASO_C, DATOS_INSUFICIENTES, DEBIL, MODOS, NO_DEBIL, ORDENES

ESQUEMA = "resultados-v1"
PATRON_CODIGO = re.compile(r"^[A-Z]{1,3}\d{2,4}$")
CONDICIONES = ("reforzado", "control", "sin_asignar")

NUMERO = (int, float)
_ESTRUCTURA = {
    "documento": {
        "esquema": str, "generado": str, "sistema": "sistema",
        "congelacion": "congelacion", "participantes": ["participante"],
    },
    "sistema": {"version": str},
    "congelacion": {"fecha": str, "modo": str, "semilla_base": int, "tamano_bloque": int},
    "participante": {
        "codigo": str, "analisis_id": str, "fecha": str, "versiones": "versiones",
        "parametros": "parametros", "n_fragmentos": int, "n_ia": int,
        "idc_global": (*NUMERO, type(None)), "ic95": (list, type(None)),
        "conceptos": ["concepto"], "asignacion": "asignacion",
    },
    "versiones": {"modelo": str, "modelo_es_demo": bool, "reglas": str, "rasgos": str},
    "parametros": {"theta": NUMERO, "lambda": NUMERO, "m": int},
    "concepto": {
        "concepto": str, "n": int, "n_ia": int, "idc": (*NUMERO, type(None)),
        "ic95": (list, type(None)), "estado": str, "condicion": str,
    },
    "asignacion": {
        "semilla": int, "debiles": list, "reforzados": list, "control": list,
        "caso": str, "orden": str, "modo": str, "congelada_en": str,
    },
}

_PROHIBIDO = {
    "una URL": re.compile(r"[a-zA-Z][\w+.-]*://|\bwww\."),
    "un correo": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "una ruta": re.compile(r"[A-Za-z]:[\\/]|\\|(^|[\s'\"])/[\w.-]+/|\.py\b"),
    "un hash": re.compile(r"\b[0-9a-fA-F]{32,}\b"),
    "código": re.compile(r"\bdef \w+\s*\(|\bimport \w+|\bclass \w+\s*[:(]|\n[ \t]+\S"),
}


def _revisar(dato: Any, tipo: str, ruta: str, errores: list[str]) -> None:
    esperado = _ESTRUCTURA[tipo]
    if not isinstance(dato, dict):
        errores.append(f"{ruta}: debe ser un objeto.")
        return
    for clave in dato.keys() - esperado.keys():
        errores.append(f"{ruta}.{clave}: campo no permitido.")
    for clave, forma in esperado.items():
        if clave not in dato:
            errores.append(f"{ruta}.{clave}: falta.")
            continue
        valor, donde = dato[clave], f"{ruta}.{clave}"
        if isinstance(forma, str):
            _revisar(valor, forma, donde, errores)
        elif isinstance(forma, list):
            if not isinstance(valor, list):
                errores.append(f"{donde}: debe ser una lista.")
            else:
                for i, elemento in enumerate(valor):
                    _revisar(elemento, forma[0], f"{donde}[{i}]", errores)
        elif isinstance(valor, bool) and bool not in (forma if isinstance(forma, tuple) else (forma,)):
            errores.append(f"{donde}: tipo inválido.")
        elif not isinstance(valor, forma):
            errores.append(f"{donde}: tipo inválido.")


def _valores(errores: list[str], ruta: str, valor: Any, permitidos) -> None:
    if valor not in permitidos:
        errores.append(f"{ruta}: valor no permitido ({valor!r}).")


def validar_documento(documento: Any) -> list[str]:
    """Estructura cerrada y valores dentro de los dominios del estudio."""
    errores: list[str] = []
    _revisar(documento, "documento", "resultados", errores)
    if errores:
        return errores
    if documento["esquema"] != ESQUEMA:
        errores.append(f"resultados.esquema: se esperaba {ESQUEMA}.")
    _valores(errores, "congelacion.modo", documento["congelacion"]["modo"], MODOS)
    for i, p in enumerate(documento["participantes"]):
        ruta = f"participantes[{i}]"
        if not PATRON_CODIGO.match(p["codigo"]):
            errores.append(f"{ruta}.codigo: no es un código anónimo.")
        try:
            uuid.UUID(p["analisis_id"])
        except ValueError:
            errores.append(f"{ruta}.analisis_id: no es un UUID.")
        for j, c in enumerate(p["conceptos"]):
            _valores(errores, f"{ruta}.conceptos[{j}].concepto", c["concepto"], CONCEPTOS)
            _valores(errores, f"{ruta}.conceptos[{j}].estado", c["estado"],
                     (DEBIL, NO_DEBIL, DATOS_INSUFICIENTES))
            _valores(errores, f"{ruta}.conceptos[{j}].condicion", c["condicion"], CONDICIONES)
        a = p["asignacion"]
        _valores(errores, f"{ruta}.asignacion.caso", a["caso"], (CASO_A, CASO_B, CASO_C))
        _valores(errores, f"{ruta}.asignacion.orden", a["orden"], ORDENES)
        _valores(errores, f"{ruta}.asignacion.modo", a["modo"], MODOS)
        for lista in ("debiles", "reforzados", "control"):
            for concepto in a[lista]:
                _valores(errores, f"{ruta}.asignacion.{lista}", concepto, CONCEPTOS)
    return errores


def _textos(dato: Any, ruta: str):
    if isinstance(dato, str):
        yield ruta, dato
    elif isinstance(dato, dict):
        for clave, valor in dato.items():
            yield f"{ruta}.<clave>", str(clave)
            yield from _textos(valor, f"{ruta}.{clave}")
    elif isinstance(dato, list):
        for i, valor in enumerate(dato):
            yield from _textos(valor, f"{ruta}[{i}]")


def validar_sin_datos_prohibidos(documento: Any) -> list[str]:
    """Cualquier texto que parezca URL, correo, ruta, hash o código (ESC-06)."""
    errores = []
    for ruta, texto in _textos(documento, "resultados"):
        for nombre, patron in _PROHIBIDO.items():
            if patron.search(texto):
                errores.append(f"{ruta}: parece {nombre}.")
    return errores
