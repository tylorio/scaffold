"""Índice de Dependencia Conductual y selección de conceptos a reforzar."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

from .conceptos import CONCEPTOS

DEBIL = "debil"
NO_DEBIL = "no_debil"
DATOS_INSUFICIENTES = "datos_insuficientes"

ETIQUETAS_ESTADO = {
    DEBIL: "Débil",
    NO_DEBIL: "No débil",
    DATOS_INSUFICIENTES: "Datos insuficientes",
}

MAXIMO_REFORZADOS = 2
Z_95 = 1.959964


@dataclass(frozen=True)
class Parametros:
    theta: float = 0.5
    lambda_: float = 0.5
    # Con menos de 4 fragmentos, ni un 100 % de IA supera λ = 0,5 con un IC del 95 %.
    m: int = 5


@dataclass(frozen=True)
class ResultadoConcepto:
    concepto: str
    n_fragmentos: int
    n_ia: int
    idc: float | None
    estado: str


@dataclass(frozen=True)
class ResultadoIDC:
    idc_global: float | None
    n_fragmentos: int
    n_ia: int
    conceptos: tuple[ResultadoConcepto, ...]

    @property
    def debiles(self) -> list[str]:
        return [c.concepto for c in self.conceptos if c.estado == DEBIL]


@dataclass(frozen=True)
class Reparto:
    reforzados: tuple[str, ...]
    control: tuple[str, ...]
    comparable: bool  # hay reforzado y control, ambos débiles


def calcular_idc(probabilidades: Iterable[float], theta: float) -> float | None:
    """Fragmentos con P(IA) ≥ θ ÷ fragmentos analizados. None si no hay fragmentos."""
    valores = list(probabilidades)
    if not valores:
        return None
    return sum(p >= theta for p in valores) / len(valores)


def intervalo_wilson(n_ia: int, n: int, z: float = Z_95) -> tuple[float, float] | None:
    """Intervalo de confianza de Wilson para n_ia / n. None si no hay fragmentos.

    Wilson se comporta bien con pocos fragmentos y con proporciones de 0 o 1,
    justo donde el intervalo normal se degenera. Supone fragmentos independientes
    y no incluye el error del clasificador: es un mínimo, no toda la incertidumbre.
    """
    if n == 0:
        return None
    p = n_ia / n
    z2 = z * z
    denominador = 1 + z2 / n
    centro = (p + z2 / (2 * n)) / denominador
    margen = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominador
    return max(0.0, centro - margen), min(1.0, centro + margen)


def evaluar_concepto(
    concepto: str, probabilidades: list[float], parametros: Parametros
) -> ResultadoConcepto:
    n_fragmentos = len(probabilidades)
    n_ia = sum(p >= parametros.theta for p in probabilidades)
    if n_fragmentos < parametros.m:
        return ResultadoConcepto(
            concepto, n_fragmentos, n_ia, None, DATOS_INSUFICIENTES
        )
    idc = n_ia / n_fragmentos
    estado = DEBIL if idc >= parametros.lambda_ else NO_DEBIL
    return ResultadoConcepto(concepto, n_fragmentos, n_ia, idc, estado)


def repartir_conceptos(debiles: Iterable[str], semilla: int) -> Reparto:
    """Reparte al azar los conceptos débiles entre refuerzo y control.

    El control también tiene que ser débil y salir por sorteo: comparar contra un
    concepto no débil mide conceptos distintos, y reforzar siempre los IDC más
    altos haría que mejoraran solo por regresión a la media.

    Con un único concepto débil se refuerza igual, por el bien del estudiante, pero
    no hay con qué compararlo y queda fuera de la comparación principal.
    """
    candidatos = [c for c in CONCEPTOS if c in set(debiles)]
    if len(candidatos) < 2:
        return Reparto(tuple(candidatos), (), False)
    cantidad = min(MAXIMO_REFORZADOS, len(candidatos) - 1)
    elegidos = set(random.Random(semilla).sample(candidatos, cantidad))
    return Reparto(
        reforzados=tuple(c for c in candidatos if c in elegidos),
        control=tuple(c for c in candidatos if c not in elegidos),
        comparable=True,
    )


def calcular_resultados(
    fragmentos: Iterable[tuple[float, Iterable[str]]],
    parametros: Parametros = Parametros(),
) -> ResultadoIDC:
    """Calcula todo a partir de pares (P(IA), conceptos del fragmento)."""
    fragmentos = [(p, set(conceptos)) for p, conceptos in fragmentos]
    probabilidades = [p for p, _ in fragmentos]

    conceptos = tuple(
        evaluar_concepto(
            concepto,
            [p for p, conceptos in fragmentos if concepto in conceptos],
            parametros,
        )
        for concepto in CONCEPTOS
    )
    return ResultadoIDC(
        idc_global=calcular_idc(probabilidades, parametros.theta),
        n_fragmentos=len(fragmentos),
        n_ia=sum(p >= parametros.theta for p in probabilidades),
        conceptos=conceptos,
    )
