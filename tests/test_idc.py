from collections import Counter

import pytest

from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.idc import (
    DATOS_INSUFICIENTES,
    DEBIL,
    NO_DEBIL,
    Parametros,
    calcular_idc,
    intervalo_wilson,
    repartir_conceptos,
)
from analisis.servicios.idc import calcular_resultados as calcular

# Estas pruebas verifican las reglas, no el valor por defecto de m: sin fijarlo,
# subir m haría que varias pasaran sin comprobar nada, porque nada se reforzaría.
PARAMETROS = Parametros(m=3)


def calcular_resultados(fragmentos, parametros=PARAMETROS):
    return calcular(fragmentos, parametros)


def test_m_por_defecto_es_5():
    assert Parametros().m == 5


def test_m_por_defecto_exige_evidencia_sobre_lambda():
    """Con 3 de 3 el intervalo aún incluye λ = 0,5; con 4 de 4 ya no."""
    assert intervalo_wilson(3, 3)[0] < Parametros().lambda_ < intervalo_wilson(4, 4)[0]


def test_con_m_por_defecto_cuatro_fragmentos_son_insuficientes():
    resultado = calcular(fragmentos_de(RECURSION, 4, 0))
    assert por_concepto(resultado)[RECURSION].estado == DATOS_INSUFICIENTES


def test_intervalo_wilson_valor_de_referencia():
    assert intervalo_wilson(5, 10) == pytest.approx((0.2366, 0.7634), abs=1e-4)


def test_intervalo_wilson_en_los_extremos_queda_entre_0_y_1():
    inferior, superior = intervalo_wilson(3, 3)
    assert inferior == pytest.approx(0.4385, abs=1e-4)
    assert superior == 1.0
    inferior, superior = intervalo_wilson(0, 4)
    assert inferior == 0.0
    assert superior == pytest.approx(0.4899, abs=1e-4)


def test_intervalo_wilson_sin_datos():
    assert intervalo_wilson(0, 0) is None


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
    assert resultado.debiles == []


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


# Reparto de conceptos

@pytest.mark.parametrize("debiles", [
    [RECURSION, ESTRUCTURAS, EXCEPCIONES],
    [EXCEPCIONES, RECURSION, ESTRUCTURAS],
])
def test_tres_debiles_refuerza_dos_y_deja_uno_de_control(debiles):
    reparto = repartir_conceptos(debiles, semilla=1)
    assert len(reparto.reforzados) == 2
    assert len(reparto.control) == 1
    assert set(reparto.reforzados) | set(reparto.control) == set(debiles)
    assert reparto.comparable


def test_dos_debiles_refuerza_uno_para_que_el_control_tambien_sea_debil():
    reparto = repartir_conceptos([RECURSION, EXCEPCIONES], semilla=1)
    assert len(reparto.reforzados) == 1
    assert len(reparto.control) == 1
    assert set(reparto.reforzados) | set(reparto.control) == {RECURSION, EXCEPCIONES}
    assert reparto.comparable


def test_un_debil_se_refuerza_pero_no_es_comparable():
    reparto = repartir_conceptos([RECURSION], semilla=1)
    assert reparto.reforzados == (RECURSION,)
    assert reparto.control == ()
    assert not reparto.comparable


def test_ningun_debil_no_reparte_nada():
    reparto = repartir_conceptos([], semilla=1)
    assert (reparto.reforzados, reparto.control) == ((), ())
    assert not reparto.comparable


def test_la_misma_semilla_reproduce_el_reparto_sin_importar_el_orden():
    debiles = [RECURSION, ESTRUCTURAS, EXCEPCIONES]
    for semilla in range(30):
        assert repartir_conceptos(debiles, semilla) == repartir_conceptos(
            list(reversed(debiles)), semilla
        )


def test_el_control_sale_al_azar_y_cualquier_concepto_puede_serlo():
    """Si dependiera del IDC, los reforzados mejorarían por regresión a la media."""
    controles = {
        repartir_conceptos([RECURSION, ESTRUCTURAS, EXCEPCIONES], semilla).control
        for semilla in range(100)
    }
    assert controles == {(RECURSION,), (ESTRUCTURAS,), (EXCEPCIONES,)}


def test_el_reparto_esta_equilibrado():
    conteo = Counter(
        repartir_conceptos([RECURSION, ESTRUCTURAS], semilla).control
        for semilla in range(1000)
    )
    assert 400 < conteo[(RECURSION,)] < 600


def test_resultado_lista_los_conceptos_debiles():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 3, 0)
        + fragmentos_de(ESTRUCTURAS, 0, 3)
        + fragmentos_de(EXCEPCIONES, 2, 0)
    )
    assert resultado.debiles == [RECURSION]
