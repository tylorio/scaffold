"""Ejecuta soluciones: en el ejecutor aislado (ADR-005) o, solo en desarrollo, en local.

Con `EjecutorRemoto`, la solución va por HTTP al contenedor del ejecutor, sin red de
salida y con límites (08 §2). Sin él, corre en un subproceso local con tiempo límite.
ESE MODO NO ES UN SANDBOX: el código tiene los permisos del usuario que levantó el
servidor. Solo sirve para el desarrollo y las pruebas; el perfil de nube exige el
ejecutor aislado.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
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


@dataclass(frozen=True)
class EjecutorRemoto:
    url: str
    token: str = field(repr=False)


NO_DISPONIBLE = "El ejecutor no está disponible en este momento. Intenta de nuevo en unos minutos."


def _carga(codigo: str, ejercicio: Ejercicio) -> dict:
    return {
        "codigo": codigo,
        "funcion": ejercicio.funcion,
        "casos": [
            {"args": list(c.args), "esperado": c.esperado, "lanza": c.lanza}
            for c in ejercicio.casos
        ],
    }


def _ejecutar_remoto(
    codigo: str, ejercicio: Ejercicio, tiempo_limite: float, remoto: EjecutorRemoto
) -> ResultadoEjecucion:
    total = len(ejercicio.casos)
    peticion = urllib.request.Request(
        remoto.url.rstrip("/") + "/ejecutar",
        data=json.dumps({**_carga(codigo, ejercicio), "tiempo_limite_s": tiempo_limite}).encode(),
        headers={"Content-Type": "application/json", "X-Token": remoto.token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=tiempo_limite + 20) as respuesta:
            dato = json.loads(respuesta.read())
    except (urllib.error.URLError, OSError, ValueError):
        return ResultadoEjecucion(0, total, error=NO_DISPONIBLE)
    if not isinstance(dato, dict):
        return ResultadoEjecucion(0, total, error=NO_DISPONIBLE)
    casos = [c for c in dato.get("casos", []) if isinstance(c, dict)]
    return ResultadoEjecucion(
        sum(1 for c in casos if c.get("paso") is True), total, casos, dato.get("error") or "",
    )


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
    codigo: str, ejercicio: Ejercicio, tiempo_limite: float = TIEMPO_LIMITE,
    remoto: EjecutorRemoto | None = None,
) -> ResultadoEjecucion:
    if remoto is not None:
        return _ejecutar_remoto(codigo, ejercicio, tiempo_limite, remoto)
    total = len(ejercicio.casos)
    carga = json.dumps(_carga(codigo, ejercicio))

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
