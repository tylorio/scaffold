"""Extracción de funciones y métodos con `ast`, y sus métricas con radon."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterator

from radon.complexity import cc_visit_ast
from radon.raw import analyze

from .conceptos import FUNCIONES, detectar_conceptos


class ErrorSintaxis(Exception):
    """El archivo no se pudo interpretar como Python válido."""


@dataclass(frozen=True)
class Fragmento:
    archivo: str
    nombre: str
    codigo: str
    linea_inicio: int
    linea_fin: int
    lineas: int
    complejidad: int
    conceptos: frozenset[str]


def desindentar(lineas: list[str], columna: int) -> str:
    """Quita la sangría de un método sin tocar líneas con menos sangría.

    `textwrap.dedent` no sirve aquí: una cadena multilínea pegada al margen lo
    dejaría sin efecto y el fragmento quedaría imposible de parsear.
    """
    resultado = []
    for linea in lineas:
        if linea[:columna].strip() == "":
            resultado.append(linea[columna:])
        else:
            resultado.append(linea)
    return "\n".join(resultado)


def _recorrer_definiciones(
    nodo: ast.AST, prefijo: tuple[str, ...], clase: ast.ClassDef | None
) -> Iterator[tuple[ast.AST, tuple[str, ...], ast.ClassDef | None]]:
    for hijo in ast.iter_child_nodes(nodo):
        # Una definición nunca está dentro de una expresión, y saltarlas evita
        # desbordar la pila con expresiones muy largas.
        if isinstance(hijo, ast.expr):
            continue
        if isinstance(hijo, ast.ClassDef):
            yield from _recorrer_definiciones(hijo, (*prefijo, hijo.name), hijo)
        elif isinstance(hijo, FUNCIONES):
            yield hijo, prefijo, clase
            yield from _recorrer_definiciones(hijo, (*prefijo, hijo.name), None)
        else:
            yield from _recorrer_definiciones(hijo, prefijo, clase)


def _complejidad(nodo: ast.AST) -> int:
    bloques = cc_visit_ast(ast.Module(body=[nodo], type_ignores=[]))
    return bloques[0].complexity if bloques else 1


def _contar_lineas(codigo: str) -> int:
    try:
        return analyze(codigo).loc
    except (SyntaxError, ValueError):
        return len(codigo.splitlines())


def extraer_funciones(fuente: str, archivo: str = "<memoria>") -> list[Fragmento]:
    """Extrae cada función o método, anidados incluidos, en orden de aparición."""
    try:
        arbol = ast.parse(fuente)
    except (SyntaxError, ValueError, RecursionError) as error:
        raise ErrorSintaxis(f"{archivo}: {error}") from error

    lineas = fuente.splitlines()
    fragmentos = []
    for nodo, prefijo, clase in _recorrer_definiciones(arbol, (), None):
        inicio = min([nodo.lineno, *(d.lineno for d in nodo.decorator_list)])
        codigo = desindentar(lineas[inicio - 1 : nodo.end_lineno], nodo.col_offset)
        fragmentos.append(
            Fragmento(
                archivo=archivo,
                nombre=".".join((*prefijo, nodo.name)),
                codigo=codigo,
                linea_inicio=inicio,
                linea_fin=nodo.end_lineno,
                lineas=_contar_lineas(codigo),
                complejidad=_complejidad(nodo),
                conceptos=detectar_conceptos(nodo, clase),
            )
        )
    return sorted(fragmentos, key=lambda f: f.linea_inicio)
