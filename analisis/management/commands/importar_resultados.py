"""Carga en el portal un archivo resultados-v1 exportado por el núcleo local."""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from analisis.perfil import exigir_perfil
from analisis.resultados import ArchivoInvalido, importar_resultados


class Command(BaseCommand):
    help = "Importa el diagnóstico congelado en el portal; rechaza código y datos personales."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=Path)

    def handle(self, *args, archivo, **opciones):
        exigir_perfil("nube")
        try:
            texto = archivo.read_text(encoding="utf-8")
            importacion, nuevos = importar_resultados(texto, usuario="manage.py")
        except OSError as error:
            raise CommandError(f"No se pudo leer {archivo}: {error}", returncode=16) from error
        except ArchivoInvalido as error:
            raise CommandError(f"Archivo rechazado: {error}", returncode=16) from error
        self.stdout.write(
            f"Importación {importacion.pk}: {nuevos} participantes nuevos de "
            f"{importacion.n_participantes} en el archivo."
        )
