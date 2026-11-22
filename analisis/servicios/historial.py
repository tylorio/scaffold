"""Índice de delegación por historial (D9): medida exploratoria para HE1.

Mide el proceso, no el producto: qué parte de las funciones del participante
entró en commits grandes, como cuando se pega de golpe la salida de un asistente.
Es independiente del clasificador, que solo mira estilo y estructura.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

HISTORIAL_VERSION = "historial-v1"

# [PENDIENTE] Provisional. Se fija antes del diagnóstico con el corpus de la sesión
# de etiquetado (por ejemplo, la mediana de inserción en las tareas con IA; 07 §2.4).
# Cambiarlo exige subir HISTORIAL_VERSION.
UMBRAL_LINEAS = 30


@dataclass(frozen=True)
class IndiceHistorial:
    valor: float | None  # None si ningún fragmento tiene historial
    n_con_historial: int
    umbral_lineas: int
    version: str = HISTORIAL_VERSION


def indice_por_historial(
    inserciones: Iterable[int | None], umbral_lineas: int = UMBRAL_LINEAS
) -> IndiceHistorial:
    """Proporción de fragmentos cuyo commit de inserción añadió ≥ umbral líneas.

    Los fragmentos sin historial no cuentan ni en el numerador ni en el
    denominador: su ausencia no es un dato.
    """
    conocidas = [i for i in inserciones if i is not None]
    valor = (
        sum(i >= umbral_lineas for i in conocidas) / len(conocidas) if conocidas else None
    )
    return IndiceHistorial(valor, len(conocidas), umbral_lineas)
