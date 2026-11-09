"""Exportación de lo que hace cada participante con el material de refuerzo."""
from collections import Counter

from analisis.models import Participante
from analisis.servicios.exportacion import (
    COLUMNAS_APERTURAS,
    COLUMNAS_INTENTOS,
    csv_de_filas,
)

from .models import AperturaRefuerzo, IntentoEjercicio


def _condicion(participante: Participante, concepto: str) -> str:
    asignacion = getattr(participante, "asignacion", None)
    return asignacion.condicion(concepto) if asignacion else ""


def _filas_intentos():
    intentos = (
        IntentoEjercicio.objects.select_related("analisis__participante__asignacion")
        .order_by("analisis__participante__codigo", "fecha", "id")
    )
    numero = Counter()
    for intento in intentos:
        participante = intento.analisis.participante
        numero[participante.pk, intento.ejercicio] += 1
        yield {
            "codigo": participante.codigo,
            "concepto": intento.concepto,
            "condicion": _condicion(participante, intento.concepto),
            "ejercicio": intento.ejercicio,
            "intento": numero[participante.pk, intento.ejercicio],
            "fecha": intento.fecha.isoformat(timespec="seconds"),
            "pasados": intento.pasados,
            "total": intento.total,
            "usa_concepto": int(intento.usa_concepto),
            "tuvo_error": int(bool(intento.error)),
        }


def _filas_aperturas():
    aperturas = (
        AperturaRefuerzo.objects.select_related("participante__asignacion")
        .order_by("participante__codigo", "fecha", "id")
    )
    for apertura in aperturas:
        yield {
            "codigo": apertura.participante.codigo,
            "concepto": apertura.concepto,
            "condicion": _condicion(apertura.participante, apertura.concepto),
            "fecha": apertura.fecha.isoformat(timespec="seconds"),
        }


def exportar_csv_intentos() -> str:
    return csv_de_filas(COLUMNAS_INTENTOS, _filas_intentos())


def exportar_csv_aperturas() -> str:
    return csv_de_filas(COLUMNAS_APERTURAS, _filas_aperturas())
