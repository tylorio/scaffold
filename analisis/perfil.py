from django.conf import settings
from django.core.management.base import CommandError


def exigir_perfil(perfil: str) -> None:
    """Los comandos que tocan código o el almacén local no existen en la nube, y viceversa."""
    if settings.PERFIL != perfil:
        raise CommandError(
            f"Este comando solo existe en el perfil {perfil} (ahora: {settings.PERFIL}).",
            returncode=17,
        )
