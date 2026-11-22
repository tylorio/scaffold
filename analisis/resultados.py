"""Exportar (núcleo local) e importar (portal) el archivo `resultados-v1` (ADR-001)."""
from __future__ import annotations

import hashlib
import json

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import (
    Analisis,
    Asignacion,
    Auditoria,
    Congelacion,
    Importacion,
    Participante,
    ResultadoConcepto,
)
from .servicios.idc import intervalo_wilson
from .servicios.resultados import (
    ESQUEMA,
    validar_documento,
    validar_sin_datos_prohibidos,
)


class ArchivoInvalido(Exception):
    """El archivo de resultados no cumple el esquema o trae datos prohibidos."""


class SinAsignacionCongelada(Exception):
    """Sin congelación no hay nada que llevar al portal."""


def _intervalo(n_ia, n):
    intervalo = intervalo_wilson(n_ia, n) if n else None
    return None if intervalo is None else [round(intervalo[0], 4), round(intervalo[1], 4)]


def construir_resultados() -> dict:
    """Documento con el diagnóstico congelado de cada participante, sin código."""
    congelacion = Congelacion.objects.first()
    if congelacion is None:
        raise SinAsignacionCongelada(
            "La asignación no está congelada: no hay resultados para el portal."
        )
    asignaciones = (
        Asignacion.objects.select_related("participante", "analisis_base")
        .prefetch_related("analisis_base__conceptos")
        .order_by("participante__codigo")
    )
    participantes = []
    for asignacion in asignaciones:
        analisis = asignacion.analisis_base
        participantes.append({
            "codigo": asignacion.participante.codigo,
            "analisis_id": str(analisis.analisis_id),
            "fecha": analisis.fecha.isoformat(timespec="seconds"),
            "versiones": {
                "modelo": analisis.modelo_version, "modelo_es_demo": analisis.modelo_es_demo,
                "reglas": analisis.version_reglas, "rasgos": analisis.version_rasgos,
            },
            "parametros": {"theta": analisis.theta, "lambda": analisis.lambda_valor, "m": analisis.m},
            "n_fragmentos": analisis.n_fragmentos,
            "n_ia": analisis.n_ia,
            "idc_global": analisis.idc_global,
            "ic95": _intervalo(analisis.n_ia, analisis.n_fragmentos),
            "conceptos": [
                {
                    "concepto": c.concepto, "n": c.n_fragmentos, "n_ia": c.n_ia, "idc": c.idc,
                    "ic95": None if c.idc is None else _intervalo(c.n_ia, c.n_fragmentos),
                    "estado": c.estado, "condicion": asignacion.condicion(c.concepto),
                }
                for c in analisis.conceptos.all()
            ],
            "asignacion": {
                "semilla": asignacion.semilla, "debiles": asignacion.debiles,
                "reforzados": asignacion.reforzados, "control": asignacion.control,
                "caso": asignacion.caso, "orden": asignacion.orden, "modo": asignacion.modo,
                "congelada_en": asignacion.fecha.isoformat(timespec="seconds"),
            },
        })
    return {
        "esquema": ESQUEMA,
        "generado": timezone.now().isoformat(timespec="seconds"),
        "sistema": {"version": settings.VERSION_SISTEMA},
        "congelacion": {
            "fecha": congelacion.fecha.isoformat(timespec="seconds"),
            "modo": congelacion.modo,
            "semilla_base": congelacion.semilla_base,
            "tamano_bloque": congelacion.tamano_bloque,
        },
        "participantes": participantes,
    }


def errores_del_documento(documento) -> list[str]:
    return validar_documento(documento) + validar_sin_datos_prohibidos(documento)


def exportar_resultados(usuario: str) -> str:
    documento = construir_resultados()
    errores = errores_del_documento(documento)
    if errores:
        raise ArchivoInvalido("; ".join(errores[:10]))
    Auditoria.anotar(usuario, Auditoria.EXPORTAR, n_participantes=len(documento["participantes"]))
    return json.dumps(documento, ensure_ascii=False, indent=2)


