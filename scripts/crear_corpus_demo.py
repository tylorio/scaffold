"""Genera un corpus SINTÉTICO en datos/corpus_demo.jsonl.

Sirve solo para que el flujo funcione de punta a punta. Las etiquetas salen de
una regla inventada aquí mismo (mismo problema escrito en dos estilos), así que
un modelo entrenado con esto aprende esa regla, no a detectar código de IA.

Uso:
    python scripts/crear_corpus_demo.py
"""
import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from string import Template

RAIZ = Path(__file__).resolve().parent.parent

MUESTRAS_POR_CLASE = 150
SEMILLA = 42

# Probabilidad de cada rasgo por clase. No son 0 ni 1 para que las clases se
# solapen: también hay estudiantes que documentan y modelos que no lo hacen.
RASGOS = {
    "ia": {"docstring": 0.85, "hints": 0.80, "comentarios": 0.70, "largos": 0.85},
    "humano": {"docstring": 0.12, "hints": 0.10, "comentarios": 0.20, "largos": 0.20},
}


@dataclass(frozen=True)
class Tarea:
    descripcion: str
    parametros: tuple[tuple[str, str], ...]  # (variable, type hint)
    retorno: str
    lineas: tuple[tuple[str, str], ...]  # (código, comentario opcional)
    nombres: dict  # variable -> (nombres cortos, nombres largos)


TAREAS = (
    Tarea(
        "Calcula la suma de los valores de una lista.",
        (("a", "list[int]"),), "int",
        (
            ("$s = 0", "Inicializa el acumulador"),
            ("for $x in $a:", "Recorre cada elemento de la lista"),
            ("    $s += $x", ""),
            ("return $s", "Devuelve el total acumulado"),
        ),
        {
            "f": (["suma", "sumar", "sumaLista", "s1"],
                  ["calculate_total_sum", "sumar_valores_de_lista"]),
            "a": (["l", "lst", "v", "datos"], ["numbers_list", "lista_de_valores"]),
            "s": (["t", "s", "res", "acum"], ["total_sum", "suma_acumulada"]),
            "x": (["i", "x", "n"], ["current_value", "valor_actual"]),
        },
    ),
    Tarea(
        "Calcula el factorial de un número de forma recursiva.",
        (("n", "int"),), "int",
        (
            ("if $n <= 1:", "Caso base de la recursión"),
            ("    return 1", ""),
            ("return $n * $f($n - 1)", "Caso recursivo"),
        ),
        {
            "f": (["fact", "fac", "factorial", "f1"],
                  ["calculate_factorial", "calcular_factorial_recursivo"]),
            "n": (["n", "x", "num"], ["input_number", "numero_entrada"]),
        },
    ),
    Tarea(
        "Calcula la longitud de una lista de forma recursiva.",
        (("a", "list"),), "int",
        (
            ("if not $a:", "Caso base: lista vacía"),
            ("    return 0", ""),
            ("return 1 + $f($a[1:])", "Reduce el problema en un elemento"),
        ),
        {
            "f": (["largo", "tam", "contar", "lenRec"],
                  ["compute_recursive_length", "calcular_longitud_recursiva"]),
            "a": (["l", "xs", "lista"], ["input_items", "elementos_de_entrada"]),
        },
    ),
    Tarea(
        "Cuenta las apariciones de cada palabra.",
        (("a", "list[str]"),), "dict[str, int]",
        (
            ("$d = {}", "Crea el diccionario de frecuencias"),
            ("for $x in $a:", "Procesa cada palabra"),
            ("    $d[$x] = $d.get($x, 0) + 1", "Incrementa el contador"),
            ("return $d", ""),
        ),
        {
            "f": (["contar", "frec", "cuenta", "wc"],
                  ["count_word_frequencies", "contar_frecuencia_palabras"]),
            "a": (["p", "ws", "lista", "pal"], ["words_list", "lista_de_palabras"]),
            "d": (["d", "m", "res", "cnt"], ["frequency_map", "mapa_frecuencias"]),
            "x": (["w", "x", "i"], ["current_word", "palabra_actual"]),
        },
    ),
    Tarea(
        "Elimina los elementos duplicados conservando el orden.",
        (("a", "list"),), "list",
        (
            ("$v = set()", "Conjunto de elementos ya vistos"),
            ("$r = []", "Lista con el resultado final"),
            ("for $x in $a:", ""),
            ("    if $x not in $v:", "Solo agrega elementos nuevos"),
            ("        $v.add($x)", ""),
            ("        $r.append($x)", ""),
            ("return $r", ""),
        ),
        {
            "f": (["unicos", "dedup", "sinRep", "u"],
                  ["remove_duplicate_items", "eliminar_elementos_duplicados"]),
            "a": (["l", "xs", "v1"], ["input_items", "lista_original"]),
            "v": (["vis", "s", "vs"], ["seen_items", "elementos_vistos"]),
            "r": (["r", "out", "res"], ["unique_items", "resultado_unico"]),
            "x": (["x", "e", "i"], ["current_item", "elemento_actual"]),
        },
    ),
    Tarea(
        "Divide dos números y maneja la división por cero.",
        (("a", "float"), ("b", "float")), "float | None",
        (
            ("try:", "Intenta realizar la división"),
            ("    return $a / $b", ""),
            ("except ZeroDivisionError:", "Maneja la división por cero"),
            ("    return None", ""),
        ),
        {
            "f": (["div", "dividir", "dv", "divSeg"],
                  ["safe_divide_numbers", "dividir_de_forma_segura"]),
            "a": (["a", "x", "n"], ["dividend_value", "valor_dividendo"]),
            "b": (["b", "y", "d"], ["divisor_value", "valor_divisor"]),
        },
    ),
    Tarea(
        "Convierte una cadena en entero y valida que no sea negativo.",
        (("a", "str"),), "int",
        (
            ("try:", "Intenta convertir el texto"),
            ("    $n = int($a)", ""),
            ("except ValueError as $e:", "Informa el error de conversión"),
            ("    raise ValueError('valor invalido') from $e", ""),
            ("if $n < 0:", "Valida el rango permitido"),
            ('    raise ValueError("negativo")', ""),
            ("return $n", ""),
        ),
        {
            "f": (["leer", "toInt", "conv", "parse1"],
                  ["parse_positive_integer", "convertir_entero_positivo"]),
            "a": (["s", "txt", "t"], ["input_text", "texto_entrada"]),
            "n": (["n", "v", "num"], ["parsed_value", "valor_convertido"]),
            "e": (["e", "ex", "err"], ["conversion_error", "error_conversion"]),
        },
    ),
    Tarea(
        "Determina si un número es primo.",
        (("n", "int"),), "bool",
        (
            ("if $n < 2:", "Los menores que dos no son primos"),
            ("    return False", ""),
            ("$i = 2", ""),
            ("while $i * $i <= $n:", "Prueba divisores hasta la raíz"),
            ("    if $n % $i == 0:", ""),
            ("        return False", ""),
            ("    $i += 1", ""),
            ("return True", ""),
        ),
        {
            "f": (["primo", "esPrimo", "isP", "p"],
                  ["is_prime_number", "determinar_si_es_primo"]),
            "n": (["n", "x", "num"], ["candidate_number", "numero_candidato"]),
            "i": (["i", "d", "k"], ["current_divisor", "divisor_actual"]),
        },
    ),
    Tarea(
        "Calcula el promedio de tres notas.",
        (("a", "float"), ("b", "float"), ("c", "float")), "float",
        (
            ("$s = $a + $b + $c", "Suma las tres notas"),
            ("return $s / 3", "Divide entre la cantidad de notas"),
        ),
        {
            "f": (["prom", "promedio", "avg", "calcProm"],
                  ["calculate_average_grade", "calcular_promedio_notas"]),
            "a": (["a", "n1", "x"], ["first_grade", "primera_nota"]),
            "b": (["b", "n2", "y"], ["second_grade", "segunda_nota"]),
            "c": (["c", "n3", "z"], ["third_grade", "tercera_nota"]),
            "s": (["s", "t", "tot"], ["grades_total", "suma_de_notas"]),
        },
    ),
)


