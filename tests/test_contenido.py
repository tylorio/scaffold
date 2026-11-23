"""Contenido real del banco de refuerzo (`refuerzo/bloques/`).

Cada bloque que se agregue pasa por aquí sin escribir pruebas nuevas:
- es válido y no choca con otro bloque;
- cada ejercicio tiene su solución de referencia en `tests/soluciones_bloques/`,
  y esa solución pasa todos sus casos con el mismo ejecutor que usan los estudiantes;
- lo que muestra cada ejemplo resuelto es lo que de verdad devuelve su código.

Las soluciones viven solo en el repositorio de pruebas: el portal no las muestra.
"""
import ast
import io
import tokenize
from pathlib import Path

import pytest
from django.conf import settings

from refuerzo.servicios.banco import cargar_carpeta, desde_json, es_de_ejemplo, ranuras_faltantes
from refuerzo.servicios.ejecutor import ejecutar_solucion

RAIZ = Path(__file__).resolve().parent.parent
BLOQUES = cargar_carpeta(RAIZ / "refuerzo" / "bloques")
SOLUCIONES = RAIZ / "tests" / "soluciones_bloques"

EJERCICIOS = [
    (contenido["concepto"], contenido["id"], ejercicio)
    for contenido in BLOQUES
    for ejercicio in desde_json(contenido).ejercicios
]


def test_hay_bloques_reales_y_ninguno_es_de_ejemplo():
    assert BLOQUES
    assert not [b["id"] for b in BLOQUES if es_de_ejemplo(b["id"])]


# Conceptos cuyos 8 bloques ya están escritos. Agrega cada concepto cuando se complete.
COMPLETOS = ("estructuras_datos", "excepciones", "recursion")


@pytest.mark.parametrize("concepto", COMPLETOS)
def test_los_conceptos_completos_tienen_sus_8_bloques(concepto):
    """Sin huecos en el plan de D20: 2 bloques por semana durante 4 semanas."""
    faltan = ranuras_faltantes([(b["concepto"], b["semana"], b["orden"]) for b in BLOQUES])
    assert faltan[concepto] == []


def test_los_ids_de_ejercicio_no_se_repiten_entre_bloques():
    ids = [e.id for _, _, e in EJERCICIOS]
    assert len(ids) == len(set(ids))


def _soluciones_de(concepto: str) -> str:
    ruta = SOLUCIONES / f"{concepto}.py"
    assert ruta.is_file(), f"Falta {ruta.name}: cada ejercicio necesita su solución de referencia."
    return ruta.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "concepto, bloque, ejercicio", EJERCICIOS, ids=[e.id for _, _, e in EJERCICIOS],
)
def test_la_solucion_de_referencia_pasa_todos_los_casos(concepto, bloque, ejercicio):
    codigo = _soluciones_de(concepto)
    assert f"def {ejercicio.funcion}(" in codigo, f"Falta la solución de {ejercicio.id}."
    # Con el límite real: algunos ejercicios (memoización) dependen de él.
    resultado = ejecutar_solucion(codigo, ejercicio, tiempo_limite=settings.TIEMPO_LIMITE_EJERCICIO)
    fallidos = [c for c in resultado.casos if not c.get("paso")]
    assert not resultado.error, resultado.error
    assert resultado.pasados == resultado.total, fallidos


def _resultado_mostrado(codigo: str):
    """El valor que el ejemplo anota en el comentario de su última línea."""
    arbol = ast.parse(codigo)
    ultima = arbol.body[-1]
    assert isinstance(ultima, ast.Expr), "El ejemplo debe terminar con la llamada que muestra."
    comentarios = [
        t for t in tokenize.generate_tokens(io.StringIO(codigo).readline)
        if t.type == tokenize.COMMENT and t.start[0] >= ultima.lineno
    ]
    assert comentarios, "El ejemplo debe anotar su resultado en un comentario."
    return ast.literal_eval(comentarios[0].string.lstrip("#").strip())


@pytest.mark.parametrize(
    "contenido", BLOQUES, ids=[b["id"] for b in BLOQUES],
)
def test_el_ejemplo_resuelto_devuelve_lo_que_muestra(contenido):
    for ejemplo in contenido["ejemplos"]:
        codigo = ejemplo["codigo"]
        arbol = ast.parse(codigo)
        espacio: dict = {}
        cuerpo = ast.Module(body=arbol.body[:-1], type_ignores=[])
        exec(compile(cuerpo, "<ejemplo>", "exec"), espacio)  # contenido del propio repositorio
        obtenido = eval(compile(ast.Expression(arbol.body[-1].value), "<ejemplo>", "eval"), espacio)
        assert obtenido == _resultado_mostrado(codigo)


# Aviso "No detectamos el concepto" (D32)

def _definiciones(concepto: str) -> dict[str, ast.AST]:
    codigo = _soluciones_de(concepto)
    return {
        nodo.name: (nodo, codigo) for nodo in ast.parse(codigo).body
        if isinstance(nodo, (ast.FunctionDef, ast.ClassDef))
    }


def solucion_completa(concepto: str, funcion: str) -> str:
    """La función y las auxiliares y clases que usa: lo que envía un estudiante."""
    definiciones = _definiciones(concepto)
    pendientes, vistas = [funcion], []
    while pendientes:
        nombre = pendientes.pop()
        if nombre in vistas or nombre not in definiciones:
            continue
        vistas.append(nombre)
        nodo, _ = definiciones[nombre]
        pendientes.extend(n.id for n in ast.walk(nodo) if isinstance(n, ast.Name))
    return "\n\n".join(
        ast.get_source_segment(definiciones[n][1], definiciones[n][0]) for n in reversed(vistas)
    )


@pytest.mark.parametrize(
    "concepto, bloque, ejercicio", EJERCICIOS, ids=[e.id for _, _, e in EJERCICIOS],
)
def test_la_solucion_correcta_activa_su_concepto_o_el_aviso_esta_apagado(concepto, bloque, ejercicio):
    """Si la regla v1 no reconoce el concepto en la solución correcta, el portal no debe
    pedirle al estudiante que la rehaga: el ejercicio lleva aviso_concepto: false."""
    from refuerzo.servicios.ejecutor import usa_concepto

    if ejercicio.aviso_concepto:
        assert usa_concepto(solucion_completa(concepto, ejercicio.funcion), concepto), (
            f"{ejercicio.id}: la solución de referencia no activa {concepto}. "
            "Agrega \"aviso_concepto\": false al ejercicio (D32)."
        )


def test_los_avisos_apagados_son_los_siete_de_d32():
    apagados = sorted(e.id for _, _, e in EJERCICIOS if not e.aviso_concepto)
    assert apagados == [
        "ed-s1-1-e1", "ed-s2-1-e1", "ed-s2-2-e1", "ed-s2-2-e2", "ed-s2-2-e3",
        "ed-s4-1-e3", "exc-s4-2-e1",
    ]
