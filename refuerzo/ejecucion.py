"""Une el ejecutor con la configuración de Django."""
from django.conf import settings

from .servicios.ejecutor import EjecutorRemoto


def ejecutor_configurado() -> EjecutorRemoto | None:
    if not settings.EJECUTOR_URL:
        return None
    return EjecutorRemoto(settings.EJECUTOR_URL, settings.EJECUTOR_TOKEN)
