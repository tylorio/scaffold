"""Exportación de lo que hace cada participante con el material de refuerzo.

Ningún CSV lleva el código de las soluciones, que tampoco se guarda (21b §5).
"""
from collections import Counter

from django.utils import timezone

from analisis.models import Configuracion, Participante
from analisis.servicios.exportacion import (
    COLUMNAS_ADHERENCIA,
    COLUMNAS_APERTURAS,
    COLUMNAS_INTENTOS,
    csv_de_filas,
)

from .models import AperturaRefuerzo, BloqueRefuerzo, IntentoEjercicio
from .servicios.adherencia import calcular
from .servicios.banco import semana_de


def _condicion(participante: Participante, concepto: str) -> str:
    asignacion = getattr(participante, "asignacion", None)
    return asignacion.condicion(concepto) if asignacion else ""


def _tras_postest(fecha, liberado_en) -> int:
    return int(liberado_en is not None and fecha >= liberado_en)


def _filas_intentos():
    liberado_en = Configuracion.obtener().control_liberado_en
    intentos = (
        IntentoEjercicio.objects.select_related("analisis__participante__asignacion")
        .order_by("analisis__participante__codigo", "fecha", "id")
    )
    numero, anterior = Counter(), {}
    for intento in intentos:
        participante = intento.analisis.participante
        clave = participante.pk, intento.bloque_id, intento.ejercicio
        numero[clave] += 1
        yield {
            "codigo": participante.codigo,
            "concepto": intento.concepto,
            "condicion": _condicion(participante, intento.concepto),
            "bloque": intento.bloque_id,
            "version": intento.bloque_version,
            "ejercicio": intento.ejercicio,
            "intento": numero[clave],
            "fecha": intento.fecha.isoformat(timespec="seconds"),
            "ejecutado": int(intento.ejecutado),
            "pasados": intento.pasados,
            "total": intento.total,
            "resuelto": int(intento.resuelto),
            "usa_concepto": int(intento.usa_concepto),
            "tuvo_error": int(bool(intento.error)),
            "longitud_codigo": intento.longitud_codigo,
            # Reenviar lo mismo sin cambios: el hash compara sin guardar el código.
            "igual_al_anterior": int(anterior.get(clave) == intento.hash_codigo),
            "tras_postest": _tras_postest(intento.fecha, liberado_en),
        }
        anterior[clave] = intento.hash_codigo


def _filas_aperturas():
    liberado_en = Configuracion.obtener().control_liberado_en
    aperturas = (
        AperturaRefuerzo.objects.select_related("participante__asignacion")
        .order_by("participante__codigo", "fecha", "id")
    )
    for apertura in aperturas:
        yield {
            "codigo": apertura.participante.codigo,
            "concepto": apertura.concepto,
            "condicion": _condicion(apertura.participante, apertura.concepto),
            "bloque": apertura.bloque_id,
            "version": apertura.bloque_version or "",
            "permitida": int(apertura.permitida),
            "motivo": apertura.motivo,
            "fecha": apertura.fecha.isoformat(timespec="seconds"),
            "tras_postest": _tras_postest(apertura.fecha, liberado_en),
        }


def _redondear(valor):
    return "" if valor is None else round(valor, 4)


def _filas_adherencia():
    """Una fila por participante y concepto reforzado, durante la intervención.

    El corte es la liberación del control (fin de la intervención) o, si aún no
    ocurre, hoy. Los envíos posteriores al corte no cuentan.
    """
    configuracion = Configuracion.obtener()
    liberado_en = configuracion.control_liberado_en
    corte = timezone.localdate(liberado_en) if liberado_en else timezone.localdate()
    semana = semana_de(corte, configuracion.inicio_intervencion)
    ejercicios = {}
    for bloque in BloqueRefuerzo.objects.filter(validado=True, semana__lte=semana):
        ejercicios.setdefault(bloque.concepto, set()).update(
            (bloque.id, e["id"]) for e in bloque.contenido["ejercicios"]
        )
    participantes = Participante.objects.select_related("asignacion").order_by("codigo")
    for participante in participantes:
        analisis = participante.ultimo_analisis
        if analisis is None:
            continue
        for resultado in analisis.conceptos.filter(reforzado=True).order_by("concepto"):
            intentos = IntentoEjercicio.objects.filter(
                analisis__participante=participante, concepto=resultado.concepto,
            )
            if liberado_en is not None:
                intentos = intentos.filter(fecha__lt=liberado_en)
            medida = calcular(
                ejercicios.get(resultado.concepto, set()),
                (((i.bloque_id, i.ejercicio), i.ejecutado, i.resuelto) for i in intentos),
            )
            yield {
                "codigo": participante.codigo,
                "concepto": resultado.concepto,
                "condicion": _condicion(participante, resultado.concepto),
                "corte": corte.isoformat(),
                "semana": semana,
                "liberados": medida.liberados,
                "intentados": medida.intentados,
                "resueltos": medida.resueltos,
                "adherencia": _redondear(medida.principal),
                "adherencia_resueltos": _redondear(medida.secundaria),
            }


def exportar_csv_intentos() -> str:
    return csv_de_filas(COLUMNAS_INTENTOS, _filas_intentos())


def exportar_csv_aperturas() -> str:
    return csv_de_filas(COLUMNAS_APERTURAS, _filas_aperturas())


def exportar_csv_adherencia() -> str:
    return csv_de_filas(COLUMNAS_ADHERENCIA, _filas_adherencia())
