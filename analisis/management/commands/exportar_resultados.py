"""Escribe el archivo resultados-v1 para el portal: sin código, rutas, URLs ni hashes."""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from analisis.perfil import exigir_perfil
from analisis.resultados import ArchivoInvalido, SinAsignacionCongelada, exportar_resultados


class Command(BaseCommand):
    help = "Exporta el diagnóstico congelado de todos los participantes para el portal (ADR-001)."

    def add_arguments(self, parser):
        parser.add_argument("--salida", type=Path, required=True)

    def handle(self, *args, salida, **opciones):
        exigir_perfil("local")
        try:
            contenido = exportar_resultados(usuario="manage.py")
        except SinAsignacionCongelada as error:
            raise CommandError(str(error), returncode=13) from error
        except ArchivoInvalido as error:
            raise CommandError(
                f"No se escribió nada: el archivo traería datos prohibidos. {error}",
                returncode=8,
            ) from error
        salida.write_text(contenido, encoding="utf-8")
        self.stdout.write(f"Resultados escritos en {salida}.")
