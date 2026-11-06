"""Convierte demo_repo/ en un repositorio Git con un historial de ejemplo.

El análisis también funciona sobre la carpeta sin Git, pero entonces no hay
tamaño de inserción. Este script crea commits pequeños y un commit grande para
que esa característica se vea en el flujo. Si el historial ya existe, no hace nada.

Uso:
    python scripts/preparar_demo_repo.py
"""
from pathlib import Path

from git import Actor, Repo

RAIZ = Path(__file__).resolve().parent.parent
DEMO = RAIZ / "demo_repo"
AUTOR = Actor("Demo", "demo@example.invalid")

COMMITS = (
    (["utilidades.py"], "Funciones básicas"),
    (["entrada_datos.py"], "Validación de entradas"),
    (["recursion_tareas.py", "colecciones.py"], "Tareas de recursión y colecciones"),
)


def preparar(ruta: Path = DEMO) -> bool:
    """Crea el historial. Devuelve False si el repositorio ya existía."""
    if (ruta / ".git").exists():
        return False
    with Repo.init(ruta) as repo:
        for archivos, mensaje in COMMITS:
            repo.index.add(archivos)
            repo.index.commit(mensaje, author=AUTOR, committer=AUTOR)
    return True


def main() -> None:
    if preparar():
        print(f"Historial creado en {DEMO}.")
    else:
        print(f"{DEMO} ya tiene historial; no se cambió nada.")


if __name__ == "__main__":
    main()
