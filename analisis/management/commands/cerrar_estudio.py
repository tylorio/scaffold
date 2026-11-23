"""Cierre del estudio (D13): borra el código y lo que lleva a los repositorios."""
from django.core.management.base import BaseCommand, CommandError

from analisis.estudio import CierreNoPermitido, cerrar_estudio
from analisis.perfil import exigir_perfil

CONFIRMACION = "borrar-codigo"


class Command(BaseCommand):
    help = (
        "Borra los fragmentos, las rutas, los hashes de correo y los códigos de acceso. "
        "Se conservan los agregados exportados. No se deshace."
    )

    def add_arguments(self, parser):
        parser.add_argument("--confirmo", default="", help=f"Escribe {CONFIRMACION}.")
        parser.add_argument("--usuario", default="manage.py")

    def handle(self, *args, confirmo, usuario, **opciones):
        exigir_perfil("local")
        if confirmo != CONFIRMACION:
            raise CommandError(
                f"No se borró nada. Para cerrar, agrega --confirmo {CONFIRMACION}.",
                returncode=21,
            )
        try:
            borrado = cerrar_estudio(usuario)
        except CierreNoPermitido as error:
            raise CommandError(str(error), returncode=21) from error
        self.stdout.write(
            f"Borrados {borrado['fragmentos']} fragmentos y las rutas de "
            f"{borrado['participantes_con_repositorio']} repositorios. Borra también la "
            "tabla de correspondencia y las carpetas de entregas de la prueba."
        )
