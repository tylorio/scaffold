"""Detección estática de conceptos con `ast`. No depende de Django.

La detección es heurística: Python no tiene tipos estáticos y aquí no se hace
inferencia, así que `s[0]` cuenta como estructura de datos aunque `s` sea una
cadena. Las limitaciones están listadas en el README.
"""
from __future__ import annotations

import ast
import re
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

FUNCIONES = (ast.FunctionDef, ast.AsyncFunctionDef)
_AMBITOS = FUNCIONES + (ast.ClassDef,)

METODOS_CONTENEDOR = frozenset({
    "append", "extend", "insert", "remove", "pop", "popleft", "appendleft",
    "clear", "sort", "reverse", "keys", "values", "items", "get", "setdefault",
    "update", "popitem", "add", "discard", "union", "intersection",
    "difference", "symmetric_difference", "issubset", "issuperset",
})
CONSTRUCTORES_CONTENEDOR = frozenset({
    "list", "dict", "set", "frozenset", "tuple", "sorted", "deque",
    "defaultdict", "OrderedDict", "Counter", "namedtuple",
})
TIPOS_CONTENEDOR = frozenset({
    "list", "dict", "set", "frozenset", "tuple", "deque", "defaultdict",
    "List", "Dict", "Set", "FrozenSet", "Tuple", "Deque", "DefaultDict",
    "OrderedDict", "Counter", "Sequence", "MutableSequence", "Mapping",
    "MutableMapping",
})
DUNDERS_CONTENEDOR = frozenset({
    "__getitem__", "__setitem__", "__delitem__", "__len__", "__iter__",
    "__contains__",
})
_COMPRENSIONES = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
_LITERALES = (ast.List, ast.Dict, ast.Set)


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


def es_recursiva(funcion: ast.AST, clase: ast.ClassDef | None = None) -> bool:
    """True si la función se llama a sí misma directamente.

    En un método solo cuentan `self.x()`, `cls.x()` y `Clase.x()`: un `x()`
    suelto dentro de un método llama a otra función, no al método.
    """
    for nodo in recorrer_cuerpo(funcion):
        if not isinstance(nodo, ast.Call):
            continue
        objetivo = nodo.func
        if clase is None:
            if isinstance(objetivo, ast.Name) and objetivo.id == funcion.name:
                return True
        elif (
            isinstance(objetivo, ast.Attribute)
            and objetivo.attr == funcion.name
            and isinstance(objetivo.value, ast.Name)
            and objetivo.value.id in {"self", "cls", clase.name}
        ):
            return True
    return False


def es_clase_contenedora(clase: ast.ClassDef | None) -> bool:
    if clase is None:
        return False
    return any(
        isinstance(hijo, FUNCIONES) and hijo.name in DUNDERS_CONTENEDOR
        for hijo in clase.body
    )


def _anotacion_es_contenedor(anotacion: ast.AST | None) -> bool:
    if anotacion is None:
        return False
    for nodo in ast.walk(anotacion):
        if isinstance(nodo, ast.Name) and nodo.id in TIPOS_CONTENEDOR:
            return True
        if isinstance(nodo, ast.Attribute) and nodo.attr in TIPOS_CONTENEDOR:
            return True
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            if TIPOS_CONTENEDOR.intersection(re.findall(r"\w+", nodo.value)):
                return True
    return False


def _firma_declara_contenedor(funcion: ast.AST) -> bool:
    argumentos = funcion.args
    parametros = [
        *argumentos.posonlyargs, *argumentos.args, *argumentos.kwonlyargs,
        argumentos.vararg, argumentos.kwarg,
    ]
    anotaciones = [p.annotation for p in parametros if p is not None]
    anotaciones.append(funcion.returns)
    return any(_anotacion_es_contenedor(a) for a in anotaciones)


def _nodo_usa_contenedor(nodo: ast.AST) -> bool:
    if isinstance(nodo, _LITERALES + _COMPRENSIONES + (ast.Subscript,)):
        return True
    # Una tupla solo cuenta cuando se guarda como dato. `return a, b`,
    # `except (A, B)` y `a, b = b, a` son sintaxis, no uso de una estructura.
    if isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Tuple):
        return len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name)
    if isinstance(nodo, ast.Call):
        objetivo = nodo.func
        if isinstance(objetivo, ast.Name):
            return objetivo.id in CONSTRUCTORES_CONTENEDOR
        if isinstance(objetivo, ast.Attribute):
            return (
                objetivo.attr in METODOS_CONTENEDOR
                or objetivo.attr in CONSTRUCTORES_CONTENEDOR
            )
    return False


def usa_estructuras_datos(funcion: ast.AST, clase: ast.ClassDef | None = None) -> bool:
    if es_clase_contenedora(clase) or _firma_declara_contenedor(funcion):
        return True
    return any(_nodo_usa_contenedor(nodo) for nodo in recorrer_cuerpo(funcion))


def maneja_excepciones(funcion: ast.AST) -> bool:
    return any(
        isinstance(nodo, (ast.Try, ast.TryStar, ast.Raise))
        for nodo in recorrer_cuerpo(funcion)
    )


def detectar_conceptos(
    funcion: ast.AST, clase: ast.ClassDef | None = None
) -> frozenset[str]:
    """Devuelve los conceptos de la función: ninguno, uno o varios."""
    encontrados = set()
    if es_recursiva(funcion, clase):
        encontrados.add(RECURSION)
    if usa_estructuras_datos(funcion, clase):
        encontrados.add(ESTRUCTURAS)
    if maneja_excepciones(funcion):
        encontrados.add(EXCEPCIONES)
    return frozenset(encontrados)
