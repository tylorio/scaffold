"""Comprueba que los datos de los participantes estén en el almacén cifrado."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from analisis.almacen import FALTA, estado_bitlocker, revisar_almacen
from analisis.perfil import exigir_perfil


class Command(BaseCommand):
    help = "Revisa el almacén local cifrado (08 §3.4) y avisa de restos sin cifrar."

    def handle(self, *args, **opciones):
        exigir_perfil("local")
        almacen = settings.ALMACEN
        revisiones = revisar_almacen(
            almacen, Path(settings.DATABASES["default"]["NAME"]), Path(settings.DATOS_DIR),
            Path(settings.BASE_DIR), estado_bitlocker(almacen) if almacen else None,
        )
        for revision in revisiones:
            self.stdout.write(f"[{revision.estado}] {revision.mensaje}")
        if any(r.estado == FALTA for r in revisiones):
            raise CommandError("El almacén no está listo.", returncode=18)
