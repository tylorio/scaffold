"""Retiro voluntario (D13): borra todos los datos de un participante."""
from django.core.management.base import BaseCommand, CommandError

from analisis.models import Participante
from analisis.participacion import CambioNoPermitido, retirar


class Command(BaseCommand):
    help = "Borra los datos de un participante que se retira. Hazlo en local y en el portal."

    def add_arguments(self, parser):
        parser.add_argument("codigo")
        parser.add_argument("--confirmo", default="", help="Repite el código del participante.")
        parser.add_argument("--usuario", default="manage.py")

    def handle(self, *args, codigo, confirmo, usuario, **opciones):
        participante = Participante.objects.filter(codigo=codigo).first()
        if participante is None:
            raise CommandError(f"No existe {codigo}.", returncode=22)
        if confirmo != codigo:
            raise CommandError(
                f"No se borró nada. Para confirmar, agrega --confirmo {codigo}.", returncode=22,
            )
        try:
            borrado = retirar(participante, usuario)
        except CambioNoPermitido as error:
            raise CommandError(str(error), returncode=22) from error
        self.stdout.write(f"{codigo} retirado. Borrado: {borrado}.")
