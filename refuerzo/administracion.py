"""Acciones del investigador sobre la intervención. Todas quedan en la auditoría.

- Cargar bloques desde JSON (versión nueva = sin validar).
- Validar un bloque, con el número de jueces que lo revisaron (HE3).
- Fijar la fecha de inicio de la intervención (D20).
- Liberar el material de todos los conceptos tras el postest (D4).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from django.db import transaction
from django.utils import timezone

from analisis.models import Auditoria, Configuracion

from .models import BloqueRefuerzo
from .servicios.banco import BloqueInvalido, es_de_ejemplo, huella, normalizar, validar


class AccionNoPermitida(Exception):
    pass


@dataclass
class ResumenCarga:
    nuevos: list[str] = field(default_factory=list)
    actualizados: list[str] = field(default_factory=list)
    sin_cambios: list[str] = field(default_factory=list)


@transaction.atomic
def cargar_bloques(contenidos: list[dict], usuario: str) -> ResumenCarga:
    """Carga todos o ninguno. Un contenido distinto exige una versión mayor."""
    contenidos = [normalizar(c) for c in contenidos]
    errores = [e for c in contenidos for e in validar(c)]
    if errores:
        raise BloqueInvalido(" ".join(errores))
    resumen = ResumenCarga()
    for contenido in contenidos:
        actual = BloqueRefuerzo.objects.filter(pk=contenido["id"]).first()
        nueva = huella(contenido)
        if actual is not None and actual.huella == nueva:
            resumen.sin_cambios.append(actual.id)
            continue
        if actual is not None and contenido["version"] <= actual.version:
            raise BloqueInvalido(
                f"{actual.id}: el contenido cambió pero la versión sigue en "
                f"{contenido['version']}; súbela a {actual.version + 1} o más."
            )
        ocupada = BloqueRefuerzo.objects.filter(
            concepto=contenido["concepto"], semana=contenido["semana"],
            orden=contenido["orden"],
        ).exclude(pk=contenido["id"]).first()
        if ocupada is not None:
            raise BloqueInvalido(
                f"{contenido['id']}: la semana {contenido['semana']}, orden "
                f"{contenido['orden']} ya es de {ocupada.id}."
            )
        BloqueRefuerzo.objects.update_or_create(pk=contenido["id"], defaults={
            "concepto": contenido["concepto"], "semana": contenido["semana"],
            "orden": contenido["orden"], "version": contenido["version"], "huella": nueva,
            "contenido": contenido,
            # Una versión nueva no está validada, aunque la anterior lo estuviera.
            "validado": False, "n_jueces": None, "validado_en": None, "validado_por": "",
        })
        (resumen.nuevos if actual is None else resumen.actualizados).append(contenido["id"])
        Auditoria.anotar(
            usuario, Auditoria.CARGAR_BLOQUE, contenido["id"],
            version=contenido["version"], huella=nueva,
            anterior=actual.version if actual else None,
        )
    return resumen


def validar_bloque(bloque_id: str, version: int, n_jueces: int, usuario: str):
    """Marca como validada la versión que vio el investigador, no otra más nueva."""
    with transaction.atomic():
        bloque = BloqueRefuerzo.objects.select_for_update().filter(pk=bloque_id).first()
        if bloque is None:
            raise AccionNoPermitida("El bloque no existe.")
        if es_de_ejemplo(bloque.id):
            raise AccionNoPermitida(
                f"{bloque.id} es un bloque de ejemplo: se solapa con la prueba y no se "
                "entrega a los estudiantes."
            )
        if bloque.version != version:
            raise AccionNoPermitida(
                f"{bloque.id} cambió a la versión {bloque.version}: revísala antes de validarla."
            )
        if n_jueces < 1:
            raise AccionNoPermitida("Indica cuántos jueces revisaron el bloque.")
        if bloque.validado:
            raise AccionNoPermitida(f"{bloque.id} v{bloque.version} ya está validado.")
        bloque.validado, bloque.n_jueces = True, n_jueces
        bloque.validado_en, bloque.validado_por = timezone.now(), usuario
        bloque.save()
        Auditoria.anotar(
            usuario, Auditoria.VALIDAR_BLOQUE, bloque.id,
            version=bloque.version, huella=bloque.huella, n_jueces=n_jueces,
        )
    return bloque


def fijar_inicio(fecha: date, usuario: str):
    configuracion = Configuracion.obtener()
    if configuracion.control_liberado_en is not None:
        raise AccionNoPermitida("La intervención ya terminó: el control está liberado.")
    anterior = configuracion.inicio_intervencion
    configuracion.inicio_intervencion = fecha
    configuracion.save(update_fields=["inicio_intervencion"])
    Auditoria.anotar(
        usuario, Auditoria.INICIO_INTERVENCION,
        fecha=fecha.isoformat(), anterior=anterior.isoformat() if anterior else None,
    )
    return configuracion


def liberar_control(usuario: str):
    """Fin de la intervención: se abre todo el material validado. No se deshace."""
    with transaction.atomic():
        configuracion = Configuracion.objects.select_for_update().get(
            pk=Configuracion.obtener().pk,
        )
        if configuracion.inicio_intervencion is None:
            raise AccionNoPermitida("Primero fija el inicio de la intervención.")
        if configuracion.control_liberado_en is not None:
            raise AccionNoPermitida("El control ya está liberado.")
        configuracion.control_liberado_en = timezone.now()
        configuracion.save(update_fields=["control_liberado_en"])
        Auditoria.anotar(
            usuario, Auditoria.LIBERAR_CONTROL,
            fecha=configuracion.control_liberado_en.isoformat(timespec="seconds"),
        )
    return configuracion
