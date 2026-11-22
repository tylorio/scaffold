"""Detección estática de conceptos con `ast` (reglas conceptos-v1). No depende de Django.

Implementa la guía del asesor (D5, D6, R4): un concepto se asigna cuando escribir
el fragmento exige haberlo aplicado, no cuando la sintaxis solo lo roza. Python no
declara tipos, así que indexar solo cuenta como estructura de datos cuando se
puede inferir que el objeto es una lista o un diccionario; si no se puede, la
indexación queda como indeterminada y no asigna el concepto.

La recursión mutua necesita ver el archivo entero y se detecta en `extraccion`.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterator

RECURSION = "recursion"
ESTRUCTURAS = "estructuras_datos"
EXCEPCIONES = "excepciones"

CONCEPTOS = (RECURSION, ESTRUCTURAS, EXCEPCIONES)

NOMBRES_CONCEPTOS = {
    RECURSION: "Recursión",
    ESTRUCTURAS: "Estructuras de datos",
    EXCEPCIONES: "Manejo de excepciones",
}

REGLAS_VERSION = "conceptos-v1"
REGLAS_AMPLIA_VERSION = "conceptos-v1-amplia"

FUNCIONES = (ast.FunctionDef, ast.AsyncFunctionDef)
_AMBITOS = FUNCIONES + (ast.ClassDef,)

# Lista cerrada y bilingüe (P7): pila, cola y protocolo de contenedor.
METODOS_CLASE_CONTENEDORA = frozenset({
    "push", "pop", "peek", "apilar", "desapilar", "cima", "tope",
    "enqueue", "dequeue", "encolar", "desencolar", "frente",
    "__len__", "__iter__", "__getitem__", "__contains__",
})
ATRIBUTOS_DE_NODO = frozenset({
    "siguiente", "anterior", "izquierda", "izquierdo", "derecha", "derecho",
    "next", "prev", "left", "right", "hijo", "hijos", "children", "padre", "parent",
})
COLECCIONES = frozenset({"deque", "Counter", "defaultdict"})
ORDENACION_Y_BUSQUEDA = frozenset({
    "sorted", "bisect", "bisect_left", "bisect_right", "insort", "insort_left",
    "insort_right", "heappush", "heappop", "heapify", "heappushpop", "heapreplace",
    "nlargest", "nsmallest",
})
MODULOS_ORDENACION = frozenset({"bisect", "heapq"})
OPERACIONES_PILA_COLA = frozenset({"pop", "popleft", "appendleft"})

LISTA = "lista"
DICCIONARIO = "diccionario"
CONJUNTO = "conjunto"
CADENA = "cadena"
TUPLA = "tupla"

_TIPO_DE_CONSTRUCTOR = {
    "list": LISTA, "sorted": LISTA, "deque": LISTA,
    "dict": DICCIONARIO, "Counter": DICCIONARIO, "defaultdict": DICCIONARIO,
    "OrderedDict": DICCIONARIO,
    "set": CONJUNTO, "frozenset": CONJUNTO,
    "str": CADENA, "input": CADENA,
    "tuple": TUPLA,
}
_METODOS_QUE_DEVUELVEN_LISTA = frozenset({"split", "rsplit", "splitlines", "readlines"})
_METODOS_QUE_DEVUELVEN_CADENA = frozenset({
    "strip", "lstrip", "rstrip", "lower", "upper", "title", "capitalize",
    "casefold", "replace", "join", "format",
})
# Métodos que solo tiene un tipo: llamarlos sobre un nombre revela qué es.
_METODOS_QUE_REVELAN_TIPO = {
    "append": LISTA, "extend": LISTA, "insert": LISTA, "sort": LISTA, "reverse": LISTA,
    "add": CONJUNTO, "discard": CONJUNTO,
    "setdefault": DICCIONARIO, "items": DICCIONARIO, "keys": DICCIONARIO,
    "values": DICCIONARIO, "popitem": DICCIONARIO,
}


@dataclass(frozen=True)
class DeteccionConceptos:
    conceptos: frozenset[str] = frozenset()
    conceptos_amplia: frozenset[str] = frozenset()  # v1 + append acumulativo + comprensión de lista
    indexaciones_indeterminadas: int = 0

    def unir(self, otra: DeteccionConceptos) -> DeteccionConceptos:
        return DeteccionConceptos(
            self.conceptos | otra.conceptos,
            self.conceptos_amplia | otra.conceptos_amplia,
            self.indexaciones_indeterminadas + otra.indexaciones_indeterminadas,
        )

    def con(self, concepto: str) -> DeteccionConceptos:
        return DeteccionConceptos(
            self.conceptos | {concepto},
            self.conceptos_amplia | {concepto},
            self.indexaciones_indeterminadas,
        )


def recorrer_cuerpo(funcion: ast.AST) -> Iterator[ast.AST]:
    """Recorre el cuerpo de una función sin entrar en anotaciones ni en ámbitos anidados.

    Cada ámbito se evalúa con su propio contexto (por ejemplo, su nombre para la
    recursión); `extraccion` suma luego los conceptos de los ámbitos anidados a
    la función que los envuelve.
    """
    pendientes: list[ast.AST] = list(funcion.body)
    while pendientes:
        nodo = pendientes.pop()
        yield nodo
        if isinstance(nodo, _AMBITOS):
            continue
        for campo, valor in ast.iter_fields(nodo):
            if campo in ("annotation", "returns"):
                continue
            if isinstance(valor, ast.AST):
                pendientes.append(valor)
            elif isinstance(valor, list):
                pendientes.extend(v for v in valor if isinstance(v, ast.AST))


# Nodos enlazados

def _es_none(nodo: ast.AST) -> bool:
    return isinstance(nodo, ast.Constant) and nodo.value is None


def _base_de_enlace(nodo: ast.AST) -> str | None:
    """`x` si el nodo es `x.<atributo de nodo>`."""
    if (
        isinstance(nodo, ast.Attribute)
        and nodo.attr in ATRIBUTOS_DE_NODO
        and isinstance(nodo.value, ast.Name)
    ):
        return nodo.value.id
    return None


def enlaces_de_la_clase(clase: ast.ClassDef | None) -> frozenset[str]:
    """Atributos que la clase usa como enlaces de nodo.

    Son los que se asignan a una instancia de la misma clase
    (`self.izquierda = Nodo(...)`, P8) y los de la lista de nodos que se inicializan
    como un nodo vacío (`self.siguiente = None`, `self.hijos = []`).
    """
    if clase is None:
        return frozenset()
    enlaces = set()
    for nodo in ast.walk(clase):
        if isinstance(nodo, ast.Assign):
            objetivos, valor = nodo.targets, nodo.value
        elif isinstance(nodo, ast.AnnAssign) and nodo.value is not None:
            objetivos, valor = [nodo.target], nodo.value
        else:
            continue
        misma_clase = (
            isinstance(valor, ast.Call)
            and isinstance(valor.func, ast.Name)
            and valor.func.id == clase.name
        )
        vacio = _es_none(valor) or (isinstance(valor, ast.List) and not valor.elts)
        for objetivo in objetivos:
            if (
                isinstance(objetivo, ast.Attribute)
                and isinstance(objetivo.value, ast.Name)
                and objetivo.value.id == "self"
                and (misma_clase or (vacio and objetivo.attr in ATRIBUTOS_DE_NODO))
            ):
                enlaces.add(objetivo.attr)
    return frozenset(enlaces)


def _variables_de_nodo(funcion: ast.AST) -> set[str]:
    """Nombres que la función trata como nodos.

    Se comparan con None (`if nodo is None`), recorren enlaces
    (`actual = actual.siguiente`) o cortan un enlace (`x.siguiente = None`).
    """
    variables = set()
    for nodo in recorrer_cuerpo(funcion):
        if isinstance(nodo, ast.Compare):
            lados = [nodo.left, *nodo.comparators]
            if any(_es_none(lado) for lado in lados):
                for lado in lados:
                    if isinstance(lado, ast.Name):
                        variables.add(lado.id)
                    elif base := _base_de_enlace(lado):
                        variables.add(base)
        elif isinstance(nodo, ast.Assign):
            for objetivo in nodo.targets:
                if isinstance(objetivo, ast.Name) and _base_de_enlace(nodo.value) == objetivo.id:
                    variables.add(objetivo.id)
                elif (base := _base_de_enlace(objetivo)) and _es_none(nodo.value):
                    variables.add(base)
    return variables


def _es_acceso_a_nodo(
    nodo: ast.AST, enlaces: frozenset[str], variables: set[str]
) -> bool:
    """Un atributo de nodo cuenta solo en un contexto de nodos (P7).

    `ruta.parent` (pathlib), `self.rect.left` (pygame) o `self.parent = ventana`
    (tkinter) usan los mismos nombres sin ser nodos enlazados.
    """
    if not isinstance(nodo, ast.Attribute):
        return False
    base = nodo.value
    if isinstance(base, ast.Name) and base.id == "self":
        return nodo.attr in enlaces
    return nodo.attr in ATRIBUTOS_DE_NODO and isinstance(base, ast.Name) and base.id in variables


# Recursión

def es_recursiva(funcion: ast.AST, clase: ast.ClassDef | None = None) -> bool:
    """True si la función se llama a sí misma, directamente o sobre un nodo.

    En un método cuentan `self.f()`, `cls.f()`, `Clase.f()` y la recursión sobre un
    atributo de nodo (P8): `self.izquierda.f()`, o `h.f()` al recorrer
    `for h in self.hijos`. Delegar en otro objeto con el mismo nombre de método
    (`self.repositorio.guardar()` dentro de `guardar`) no es recursión. Un `f()`
    suelto dentro de un método llama a otra función, no al método.
    """
    enlaces = ATRIBUTOS_DE_NODO | enlaces_de_la_clase(clase)
    hijos = {
        nodo.target.id
        for nodo in recorrer_cuerpo(funcion)
        if isinstance(nodo, (ast.For, ast.AsyncFor, ast.comprehension))
        and isinstance(nodo.target, ast.Name)
        and isinstance(nodo.iter, ast.Attribute)
        and nodo.iter.attr in enlaces
    }
    for nodo in recorrer_cuerpo(funcion):
        if not isinstance(nodo, ast.Call):
            continue
        objetivo = nodo.func
        if clase is None:
            if isinstance(objetivo, ast.Name) and objetivo.id == funcion.name:
                return True
        elif isinstance(objetivo, ast.Attribute) and objetivo.attr == funcion.name:
            receptor = objetivo.value
            if isinstance(receptor, ast.Attribute) and receptor.attr in enlaces:
                return True
            if isinstance(receptor, ast.Name) and (
                receptor.id in {"self", "cls", clase.name} or receptor.id in hijos
            ):
                return True
    return False


# Estructuras de datos

def _nombre_llamado(funcion: ast.AST) -> str | None:
    if isinstance(funcion, ast.Name):
        return funcion.id
    if isinstance(funcion, ast.Attribute):
        return funcion.attr
    return None


def _tipo_de_expresion(nodo: ast.AST) -> str | None:
    if isinstance(nodo, (ast.List, ast.ListComp)):
        return LISTA
    if isinstance(nodo, (ast.Dict, ast.DictComp)):
        return DICCIONARIO
    if isinstance(nodo, (ast.Set, ast.SetComp)):
        return CONJUNTO
    if isinstance(nodo, ast.Tuple):
        return TUPLA
    if isinstance(nodo, ast.JoinedStr) or (
        isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
    ):
        return CADENA
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, (ast.Add, ast.Mult)):
        lados = {_tipo_de_expresion(nodo.left), _tipo_de_expresion(nodo.right)} - {None}
        return lados.pop() if len(lados) == 1 and lados <= {LISTA, CADENA, TUPLA} else None
    if isinstance(nodo, ast.Call):
        funcion = nodo.func
        if isinstance(funcion, ast.Attribute):
            if funcion.attr in _METODOS_QUE_DEVUELVEN_LISTA:
                return LISTA
            if funcion.attr in _METODOS_QUE_DEVUELVEN_CADENA:
                return CADENA
            if isinstance(funcion.value, ast.Name) and funcion.value.id == "collections":
                return _TIPO_DE_CONSTRUCTOR.get(funcion.attr)
            return None
        return _TIPO_DE_CONSTRUCTOR.get(_nombre_llamado(funcion))
    return None


def inferir_tipos(funcion: ast.AST) -> dict[str, str]:
    """Tipo de cada nombre local cuando la función lo deja claro y no se contradice."""
    vistos: dict[str, set[str]] = {}

    def anotar(nombre: str, tipo: str | None) -> None:
        if tipo is not None:
            vistos.setdefault(nombre, set()).add(tipo)

    for nodo in recorrer_cuerpo(funcion):
        if isinstance(nodo, ast.Assign):
            for objetivo in nodo.targets:
                if isinstance(objetivo, ast.Name):
                    anotar(objetivo.id, _tipo_de_expresion(nodo.value))
        elif (
            isinstance(nodo, (ast.AnnAssign, ast.AugAssign))
            and isinstance(nodo.target, ast.Name)
            and nodo.value is not None
        ):
            anotar(nodo.target.id, _tipo_de_expresion(nodo.value))
        elif (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and isinstance(nodo.func.value, ast.Name)
        ):
            anotar(nodo.func.value.id, _METODOS_QUE_REVELAN_TIPO.get(nodo.func.attr))
    return {nombre: tipos.pop() for nombre, tipos in vistos.items() if len(tipos) == 1}


def _es_coleccion(nodo: ast.AST) -> bool:
    if isinstance(nodo, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    if isinstance(nodo, ast.BinOp):
        return _es_coleccion(nodo.left) or _es_coleccion(nodo.right)
    return (
        isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
        and nodo.func.id in {"list", "dict", "set"}
    )


def _anida_colecciones(nodo: ast.AST) -> bool:
    """Lista de listas, diccionario de listas, etc. (D5.5)."""
    if isinstance(nodo, (ast.List, ast.Set)):
        return any(_es_coleccion(e) for e in nodo.elts)
    if isinstance(nodo, ast.Dict):
        return any(_es_coleccion(v) for v in nodo.values)
    if isinstance(nodo, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return _es_coleccion(nodo.elt)
    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
        return nodo.func.attr in {"append", "insert"} and any(
            _es_coleccion(a) for a in nodo.args
        )
    return False


def _llamada_es_estructura(nodo: ast.Call, tipos: dict[str, str]) -> bool:
    funcion = nodo.func
    if isinstance(funcion, ast.Name):
        return funcion.id in ORDENACION_Y_BUSQUEDA or funcion.id in COLECCIONES
    if not isinstance(funcion, ast.Attribute):
        return False
    if funcion.attr in {"sort", "setdefault"} | OPERACIONES_PILA_COLA:
        return True
    if funcion.attr in COLECCIONES:
        return True
    receptor = funcion.value
    if isinstance(receptor, ast.Name) and receptor.id in MODULOS_ORDENACION:
        return True
    return (
        funcion.attr == "get"
        and isinstance(receptor, ast.Name)
        and tipos.get(receptor.id) == DICCIONARIO
    )


def _cuenta_como_estructura(
    nodo: ast.AST, tipos: dict[str, str], enlaces: frozenset[str], variables: set[str],
) -> bool:
    if isinstance(nodo, (ast.DictComp, ast.SetComp)):
        return True
    if _anida_colecciones(nodo):
        return True
    if _es_acceso_a_nodo(nodo, enlaces, variables):
        return True
    if isinstance(nodo, ast.Subscript):
        base = nodo.value
        return isinstance(base, ast.Name) and tipos.get(base.id) in {LISTA, DICCIONARIO}
    if isinstance(nodo, ast.Compare) and any(
        isinstance(op, (ast.In, ast.NotIn)) for op in nodo.ops
    ):
        return any(
            isinstance(c, ast.Name) and tipos.get(c.id) in {DICCIONARIO, CONJUNTO}
            for c in nodo.comparators
        )
    if isinstance(nodo, ast.Call):
        return _llamada_es_estructura(nodo, tipos)
    return False


def _es_indexacion_indeterminada(nodo: ast.AST, tipos: dict[str, str]) -> bool:
    """Indexación sobre un nombre o atributo cuyo tipo no se pudo inferir (R4).

    Indexar el resultado de una llamada, como `requests.get(url)["datos"]`, es leer
    lo que devuelve una biblioteca: no cuenta y tampoco es indeterminado.
    """
    if not isinstance(nodo, ast.Subscript):
        return False
    base = nodo.value
    if isinstance(base, ast.Name):
        return base.id not in tipos
    return isinstance(base, ast.Attribute)


def es_clase_contenedora(clase: ast.ClassDef | None) -> bool:
    if clase is None:
        return False
    return any(
        isinstance(hijo, FUNCIONES) and hijo.name in METODOS_CLASE_CONTENEDORA
        for hijo in clase.body
    )


def _es_append(nodo: ast.AST) -> bool:
    return (
        isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "append"
    )


# Manejo de excepciones

def maneja_excepciones(funcion: ast.AST) -> bool:
    return any(
        isinstance(nodo, (ast.Try, ast.TryStar, ast.Raise))
        for nodo in recorrer_cuerpo(funcion)
    )


def analizar_conceptos(
    funcion: ast.AST, clase: ast.ClassDef | None = None
) -> DeteccionConceptos:
    """Conceptos del ámbito de la función, sin sus definiciones anidadas."""
    tipos = inferir_tipos(funcion)
    enlaces = enlaces_de_la_clase(clase)
    variables = _variables_de_nodo(funcion)
    estructura = es_clase_contenedora(clase)
    amplia = False
    indeterminadas = 0
    for nodo in recorrer_cuerpo(funcion):
        estructura = estructura or _cuenta_como_estructura(nodo, tipos, enlaces, variables)
        amplia = amplia or isinstance(nodo, ast.ListComp) or _es_append(nodo)
        indeterminadas += _es_indexacion_indeterminada(nodo, tipos)

    conceptos = set()
    if es_recursiva(funcion, clase):
        conceptos.add(RECURSION)
    if estructura:
        conceptos.add(ESTRUCTURAS)
    if maneja_excepciones(funcion):
        conceptos.add(EXCEPCIONES)
    conceptos_amplia = conceptos | ({ESTRUCTURAS} if amplia else set())
    return DeteccionConceptos(frozenset(conceptos), frozenset(conceptos_amplia), indeterminadas)


def detectar_conceptos(
    funcion: ast.AST, clase: ast.ClassDef | None = None
) -> frozenset[str]:
    """Conceptos v1 de la función: ninguno, uno o varios."""
    return analizar_conceptos(funcion, clase).conceptos
