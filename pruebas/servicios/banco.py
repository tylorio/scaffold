"""Banco de la prueba de desempeño: formas A y B con los ítems T1–T3 (plan 8.3.2).

El banco real no se versiona: vive en el almacén local (`datos/banco_prueba/`) y
nunca va al portal (D21), porque los estudiantes no deben poder verlo. En el
repositorio solo hay un banco de ejemplo.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION

FORMAS = ("A", "B")
CONCEPTO_DE_ITEM = {"T1": RECURSION, "T2": ESTRUCTURAS, "T3": EXCEPCIONES}


class BancoInvalido(Exception):
    """El banco no tiene la forma esperada o sus soluciones de referencia fallan."""


@dataclass(frozen=True)
class Caso:
    args: tuple
    esperado: Any = None
    lanza: str | None = None  # nombre de la excepción que debe lanzarse


@dataclass(frozen=True)
class ItemPrueba:
    item: str  # T1, T2 o T3
    concepto: str
    enunciado: str
    funcion: str
    referencia: str  # solución de referencia: base de cc_ref y lin_ref (D1)
    casos: tuple[Caso, ...]


@dataclass(frozen=True)
class Banco:
    forma: str
    version: str
    items: tuple[ItemPrueba, ...]

    def item(self, nombre: str) -> ItemPrueba:
        return next(i for i in self.items if i.item == nombre)


def _caso(dato: dict) -> Caso:
    return Caso(tuple(dato["args"]), dato.get("esperado"), dato.get("lanza"))


def cargar_banco(ruta: Path) -> Banco:
    try:
        dato = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return Banco(
            forma=dato["forma"],
            version=dato["version"],
            items=tuple(
                ItemPrueba(
                    item=i["item"], concepto=i["concepto"], enunciado=i["enunciado"],
                    funcion=i["funcion"], referencia=i["referencia"],
                    casos=tuple(_caso(c) for c in i["casos"]),
                )
                for i in dato["items"]
            ),
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise BancoInvalido(f"No se pudo leer {ruta}: {error}") from error


def cargar_bancos(carpeta: Path) -> dict[str, Banco]:
    """Lee `forma_A.json` y `forma_B.json` y comprueba que son formas paralelas (D16)."""
    carpeta = Path(carpeta)
    bancos = {forma: cargar_banco(carpeta / f"forma_{forma}.json") for forma in FORMAS}
    errores = []
    for forma, banco in bancos.items():
        if banco.forma != forma:
            errores.append(f"forma_{forma}.json declara la forma {banco.forma}.")
        nombres = [i.item for i in banco.items]
        if sorted(nombres) != sorted(CONCEPTO_DE_ITEM):
            errores.append(f"La forma {forma} debe tener T1, T2 y T3 una vez cada uno.")
        for item in banco.items:
            if CONCEPTO_DE_ITEM.get(item.item) != item.concepto:
                errores.append(f"{forma}/{item.item} debe evaluar {CONCEPTO_DE_ITEM.get(item.item)}.")
            if not item.casos:
                errores.append(f"{forma}/{item.item} no tiene casos de prueba.")
    if errores:
        raise BancoInvalido(" ".join(errores))
    return bancos
