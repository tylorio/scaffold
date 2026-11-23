"""Permite ejecutar los scripts desde cualquier carpeta y ubica la carpeta de datos."""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def _almacen() -> str:
    """IDC_ALMACEN del entorno o del .env del proyecto, como lo lee config/settings.py."""
    if os.environ.get("IDC_ALMACEN"):
        return os.environ["IDC_ALMACEN"]
    env = RAIZ / ".env"
    if env.is_file():
        for linea in env.read_text(encoding="utf-8").splitlines():
            clave, _, valor = linea.strip().partition("=")
            if clave.strip() == "IDC_ALMACEN":
                return valor.strip().strip("\"'")
    return ""


DATOS = Path(_almacen()) / "datos" if _almacen() else RAIZ / "datos"
