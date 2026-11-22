"""Índice de delegación por historial (D9, P10): medida exploratoria para HE1.

Mide el proceso, no el producto: cuánto del código del participante entró en
commits grandes, como cuando se pega de golpe la salida de un asistente. Es
independiente del clasificador, que solo mira estilo y estructura.

Se reportan dos medidas (P10):
- la proporción de líneas propias que entraron en commits de `UMBRAL_LINEAS` o más
  líneas, también con los umbrales de sensibilidad;
- la media de log(1 + tamaño de inserción) de los fragmentos, que no usa umbral.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

HISTORIAL_VERSION = "historial-v1"

# Fijado a priori, antes de ver datos (P10). No se calibra con la sesión de
# etiquetado: allí se pidió un commit por tarea y el tamaño de inserción es artificial.
UMBRAL_LINEAS = 30
UMBRALES_SENSIBILIDAD = (15, 60)


@dataclass(frozen=True)
class IndiceHistorial:
    proporcion_lineas: float | None  # con UMBRAL_LINEAS; None si no hay historial
    proporcion_lineas_15: float | None
    proporcion_lineas_60: float | None
    media_log_insercion: float | None
    n_lineas_con_historial: int
    n_fragmentos_con_historial: int
    umbral_lineas: int = UMBRAL_LINEAS
    version: str = HISTORIAL_VERSION


def _proporcion(lineas: list[int], umbral: int) -> float | None:
    return sum(i >= umbral for i in lineas) / len(lineas) if lineas else None


def indice_por_historial(
    inserciones_fragmentos: Iterable[int | None], inserciones_lineas: Iterable[int],
) -> IndiceHistorial:
    """Calcula el índice a partir del tamaño de inserción de fragmentos y de líneas.

    Los fragmentos sin historial no cuentan ni en el numerador ni en el
    denominador: su ausencia no es un dato.
    """
    fragmentos = [i for i in inserciones_fragmentos if i is not None]
    lineas = list(inserciones_lineas)
    bajo, alto = UMBRALES_SENSIBILIDAD
    return IndiceHistorial(
        proporcion_lineas=_proporcion(lineas, UMBRAL_LINEAS),
        proporcion_lineas_15=_proporcion(lineas, bajo),
        proporcion_lineas_60=_proporcion(lineas, alto),
        media_log_insercion=(
            sum(math.log1p(max(i, 0)) for i in fragmentos) / len(fragmentos)
            if fragmentos else None
        ),
        n_lineas_con_historial=len(lineas),
        n_fragmentos_con_historial=len(fragmentos),
    )
