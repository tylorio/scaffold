"""CSV de puntajes T para la base codificada (D17, parte T).

No lleva `reforzado`, `caso`, `orden` ni la semilla: los calificadores no deben
conocer la asignación (D3). La unión con la asignación y con Q se hace después de
cerrar la calificación.
"""
from __future__ import annotations

from typing import Iterable

from analisis.servicios.exportacion import csv_de_filas

COLUMNAS_PUNTAJES = (
    "participante", "concepto", "momento", "forma", "item", "T_pct",
    "casos_pasados", "casos_total", "cc_sol", "cc_ref", "lin_sol", "lin_ref",
    "n_funciones", "estado", "banco_version",
)
PROHIBIDAS = frozenset({"reforzado", "caso", "orden", "semilla", "condicion", "control"})


def generar_csv_puntajes(filas: Iterable[dict]) -> str:
    return csv_de_filas(COLUMNAS_PUNTAJES, (
        {k: ("" if v is None else v) for k, v in fila.items() if k in COLUMNAS_PUNTAJES}
        for fila in filas
    ))
