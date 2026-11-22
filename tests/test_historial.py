"""Índice de delegación por historial (D9)."""
from analisis.servicios.historial import HISTORIAL_VERSION, indice_por_historial


def test_proporcion_de_inserciones_grandes():
    indice = indice_por_historial([5, 40, 30, 2], umbral_lineas=30)
    assert indice.valor == 0.5
    assert (indice.n_con_historial, indice.umbral_lineas) == (4, 30)
    assert indice.version == HISTORIAL_VERSION


def test_los_fragmentos_sin_historial_no_cuentan():
    indice = indice_por_historial([None, 100, None, 1], umbral_lineas=30)
    assert indice.valor == 0.5
    assert indice.n_con_historial == 2


def test_sin_historial_no_hay_indice():
    indice = indice_por_historial([None, None])
    assert indice.valor is None
    assert indice.n_con_historial == 0


def test_sin_fragmentos_no_hay_indice():
    assert indice_por_historial([]).valor is None
