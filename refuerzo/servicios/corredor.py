"""Proceso hijo que ejecuta la solución de un estudiante.

Se lanza con `python -I corredor.py`, recibe un JSON por stdin y escribe otro por
stdout. Usa solo la biblioteca estándar y no importa nada del proyecto.
"""
import io
import json
import math
import sys

MAXIMO_REPR = 200


class Descarte(io.TextIOBase):
    """Ignora los print del estudiante para que no se mezclen con el resultado."""

    def writable(self):
        return True

    def write(self, texto):
        return len(texto)


def representar(valor):
    try:
        texto = repr(valor)
    except Exception:
        return "<sin representación>"
    return texto if len(texto) <= MAXIMO_REPR else texto[:MAXIMO_REPR] + "…"


def coincide(obtenido, esperado):
    if isinstance(esperado, bool) != isinstance(obtenido, bool):
        return False
    try:
        if isinstance(esperado, float) or isinstance(obtenido, float):
            return math.isclose(obtenido, esperado, rel_tol=1e-9, abs_tol=1e-9)
        return bool(obtenido == esperado)
    except Exception:
        return False


def nombres_excepcion(error):
    return {clase.__name__ for clase in type(error).__mro__}


def ejecutar_caso(funcion, caso):
    resultado = {
        "entrada": ", ".join(representar(a) for a in caso["args"]),
        "esperado": (
            f"lanza {caso['lanza']}" if caso["lanza"] else representar(caso["esperado"])
        ),
        "obtenido": "",
        "paso": False,
    }
    try:
        obtenido = funcion(*caso["args"])
    except BaseException as error:
        resultado["obtenido"] = f"{type(error).__name__}: {error}"[:MAXIMO_REPR]
        resultado["paso"] = bool(caso["lanza"]) and caso["lanza"] in nombres_excepcion(error)
        return resultado

    resultado["obtenido"] = representar(obtenido)
    resultado["paso"] = not caso["lanza"] and coincide(obtenido, caso["esperado"])
    return resultado


def aplicar_limites(argumentos):
    """En el ejecutor aislado: límites del sistema antes de tocar el código ajeno."""
    if "--limites" not in argumentos:
        return
    import resource

    limites = json.loads(argumentos[argumentos.index("--limites") + 1])
    for nombre, valor in limites.items():
        resource.setrlimit(getattr(resource, nombre), (valor, valor))


def main():
    aplicar_limites(sys.argv)
    salida_real = sys.stdout
    entrada = json.loads(sys.stdin.read())
    sys.stdin = io.StringIO("")
    sys.stdout = sys.stderr = Descarte()

    espacio = {"__name__": "solucion"}
    try:
        exec(compile(entrada["codigo"], "solucion.py", "exec"), espacio)
    except BaseException as error:
        linea = getattr(error, "lineno", None)
        detalle = f" (línea {linea})" if linea else ""
        respuesta = {"error": f"{type(error).__name__}{detalle}: {error}"[:300]}
        salida_real.write(json.dumps(respuesta))
        return

    funcion = espacio.get(entrada["funcion"])
    if not callable(funcion):
        respuesta = {"error": f"No se encontró la función {entrada['funcion']}."}
    else:
        respuesta = {"casos": [ejecutar_caso(funcion, c) for c in entrada["casos"]]}
    salida_real.write(json.dumps(respuesta))


if __name__ == "__main__":
    main()
