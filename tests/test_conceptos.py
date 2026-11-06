import pytest

from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.extraccion import extraer_funciones


def conceptos(fuente, nombre=None):
    fragmentos = extraer_funciones(fuente)
    if nombre is None:
        return fragmentos[0].conceptos
    return next(f.conceptos for f in fragmentos if f.nombre == nombre)


# Recursión

def test_recursion_directa():
    assert RECURSION in conceptos(
        "def f(n):\n    if n == 0:\n        return 0\n    return f(n - 1)\n"
    )


@pytest.mark.parametrize("receptor", ["self", "cls", "A"])
def test_recursion_en_metodo(receptor):
    fuente = f"class A:\n    def f(self, n):\n        return {receptor}.f(n - 1)\n"
    assert RECURSION in conceptos(fuente)


def test_llamar_a_otra_funcion_no_es_recursion():
    assert RECURSION not in conceptos("def f(n):\n    return g(n)\n")


def test_llamada_suelta_dentro_de_un_metodo_no_es_recursion():
    fuente = "class A:\n    def f(self):\n        return f()\n"
    assert RECURSION not in conceptos(fuente)


def test_metodo_homonimo_de_otro_objeto_no_es_recursion():
    fuente = "class A:\n    def f(self):\n        return self.b.f()\n"
    assert RECURSION not in conceptos(fuente)


def test_recursion_de_funcion_anidada_es_de_la_anidada():
    fuente = (
        "def f(n):\n"
        "    def g(i):\n        return g(i - 1)\n"
        "    return g(n)\n"
    )
    assert RECURSION not in conceptos(fuente, "f")
    assert RECURSION in conceptos(fuente, "f.g")


# Estructuras de datos

@pytest.mark.parametrize("cuerpo", [
    "x = [1, 2]",
    "x = {'a': 1}",
    "x = {1, 2}",
    "x = (1, 2)",
    "x = [i for i in y]",
    "x = {i: 1 for i in y}",
    "x = {i for i in y}",
    "x = sum(i for i in y)",
    "y.append(1)",
    "y.pop()",
    "x = y.keys()",
    "x = y.items()",
    "x = list(y)",
    "x = dict()",
    "x = deque()",
    "x = y[0]",
    "y[0] = 1",
])
def test_detecta_estructuras_de_datos(cuerpo):
    assert ESTRUCTURAS in conceptos(f"def f(y):\n    {cuerpo}\n")


def test_anotacion_de_contenedor_cuenta():
    assert ESTRUCTURAS in conceptos("def f(y: list[int]) -> int:\n    return 1\n")


def test_anotacion_como_texto_cuenta():
    assert ESTRUCTURAS in conceptos("def f(y: 'dict[str, int]'):\n    return 1\n")


def test_metodos_de_clase_contenedora():
    fuente = (
        "class Pila:\n"
        "    def __len__(self):\n        return 0\n"
        "    def vacia(self):\n        return True\n"
    )
    assert ESTRUCTURAS in conceptos(fuente, "Pila.vacia")


@pytest.mark.parametrize("cuerpo", [
    "return 1 + 2",
    "return a, b",
    "a, b = b, a",
    "x: int = 1",
])
def test_no_marca_estructuras_de_datos_sin_evidencia(cuerpo):
    assert ESTRUCTURAS not in conceptos(f"def f(a, b):\n    {cuerpo}\n")


def test_tupla_de_excepciones_no_cuenta_como_estructura():
    fuente = "def f():\n    try:\n        g()\n    except (A, B):\n        pass\n"
    assert ESTRUCTURAS not in conceptos(fuente)


# Manejo de excepciones

@pytest.mark.parametrize("cuerpo", [
    "try:\n        g()\n    except ValueError:\n        pass",
    "try:\n        g()\n    finally:\n        h()",
    "raise ValueError('x')",
])
def test_detecta_excepciones(cuerpo):
    assert EXCEPCIONES in conceptos(f"def f():\n    {cuerpo}\n")


def test_sin_excepciones():
    assert EXCEPCIONES not in conceptos("def f():\n    return 1\n")


def test_try_de_funcion_anidada_es_de_la_anidada():
    fuente = (
        "def f():\n"
        "    def g():\n        raise ValueError\n"
        "    return g\n"
    )
    assert EXCEPCIONES not in conceptos(fuente, "f")
    assert EXCEPCIONES in conceptos(fuente, "f.g")


# Combinaciones

def test_ningun_concepto():
    assert conceptos("def f(a):\n    return a + 1\n") == frozenset()


def test_varios_conceptos_a_la_vez():
    fuente = (
        "def f(l):\n"
        "    try:\n"
        "        return l[0] + f(l[1:])\n"
        "    except IndexError:\n"
        "        return 0\n"
    )
    assert conceptos(fuente) == {RECURSION, ESTRUCTURAS, EXCEPCIONES}
