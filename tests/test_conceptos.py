"""Reglas conceptos-v1 (decisiones del asesor D5, D6 y R4)."""
import pytest

from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.extraccion import extraer_funciones


def fragmento(fuente, nombre=None):
    fragmentos = extraer_funciones(fuente)
    if nombre is None:
        return fragmentos[0]
    return next(f for f in fragmentos if f.nombre == nombre)


def conceptos(fuente, nombre=None):
    return fragmento(fuente, nombre).conceptos


def en_funcion(cuerpo, parametros="y"):
    lineas = "\n".join(f"    {linea}" for linea in cuerpo.splitlines())
    return f"def f({parametros}):\n{lineas}\n"


# Recursión

def test_recursion_directa():
    assert RECURSION in conceptos(
        "def f(n):\n    if n == 0:\n        return 0\n    return f(n - 1)\n"
    )


@pytest.mark.parametrize("receptor", ["self", "cls", "A"])
def test_recursion_en_metodo(receptor):
    fuente = f"class A:\n    def f(self, n):\n        return {receptor}.f(n - 1)\n"
    assert RECURSION in conceptos(fuente)


def test_recursion_sobre_atributo():
    fuente = (
        "class Nodo:\n"
        "    def insertar(self, x):\n"
        "        if x < self.valor:\n"
        "            self.izquierda.insertar(x)\n"
    )
    assert RECURSION in conceptos(fuente)


def test_delegar_en_otro_objeto_con_el_mismo_nombre_no_es_recursion():
    """P8: el patrón servicio → repositorio no es recursión."""
    fuente = (
        "class Servicio:\n"
        "    def guardar(self, x):\n"
        "        return self.repositorio.guardar(x)\n"
    )
    assert RECURSION not in conceptos(fuente)


def test_metodo_homonimo_de_un_atributo_que_no_es_nodo_no_es_recursion():
    fuente = "class A:\n    def f(self):\n        return self.b.f()\n"
    assert RECURSION not in conceptos(fuente)


def test_recursion_al_recorrer_los_hijos():
    fuente = (
        "class Nodo:\n"
        "    def recorrer(self):\n"
        "        for h in self.hijos:\n"
        "            h.recorrer()\n"
    )
    assert RECURSION in conceptos(fuente)


def test_recursion_sobre_un_atributo_de_la_misma_clase():
    fuente = (
        "class Celda:\n"
        "    def agregar(self, valor):\n"
        "        if self.resto is None:\n"
        "            self.resto = Celda()\n"
        "        self.resto.agregar(valor)\n"
    )
    assert RECURSION in conceptos(fuente)


def test_recursion_mutua_marca_las_dos_funciones():
    fuente = (
        "def es_par(n):\n    return True if n == 0 else es_impar(n - 1)\n\n"
        "def es_impar(n):\n    return False if n == 0 else es_par(n - 1)\n"
    )
    assert RECURSION in conceptos(fuente, "es_par")
    assert RECURSION in conceptos(fuente, "es_impar")


def test_recursion_mutua_de_tres_funciones():
    fuente = (
        "def a(n):\n    return b(n)\n\n"
        "def b(n):\n    return c(n)\n\n"
        "def c(n):\n    return a(n - 1) if n else 0\n"
    )
    assert all(RECURSION in conceptos(fuente, nombre) for nombre in "abc")


def test_recursion_mutua_entre_metodos():
    fuente = (
        "class A:\n"
        "    def a(self, n):\n        return self.b(n)\n"
        "    def b(self, n):\n        return self.a(n - 1)\n"
    )
    assert RECURSION in conceptos(fuente, "A.a")


def test_llamar_a_una_funcion_recursiva_no_es_recursion_mutua():
    fuente = (
        "def f(n):\n    return f(n - 1)\n\n"
        "def g(n):\n    return f(n)\n"
    )
    assert RECURSION not in conceptos(fuente, "g")


def test_recursion_mutua_no_vuelve_trivial_una_funcion_de_una_linea():
    fuente = (
        "def a(n):\n    return b(n)\n\n"
        "def b(n):\n    return a(n - 1) if n else 0\n"
    )
    assert not fragmento(fuente, "a").trivial


def test_llamar_a_otra_funcion_no_es_recursion():
    assert RECURSION not in conceptos("def f(n):\n    return g(n)\n")


def test_llamada_suelta_dentro_de_un_metodo_no_es_recursion():
    fuente = "class A:\n    def f(self):\n        return f()\n"
    assert RECURSION not in conceptos(fuente)


def test_recursion_de_funcion_anidada_se_suma_a_la_externa():
    fuente = (
        "def f(n):\n"
        "    def g(i):\n        return g(i - 1)\n"
        "    return g(n)\n"
    )
    assert RECURSION in conceptos(fuente, "f")


