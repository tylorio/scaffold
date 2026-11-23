"""Qué bloques ve cada participante y desde cuándo (D4, D20).

- Antes del postest, solo los conceptos reforzados, y de ellos los bloques validados
  de las semanas ya empezadas, contadas desde el inicio de la intervención.
- Tras liberar el control (lista de espera, D4), todos los bloques validados de los
  tres conceptos, para cualquier participante con diagnóstico.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from analisis.models import Configuracion

from .models import AperturaRefuerzo, BloqueRefuerzo
from .servicios.banco import inicio_de_semana, semana_de


@dataclass(frozen=True)
class Intervencion:
    inicio: date | None
    semana: int  # 0 antes de empezar
    liberado: bool  # el control ya se abrió tras el postest

    @property
    def proxima_liberacion(self) -> date | None:
        if self.inicio is None or self.liberado:
            return None
        return inicio_de_semana(self.inicio, self.semana + 1)


def intervencion(configuracion: Configuracion | None = None, hoy: date | None = None):
    configuracion = configuracion or Configuracion.obtener()
    hoy = hoy or timezone.localdate()
    return Intervencion(
        configuracion.inicio_intervencion,
        semana_de(hoy, configuracion.inicio_intervencion),
        configuracion.control_liberado_en is not None,
    )


def concepto_abierto(participante, concepto: str, estado: Intervencion) -> bool:
    """El concepto le toca al participante (aunque aún no tenga bloques liberados)."""
    analisis = participante.ultimo_analisis
    if analisis is None:
        return False
    if estado.liberado:
        return True
    return analisis.conceptos.filter(concepto=concepto, reforzado=True).exists()


def bloque_liberado(bloque: BloqueRefuerzo, estado: Intervencion) -> bool:
    return bloque.validado and (estado.liberado or bloque.semana <= estado.semana)


def bloques_liberados(concepto: str, estado: Intervencion):
    bloques = BloqueRefuerzo.objects.filter(concepto=concepto, validado=True)
    if not estado.liberado:
        bloques = bloques.filter(semana__lte=estado.semana)
    return bloques


def registrar_bloqueo(participante, concepto, motivo, bloque: BloqueRefuerzo | None = None):
    AperturaRefuerzo.objects.create(
        participante=participante, concepto=concepto, permitida=False, motivo=motivo,
        bloque_id=bloque.id if bloque else "", bloque_version=bloque.version if bloque else None,
    )
