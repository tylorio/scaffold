"""Características de un fragmento y su transformador para scikit-learn."""
from __future__ import annotations

import ast
import builtins
import io
import math
import re
import tokenize
from collections import Counter

import numpy as np
from radon.complexity import cc_visit_ast
from radon.raw import analyze
from sklearn.base import BaseEstimator, TransformerMixin

from .conceptos import FUNCIONES

NOMBRES_CARACTERISTICAS = (
    "densidad_comentarios",
    "tiene_docstring",
    "proporcion_type_hints",
    "longitud_media_identificadores",
    "uniformidad_estilo",
    "complejidad",
    "lineas",
    "log_insercion_commit",
)

_SNAKE = re.compile(r"^_*[a-z][a-z0-9]*(_[a-z0-9]+)*_*$")
_CAMEL = re.compile(r"^_*[a-z]+[a-z0-9]*([A-Z][a-z0-9]*)+$")
_PASCAL = re.compile(r"^_*[A-Z][a-z0-9]+([A-Z][a-z0-9]*)*$")
_MAYUSCULAS = re.compile(r"^_*[A-Z][A-Z0-9_]*$")
_IGNORADOS = {"self", "cls", "_"} | set(dir(builtins))


def _parsear(codigo: str) -> ast.AST | None:
    """Parsea el fragmento; acepta código con sangría residual."""
    for intento in (codigo, "if True:\n" + codigo):
        try:
            return ast.parse(intento)
        except (SyntaxError, ValueError, RecursionError):
            continue
    return None


def _primera_funcion(arbol: ast.AST | None) -> ast.AST | None:
    if arbol is None:
        return None
    for nodo in ast.walk(arbol):
        if isinstance(nodo, FUNCIONES):
            return nodo
    return None


def _tokens(codigo: str) -> list[tokenize.TokenInfo]:
    tokens = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(codigo).readline):
            tokens.append(token)
    except (tokenize.TokenError, SyntaxError):
        pass
    return tokens


def densidad_comentarios(codigo: str) -> float:
    lineas = len(codigo.splitlines())
    if lineas == 0:
        return 0.0
    con_comentario = {
        t.start[0] for t in _tokens(codigo) if t.type == tokenize.COMMENT
    }
    return len(con_comentario) / lineas


def proporcion_type_hints(funcion: ast.AST) -> float:
    """Parte anotada de la firma: parámetros más el valor de retorno."""
    args = funcion.args
    parametros = [
        p for p in (*args.posonlyargs, *args.args, *args.kwonlyargs)
        if p.arg not in ("self", "cls")
    ]
    parametros += [p for p in (args.vararg, args.kwarg) if p is not None]
    anotados = sum(p.annotation is not None for p in parametros)
    anotados += funcion.returns is not None
    return anotados / (len(parametros) + 1)


def _identificadores(funcion: ast.AST) -> list[str]:
    """Nombres que eligió quien escribió el código, sin builtins ni `self`."""
    nombres = [funcion.name]
    args = funcion.args
    for parametro in (
        *args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg,
    ):
        if parametro is not None:
            nombres.append(parametro.arg)
    for nodo in ast.walk(funcion):
        if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
            nombres.append(nodo.id)
    return [n for n in dict.fromkeys(nombres) if n not in _IGNORADOS]


def longitud_media_identificadores(funcion: ast.AST) -> float:
    nombres = _identificadores(funcion)
    return sum(map(len, nombres)) / len(nombres) if nombres else 0.0


def _convencion(nombre: str) -> str:
    if _SNAKE.match(nombre):
        return "snake"
    if _CAMEL.match(nombre):
        return "camel"
    if _PASCAL.match(nombre):
        return "pascal"
    if _MAYUSCULAS.match(nombre):
        return "mayusculas"
    return "otra"


def _proporcion_dominante(valores: list[str]) -> float | None:
    if not valores:
        return None
    return Counter(valores).most_common(1)[0][1] / len(valores)


def _comillas(codigo: str) -> list[str]:
    """Comillas de cadenas simples. Las triples quedan fuera: son docstrings."""
    comillas = []
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    for token in _tokens(codigo):
        if token.type != tokenize.STRING and token.type != fstring_start:
            continue
        texto = token.string.lstrip("rRbBfFuU")
        if texto[:3] in ('"""', "'''"):
            continue
        if texto[:1] in ("'", '"'):
            comillas.append(texto[0])
    return comillas


def uniformidad_estilo(codigo: str, funcion: ast.AST) -> float:
    """Media de la consistencia de nombres y de comillas (1 = uniforme)."""
    medidas = [
        _proporcion_dominante([_convencion(n) for n in _identificadores(funcion)]),
        _proporcion_dominante(_comillas(codigo)),
    ]
    disponibles = [m for m in medidas if m is not None]
    return sum(disponibles) / len(disponibles) if disponibles else 1.0


def _complejidad(arbol: ast.AST | None) -> float:
    if arbol is None:
        return 1.0
    try:
        bloques = cc_visit_ast(arbol)
    except (SyntaxError, ValueError):
        return 1.0
    return float(max((b.complexity for b in bloques), default=1))


def _lineas(codigo: str) -> float:
    try:
        return float(analyze(codigo).loc)
    except (SyntaxError, ValueError):
        return float(len(codigo.splitlines()))


def extraer_caracteristicas(
    codigo: str, insercion_commit: int | None = None
) -> list[float]:
    """Vector en el orden de NOMBRES_CARACTERISTICAS.

    `log_insercion_commit` queda en NaN cuando no hay historial; el imputador
    del pipeline se encarga de ese caso.
    """
    arbol = _parsear(codigo)
    funcion = _primera_funcion(arbol)
    insercion = (
        math.nan if insercion_commit is None else math.log1p(max(insercion_commit, 0))
    )
    if funcion is None:
        return [
            densidad_comentarios(codigo), 0.0, 0.0, 0.0, 1.0, 1.0,
            _lineas(codigo), insercion,
        ]
    return [
        densidad_comentarios(codigo),
        float(ast.get_docstring(funcion) is not None),
        proporcion_type_hints(funcion),
        longitud_media_identificadores(funcion),
        uniformidad_estilo(codigo, funcion),
        _complejidad(arbol),
        _lineas(codigo),
        insercion,
    ]


class ExtractorCaracteristicas(BaseEstimator, TransformerMixin):
    """Convierte `{"codigo": str, "insercion_commit": int | None}` en una matriz."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array(
            [
                extraer_caracteristicas(m["codigo"], m.get("insercion_commit"))
                for m in X
            ],
            dtype=float,
        ).reshape(len(X), len(NOMBRES_CARACTERISTICAS))

    def get_feature_names_out(self, input_features=None):
        return np.array(NOMBRES_CARACTERISTICAS, dtype=object)