# Estructuras de datos: los 8 elementos de la lista cerrada (D5)

@pytest.mark.parametrize("cuerpo", [
    # 1. Diccionario o conjunto construido y consultado
    "d = {}\nd['a'] = 1",
    "d = dict()\nreturn d['a']",
    "d = {'a': 1}\nreturn 'a' in d",
    "s = set()\nreturn y not in s",
    "d = {}\nreturn d.get(y)",
    "y.setdefault('a', []).append(1)",
    # 2. Comprensión de diccionario o de conjunto
    "return {i: 1 for i in y}",
    "return {i for i in y}",
    # 3. Ordenación o búsqueda
    "return sorted(y)",
    "y.sort()",
    "return bisect.bisect_left(y, 3)",
    "heapq.heappush(y, 1)",
    "return heappop(y)",
    # 4. collections
    "return deque(y)",
    "return Counter(y)",
    "return collections.defaultdict(list)",
    # 5. Colecciones anidadas
    "return [[0] * 3 for _ in y]",
    "return {'a': [1, 2]}",
    "y.append([1, 2])",
    # 6. Índices sobre listas
    "a = [3, 1]\nreturn a[0]",
    "a = list(y)\na[0], a[1] = a[1], a[0]",
    "y.append(1)\nreturn y[-1]",
    "partes = y.split(',')\nreturn partes[1]",
    # 7. Pila o cola
    "return y.pop()",
    "y.appendleft(1)",
])
def test_detecta_estructuras_de_datos(cuerpo):
    assert ESTRUCTURAS in conceptos(en_funcion(cuerpo))


def test_metodo_de_clase_contenedora_aunque_tenga_una_linea():
    fuente = (
        "class Pila:\n"
        "    def push(self, x):\n        self.items.append(x)\n"
        "    def vacia(self):\n        return not self.items\n"
    )
    assert ESTRUCTURAS in conceptos(fuente, "Pila.vacia")
    assert not fragmento(fuente, "Pila.vacia").trivial


@pytest.mark.parametrize("metodo", ["apilar", "desencolar", "peek", "frente", "__contains__"])
def test_clase_contenedora_con_nombres_en_espanol_o_ingles(metodo):
    """P7: la lista cerrada es bilingüe para no sesgar según el idioma del estudiante."""
    fuente = (
        "class Estructura:\n"
        f"    def {metodo}(self, *a):\n        return None\n"
        "    def vacia(self):\n        return not self.items\n"
    )
    assert ESTRUCTURAS in conceptos(fuente, "Estructura.vacia")


def test_un_metodo_cualquiera_no_hace_contenedora_a_la_clase():
    fuente = (
        "class Servicio:\n"
        "    def guardar(self):\n        return None\n"
        "    def vacia(self):\n        return not self.items\n"
    )
    assert ESTRUCTURAS not in conceptos(fuente, "Servicio.vacia")


@pytest.mark.parametrize("atributo", [
    "siguiente", "izquierda", "derecha", "next", "hijo", "padre", "parent", "children",
])
def test_nodos_enlazados(atributo):
    cuerpo = f"actual = y\nwhile actual:\n    actual = actual.{atributo}"
    assert ESTRUCTURAS in conceptos(en_funcion(cuerpo))


def test_nodo_de_un_arbol_comparado_con_none():
    fuente = (
        "def altura(nodo):\n"
        "    if nodo is None:\n        return 0\n"
        "    return 1 + max(altura(nodo.izquierda), altura(nodo.derecha))\n"
    )
    assert conceptos(fuente) == {RECURSION, ESTRUCTURAS}


def test_enlace_declarado_en_la_clase():
    fuente = (
        "class Nodo:\n"
        "    def __init__(self, valor):\n"
        "        self.valor = valor\n"
        "        self.siguiente = None\n"
        "    def ultimo(self):\n"
        "        return self.siguiente\n"
    )
    assert ESTRUCTURAS in conceptos(fuente, "Nodo.ultimo")


@pytest.mark.parametrize("fuente", [
    "def carpeta(ruta):\n    return ruta.parent\n",  # pathlib
    "def borde(rect):\n    return rect.left + rect.right\n",  # pygame
    "class Jugador:\n    def mover(self):\n        return self.rect.left + 1\n",
    "class Ventana:\n"  # tkinter
    "    def __init__(self, parent):\n        self.parent = parent\n"
    "    def cerrar(self):\n        return self.parent\n",
])
def test_nombres_de_nodo_fuera_de_un_contexto_de_nodos_no_cuentan(fuente):
    assert all(ESTRUCTURAS not in f.conceptos for f in extraer_funciones(fuente))


