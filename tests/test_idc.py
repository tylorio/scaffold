import pytest

from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.idc import (
    DATOS_INSUFICIENTES,
    DEBIL,
    NO_DEBIL,
    Parametros,
    calcular_idc,
    calcular_resultados,
)


def fragmentos_de(concepto, altos, bajos):
    """Crea fragmentos de un concepto: `altos` con P=0.9 y `bajos` con P=0.1."""
    return [(0.9, {concepto})] * altos + [(0.1, {concepto})] * bajos


def por_concepto(resultado):
    return {c.concepto: c for c in resultado.conceptos}


# Cálculo del IDC

def test_idc_es_la_proporcion_sobre_theta():
    assert calcular_idc([0.9, 0.8, 0.2, 0.1], 0.5) == 0.5


def test_theta_es_inclusivo():
    assert calcular_idc([0.5], 0.5) == 1.0


def test_idc_sin_fragmentos_es_none():
    assert calcular_idc([], 0.5) is None


def test_theta_configurable_cambia_el_resultado():
    probabilidades = [0.9, 0.6, 0.4]
    assert calcular_idc(probabilidades, 0.5) == pytest.approx(2 / 3)
    assert calcular_idc(probabilidades, 0.7) == pytest.approx(1 / 3)


def test_idc_global_incluye_fragmentos_sin_concepto():
    resultado = calcular_resultados([(0.9, set()), (0.1, set())])
    assert resultado.idc_global == 0.5
    assert resultado.n_fragmentos == 2
    assert resultado.n_ia == 1


def test_idc_por_concepto_usa_solo_sus_fragmentos():
    resultado = por_concepto(calcular_resultados(
        fragmentos_de(RECURSION, 3, 1) + fragmentos_de(ESTRUCTURAS, 1, 3)
    ))
    assert resultado[RECURSION].idc == 0.75
    assert resultado[ESTRUCTURAS].idc == 0.25


def test_fragmento_con_varios_conceptos_cuenta_en_cada_uno():
    resultado = por_concepto(calcular_resultados(
        [(0.9, {RECURSION, ESTRUCTURAS})] * 3
    ))
    assert resultado[RECURSION].n_fragmentos == 3
    assert resultado[ESTRUCTURAS].n_fragmentos == 3


def test_repositorio_vacio_no_falla():
    resultado = calcular_resultados([])
    assert resultado.idc_global is None
    assert resultado.reforzados == []
    assert len(resultado.no_reforzados) == 3


# Conceptos débiles

def test_concepto_debil_si_idc_alcanza_lambda():
    resultado = por_concepto(calcular_resultados(fragmentos_de(RECURSION, 2, 2)))
    assert resultado[RECURSION].idc == 0.5
    assert resultado[RECURSION].estado == DEBIL


def test_concepto_no_debil_bajo_lambda():
    resultado = por_concepto(calcular_resultados(fragmentos_de(RECURSION, 1, 3)))
    assert resultado[RECURSION].estado == NO_DEBIL


def test_menos_de_m_fragmentos_son_datos_insuficientes_y_sin_idc():
    resultado = por_concepto(calcular_resultados(fragmentos_de(RECURSION, 2, 0)))
    assert resultado[RECURSION].estado == DATOS_INSUFICIENTES
    assert resultado[RECURSION].idc is None
    assert resultado[RECURSION].n_fragmentos == 2


def test_exactamente_m_fragmentos_se_calcula():
    resultado = por_concepto(calcular_resultados(fragmentos_de(RECURSION, 3, 0)))
    assert resultado[RECURSION].idc == 1.0
    assert resultado[RECURSION].estado == DEBIL


def test_lambda_y_m_son_configurables():
    fragmentos = fragmentos_de(RECURSION, 1, 3)
    parametros = Parametros(lambda_=0.2, m=5)
    assert por_concepto(calcular_resultados(fragmentos, parametros))[
        RECURSION
    ].estado == DATOS_INSUFICIENTES

    parametros = Parametros(lambda_=0.2, m=4)
    assert por_concepto(calcular_resultados(fragmentos, parametros))[
        RECURSION
    ].estado == DEBIL


# Selección de conceptos a reforzar

def test_tres_debiles_refuerza_los_dos_de_mayor_idc():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 3, 1)      # 0.75
        + fragmentos_de(ESTRUCTURAS, 4, 0)  # 1.00
        + fragmentos_de(EXCEPCIONES, 2, 2)  # 0.50
    )
    assert all(c.estado == DEBIL for c in resultado.conceptos)
    assert set(resultado.reforzados) == {ESTRUCTURAS, RECURSION}
    assert resultado.no_reforzados == [EXCEPCIONES]


def test_tres_debiles_con_empate_total_deja_uno_sin_reforzar_y_es_reproducible():
    fragmentos = (
        fragmentos_de(RECURSION, 3, 0)
        + fragmentos_de(ESTRUCTURAS, 3, 0)
        + fragmentos_de(EXCEPCIONES, 3, 0)
    )
    primera = calcular_resultados(fragmentos)
    segunda = calcular_resultados(list(reversed(fragmentos)))
    assert len(primera.reforzados) == 2
    assert len(primera.no_reforzados) == 1
    assert primera.reforzados == segunda.reforzados


def test_empate_de_idc_prefiere_el_concepto_con_mas_fragmentos():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 3, 0)
        + fragmentos_de(ESTRUCTURAS, 6, 0)
        + fragmentos_de(EXCEPCIONES, 5, 0)
    )
    assert resultado.no_reforzados == [RECURSION]


def test_dos_debiles_se_refuerzan_ambos():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 4, 0)
        + fragmentos_de(ESTRUCTURAS, 3, 1)
        + fragmentos_de(EXCEPCIONES, 0, 4)
    )
    assert set(resultado.reforzados) == {RECURSION, ESTRUCTURAS}
    assert resultado.no_reforzados == [EXCEPCIONES]


def test_un_debil_se_refuerza_solo_ese():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 4, 0)
        + fragmentos_de(ESTRUCTURAS, 0, 4)
        + fragmentos_de(EXCEPCIONES, 0, 4)
    )
    assert resultado.reforzados == [RECURSION]


def test_ningun_debil_no_refuerza_nada():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 0, 4) + fragmentos_de(ESTRUCTURAS, 0, 4)
    )
    assert resultado.reforzados == []


def test_datos_insuficientes_nunca_se_refuerza():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 2, 0) + fragmentos_de(ESTRUCTURAS, 4, 0)
    )
    assert resultado.reforzados == [ESTRUCTURAS]


@pytest.mark.parametrize("altos", [(4, 4, 4), (4, 3, 2), (3, 3, 3), (4, 0, 4)])
def test_siempre_queda_al_menos_un_concepto_sin_reforzar(altos):
    a, b, c = altos
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, a, 4 - a if a < 4 else 0)
        + fragmentos_de(ESTRUCTURAS, b, 4 - b if b < 4 else 0)
        + fragmentos_de(EXCEPCIONES, c, 4 - c if c < 4 else 0)
    )
    assert len(resultado.reforzados) <= 2
    assert len(resultado.no_reforzados) >= 1
