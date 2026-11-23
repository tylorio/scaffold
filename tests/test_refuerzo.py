import contextlib
import io

import pytest

from analisis.servicios.conceptos import (
    CONCEPTOS,
    ESTRUCTURAS,
    EXCEPCIONES,
    RECURSION,
)
from refuerzo.servicios.contenido import PLANTILLAS
from refuerzo.servicios.ejecutor import ejecutar_solucion, usa_concepto

SOLUCIONES = {
    "rec-facil": """
def suma_digitos(n):
    if n < 10:
        return n
    return n % 10 + suma_digitos(n // 10)
""",
    "rec-medio": """
def es_palindromo(texto):
    if len(texto) < 2:
        return True
    return texto[0] == texto[-1] and es_palindromo(texto[1:-1])
""",
    "rec-dificil": """
def aplanar(lista):
    resultado = []
    for elemento in lista:
        if isinstance(elemento, list):
            resultado.extend(aplanar(elemento))
        else:
            resultado.append(elemento)
    return resultado
""",
    "est-facil": """
def unicos(lista):
    vistos = set()
    resultado = []
    for elemento in lista:
        if elemento not in vistos:
            vistos.add(elemento)
            resultado.append(elemento)
    return resultado
""",
    "est-medio": """
def mas_frecuente(palabras):
    conteo = {}
    for palabra in palabras:
        conteo[palabra] = conteo.get(palabra, 0) + 1
    if not conteo:
        return None
    return max(conteo, key=conteo.get)
""",
    "est-dificil": """
def agrupar_anagramas(palabras):
    grupos = {}
    for palabra in palabras:
        grupos.setdefault(''.join(sorted(palabra)), []).append(palabra)
    return list(grupos.values())
""",
    "exc-facil": """
def dividir_seguro(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
""",
    "exc-medio": """
def convertir_enteros(valores):
    resultado = []
    for valor in valores:
        try:
            resultado.append(int(valor))
        except (ValueError, TypeError):
            pass
    return resultado
""",
    "exc-dificil": """
class SaldoInsuficienteError(Exception):
    pass

def retirar(saldo, monto):
    if monto <= 0:
        raise ValueError("monto inválido")
    if monto > saldo:
        raise SaldoInsuficienteError("saldo insuficiente")
    return saldo - monto
""",
}

TODOS_LOS_EJERCICIOS = [
    (concepto, ejercicio)
    for concepto, plantilla in PLANTILLAS.items()
    for ejercicio in plantilla.ejercicios
]
EJERCICIO_RAPIDO = PLANTILLAS[RECURSION].ejercicios[0]


# Contenido

def test_hay_material_para_los_tres_conceptos():
    assert set(PLANTILLAS) == set(CONCEPTOS)


@pytest.mark.parametrize("concepto", CONCEPTOS)
def test_cada_plantilla_tiene_la_estructura_pedida(concepto):
    plantilla = PLANTILLAS[concepto]
    assert plantilla.explicacion
    assert len(plantilla.ejemplos) == 2
    assert [e.nivel for e in plantilla.ejercicios] == ["Fácil", "Medio", "Difícil"]
    assert all(len(e.casos) >= 3 for e in plantilla.ejercicios)


@pytest.mark.parametrize(
    "ejemplo",
    [e for p in PLANTILLAS.values() for e in p.ejemplos],
    ids=lambda e: e.titulo,
)
def test_los_ejemplos_resueltos_producen_la_salida_que_muestran(ejemplo):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        exec(ejemplo.codigo, {})
    assert salida.getvalue().strip() == ejemplo.salida


@pytest.mark.parametrize(
    "concepto,ejercicio", TODOS_LOS_EJERCICIOS, ids=[e.id for _, e in TODOS_LOS_EJERCICIOS]
)
def test_la_solucion_de_referencia_pasa_todos_los_casos(concepto, ejercicio):
    resultado = ejecutar_solucion(SOLUCIONES[ejercicio.id], ejercicio, tiempo_limite=20)
    assert resultado.error == ""
    assert resultado.pasados == resultado.total
    assert usa_concepto(SOLUCIONES[ejercicio.id], concepto)


@pytest.mark.parametrize(
    "concepto,ejercicio", TODOS_LOS_EJERCICIOS, ids=[e.id for _, e in TODOS_LOS_EJERCICIOS]
)
def test_la_plantilla_sin_resolver_no_pasa_todos_los_casos(concepto, ejercicio):
    resultado = ejecutar_solucion(ejercicio.plantilla, ejercicio, tiempo_limite=20)
    assert resultado.pasados < resultado.total


