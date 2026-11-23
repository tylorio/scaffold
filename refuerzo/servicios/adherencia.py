"""Adherencia a la intervención (D20, P6).

- Principal: ejercicios intentados ÷ ejercicios liberados.
- Secundaria: ejercicios resueltos ÷ ejercicios liberados.

"Intentado" es un ejercicio con al menos un envío ejecutado: abrir el bloque no
cuenta, un envío que no llegó a ejecutarse tampoco, y varios envíos al mismo
ejercicio cuentan como uno. "Resuelto" es un ejercicio con al menos un envío que
pasó todos sus casos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable


@dataclass(frozen=True)
class Adherencia:
    liberados: int
    intentados: int
    resueltos: int

    @property
    def principal(self) -> float | None:
        return self.intentados / self.liberados if self.liberados else None

    @property
    def secundaria(self) -> float | None:
        return self.resueltos / self.liberados if self.liberados else None


def calcular(
    liberados: Iterable[Hashable], envios: Iterable[tuple[Hashable, bool, bool]],
) -> Adherencia:
    """`envios`: (ejercicio, ejecutado, resuelto). Solo cuentan los ejercicios liberados."""
    liberados = set(liberados)
    intentados, resueltos = set(), set()
    for ejercicio, ejecutado, resuelto in envios:
        if ejercicio in liberados and ejecutado:
            intentados.add(ejercicio)
            if resuelto:
                resueltos.add(ejercicio)
    return Adherencia(len(liberados), len(intentados), len(resueltos))
