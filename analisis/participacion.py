"""Quién está en la muestra: exclusión (D15) y retiro con borrado de datos (D13).

Corre en los dos perfiles: no importa nada que traiga Git ni el modelo. El retiro
se hace en el núcleo local y también en el portal, porque cada uno tiene su base.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Auditoria, Congelacion, Participante


class CambioNoPermitido(Exception):
    pass


def carpeta_a_borrar(repositorio: str) -> str | None:
    """La carpeta local que entregó el participante, si no dio una URL.

    El consentimiento promete borrar también esa copia (D13). El sistema no la
    borra solo, porque es una ruta del disco elegida por el investigador; se la
    recuerda. La ruta no se guarda en la auditoría.
    """
    origen = repositorio.strip()
    if not origen or origen.startswith(("http://", "https://", "ssh://", "git@")):
        return None
    return origen


def excluir(participante: Participante, motivo: str, usuario: str) -> Participante:
    """Deja al participante fuera de la muestra. Antes de congelar, no entra al sorteo.

    Después de congelar conserva su asignación (no se vuelve a sortear a nadie),
    pero sale de la base para el análisis.
    """
    if motivo not in dict(Participante.MOTIVOS_EXCLUSION):
        raise CambioNoPermitido("Motivo de exclusión desconocido.")
    if participante.retirado_en is not None:
        raise CambioNoPermitido(f"{participante.codigo} se retiró: ya no tiene datos.")
    if participante.motivo_exclusion == motivo:
        return participante
    anterior = participante.motivo_exclusion
    participante.motivo_exclusion, participante.excluido_en = motivo, timezone.now()
    participante.save(update_fields=["motivo_exclusion", "excluido_en"])
    Auditoria.anotar(
        usuario, Auditoria.EXCLUIR, participante.codigo, motivo=motivo,
        anterior=anterior or None, tras_congelar=Congelacion.objects.exists(),
    )
    return participante


def incluir(participante: Participante, usuario: str) -> Participante:
    """Quita una exclusión puesta por error.

    No se puede si la congelación ya ocurrió sin esa persona: entraría sin asignación.
    """
    if not participante.excluido:
        return participante
    if Congelacion.objects.exists() and not hasattr(participante, "asignacion"):
        raise CambioNoPermitido(
            f"{participante.codigo} quedó fuera del sorteo: no puede volver a la muestra."
        )
    anterior = participante.motivo_exclusion
    participante.motivo_exclusion, participante.excluido_en = "", None
    participante.save(update_fields=["motivo_exclusion", "excluido_en"])
    Auditoria.anotar(usuario, Auditoria.INCLUIR, participante.codigo, anterior=anterior)
    return participante


@transaction.atomic
def retirar(participante: Participante, usuario: str) -> dict:
    """Borra todos los datos del participante y deja solo su código y la fecha.

    Queda el código para contar el retiro en el diagrama de flujo; la tabla que une
    el código con el nombre está fuera del sistema y la borra el investigador.
    """
    from pruebas.models import PuntajeItem
    from refuerzo.models import AperturaRefuerzo, IntentoAcceso, IntentoEjercicio

    if participante.retirado_en is not None:
        raise CambioNoPermitido(f"{participante.codigo} ya se retiró.")
    asignacion = getattr(participante, "asignacion", None)
    borrado = {
        "analisis": participante.analisis.count(),
        "intentos": IntentoEjercicio.objects.filter(analisis__participante=participante).count(),
        "aperturas": AperturaRefuerzo.objects.filter(participante=participante).count(),
        "puntajes": PuntajeItem.objects.filter(participante=participante).count(),
    }
    if asignacion is not None:
        asignacion.delete()  # protege el análisis base: va primero
    participante.analisis.all().delete()  # con sus fragmentos, conceptos e intentos
    AperturaRefuerzo.objects.filter(participante=participante).delete()
    PuntajeItem.objects.filter(participante=participante).delete()
    IntentoAcceso.objects.filter(participante=participante).update(participante=None)

    participante.repositorio = ""
    participante.hashes_correos = []
    participante.codigo_acceso = ""
    participante.retirado_en = timezone.now()
    participante.save(update_fields=[
        "repositorio", "hashes_correos", "codigo_acceso", "retirado_en",
    ])
    Auditoria.anotar(
        usuario, Auditoria.RETIRO, participante.codigo, borrado=borrado,
        # Para el diagrama de flujo: en qué rama del sorteo estaba.
        caso=asignacion.caso if asignacion else None,
        orden=asignacion.orden if asignacion else None,
    )
    return borrado