@pytest.mark.parametrize("cuerpo", [
    # Lo que D5 excluye de forma explícita
    "r = []\nfor x in y:\n    r.append(x)\nreturn r",
    "return [x * 2 for x in y]",
    "s = 'hola'\nreturn s[0]",
    "s = input()\nreturn s[1:3]",
    "return requests.get(y)['datos']",
    "return a, b",
    "a, b = b, a",
    # Construir sin consultar, o construir algo que no está en la lista
    "return list(set(y))",
    "x = [1, 2]",
    "x = (1, 2)\nreturn x[0]",
    "return sum(i for i in y)",
    "return y.keys()",
])
def test_no_cuenta_como_estructura_de_datos(cuerpo):
    assert ESTRUCTURAS not in conceptos(en_funcion(cuerpo, "y, a, b"))


def test_las_anotaciones_de_tipo_ya_no_cuentan():
    assert ESTRUCTURAS not in conceptos("def f(y: list[int]) -> int:\n    return 1\n")


def test_tupla_de_excepciones_no_cuenta_como_estructura():
    fuente = "def f():\n    try:\n        g()\n    except (A, B):\n        pass\n"
    assert ESTRUCTURAS not in conceptos(fuente)


# Definición amplia, solo para el análisis de sensibilidad (D5)

@pytest.mark.parametrize("cuerpo", [
    "r = []\nfor x in y:\n    r.append(x)\nreturn r",
    "return [x * 2 for x in y]",
])
def test_la_definicion_amplia_suma_append_y_comprension_de_lista(cuerpo):
    resultado = fragmento(en_funcion(cuerpo))
    assert ESTRUCTURAS not in resultado.conceptos
    assert ESTRUCTURAS in resultado.conceptos_amplia


def test_la_definicion_amplia_incluye_lo_de_v1():
    resultado = fragmento("def f(n):\n    return f(n - 1)\n")
    assert resultado.conceptos_amplia == {RECURSION}


# Indexación de tipo desconocido (R4)

@pytest.mark.parametrize("cuerpo, esperadas", [
    ("return y[0]", 1),
    ("return self.datos[0]", 1),
    ("return y[0] + y[1]", 2),
    ("return matriz[0][1]", 1),
    ("a = [1]\nreturn a[0]", 0),
    ("s = 'x'\nreturn s[0]", 0),
    ("return requests.get(y)['datos']", 0),
])
def test_cuenta_indexaciones_indeterminadas(cuerpo, esperadas):
    resultado = fragmento(en_funcion(cuerpo, "self, y, matriz"))
    assert resultado.indexaciones_indeterminadas == esperadas


def test_indexacion_indeterminada_no_asigna_el_concepto():
    assert ESTRUCTURAS not in conceptos("def f(lista):\n    return lista[0] + 1\n")


# Manejo de excepciones

@pytest.mark.parametrize("cuerpo", [
    "try:\n    g()\nexcept ValueError:\n    pass",
    "try:\n    g()\nfinally:\n    h()",
    "try:\n    g()\nexcept:\n    pass",
    "raise ValueError('x')",
])
def test_detecta_excepciones(cuerpo):
    assert EXCEPCIONES in conceptos(en_funcion(cuerpo))


def test_raise_en_funcion_corta_de_validacion_no_es_trivial():
    fuente = "def validar(x):\n    if x < 0:\n        raise ValueError('negativo')\n"
    resultado = fragmento(fuente)
    assert EXCEPCIONES in resultado.conceptos
    assert not resultado.trivial


def test_sin_excepciones():
    assert EXCEPCIONES not in conceptos("def f():\n    return 1\n")


def test_try_de_funcion_anidada_se_suma_a_la_externa():
    fuente = (
        "def f():\n"
        "    def g():\n        raise ValueError\n"
        "    return g\n"
    )
    assert EXCEPCIONES in conceptos(fuente, "f")


def test_metodo_de_clase_local_se_suma_a_la_funcion_que_la_contiene():
    fuente = (
        "def f():\n"
        "    class A:\n"
        "        def g(self, n):\n            return self.g(n - 1)\n"
        "    return A\n"
    )
    assert RECURSION in conceptos(fuente, "f")


# Combinaciones

def test_ningun_concepto():
    assert conceptos("def f(a):\n    return a + 1\n") == frozenset()


def test_varios_conceptos_a_la_vez():
    fuente = (
        "def f(l):\n"
        "    l = list(l)\n"
        "    try:\n"
        "        return l[0] + f(l[1:])\n"
        "    except IndexError:\n"
        "        return 0\n"
    )
    assert conceptos(fuente) == {RECURSION, ESTRUCTURAS, EXCEPCIONES}
