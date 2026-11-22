"""Métricas de calidad de una solución, iguales para la del estudiante y la de referencia.

D1 compara la solución con la referencia de su ítem:
- `cc`: complejidad ciclomática media por función (radon), como dice el plan (8.3.2);
- `lineas`: líneas de código fuente de toda la solución, sin blancos ni comentarios.
"""
from __future__ import annotations

from dataclasses import dataclass

from radon.complexity import cc_visit
from radon.raw import analyze
from radon.visitors import Function


@dataclass(frozen=True)
class MetricasCalidad:
    cc: float
    lineas: int
    n_funciones: int


def metricas_calidad(codigo: str) -> MetricasCalidad | None:
    """None si el código no es Python válido."""
    try:
        funciones = [b for b in cc_visit(codigo) if isinstance(b, Function)]
        lineas = analyze(codigo).sloc
    except (SyntaxError, ValueError, RecursionError):
        return None
    cc = sum(f.complexity for f in funciones) / len(funciones) if funciones else 1.0
    return MetricasCalidad(cc=round(cc, 4), lineas=lineas, n_funciones=len(funciones))
