"""Corrección automática de T1–T3: porcentaje de casos superados y métricas de calidad.

Reutiliza el corredor de los ejercicios de refuerzo. Corre en la máquina del
investigador, con las soluciones de la sesión supervisada; no es un sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass

from refuerzo.servicios.ejecutor import ejecutar_solucion

from .banco import Banco, BancoInvalido, ItemPrueba
from .calidad import metricas_calidad

OK = "ok"
SIN_RESPUESTA = "sin_respuesta"  # no entregó archivo para el ítem: cuenta como 0 %
ILEGIBLE = "ilegible"  # no es Python válido: 0 % y sin métricas de calidad


@dataclass(frozen=True)
class ResultadoItem:
    item: str
    concepto: str
    estado: str
    casos_pasados: int
    casos_total: int
    t_pct: float
    cc_sol: float | None
    lin_sol: int | None
    n_funciones: int | None
    cc_ref: float
    lin_ref: int


def corregir_item(
    solucion: str | None, item: ItemPrueba, tiempo_limite: float = 5.0
) -> ResultadoItem:
    referencia = metricas_calidad(item.referencia)
    total = len(item.casos)
    metricas = None if solucion is None else metricas_calidad(solucion)
    if solucion is None or metricas is None:
        estado, pasados = (SIN_RESPUESTA if solucion is None else ILEGIBLE), 0
    else:
        estado = OK
        pasados = ejecutar_solucion(solucion, item, tiempo_limite).pasados
    return ResultadoItem(
        item=item.item,
        concepto=item.concepto,
        estado=estado,
        casos_pasados=pasados,
        casos_total=total,
        t_pct=round(100 * pasados / total, 2),
        cc_sol=metricas.cc if metricas else None,
        lin_sol=metricas.lineas if metricas else None,
        n_funciones=metricas.n_funciones if metricas else None,
        cc_ref=referencia.cc,
        lin_ref=referencia.lineas,
    )


def verificar_referencias(bancos: dict[str, Banco], tiempo_limite: float = 5.0) -> None:
    """Cada solución de referencia debe superar todos los casos de su ítem."""
    fallas = []
    for forma, banco in bancos.items():
        for item in banco.items:
            if metricas_calidad(item.referencia) is None:
                fallas.append(f"{forma}/{item.item}: la referencia no es Python válido.")
                continue
            resultado = corregir_item(item.referencia, item, tiempo_limite)
            if resultado.casos_pasados != resultado.casos_total:
                fallas.append(
                    f"{forma}/{item.item}: la referencia supera {resultado.casos_pasados} "
                    f"de {resultado.casos_total} casos."
                )
    if fallas:
        raise BancoInvalido(" ".join(fallas))
