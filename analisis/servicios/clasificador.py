"""Carga del modelo entrenado y estimación de P(IA)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib


class ModeloNoDisponible(Exception):
    """No hay un modelo entrenado en la ruta configurada."""


@dataclass(frozen=True)
class ModeloCargado:
    pipeline: object
    version: str
    es_demo: bool
    entrenado_en: str = ""
    metricas_cv: dict = field(default_factory=dict)

    def predecir(self, entradas: list[dict]) -> list[float]:
        """Devuelve P(IA) para cada `{"codigo": ..., "insercion_commit": ...}`."""
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
    return ModeloCargado(
        pipeline=paquete["pipeline"],
        version=paquete["version"],
        es_demo=paquete["es_demo"],
        entrenado_en=paquete.get("entrenado_en", ""),
        metricas_cv=paquete.get("metricas_cv", {}),
    )
