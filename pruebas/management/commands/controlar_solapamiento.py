"""Lista pares sospechosos entre la prueba y el material de refuerzo (D21)."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from analisis.perfil import exigir_perfil
from pruebas.servicios.banco import BancoInvalido, cargar_bancos
from pruebas.servicios.solapamiento import (
    ficha_para_jueces,
    material_de_refuerzo,
    pares_sospechosos,
    soluciones_de_carpeta,
)
from refuerzo.servicios.banco import BloqueInvalido, cargar_carpeta


class Command(BaseCommand):
    help = "Compara enunciados y soluciones de la prueba con los bloques de refuerzo (D21)."

    def add_arguments(self, parser):
        parser.add_argument("--banco", type=Path, default=None)
        parser.add_argument("--bloques", type=Path, default=None)
        parser.add_argument(
            "--soluciones", type=Path, default=None,
            help="Carpeta con las soluciones de referencia de los bloques (D22).",
        )
        parser.add_argument(
            "--ficha", type=Path, default=None,
            help="Escribe un CSV con los pares para que cada juez los clasifique (D23). "
                 "Guárdalo en el almacén: nombra ítems de la prueba.",
        )

    def handle(self, *args, banco, bloques, soluciones, ficha, **opciones):
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
        carpeta = soluciones or Path(settings.SOLUCIONES_BLOQUES_DIR)
        codigos = soluciones_de_carpeta(carpeta) if carpeta.is_dir() else {}
        if contenidos and not codigos:
            self.stdout.write("Sin soluciones de referencia: solo se comparan los enunciados.")
        pares = pares_sospechosos(bancos, material_de_refuerzo(contenidos or None, codigos))
        if not pares:
            self.stdout.write("Sin pares sospechosos.")
            return
        for par in pares:
            self.stdout.write(
                f"  {par.item_prueba} ~ {par.material}  ({par.motivo}, {par.similitud:.2f})"
            )
        if ficha is not None:
            # newline="": el CSV ya trae sus saltos; si no, Windows los duplica.
            ficha.write_text(ficha_para_jueces(pares), encoding="utf-8", newline="")
            self.stdout.write(f"Ficha para los jueces en {ficha}.")
        raise CommandError(
            f"{len(pares)} pares sospechosos: revísalos a mano y con los jueces.",
            returncode=12,
        )
