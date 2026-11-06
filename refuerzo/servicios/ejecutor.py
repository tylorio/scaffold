"""Ejecuta soluciones en un subproceso con tiempo límite.

ESTO NO ES UN SANDBOX. El tiempo límite corta bucles infinitos, pero el código
corre con los permisos del usuario que levantó el servidor: puede leer y borrar
archivos o usar la red. Solo sirve para un prototipo en una máquina controlada.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from analisis.servicios.extraccion import ErrorSintaxis, extraer_funciones

from .contenido import Ejercicio

CORREDOR = Path(__file__).with_name("corredor.py")
TIEMPO_LIMITE = 5.0


@dataclass(frozen=True)
class ResultadoEjecucion:
    pasados: int
    total: int
    casos: list[dict] = field(default_factory=list)
    error: str = ""


def _interprete() -> str:
    """Devuelve el Python real, no el lanzador del entorno virtual.

    En Windows, `.venv\\Scripts\\python.exe` es un lanzador que crea otro proceso.
    Al vencer el tiempo límite solo moriría el lanzador y el bucle infinito del
    estudiante seguiría corriendo huérfano.
    """
    return getattr(sys, "_base_executable", None) or sys.executable


def _entorno(carpeta: str) -> dict[str, str]:
    """Entorno mínimo: el código del estudiante no hereda claves ni rutas."""
    entorno = {"TEMP": carpeta, "TMP": carpeta, "PYTHONDONTWRITEBYTECODE": "1"}
    if "SYSTEMROOT" in os.environ:  # Python no arranca en Windows sin esta variable
        entorno["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return entorno


def ejecutar_solucion(
    codigo: str, ejercicio: Ejercicio, tiempo_limite: float = TIEMPO_LIMITE
) -> ResultadoEjecucion:
    total = len(ejercicio.casos)
    carga = json.dumps({
        "codigo": codigo,
        "funcion": ejercicio.funcion,
        "casos": [
            {"args": list(c.args), "esperado": c.esperado, "lanza": c.lanza}
            for c in ejercicio.casos
        ],
    })

    with tempfile.TemporaryDirectory(
        prefix="idc_solucion_", ignore_cleanup_errors=True
    ) as carpeta:
        try:
            proceso = subprocess.run(
                [_interprete(), "-I", str(CORREDOR)],
                input=carga,
                capture_output=True,
                text=True,
                timeout=tiempo_limite,
                cwd=carpeta,
                env=_entorno(carpeta),
            )
        except subprocess.TimeoutExpired:
            return ResultadoEjecucion(
                0, total,
                error=(
                    f"Se superó el límite de {tiempo_limite:g} s. "
                    "Revisa si hay un bucle o una recursión que no termina."
                ),
            )

    try:
        respuesta = json.loads(proceso.stdout)
    except (json.JSONDecodeError, TypeError):
        return ResultadoEjecucion(
            0, total, error="El programa terminó sin entregar un resultado."
        )

    if "error" in respuesta:
        return ResultadoEjecucion(0, total, error=respuesta["error"])
    casos = respuesta["casos"]
    return ResultadoEjecucion(sum(c["paso"] for c in casos), total, casos)


def usa_concepto(codigo: str, concepto: str) -> bool:
    """Indica si la solución usa el concepto, para detectar atajos.

    Una solución iterativa puede pasar todas las pruebas de un ejercicio de
    recursión; esto permite avisarlo sin rechazarla.
    """
    try:
        fragmentos = extraer_funciones(codigo)
    except ErrorSintaxis:
        return False
    return any(concepto in f.conceptos for f in fragmentos)
