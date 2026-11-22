"""Índice de Dependencia Conductual y selección de conceptos a reforzar."""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence

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

# Casos de la asignación escalonada (D2, ADR-004)
CASO_A = "A"  # 2 o más débiles: se sortea entre los débiles
CASO_B = "B"  # menos de 2 débiles y 2 o más calculables: entre los calculables
CASO_C = "C"  # menos de 2 calculables: entre los 3 conceptos

CONFIRMATORIO = "confirmatorio"
EXPLORATORIO = "exploratorio"  # F1 < 0,70: "débil" no es confiable y se omite el caso A (R3)
MODOS = (CONFIRMATORIO, EXPLORATORIO)

ORDENES = ("AB", "BA")


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

    @property
    def calculables(self) -> list[str]:
        return [c.concepto for c in self.conceptos if c.estado != DATOS_INSUFICIENTES]


@dataclass(frozen=True)
class Reparto:
    reforzados: tuple[str, ...]
    control: tuple[str, ...]
    caso: str
    modo: str
    semilla: int


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


def conjunto_elegible(
    resultado: ResultadoIDC, modo: str = CONFIRMATORIO
) -> tuple[str, tuple[str, ...]]:
    """Caso y conceptos entre los que se sortea (D2). Siempre hay al menos 2."""
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo}")
    if modo == CONFIRMATORIO and len(resultado.debiles) >= 2:
        return CASO_A, tuple(resultado.debiles)
    if len(resultado.calculables) >= 2:
        return CASO_B, tuple(resultado.calculables)
    return CASO_C, CONCEPTOS


def repartir_conceptos(
    resultado: ResultadoIDC, semilla: int, modo: str = CONFIRMATORIO
) -> Reparto:
    """Sortea hasta 2 reforzados y al menos 1 de control entre los elegibles.

    El control sale por sorteo y del mismo conjunto: reforzar siempre los IDC más
    altos haría que mejoraran solo por regresión a la media. Los conceptos que no
    son elegibles quedan sin asignar.
    """
    caso, elegibles = conjunto_elegible(resultado, modo)
    elegibles = tuple(c for c in CONCEPTOS if c in elegibles)
    cantidad = min(MAXIMO_REFORZADOS, len(elegibles) - 1)
    elegidos = set(random.Random(semilla).sample(elegibles, cantidad))
    return Reparto(
        reforzados=tuple(c for c in elegibles if c in elegidos),
        control=tuple(c for c in elegibles if c not in elegidos),
        caso=caso,
        modo=modo,
        semilla=semilla,
    )


def derivar_semilla(semilla_base: int, *partes: str) -> int:
    """Semilla de un flujo aleatorio propio, reproducible en cualquier proceso.

    No se usa `hash()`: Python lo aleatoriza en cada proceso y el sorteo no se
    podría repetir.
    """
    texto = ":".join((str(semilla_base), *partes)).encode("utf-8")
    # 7 bytes: cabe en un entero con signo de 64 bits de la base de datos.
    return int.from_bytes(hashlib.sha256(texto).digest()[:7], "big")


def sortear_orden(
    codigos: Sequence[str], semilla_base: int, tamano_bloque: int = 4
) -> dict[str, str]:
    """Orden de las formas por bloques permutados, en el orden de los códigos (R2).

    Cada bloque completo tiene tantos AB como BA. El último, si queda incompleto, se
    reparte por pares para que en total |#AB − #BA| ≤ 1.
    """
    if tamano_bloque not in (2, 4):
        raise ValueError("El tamaño de bloque debe ser 2 o 4.")
    azar = random.Random(derivar_semilla(semilla_base, "orden"))
    ordenados = sorted(codigos)
    resultado: dict[str, str] = {}
    for inicio in range(0, len(ordenados), tamano_bloque):
        bloque = ordenados[inicio:inicio + tamano_bloque]
        mitad = len(bloque) // 2
        ordenes = ["AB"] * mitad + ["BA"] * mitad
        if len(bloque) % 2:
            ordenes.append(azar.choice(ORDENES))
        azar.shuffle(ordenes)
        resultado.update(zip(bloque, ordenes))
    return resultado


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