# Ejecutor

def test_solucion_parcial_reporta_cuantos_paso():
    codigo = "def suma_digitos(n):\n    return n\n"
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 2
    assert resultado.total == 4
    assert [c["paso"] for c in resultado.casos] == [True, True, False, False]


def test_error_de_sintaxis_se_informa():
    resultado = ejecutar_solucion("def roto(:", EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 0
    assert "SyntaxError" in resultado.error


def test_funcion_faltante_se_informa():
    resultado = ejecutar_solucion("x = 1", EJERCICIO_RAPIDO, tiempo_limite=20)
    assert "suma_digitos" in resultado.error


def test_excepcion_en_un_caso_no_detiene_los_demas():
    codigo = "def suma_digitos(n):\n    if n == 7:\n        raise KeyError\n    return 0\n"
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 1
    assert "KeyError" in resultado.casos[1]["obtenido"]


def test_bucle_infinito_se_corta_por_tiempo():
    codigo = "def suma_digitos(n):\n    while True:\n        pass\n"
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=1)
    assert resultado.pasados == 0
    assert "límite" in resultado.error


def test_recursion_infinita_falla_sin_romper_el_ejecutor():
    codigo = "def suma_digitos(n):\n    return suma_digitos(n)\n"
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 0
    assert "RecursionError" in resultado.casos[0]["obtenido"]


def test_print_del_estudiante_no_corrompe_el_resultado():
    codigo = (
        "print('al importar')\n"
        "def suma_digitos(n):\n"
        "    print('ruido', 'ñandú')\n"
        "    return 0\n"
    )
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.error == ""
    assert resultado.pasados == 1


def test_exit_del_estudiante_no_cuenta_como_exito():
    codigo = "import os\ndef suma_digitos(n):\n    os._exit(0)\n"
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 0
    assert resultado.error


def test_el_codigo_no_hereda_el_entorno(monkeypatch):
    monkeypatch.setenv("SECRETO_DE_PRUEBA", "valor")
    codigo = (
        "import os\n"
        "def suma_digitos(n):\n"
        "    return 0 if 'SECRETO_DE_PRUEBA' in os.environ else n\n"
    )
    resultado = ejecutar_solucion(codigo, EJERCICIO_RAPIDO, tiempo_limite=20)
    assert resultado.pasados == 2  # devuelve n: acierta 0 y 7


def test_excepcion_propia_se_compara_por_nombre_y_herencia():
    ejercicio = PLANTILLAS[EXCEPCIONES].ejercicios[2]
    codigo = SOLUCIONES["exc-dificil"].replace(
        "class SaldoInsuficienteError(Exception):\n    pass\n",
        "class Base(Exception):\n    pass\n\n"
        "class SaldoInsuficienteError(Base):\n    pass\n",
    )
    assert ejecutar_solucion(codigo, ejercicio, tiempo_limite=20).pasados == 5


def test_no_lanzar_la_excepcion_esperada_falla():
    ejercicio = PLANTILLAS[EXCEPCIONES].ejercicios[2]
    codigo = "def retirar(saldo, monto):\n    return saldo - monto\n"
    assert ejecutar_solucion(codigo, ejercicio, tiempo_limite=20).pasados == 2


def test_devolver_uno_en_vez_de_true_falla():
    ejercicio = PLANTILLAS[RECURSION].ejercicios[1]
    codigo = "def es_palindromo(texto):\n    return 1\n"
    assert ejecutar_solucion(codigo, ejercicio, tiempo_limite=20).pasados == 0


# Uso del concepto en la solución

def test_detecta_solucion_iterativa_en_ejercicio_de_recursion():
    codigo = "def suma_digitos(n):\n    return sum(int(c) for c in str(n))\n"
    assert not usa_concepto(codigo, RECURSION)
    # Un generador sobre una cadena no está en la lista cerrada de D5.
    assert not usa_concepto(codigo, ESTRUCTURAS)


def test_detecta_estructuras_en_una_solucion_con_diccionario():
    codigo = "def contar(xs):\n    d = {}\n    for x in xs:\n        d[x] = d.get(x, 0) + 1\n    return d\n"
    assert usa_concepto(codigo, ESTRUCTURAS)


def test_codigo_invalido_no_usa_ningun_concepto():
    assert not usa_concepto("def roto(:", RECURSION)
