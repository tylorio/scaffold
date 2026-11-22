"""Extracción de funciones y métodos con `ast`, y sus métricas con radon."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterator

from radon.complexity import cc_visit_ast
from radon.raw import analyze

from .conceptos import (
    FUNCIONES,
    RECURSION,
    DeteccionConceptos,
    analizar_conceptos,
    recorrer_cuerpo,
)


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
    trivial: bool = False  # el flujo la omite: no aporta evidencia para el IDC
    conceptos_amplia: frozenset[str] = frozenset()  # solo para el análisis de sensibilidad (D5)
    indexaciones_indeterminadas: int = 0  # R4


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
            # No se entra en ella: lo anidado ya forma parte de su código y
            # contarlo aparte duplicaría esas líneas en el IDC.
            yield hijo, prefijo, clase
        else:
            yield from _recorrer_definiciones(hijo, prefijo, clase)


def _conceptos_con_anidadas(
    funcion: ast.AST, clase: ast.ClassDef | None
) -> DeteccionConceptos:
    """Conceptos de la función más los de las definiciones que contiene."""
    deteccion = analizar_conceptos(funcion, clase)
    for anidada, _, clase_anidada in _recorrer_definiciones(funcion, (), None):
        deteccion = deteccion.unir(_conceptos_con_anidadas(anidada, clase_anidada))
    return deteccion


Clave = tuple[tuple[str, ...], str]


def _destino(llamada: ast.Call, prefijo: tuple[str, ...]) -> Clave | None:
    objetivo = llamada.func
    if isinstance(objetivo, ast.Name):
        return (), objetivo.id
    if (
        prefijo
        and isinstance(objetivo, ast.Attribute)
        and isinstance(objetivo.value, ast.Name)
        and objetivo.value.id in {"self", "cls", prefijo[-1]}
    ):
        return prefijo, objetivo.attr
    return None


def _en_recursion_mutua(definiciones: list) -> set[Clave]:
    """Funciones del archivo que forman un ciclo de llamadas de dos o más (D6).

    Las llamadas a sí misma no cuentan aquí: ya son recursión directa.
    """
    claves = {(prefijo, nodo.name) for nodo, prefijo, _ in definiciones}
    grafo: dict[Clave, set[Clave]] = {}
    for nodo, prefijo, _ in definiciones:
        origen = (prefijo, nodo.name)
        destinos = {
            destino
            for llamada in ast.walk(nodo)
            if isinstance(llamada, ast.Call)
            and (destino := _destino(llamada, prefijo)) in claves
        }
        grafo.setdefault(origen, set()).update(destinos - {origen})

    def alcanzables(origen: Clave) -> set[Clave]:
        vistos: set[Clave] = set()
        pendientes = [origen]
        while pendientes:
            for destino in grafo.get(pendientes.pop(), ()):
                if destino not in vistos:
                    vistos.add(destino)
                    pendientes.append(destino)
        return vistos

    return {clave for clave in grafo if clave in alcanzables(clave)}


def _es_trivial(funcion: ast.AST, conceptos: frozenset[str]) -> bool:
    """Una sola sentencia sin conceptos, como un getter: no revela cómo se escribió."""
    if conceptos:
        return False
    sentencias = sum(isinstance(n, ast.stmt) for n in recorrer_cuerpo(funcion))
    return sentencias - (ast.get_docstring(funcion) is not None) <= 1


def _complejidad(nodo: ast.AST) -> int:
    bloques = cc_visit_ast(ast.Module(body=[nodo], type_ignores=[]))
    return bloques[0].complexity if bloques else 1


def _contar_lineas(codigo: str) -> int:
    try:
        return analyze(codigo).loc
    except (SyntaxError, ValueError):
        return len(codigo.splitlines())


def extraer_funciones(fuente: str, archivo: str = "<memoria>") -> list[Fragmento]:
    """Extrae cada función o método en orden de aparición.

    Una función anidada es parte de la que la envuelve, no un fragmento propio.
    """
    try:
        arbol = ast.parse(fuente)
    except (SyntaxError, ValueError, RecursionError) as error:
        raise ErrorSintaxis(f"{archivo}: {error}") from error

    lineas = fuente.splitlines()
    definiciones = list(_recorrer_definiciones(arbol, (), None))
    mutuas = _en_recursion_mutua(definiciones)
    fragmentos = []
    for nodo, prefijo, clase in definiciones:
        inicio = min([nodo.lineno, *(d.lineno for d in nodo.decorator_list)])
        codigo = desindentar(lineas[inicio - 1 : nodo.end_lineno], nodo.col_offset)
        deteccion = _conceptos_con_anidadas(nodo, clase)
        if (prefijo, nodo.name) in mutuas:
            deteccion = deteccion.con(RECURSION)
        fragmentos.append(
            Fragmento(
                archivo=archivo,
                nombre=".".join((*prefijo, nodo.name)),
                codigo=codigo,
                linea_inicio=inicio,
                linea_fin=nodo.end_lineno,
                lineas=_contar_lineas(codigo),
                complejidad=_complejidad(nodo),
                conceptos=deteccion.conceptos,
                trivial=_es_trivial(nodo, deteccion.conceptos),
                conceptos_amplia=deteccion.conceptos_amplia,
                indexaciones_indeterminadas=deteccion.indexaciones_indeterminadas,
            )
        )
    return sorted(fragmentos, key=lambda f: f.linea_inicio)
