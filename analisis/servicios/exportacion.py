"""CSV para el análisis estadístico.

Solo llevan códigos anónimos. Tampoco incluyen el código de las soluciones, que
puede traer nombres en comentarios, ni los hashes de commit, que en un repositorio
público llevan directo a su autor.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Iterable

from .conceptos import CONCEPTOS
from .idc import intervalo_wilson

COLUMNAS_ANALISIS = (
    "codigo", "analisis", "fase", "fecha", "concepto", "condicion", "comparable",
    "semilla", "n_fragmentos", "n_ia", "idc", "idc_ic_inf", "idc_ic_sup", "estado",
    "n_autores", "theta", "lambda", "m", "modelo_version", "modelo_es_demo",
    "version_reglas",
)
COLUMNAS_INTENTOS = (
    "codigo", "concepto", "condicion", "ejercicio", "intento", "fecha", "pasados",
    "total", "usa_concepto", "tuvo_error",
)
COLUMNAS_APERTURAS = ("codigo", "concepto", "condicion", "fecha")


@dataclass(frozen=True)
class RegistroParticipante:
    codigo: str
    fase: str = ""
    comparable: bool | None = None
    control: tuple = ()
    fecha: str = ""
    n_fragmentos: int | None = None
    n_ia: int | None = None
    n_autores: int | None = None
    n_triviales: int | None = None
    idc_global: float | None = None
    indice_historial: float | None = None
    version_reglas: str = ""
    theta: float | None = None
    lambda_: float | None = None
    m: int | None = None
    modelo_version: str = ""
    modelo_es_demo: bool | None = None
    conceptos: tuple = ()  # objetos con concepto, n_fragmentos, n_ia, idc, estado, reforzado


def _columnas() -> list[str]:
    columnas = [
        "codigo", "fase", "comparable", "fecha_analisis", "n_fragmentos",
        "n_triviales", "n_autores", "idc_global", "idc_global_ic_inf", "idc_global_ic_sup",
        "indice_historial", "theta", "lambda", "m", "modelo_version", "modelo_es_demo",
        "version_reglas",
    ]
    for concepto in CONCEPTOS:
        columnas += [
            f"idc_{concepto}", f"idc_{concepto}_ic_inf", f"idc_{concepto}_ic_sup",
            f"n_{concepto}", f"estado_{concepto}", f"reforzado_{concepto}",
        ]
    return columnas + ["conceptos_reforzados", "conceptos_control"]


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
        "fase": registro.fase,
        "comparable": "" if registro.comparable is None else int(registro.comparable),
        "conceptos_control": ";".join(registro.control),
        "fecha_analisis": registro.fecha,
        "n_fragmentos": _entero(registro.n_fragmentos),
        "n_triviales": _entero(registro.n_triviales),
        "n_autores": _entero(registro.n_autores),
        "idc_global": _numero(registro.idc_global),
        **_intervalo(
            "idc_global", registro.idc_global, registro.n_ia, registro.n_fragmentos
        ),
        "indice_historial": _numero(registro.indice_historial),
        "version_reglas": registro.version_reglas,
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


def csv_de_filas(columnas: Iterable[str], filas: Iterable[dict]) -> str:
    salida = io.StringIO(newline="")
    escritor = csv.DictWriter(salida, fieldnames=list(columnas), restval="")
    escritor.writeheader()
    escritor.writerows(filas)
    return salida.getvalue()


def generar_csv(registros: Iterable[RegistroParticipante]) -> str:
    """Una fila por participante, con su último análisis."""
    return csv_de_filas(_columnas(), (_fila(r) for r in registros))


def generar_csv_analisis(filas: Iterable[dict]) -> str:
    """Una fila por análisis y concepto: es la tabla para comparar pre y post."""
    return csv_de_filas(COLUMNAS_ANALISIS, (
        {
            **fila,
            "idc": _numero(fila["idc"]),
            **_intervalo("idc", fila["idc"], fila["n_ia"], fila["n_fragmentos"]),
        }
        for fila in filas
    ))
