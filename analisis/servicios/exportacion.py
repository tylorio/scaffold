"""Filas del CSV para el análisis estadístico. Solo contiene códigos anónimos."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Iterable

from .conceptos import CONCEPTOS


@dataclass(frozen=True)
class RegistroParticipante:
    codigo: str
    fecha: str = ""
    n_fragmentos: int | None = None
    idc_global: float | None = None
    theta: float | None = None
    lambda_: float | None = None
    m: int | None = None
    modelo_version: str = ""
    modelo_es_demo: bool | None = None
    conceptos: tuple = ()  # objetos con concepto, n_fragmentos, idc, estado, reforzado


def _columnas() -> list[str]:
    columnas = [
        "codigo", "fecha_analisis", "n_fragmentos", "idc_global", "theta",
        "lambda", "m", "modelo_version", "modelo_es_demo",
    ]
    for concepto in CONCEPTOS:
        columnas += [
            f"idc_{concepto}", f"n_{concepto}", f"estado_{concepto}",
            f"reforzado_{concepto}",
        ]
    return columnas + ["conceptos_reforzados"]


def _numero(valor: float | None) -> float | str:
    return "" if valor is None else round(valor, 4)


def _fila(registro: RegistroParticipante) -> dict:
    fila = {
        "codigo": registro.codigo,
        "fecha_analisis": registro.fecha,
        "n_fragmentos": "" if registro.n_fragmentos is None else registro.n_fragmentos,
        "idc_global": _numero(registro.idc_global),
        "theta": _numero(registro.theta),
        "lambda": _numero(registro.lambda_),
        "m": "" if registro.m is None else registro.m,
        "modelo_version": registro.modelo_version,
        "modelo_es_demo": (
            "" if registro.modelo_es_demo is None else int(registro.modelo_es_demo)
        ),
    }
    for resultado in registro.conceptos:
        concepto = resultado.concepto
        fila[f"idc_{concepto}"] = _numero(resultado.idc)
        fila[f"n_{concepto}"] = resultado.n_fragmentos
        fila[f"estado_{concepto}"] = resultado.estado
        fila[f"reforzado_{concepto}"] = int(resultado.reforzado)
    fila["conceptos_reforzados"] = ";".join(
        c.concepto for c in registro.conceptos if c.reforzado
    )
    return fila


def generar_csv(registros: Iterable[RegistroParticipante]) -> str:
    salida = io.StringIO(newline="")
    escritor = csv.DictWriter(salida, fieldnames=_columnas(), restval="")
    escritor.writeheader()
    escritor.writerows(_fila(r) for r in registros)
    return salida.getvalue()
