"""Carga del modelo entrenado y estimación de P(IA)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib

from .caracteristicas import RASGOS_VERSION


class ModeloNoDisponible(Exception):
    """No hay un modelo entrenado en la ruta configurada, o no sirve con este código."""


@dataclass(frozen=True)
class ModeloCargado:
    pipeline: object
    version: str
    es_demo: bool
    entrenado_en: str = ""
    metricas_cv: dict = field(default_factory=dict)
    rasgos_version: str = RASGOS_VERSION

    def predecir(self, entradas: list[dict]) -> list[float]:
        """Devuelve P(IA) para cada `{"codigo": ...}`."""
        if not entradas:
            return []
        clases = list(self.pipeline.classes_)
        probabilidades = self.pipeline.predict_proba(entradas)
        return [float(p) for p in probabilidades[:, clases.index(1)]]


def cargar_modelo(ruta: str | Path) -> ModeloCargado:
    ruta = Path(ruta)
    if not ruta.exists():
        raise ModeloNoDisponible(
            f"No existe el modelo en {ruta}. "
            "Ejecuta scripts/crear_corpus_demo.py y scripts/entrenar_modelo.py."
        )
    paquete = joblib.load(ruta)
    # Un modelo de otra versión espera otro vector: fallaría o, peor, mediría mal.
    rasgos = paquete.get("rasgos_version", "rasgos-v1")
    if rasgos != RASGOS_VERSION:
        raise ModeloNoDisponible(
            f"El modelo de {ruta} se entrenó con {rasgos} y este código usa "
            f"{RASGOS_VERSION}. Vuelve a entrenarlo con scripts/entrenar_modelo.py."
        )
    return ModeloCargado(
        pipeline=paquete["pipeline"],
        version=paquete["version"],
        es_demo=paquete["es_demo"],
        entrenado_en=paquete.get("entrenado_en", ""),
        metricas_cv=paquete.get("metricas_cv", {}),
        rasgos_version=rasgos,
    )
