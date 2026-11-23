"""Lista pares sospechosos entre la prueba y el material de refuerzo (D21)."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from analisis.perfil import exigir_perfil
from pruebas.servicios.banco import BancoInvalido, cargar_bancos
from pruebas.servicios.solapamiento import material_de_refuerzo, pares_sospechosos
from refuerzo.servicios.banco import BloqueInvalido, cargar_carpeta


class Command(BaseCommand):
    help = "Compara enunciados y soluciones de la prueba con los bloques de refuerzo (D21)."

    def add_arguments(self, parser):
        parser.add_argument("--banco", type=Path, default=None)
        parser.add_argument("--bloques", type=Path, default=None)

    def handle(self, *args, banco, bloques, **opciones):
        exigir_perfil("local")
        try:
            bancos = cargar_bancos(banco or Path(settings.BANCO_PRUEBA_DIR))
        except BancoInvalido as error:
            raise CommandError(f"Banco inválido: {error}", returncode=14) from error
        try:
            contenidos = cargar_carpeta(bloques or Path(settings.BLOQUES_REFUERZO_DIR))
        except BloqueInvalido as error:
            raise CommandError(f"Bloques inválidos: {error}", returncode=19) from error
        if not contenidos:
            self.stdout.write("Sin bloques reales: se comparan los bloques de ejemplo.")
        pares = pares_sospechosos(bancos, material_de_refuerzo(contenidos or None))
        if not pares:
            self.stdout.write("Sin pares sospechosos.")
            return
        for par in pares:
            self.stdout.write(
                f"  {par.item_prueba} ~ {par.material}  ({par.motivo}, {par.similitud:.2f})"
            )
        raise CommandError(
            f"{len(pares)} pares sospechosos: revísalos a mano y con los jueces.",
            returncode=12,
        )
