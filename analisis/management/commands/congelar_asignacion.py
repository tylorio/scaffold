"""Congela la asignación de toda la muestra, igual que el botón de la interfaz."""
from django.core.management.base import BaseCommand, CommandError

from analisis.persistencia import (
    AsignacionCongelada,
    NoSePuedeCongelar,
    congelar_asignacion,
    estado_congelacion,
)
from analisis.models import Asignacion


class Command(BaseCommand):
    help = "Sortea y fija, una sola vez, los conceptos y el orden AB/BA de todos (D3, R2)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semilla-base", type=int,
            help="Semilla base del estudio. Sin ella se genera una al azar y se registra.",
        )
        parser.add_argument("--tamano-bloque", type=int, choices=(2, 4), default=4)

    def handle(self, *args, semilla_base, tamano_bloque, **opciones):
        estado = estado_congelacion()
        if estado.congelada is not None:
            raise CommandError("La asignación ya se congeló.", returncode=11)
        if estado.faltantes:
            raise CommandError(" ".join(estado.faltantes), returncode=10)
        try:
            hecha = congelar_asignacion(semilla_base, tamano_bloque)
        except (NoSePuedeCongelar, AsignacionCongelada) as error:
            raise CommandError(str(error), returncode=10) from error

        self.stdout.write(
            f"Congelada el {hecha.fecha:%Y-%m-%d %H:%M}, modo {hecha.modo}, "
            f"semilla base {hecha.semilla_base}, bloques de {hecha.tamano_bloque}."
        )
        for a in Asignacion.objects.select_related("participante").order_by(
            "participante__codigo"
        ):
            self.stdout.write(
                f"  {a.participante.codigo}  caso {a.caso}  orden {a.orden}  "
                f"reforzados={','.join(a.reforzados)}  control={','.join(a.control)}"
            )
