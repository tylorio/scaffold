"""Entrena el clasificador y lo guarda con joblib.

Uso:
    python scripts/entrenar_modelo.py
    python scripts/entrenar_modelo.py --corpus datos/corpus_real.jsonl
        --salida datos/modelos/modelo_real.joblib --version real-v1 --real
"""
import argparse

from _ruta import RAIZ
from analisis.servicios.entrenamiento import (
    cargar_corpus,
    entrenar_modelo,
    guardar_modelo,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el clasificador P(IA).")
    parser.add_argument("--corpus", default=RAIZ / "datos" / "corpus_demo.jsonl")
    parser.add_argument(
        "--salida", default=RAIZ / "datos" / "modelos" / "modelo_demo.joblib"
    )
    parser.add_argument("--version", default="demo-v1")
    parser.add_argument(
        "--real", action="store_true",
        help="Marca el modelo como real: la interfaz deja de mostrar el aviso de demo.",
    )
    args = parser.parse_args()

    muestras = cargar_corpus(args.corpus)
    paquete = entrenar_modelo(muestras, version=args.version, es_demo=not args.real)
    guardar_modelo(paquete, args.salida)

    print(f"Modelo guardado en {args.salida} ({len(muestras)} muestras).")
    for nombre, valor in paquete["metricas_cv"].items():
        print(f"  {nombre} (validación cruzada): {valor:.3f}")
    if paquete["es_demo"]:
        print("  Aviso: el corpus es sintético; estas métricas no dicen nada real.")


if __name__ == "__main__":
    main()
