"""Entrenamiento del clasificador.

Este es el ÚNICO módulo que hay que tocar para cambiar de corpus: cuando exista
el corpus real etiquetado basta con pasar otras muestras a `entrenar_modelo`
y marcarlas con `es_demo=False`. El resto del sistema solo usa `clasificador.py`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .caracteristicas import ExtractorCaracteristicas


@dataclass(frozen=True)
class Muestra:
    codigo: str
    etiqueta: int  # 1 = generado por IA, 0 = escrito por una persona
    insercion_commit: int | None = None


def cargar_corpus(ruta: str | Path) -> list[Muestra]:
    """Lee un corpus JSONL con las claves `codigo`, `etiqueta` e `insercion_commit`."""
    muestras = []
    with open(ruta, encoding="utf-8") as archivo:
        for linea in archivo:
            if linea.strip():
                dato = json.loads(linea)
                muestras.append(
                    Muestra(
                        codigo=dato["codigo"],
                        etiqueta=int(dato["etiqueta"]),
                        insercion_commit=dato.get("insercion_commit"),
                    )
                )
    return muestras


def construir_pipeline() -> Pipeline:
    return Pipeline([
        ("caracteristicas", ExtractorCaracteristicas()),
        ("imputador", SimpleImputer(
            strategy="median", add_indicator=True, keep_empty_features=True,
        )),
        ("escala", StandardScaler()),
        ("modelo", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def entrenar_modelo(
    muestras: list[Muestra], *, version: str, es_demo: bool
) -> dict:
    """Entrena con todas las muestras y devuelve el paquete que se guarda."""
    etiquetas = [m.etiqueta for m in muestras]
    if set(etiquetas) != {0, 1}:
        raise ValueError("El corpus necesita muestras de ambas clases (0 y 1).")

    entradas = [
        {"codigo": m.codigo, "insercion_commit": m.insercion_commit}
        for m in muestras
    ]
    pliegues = min(5, etiquetas.count(0), etiquetas.count(1))
    metricas = {}
    if pliegues >= 2:
        cv = StratifiedKFold(n_splits=pliegues, shuffle=True, random_state=42)
        puntajes = cross_validate(
            construir_pipeline(), entradas, etiquetas, cv=cv,
            scoring=("accuracy", "f1", "roc_auc"),
        )
        metricas = {
            "accuracy": float(puntajes["test_accuracy"].mean()),
            "f1": float(puntajes["test_f1"].mean()),
            "roc_auc": float(puntajes["test_roc_auc"].mean()),
        }

    pipeline = construir_pipeline().fit(entradas, etiquetas)
    return {
        "pipeline": pipeline,
        "version": version,
        "es_demo": es_demo,
        "entrenado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_muestras": len(muestras),
        "metricas_cv": metricas,
    }


def guardar_modelo(paquete: dict, ruta: str | Path) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(paquete, ruta)