def _fecha(texto: str):
    fecha = parse_datetime(texto)
    if fecha is None:
        raise ArchivoInvalido(f"Fecha inválida: {texto}")
    return fecha


def importar_resultados(texto: str, usuario: str) -> tuple[Importacion, int]:
    """Carga en el portal el diagnóstico y la asignación. Devuelve cuántos son nuevos.

    Es idempotente: un participante que ya está con el mismo `analisis_id` no se
    toca. Si llega con otro diagnóstico, o el archivo trae otra congelación, se
    rechaza: la asignación es única (D3).
    """
    try:
        documento = json.loads(texto)
    except ValueError as error:
        raise ArchivoInvalido(f"No es JSON válido: {error}") from error
    errores = errores_del_documento(documento)
    if errores:
        raise ArchivoInvalido("; ".join(errores[:10]))
    huella = hashlib.sha256(texto.encode("utf-8")).hexdigest()

    with transaction.atomic():
        anterior = Importacion.objects.filter(hash_archivo=huella).first()
        if anterior is not None:
            return anterior, 0
        datos = documento["congelacion"]
        congelacion = Congelacion.objects.first()
        if congelacion is None:
            congelacion = Congelacion.objects.create(
                semilla_base=datos["semilla_base"], modo=datos["modo"],
                tamano_bloque=datos["tamano_bloque"],
            )
            Congelacion.objects.filter(pk=congelacion.pk).update(fecha=_fecha(datos["fecha"]))
        elif congelacion.semilla_base != datos["semilla_base"]:
            raise ArchivoInvalido("El portal ya tiene otra asignación congelada.")

        nuevos = 0
        for p in documento["participantes"]:
            existente = Participante.objects.filter(codigo=p["codigo"]).first()
            if existente is not None:
                analisis = existente.ultimo_analisis
                if analisis is None or str(analisis.analisis_id) != p["analisis_id"]:
                    raise ArchivoInvalido(
                        f"{p['codigo']} ya está en el portal con otro diagnóstico."
                    )
                continue
            participante = Participante.objects.create(codigo=p["codigo"], repositorio="")
            analisis = Analisis.objects.create(
                participante=participante, analisis_id=p["analisis_id"],
                theta=p["parametros"]["theta"], lambda_valor=p["parametros"]["lambda"],
                m=p["parametros"]["m"], modelo_version=p["versiones"]["modelo"],
                modelo_es_demo=p["versiones"]["modelo_es_demo"],
                version_reglas=p["versiones"]["reglas"], version_rasgos=p["versiones"]["rasgos"],
                n_fragmentos=p["n_fragmentos"], n_ia=p["n_ia"], idc_global=p["idc_global"],
            )
            Analisis.objects.filter(pk=analisis.pk).update(fecha=_fecha(p["fecha"]))
            ResultadoConcepto.objects.bulk_create(
                ResultadoConcepto(
                    analisis=analisis, concepto=c["concepto"], n_fragmentos=c["n"],
                    n_ia=c["n_ia"], idc=c["idc"], estado=c["estado"],
                    reforzado=c["condicion"] == "reforzado",
                )
                for c in p["conceptos"]
            )
            a = p["asignacion"]
            asignacion = Asignacion.objects.create(
                participante=participante, analisis_base=analisis, semilla=a["semilla"],
                debiles=a["debiles"], reforzados=a["reforzados"], control=a["control"],
                caso=a["caso"], orden=a["orden"], modo=a["modo"],
            )
            Asignacion.objects.filter(pk=asignacion.pk).update(fecha=_fecha(a["congelada_en"]))
            nuevos += 1

        importacion = Importacion.objects.create(
            usuario=usuario, esquema=documento["esquema"], hash_archivo=huella,
            n_participantes=len(documento["participantes"]), generado=documento["generado"],
        )
        Auditoria.anotar(
            usuario, Auditoria.IMPORTAR, nuevos=nuevos, hash_archivo=huella,
            n_participantes=len(documento["participantes"]),
        )
    return importacion, nuevos
