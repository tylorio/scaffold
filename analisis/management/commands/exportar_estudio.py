"""Escribe la base para el análisis estadístico (D17): largo, participantes y flujo."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analisis.estudio import exportar_estudio
from analisis.perfil import exigir_perfil
from analisis.persistencia import NoSePuedeCongelar
from analisis.servicios.estudio import CalificacionesInvalidas, leer_calificaciones


class Command(BaseCommand):
    help = "Exporta la base del estudio en formato largo (D17), sin código ni rutas."

    def add_arguments(self, parser):
        parser.add_argument("--salida", type=Path, default=None)
        parser.add_argument(
            "--calificaciones", type=Path, default=None,
            help="CSV de la rúbrica: participante, concepto, momento, calificador, Q.",
        )
        parser.add_argument("--convocados", type=int, default=None)
        parser.add_argument("--usuario", default="manage.py")

    def handle(self, *args, salida, calificaciones, convocados, usuario, **opciones):
        exigir_perfil("local")
        notas = {}
        if calificaciones is not None:
            try:
                notas = leer_calificaciones(calificaciones.read_text(encoding="utf-8"))
            except (OSError, CalificacionesInvalidas) as error:
                raise CommandError(f"Calificaciones inválidas: {error}", returncode=20) from error
        salida = salida or (
            Path(settings.DATOS_DIR) / "estudio" / timezone.localtime().strftime("%Y%m%d-%H%M%S")
        )
        try:
            resultado = exportar_estudio(salida, usuario, notas, convocados)
        except NoSePuedeCongelar as error:
            raise CommandError(str(error), returncode=13) from error
        self.stdout.write(f"Base escrita en {salida}.")
        if resultado["sobrantes"]:
            self.stdout.write(
                "Aviso: hay notas Q de participantes que no están en la base: "
                + ", ".join(resultado["sobrantes"])
            )
