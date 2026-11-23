"""Carga los bloques de refuerzo desde archivos JSON (D20).

Un bloque nuevo, o una versión nueva de uno existente, queda sin validar: no se
entrega hasta que el investigador registre la validación de los jueces en Gestión.
"""
from pathlib import Path

from django.conf import settings

from analisis.perfil import exigir_perfil
from django.core.management.base import BaseCommand, CommandError

from refuerzo.administracion import cargar_bloques
from refuerzo.servicios.banco import BloqueInvalido, bloques_de_ejemplo, cargar_carpeta


class Command(BaseCommand):
    help = "Carga los bloques de refuerzo de una carpeta de JSON (o los de ejemplo)."

    def add_arguments(self, parser):
        parser.add_argument("--carpeta", type=Path, default=None)
        parser.add_argument(
            "--ejemplo", action="store_true",
            help="Carga el bloque de ejemplo de cada concepto. Solo en local y para "
                 "desarrollo: se solapan con la prueba y no se pueden validar.",
        )
        parser.add_argument("--usuario", default="consola")

    def handle(self, *args, carpeta, ejemplo, usuario, **opciones):
        try:
            if ejemplo:
                # Se solapan con la prueba: nunca en el portal real.
                exigir_perfil("local")
                contenidos = bloques_de_ejemplo()
            else:
                carpeta = carpeta or Path(settings.BLOQUES_REFUERZO_DIR)
                contenidos = cargar_carpeta(carpeta)
                if not contenidos:
                    raise CommandError(f"No hay bloques *.json en {carpeta}.", returncode=19)
            resumen = cargar_bloques(contenidos, usuario)
        except BloqueInvalido as error:
            raise CommandError(f"Bloques inválidos, no se cargó ninguno: {error}",
                               returncode=19) from error
        self.stdout.write(
            f"Nuevos: {len(resumen.nuevos)}. Versiones nuevas: {len(resumen.actualizados)}. "
            f"Sin cambios: {len(resumen.sin_cambios)}."
        )
        if resumen.nuevos or resumen.actualizados:
            self.stdout.write(
                "Los bloques nuevos o cambiados quedan sin validar: regístralo en Gestión "
                "cuando los jueces los aprueben."
            )
