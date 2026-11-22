"""Comprueba que la lógica de negocio se puede usar sin Django."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

CODIGO = """
import sys
import analisis.servicios.autoria
import analisis.servicios.conceptos
import analisis.servicios.extraccion
import analisis.servicios.caracteristicas
import analisis.servicios.entrenamiento
import analisis.servicios.clasificador
import analisis.servicios.historial
import analisis.servicios.idc
import analisis.servicios.repositorio
import analisis.servicios.flujo
import analisis.servicios.exportacion
import refuerzo.servicios.contenido
import refuerzo.servicios.ejecutor
sys.exit(1 if any(m.split(".")[0] == "django" for m in sys.modules) else 0)
"""


def test_los_servicios_no_importan_django():
    proceso = subprocess.run(
        [sys.executable, "-c", CODIGO], cwd=RAIZ, capture_output=True, text=True
    )
    assert proceso.returncode == 0, proceso.stderr
