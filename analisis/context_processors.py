"""Aviso global sobre el modelo, visible en todas las páginas."""
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .servicios.clasificador import ModeloNoDisponible, cargar_modelo


@lru_cache(maxsize=1)
def _leer_modelo(ruta: str, modificado: float) -> dict:
    # La fecha de modificación forma parte de la clave de caché para que
    # reentrenar actualice el aviso sin reiniciar el servidor.
    modelo = cargar_modelo(ruta)
    return {"version": modelo.version, "es_demo": modelo.es_demo}


def estado_modelo(request):
    ruta = Path(settings.RUTA_MODELO)
    try:
        return {"modelo": _leer_modelo(str(ruta), ruta.stat().st_mtime)}
    except (FileNotFoundError, ModeloNoDisponible):
        return {"modelo": None}
