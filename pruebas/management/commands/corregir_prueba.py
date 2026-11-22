"""Corrige T1–T3 de una sesión (pretest o postest) y escribe el CSV de puntajes T."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from analisis.perfil import exigir_perfil
from analisis.persistencia import NoSePuedeCongelar
from pruebas.persistencia import corregir_momento
from pruebas.servicios.banco import BancoInvalido, cargar_bancos
from pruebas.servicios.corrector import verificar_referencias
from pruebas.servicios.exportacion import generar_csv_puntajes
from refuerzo.ejecucion import ejecutor_configurado


class Command(BaseCommand):
    help = (
        "Corrige soluciones/<código>/T1.py, T2.py y T3.py con la forma que le tocó a "
        "cada participante y escribe un CSV sin datos de la asignación (D3, D17)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--momento", choices=("pre", "post"), required=True)
        parser.add_argument("--soluciones", type=Path, required=True)
        parser.add_argument("--salida", type=Path, required=True)
        parser.add_argument(
            "--banco", type=Path, default=None,
            help="Carpeta con forma_A.json y forma_B.json (por defecto, BANCO_PRUEBA_DIR).",
        )

    def handle(self, *args, momento, soluciones, salida, banco, **opciones):
        exigir_perfil("local")
        carpeta_banco = banco or Path(settings.BANCO_PRUEBA_DIR)
        remoto = ejecutor_configurado()
        if remoto is None:
            self.stdout.write(
                "Aviso: sin IDC_EJECUTOR_URL, las soluciones corren en un subproceso local "
                "que no es un sandbox. Lo recomendable es usar el ejecutor aislado."
            )
        try:
            bancos = cargar_bancos(carpeta_banco)
            verificar_referencias(bancos, settings.TIEMPO_LIMITE_EJERCICIO, remoto)
        except BancoInvalido as error:
            raise CommandError(f"Banco inválido: {error}", returncode=14) from error
        if not soluciones.is_dir():
            raise CommandError(f"No existe la carpeta {soluciones}.", returncode=15)
        try:
            correccion = corregir_momento(
                momento, soluciones, bancos, settings.TIEMPO_LIMITE_EJERCICIO, remoto,
            )
        except NoSePuedeCongelar as error:
            raise CommandError(str(error), returncode=13) from error

        salida.write_text(generar_csv_puntajes(correccion.filas), encoding="utf-8", newline="")
        participantes = {f["participante"] for f in correccion.filas}
        self.stdout.write(
            f"{len(correccion.filas)} ítems corregidos de {len(participantes)} "
            f"participantes ({momento}). CSV en {salida}."
        )
        for aviso in correccion.avisos:
            self.stdout.write(f"  Aviso: {aviso}")
        if correccion.hay_ilegibles:
            raise CommandError(
                "Hay soluciones ilegibles: quedaron con 0 % y sin métricas de calidad. "
                "Revísalas en el CSV (estado = ilegible).",
                returncode=9,
            )
