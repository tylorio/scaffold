import subprocess
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import pytest

from analisis.servicios.conceptos import CONCEPTOS, ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.idc import (
    CASO_A,
    CASO_B,
    CASO_C,
    CONFIRMATORIO,
    DATOS_INSUFICIENTES,
    DEBIL,
    EXPLORATORIO,
    NO_DEBIL,
    Parametros,
    ResultadoConcepto,
    ResultadoIDC,
    calcular_idc,
    derivar_semilla,
    intervalo_wilson,
    repartir_conceptos,
    sortear_orden,
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


# Asignación escalonada (D2, R3, ADR-004)

def resultado(**estados):
    """ResultadoIDC con el estado indicado por concepto; el resto, insuficiente."""
    return ResultadoIDC(None, 0, 0, tuple(
        ResultadoConcepto(c, 5, 0, None, estados.get(c, DATOS_INSUFICIENTES))
        for c in CONCEPTOS
    ))


TRES_DEBILES = resultado(recursion=DEBIL, estructuras_datos=DEBIL, excepciones=DEBIL)


def test_caso_a_con_tres_debiles_refuerza_dos_y_deja_uno_de_control():
    reparto = repartir_conceptos(TRES_DEBILES, semilla=1)
    assert reparto.caso == CASO_A
    assert (len(reparto.reforzados), len(reparto.control)) == (2, 1)
    assert set(reparto.reforzados) | set(reparto.control) == set(CONCEPTOS)


def test_caso_a_con_dos_debiles_deja_sin_asignar_al_no_debil():
    reparto = repartir_conceptos(
        resultado(recursion=DEBIL, excepciones=DEBIL, estructuras_datos=NO_DEBIL), 1
    )
    assert reparto.caso == CASO_A
    assert set(reparto.reforzados) | set(reparto.control) == {RECURSION, EXCEPCIONES}


def test_caso_b_sortea_entre_los_calculables():
    reparto = repartir_conceptos(resultado(recursion=DEBIL, excepciones=NO_DEBIL), 1)
    assert reparto.caso == CASO_B
    assert set(reparto.reforzados) | set(reparto.control) == {RECURSION, EXCEPCIONES}


def test_caso_b_sin_ningun_debil():
    reparto = repartir_conceptos(
        resultado(recursion=NO_DEBIL, estructuras_datos=NO_DEBIL, excepciones=NO_DEBIL), 1
    )
    assert reparto.caso == CASO_B
    assert (len(reparto.reforzados), len(reparto.control)) == (2, 1)


@pytest.mark.parametrize("estados", [{}, {"recursion": DEBIL}, {"excepciones": NO_DEBIL}])
def test_caso_c_con_menos_de_dos_calculables_sortea_entre_los_tres(estados):
    reparto = repartir_conceptos(resultado(**estados), 1)
    assert reparto.caso == CASO_C
    assert set(reparto.reforzados) | set(reparto.control) == set(CONCEPTOS)


def test_modo_exploratorio_omite_el_caso_a():
    reparto = repartir_conceptos(TRES_DEBILES, 1, EXPLORATORIO)
    assert (reparto.caso, reparto.modo) == (CASO_B, EXPLORATORIO)


def test_modo_exploratorio_con_un_calculable_va_al_caso_c():
    assert repartir_conceptos(resultado(recursion=DEBIL), 1, EXPLORATORIO).caso == CASO_C


def test_modo_desconocido_da_error():
    with pytest.raises(ValueError):
        repartir_conceptos(TRES_DEBILES, 1, "otro")


@pytest.mark.parametrize("estados", list(product([DEBIL, NO_DEBIL, DATOS_INSUFICIENTES], repeat=3)))
@pytest.mark.parametrize("modo", [CONFIRMATORIO, EXPLORATORIO])
def test_siempre_hay_hasta_dos_reforzados_y_al_menos_un_control(estados, modo):
    reparto = repartir_conceptos(resultado(**dict(zip(CONCEPTOS, estados))), 7, modo)
    assert 1 <= len(reparto.reforzados) <= 2
    assert len(reparto.control) >= 1
    assert not set(reparto.reforzados) & set(reparto.control)


def test_la_misma_semilla_reproduce_el_reparto():
    for semilla in range(30):
        assert repartir_conceptos(TRES_DEBILES, semilla) == repartir_conceptos(
            TRES_DEBILES, semilla
        )


def test_el_control_sale_al_azar_y_cualquier_concepto_puede_serlo():
    """Si dependiera del IDC, los reforzados mejorarían por regresión a la media."""
    controles = {repartir_conceptos(TRES_DEBILES, semilla).control for semilla in range(100)}
    assert controles == {(RECURSION,), (ESTRUCTURAS,), (EXCEPCIONES,)}


def test_el_reparto_esta_equilibrado():
    dos = resultado(recursion=DEBIL, estructuras_datos=DEBIL)
    conteo = Counter(repartir_conceptos(dos, semilla).control for semilla in range(1000))
    assert 400 < conteo[(RECURSION,)] < 600


# Semillas y orden de las formas (R2)

RAIZ = Path(__file__).resolve().parent.parent


def en_otro_proceso(codigo):
    proceso = subprocess.run(
        [sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True,
    )
    assert proceso.returncode == 0, proceso.stderr
    return proceso.stdout.strip()


def test_la_semilla_derivada_es_igual_en_otro_proceso():
    otra = en_otro_proceso(
        "from analisis.servicios.idc import derivar_semilla;"
        "print(derivar_semilla(123, 'conceptos', 'P01'))"
    )
    assert int(otra) == derivar_semilla(123, "conceptos", "P01")


def test_la_semilla_derivada_cabe_en_la_base_de_datos_y_separa_flujos():
    conceptos, orden = derivar_semilla(123, "conceptos", "P01"), derivar_semilla(123, "orden")
    assert conceptos != orden
    assert max(conceptos, orden) < 2**63


@pytest.mark.parametrize("n", range(1, 14))
@pytest.mark.parametrize("bloque", [2, 4])
def test_el_orden_queda_equilibrado(n, bloque):
    codigos = [f"P{i:02d}" for i in range(1, n + 1)]
    ordenes = sortear_orden(codigos, semilla_base=5, tamano_bloque=bloque)
    assert set(ordenes) == set(codigos)
    conteo = Counter(ordenes.values())
    assert abs(conteo["AB"] - conteo["BA"]) <= 1


def test_cada_bloque_completo_tiene_tantos_ab_como_ba():
    codigos = [f"P{i:02d}" for i in range(1, 13)]
    ordenes = sortear_orden(codigos, semilla_base=9, tamano_bloque=4)
    for inicio in range(0, 12, 4):
        bloque = [ordenes[c] for c in codigos[inicio:inicio + 4]]
        assert bloque.count("AB") == 2


def test_el_orden_no_depende_del_orden_de_entrada_y_se_reproduce():
    codigos = ["P03", "P01", "P02", "P04", "P05"]
    assert sortear_orden(codigos, 11) == sortear_orden(sorted(codigos), 11)


def test_el_orden_es_igual_en_otro_proceso():
    otro = en_otro_proceso(
        "from analisis.servicios.idc import sortear_orden;"
        "print(sorted(sortear_orden(['P01','P02','P03','P04','P05'], 42).items()))"
    )
    assert otro == str(sorted(sortear_orden(["P01", "P02", "P03", "P04", "P05"], 42).items()))


def test_distintas_semillas_dan_distintos_ordenes():
    codigos = [f"P{i:02d}" for i in range(1, 9)]
    assert len({tuple(sortear_orden(codigos, s).values()) for s in range(20)}) > 1


def test_tamano_de_bloque_invalido():
    with pytest.raises(ValueError):
        sortear_orden(["P01"], 1, tamano_bloque=3)


def test_resultado_lista_los_conceptos_debiles():
    resultado = calcular_resultados(
        fragmentos_de(RECURSION, 3, 0)
        + fragmentos_de(ESTRUCTURAS, 0, 3)
        + fragmentos_de(EXCEPCIONES, 2, 0)
    )
    assert resultado.debiles == [RECURSION]