def _elegir_nombres(tarea: Tarea, largos: bool, rng: random.Random) -> dict:
    return {
        variable: rng.choice(opciones[1 if largos else 0])
        for variable, opciones in tarea.nombres.items()
    }


def _docstring(tarea: Tarea, nombres: dict) -> list[str]:
    lineas = ['    """' + tarea.descripcion, "", "    Args:"]
    for variable, tipo in tarea.parametros:
        lineas.append(f"        {nombres[variable]} ({tipo}): Valor de entrada.")
    lineas += ["", "    Returns:", f"        {tarea.retorno}: Resultado.", '    """']
    return lineas


def renderizar(tarea: Tarea, clase: str, rng: random.Random) -> str:
    rasgos = RASGOS[clase]
    con = {rasgo: rng.random() < p for rasgo, p in rasgos.items()}
    nombres = _elegir_nombres(tarea, con["largos"], rng)

    parametros = ", ".join(
        f"{nombres[v]}: {t}" if con["hints"] else nombres[v]
        for v, t in tarea.parametros
    )
    retorno = f" -> {tarea.retorno}" if con["hints"] else ""
    lineas = [f"def {nombres['f']}({parametros}){retorno}:"]
    if con["docstring"]:
        lineas += _docstring(tarea, nombres)

    for codigo, comentario in tarea.lineas:
        texto = Template(codigo).substitute(nombres)
        sangria = " " * (4 + len(texto) - len(texto.lstrip()))
        if comentario and con["comentarios"]:
            lineas.append(f"{sangria}# {comentario}")
        lineas.append(f"    {texto}")
    return "\n".join(lineas)


def _insercion(clase: str, rng: random.Random) -> int | None:
    """Líneas añadidas en el commit. Un 15 % de las muestras no tiene historial."""
    if rng.random() < 0.15:
        return None
    mediana = 60 if clase == "ia" else 12
    return max(1, int(rng.lognormvariate(0, 0.8) * mediana))


def generar_corpus(semilla: int = SEMILLA, por_clase: int = MUESTRAS_POR_CLASE) -> list[dict]:
    rng = random.Random(semilla)
    muestras = []
    for clase, etiqueta in (("ia", 1), ("humano", 0)):
        for _ in range(por_clase):
            tarea = rng.choice(TAREAS)
            muestras.append({
                "codigo": renderizar(tarea, clase, rng),
                "etiqueta": etiqueta,
                "insercion_commit": _insercion(clase, rng),
            })
    rng.shuffle(muestras)
    return muestras


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el corpus sintético de demo.")
    parser.add_argument("--salida", default=RAIZ / "datos" / "corpus_demo.jsonl")
    args = parser.parse_args()

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    muestras = generar_corpus()
    with open(salida, "w", encoding="utf-8") as archivo:
        for muestra in muestras:
            archivo.write(json.dumps(muestra, ensure_ascii=False) + "\n")
    print(f"Corpus sintético guardado en {salida} ({len(muestras)} muestras).")


if __name__ == "__main__":
    main()
