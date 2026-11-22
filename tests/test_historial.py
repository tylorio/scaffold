"""Índice de delegación por historial (D9, P10)."""
import math

import pytest
from git import Actor, Repo

from analisis.servicios.historial import (
    HISTORIAL_VERSION,
    UMBRAL_LINEAS,
    UMBRALES_SENSIBILIDAD,
    indice_por_historial,
)
from analisis.servicios.repositorio import abrir_repositorio

AUTOR = Actor("Persona Real", "persona@example.invalid")


def test_umbral_fijado_a_priori_con_su_sensibilidad():
    assert (UMBRAL_LINEAS, UMBRALES_SENSIBILIDAD) == (30, (15, 60))


def test_proporcion_de_lineas_en_commits_grandes():
    lineas = [10] * 6 + [20] * 2 + [40] * 2  # 10 líneas propias
    indice = indice_por_historial([10, 20, 40], lineas)
    assert indice.proporcion_lineas == 0.2
    assert indice.proporcion_lineas_15 == 0.4
    assert indice.proporcion_lineas_60 == 0.0
    assert indice.n_lineas_con_historial == 10
    assert indice.version == HISTORIAL_VERSION


def test_media_del_logaritmo_sin_umbral():
    indice = indice_por_historial([0, 9, None], [])
    assert indice.media_log_insercion == pytest.approx((math.log1p(0) + math.log1p(9)) / 2)
    assert indice.n_fragmentos_con_historial == 2


def test_sin_historial_no_hay_indice():
    indice = indice_por_historial([None, None], [])
    assert (indice.proporcion_lineas, indice.media_log_insercion) == (None, None)
    assert (indice.n_lineas_con_historial, indice.n_fragmentos_con_historial) == (0, 0)


def confirmar(repo, carpeta, nombre, contenido):
    (carpeta / nombre).write_text(contenido, encoding="utf-8")
    repo.index.add([nombre])
    repo.index.commit(nombre, author=AUTOR, committer=AUTOR)


def test_cada_linea_toma_el_tamano_del_commit_que_la_escribio(tmp_path):
    grande = "def grande():\n" + "    x = 1\n" * 38 + "    return x\n"  # 40 líneas
    with Repo.init(tmp_path) as repo:
        confirmar(repo, tmp_path, "a.py", "def a():\n    y = 1\n    return y\n")
        confirmar(repo, tmp_path, "b.py", grande)

    with abrir_repositorio(str(tmp_path)) as repositorio:
        assert repositorio.inserciones_por_linea("a.py", 1, 3) == [3, 3, 3]
        lineas_b = repositorio.inserciones_por_linea("b.py", 1, 40)
        assert lineas_b == [40] * 40
        indice = indice_por_historial([3, 40], [3, 3, 3] + lineas_b)

    assert indice.proporcion_lineas == pytest.approx(40 / 43)


def test_carpeta_sin_historial_no_tiene_inserciones(tmp_path):
    (tmp_path / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    with abrir_repositorio(str(tmp_path)) as repositorio:
        assert repositorio.inserciones_por_linea("a.py", 1, 2) == []
