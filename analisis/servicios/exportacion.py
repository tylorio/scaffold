"""Filas del CSV para el análisis estadístico. Solo contiene códigos anónimos."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Iterable

from .conceptos import CONCEPTOS
from .idc import intervalo_wilson


@dataclass(frozen=True)
class RegistroParticipante:
    codigo: str
    fecha: str = ""
    n_fragmentos: int | None = None
    n_ia: int | None = None
    n_autores: int | None = None
    n_triviales: int | None = None
    idc_global: float | None = None
    theta: float | None = None
    lambda_: float | None = None
    m: int | None = None
    modelo_version: str = ""
    modelo_es_demo: bool | None = None
    conceptos: tuple = ()  # objetos con concepto, n_fragmentos, n_ia, idc, estado, reforzado


def _columnas() -> list[str]:
    columnas = [
        "codigo", "fecha_analisis", "n_fragmentos", "n_triviales", "n_autores",
        "idc_global", "idc_global_ic_inf", "idc_global_ic_sup", "theta",
        "lambda", "m", "modelo_version", "modelo_es_demo",
    ]
    for concepto in CONCEPTOS:
        columnas += [
            f"idc_{concepto}", f"idc_{concepto}_ic_inf", f"idc_{concepto}_ic_sup",
            f"n_{concepto}", f"estado_{concepto}", f"reforzado_{concepto}",
        ]
    return columnas + ["conceptos_reforzados"]


def _numero(valor: float | None) -> float | str:
    return "" if valor is None else round(valor, 4)


def _entero(valor: int | None) -> int | str:
    return "" if valor is None else valor


def _intervalo(prefijo: str, idc: float | None, n_ia: int | None, n: int | None) -> dict:
    inferior, superior = (
        (None, None) if idc is None else intervalo_wilson(n_ia, n) or (None, None)
    )
    return {f"{prefijo}_ic_inf": _numero(inferior), f"{prefijo}_ic_sup": _numero(superior)}


def _fila(registro: RegistroParticipante) -> dict:
    fila = {
        "codigo": registro.codigo,
        "fecha_analisis": registro.fecha,
        "n_fragmentos": _entero(registro.n_fragmentos),
        "n_triviales": _entero(registro.n_triviales),
        "n_autores": _entero(registro.n_autores),
        "idc_global": _numero(registro.idc_global),
        **_intervalo(
            "idc_global", registro.idc_global, registro.n_ia, registro.n_fragmentos
        ),
        "theta": _numero(registro.theta),
        "lambda": _numero(registro.lambda_),
        "m": _entero(registro.m),
        "modelo_version": registro.modelo_version,
        "modelo_es_demo": (
            "" if registro.modelo_es_demo is None else int(registro.modelo_es_demo)
        ),
    }
    for resultado in registro.conceptos:
        concepto = resultado.concepto
        fila[f"idc_{concepto}"] = _numero(resultado.idc)
        fila.update(_intervalo(
            f"idc_{concepto}", resultado.idc, resultado.n_ia, resultado.n_fragmentos
        ))
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
