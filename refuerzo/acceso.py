"""Acceso del estudiante al portal con su código (08 §3.2).

- El código se genera al azar, se muestra una sola vez y se guarda solo su hash.
- Para entrar se pide el código anónimo del participante y su código de acceso, así
  se verifica un solo hash por intento.
- Tras 10 intentos fallidos en 15 minutos desde la misma conexión, se bloquea.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect
from django.utils import timezone

from analisis.models import Auditoria, Participante

from .models import IntentoAcceso

ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin 0, O, 1, I ni L, que se confunden
LARGO = 10
MAXIMO_FALLOS = 10
VENTANA = timedelta(minutes=15)
RETENCION = timedelta(hours=24)
SESION_ESTUDIANTE = "participante_id"


class ParticipanteRetirado(Exception):
    pass


class AccesoBloqueado(Exception):
    pass


def generar_codigo_acceso(participante: Participante, usuario: str) -> str:
    """Devuelve el código en claro, para entregarlo; reemplaza al anterior."""
    if participante.retirado_en is not None:
        raise ParticipanteRetirado(f"{participante.codigo} se retiró del estudio.")
    codigo = "".join(secrets.choice(ALFABETO) for _ in range(LARGO))
    participante.codigo_acceso = make_password(codigo)
    participante.save(update_fields=["codigo_acceso"])
    Auditoria.anotar(usuario, Auditoria.CODIGO_ACCESO, participante.codigo)
    return codigo


def normalizar(codigo: str) -> str:
    return "".join(c for c in codigo.upper() if c.isalnum())


def huella_ip(ip: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()


def esta_bloqueado(ip: str) -> bool:
    desde = timezone.now() - VENTANA
    fallos = IntentoAcceso.objects.filter(ip_hash=huella_ip(ip), exito=False, fecha__gte=desde)
    return fallos.count() >= MAXIMO_FALLOS


def verificar(codigo_participante: str, codigo_acceso: str, ip: str) -> Participante | None:
    IntentoAcceso.objects.filter(fecha__lt=timezone.now() - RETENCION).delete()
    if esta_bloqueado(ip):
        raise AccesoBloqueado
    participante = Participante.objects.filter(
        codigo=codigo_participante.strip().upper(),
    ).exclude(codigo_acceso="").first()
    valido = participante is not None and check_password(
        normalizar(codigo_acceso), participante.codigo_acceso,
    )
    IntentoAcceso.objects.create(
        ip_hash=huella_ip(ip), exito=valido, participante=participante if valido else None,
    )
    return participante if valido else None


def estudiante_requerido(vista):
    """La vista recibe al participante de la sesión: nunca un código desde la URL."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        participante = Participante.objects.filter(
            pk=request.session.get(SESION_ESTUDIANTE), retirado_en__isnull=True,
        ).first()
        if participante is None:
            return redirect("estudiante:acceso")
        return vista(request, participante, *args, **kwargs)

    return envoltura
