"""Tipos del material de refuerzo y el material de ejemplo, escrito a mano.

El material real son los bloques de `banco.py` (D20). Estas plantillas, una por
concepto, solo sirven como banco de ejemplo para desarrollo y pruebas. Nada aquí
cita el análisis del estudiante: durante la intervención no ve su IDC (D11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analisis.servicios.conceptos import (
    ESTRUCTURAS,
    EXCEPCIONES,
    RECURSION,
)


@dataclass(frozen=True)
class CasoPrueba:
    args: tuple
    esperado: Any = None
    lanza: str | None = None  # nombre de la excepción que debe lanzarse


@dataclass(frozen=True)
class Ejemplo:
    titulo: str
    enunciado: str
    codigo: str
    salida: str  # lo que imprime `codigo`; las pruebas lo verifican
    explicacion: str


@dataclass(frozen=True)
class Ejercicio:
    id: str
    nivel: str
    titulo: str
    enunciado: str
    plantilla: str
    funcion: str
    casos: tuple[CasoPrueba, ...]
    # False si la solución correcta no activa el concepto con las reglas v1 (D32):
    # entonces el portal no le pide al estudiante que lo rehaga.
    aviso_concepto: bool = True


@dataclass(frozen=True)
class Plantilla:
    concepto: str
    explicacion: tuple[str, ...]
    ejemplos: tuple[Ejemplo, ...]
    ejercicios: tuple[Ejercicio, ...]


PLANTILLAS = {
    RECURSION: Plantilla(
        concepto=RECURSION,
        explicacion=(
            "Una función es recursiva cuando se llama a sí misma para resolver "
            "una versión más pequeña del mismo problema.",
            "Toda función recursiva necesita dos partes. El caso base es la "
            "situación tan simple que se responde sin volver a llamar a la "
            "función. El caso recursivo reduce el problema y se llama a sí "
            "misma con esa versión reducida.",
            "Cada llamada queda en espera en la pila de llamadas hasta que la "
            "siguiente termina. Si falta el caso base, o si el problema no se "
            "acerca a él, las llamadas nunca terminan y Python lanza "
            "RecursionError.",
            "Para escribir una recursión, pregúntate primero: ¿cuál es la "
            "entrada más simple posible?, y después: si ya tuviera la respuesta "
            "para una entrada un poco menor, ¿cómo obtendría la de esta?",
        ),
        ejemplos=(
            Ejemplo(
                titulo="Factorial",
                enunciado="Calcula n! = n × (n−1) × … × 1, sabiendo que 0! = 1.",
                codigo=(
                    "def factorial(n):\n"
                    "    if n == 0:              # caso base\n"
                    "        return 1\n"
                    "    return n * factorial(n - 1)  # caso recursivo\n"
                    "\n"
                    "print(factorial(4))"
                ),
                salida="24",
                explicacion=(
                    "factorial(4) espera a factorial(3), que espera a "
                    "factorial(2), y así hasta factorial(0), que responde 1 sin "
                    "llamar a nadie. Luego las respuestas regresan: 1, 1, 2, 6 y "
                    "finalmente 24."
                ),
            ),
            Ejemplo(
                titulo="Suma de una lista",
                enunciado="Suma los elementos de una lista sin usar bucles ni sum().",
                codigo=(
                    "def sumar(lista):\n"
                    "    if not lista:           # caso base: lista vacía\n"
                    "        return 0\n"
                    "    return lista[0] + sumar(lista[1:])\n"
                    "\n"
                    "print(sumar([2, 4, 6]))"
                ),
                salida="12",
                explicacion=(
                    "La suma de una lista es su primer elemento más la suma del "
                    "resto. Cada llamada recibe una lista con un elemento menos, "
                    "así que siempre se llega a la lista vacía, cuya suma es 0."
                ),
            ),
        ),
        ejercicios=(
            Ejercicio(
                id="rec-facil",
                nivel="Fácil",
                titulo="Suma de dígitos",
                enunciado=(
                    "Escribe suma_digitos(n), que devuelva la suma de los dígitos "
                    "de un entero n ≥ 0 usando recursión. Pista: n % 10 es el "
                    "último dígito y n // 10 quita ese dígito."
                ),
                plantilla="def suma_digitos(n):\n    pass\n",
                funcion="suma_digitos",
                casos=(
                    CasoPrueba((0,), 0),
                    CasoPrueba((7,), 7),
                    CasoPrueba((123,), 6),
                    CasoPrueba((9045,), 18),
                ),
            ),
            Ejercicio(
                id="rec-medio",
                nivel="Medio",
                titulo="Palíndromo",
                enunciado=(
                    "Escribe es_palindromo(texto), que devuelva True si el texto "
                    "se lee igual en ambos sentidos, usando recursión. Compara el "
                    "primer y el último carácter, y sigue con lo que queda entre "
                    "ellos. Distingue mayúsculas de minúsculas."
                ),
                plantilla="def es_palindromo(texto):\n    pass\n",
                funcion="es_palindromo",
                casos=(
                    CasoPrueba(("",), True),
                    CasoPrueba(("a",), True),
                    CasoPrueba(("reconocer",), True),
                    CasoPrueba(("python",), False),
                    CasoPrueba(("abca",), False),
                    CasoPrueba(("Ana",), False),
                ),
            ),
            Ejercicio(
                id="rec-dificil",
                nivel="Difícil",
                titulo="Aplanar una lista anidada",
                enunciado=(
                    "Escribe aplanar(lista), que reciba una lista cuyos elementos "
                    "pueden ser enteros u otras listas, con cualquier nivel de "
                    "anidación, y devuelva una lista plana con todos los enteros "
                    "en el mismo orden. Usa isinstance(x, list) para saber si un "
                    "elemento es una lista."
                ),
                plantilla="def aplanar(lista):\n    pass\n",
                funcion="aplanar",
                casos=(
                    CasoPrueba(([],), []),
                    CasoPrueba(([1, 2, 3],), [1, 2, 3]),
                    CasoPrueba(([1, [2, 3], 4],), [1, 2, 3, 4]),
                    CasoPrueba(([[1, [2, [3, [4]]]], 5],), [1, 2, 3, 4, 5]),
                    CasoPrueba(([[], [[]], [1]],), [1]),
                ),
            ),
        ),
    ),
    ESTRUCTURAS: Plantilla(
        concepto=ESTRUCTURAS,
        explicacion=(
            "Una estructura de datos organiza información para que ciertas "
            "operaciones sean simples y rápidas. Elegir bien la estructura suele "
            "simplificar más el código que cualquier otro cambio.",
            "Lista (list): colección ordenada y modificable; se accede por "
            "posición. Usa append para agregar al final y pop para quitar.",
            "Tupla (tuple): colección ordenada que no se puede modificar. Sirve "
            "para datos que van juntos y no cambian, como unas coordenadas.",
            "Diccionario (dict): asocia claves con valores. Buscar por clave es "
            "muy rápido aunque tenga muchos elementos. get(clave, valor) evita "
            "el error cuando la clave no existe.",
            "Conjunto (set): colección sin orden y sin repetidos. Preguntar si "
            "un elemento está dentro es muy rápido, y permite unión e "
            "intersección.",
        ),
        ejemplos=(
            Ejemplo(
                titulo="Contar votos con un diccionario",
                enunciado="Dada una lista de votos, indica cuántos recibió cada opción.",
                codigo=(
                    "def contar_votos(votos):\n"
                    "    conteo = {}\n"
                    "    for voto in votos:\n"
                    "        conteo[voto] = conteo.get(voto, 0) + 1\n"
                    "    return conteo\n"
                    "\n"
                    'print(contar_votos(["si", "no", "si"]))'
                ),
                salida="{'si': 2, 'no': 1}",
                explicacion=(
                    "El diccionario guarda un contador por opción. conteo.get(voto, 0) "
                    "devuelve el contador actual, o 0 la primera vez que aparece "
                    "esa opción, y por eso no hace falta un if."
                ),
            ),
            Ejemplo(
                titulo="Alumnos en común con conjuntos",
                enunciado="Encuentra qué alumnos están matriculados en dos cursos.",
                codigo=(
                    "def en_ambos_cursos(curso_a, curso_b):\n"
                    "    comunes = set(curso_a) & set(curso_b)\n"
                    "    return sorted(comunes)\n"
                    "\n"
                    'print(en_ambos_cursos(["A1", "A2", "A3"], ["A3", "A1", "A9"]))'
                ),
                salida="['A1', 'A3']",
                explicacion=(
                    "Convertir las listas a conjuntos permite usar la intersección "
                    "(&) en vez de dos bucles anidados. Como un conjunto no tiene "
                    "orden, sorted devuelve una lista ordenada y predecible."
                ),
            ),
        ),
        ejercicios=(
            Ejercicio(
                id="est-facil",
                nivel="Fácil",
                titulo="Elementos únicos",
                enunciado=(
                    "Escribe unicos(lista), que devuelva una lista nueva sin "
                    "repetidos, conservando el orden de la primera aparición de "
                    "cada elemento."
                ),
                plantilla="def unicos(lista):\n    pass\n",
                funcion="unicos",
                casos=(
                    CasoPrueba(([],), []),
                    CasoPrueba(([1, 2, 3],), [1, 2, 3]),
                    CasoPrueba(([3, 1, 3, 2, 1],), [3, 1, 2]),
                    CasoPrueba((["a", "a", "a"],), ["a"]),
                ),
            ),
            Ejercicio(
                id="est-medio",
                nivel="Medio",
                titulo="Palabra más frecuente",
                enunciado=(
                    "Escribe mas_frecuente(palabras), que devuelva la palabra que "
                    "más veces aparece en la lista. Si hay empate, devuelve la que "
                    "apareció primero. Si la lista está vacía, devuelve None."
                ),
                plantilla="def mas_frecuente(palabras):\n    pass\n",
                funcion="mas_frecuente",
                casos=(
                    CasoPrueba(([],), None),
                    CasoPrueba((["sol"],), "sol"),
                    CasoPrueba((["a", "b", "b"],), "b"),
                    CasoPrueba((["x", "y", "y", "x"],), "x"),
                    CasoPrueba((["c", "a", "b", "a", "c", "c"],), "c"),
                ),
            ),
            Ejercicio(
                id="est-dificil",
                nivel="Difícil",
                titulo="Agrupar anagramas",
                enunciado=(
                    "Escribe agrupar_anagramas(palabras), que agrupe las palabras "
                    "formadas por las mismas letras. Devuelve una lista de listas: "
                    "los grupos van en el orden en que apareció su primera palabra, "
                    "y dentro de cada grupo se conserva el orden original. Pista: "
                    "dos anagramas tienen el mismo ''.join(sorted(palabra))."
                ),
                plantilla="def agrupar_anagramas(palabras):\n    pass\n",
                funcion="agrupar_anagramas",
                casos=(
                    CasoPrueba(([],), []),
                    CasoPrueba((["sol"],), [["sol"]]),
                    CasoPrueba((["amor", "roma", "sol"],), [["amor", "roma"], ["sol"]]),
                    CasoPrueba(
                        (["ab", "c", "ba", "c", "d"],),
                        [["ab", "ba"], ["c", "c"], ["d"]],
                    ),
                ),
            ),
        ),
    ),
    EXCEPCIONES: Plantilla(
        concepto=EXCEPCIONES,
        explicacion=(
            "Una excepción es la señal de que algo impidió continuar: dividir "
            "entre cero, convertir un texto que no es un número, abrir un archivo "
            "que no existe. Si nadie la atiende, el programa termina con un error.",
            "try encierra el código que puede fallar. except atiende un tipo de "
            "error concreto. else se ejecuta si no hubo error, y finally se "
            "ejecuta siempre, haya fallado o no, por lo que sirve para liberar "
            "recursos.",
            "raise lanza una excepción a propósito cuando un dato no es válido, "
            "para que quien llamó a la función decida qué hacer. También puedes "
            "crear tus propias excepciones heredando de Exception.",
            "Captura solo los errores que sabes manejar. Un except sin tipo "
            "esconde errores de programación, como un nombre mal escrito, y hace "
            "el código mucho más difícil de depurar.",
        ),
        ejemplos=(
            Ejemplo(
                titulo="Convertir con valor por defecto",
                enunciado="Convierte un texto en entero; si no se puede, usa un valor por defecto.",
                codigo=(
                    "def a_entero(texto, defecto=0):\n"
                    "    try:\n"
                    "        return int(texto)\n"
                    "    except ValueError:\n"
                    "        return defecto\n"
                    "\n"
                    'print(a_entero("15"), a_entero("hola"))'
                ),
                salida="15 0",
                explicacion=(
                    "int('hola') lanza ValueError y el control salta al bloque "
                    "except. Solo se captura ValueError, de modo que cualquier otro "
                    "error sigue siendo visible."
                ),
            ),
            Ejemplo(
                titulo="Validar y lanzar con raise",
                enunciado="Registra una nota solo si está entre 0 y 20.",
                codigo=(
                    "def registrar_nota(nota):\n"
                    "    if not 0 <= nota <= 20:\n"
                    '        raise ValueError("La nota debe estar entre 0 y 20")\n'
                    "    return nota\n"
                    "\n"
                    "try:\n"
                    "    registrar_nota(25)\n"
                    "except ValueError as error:\n"
                    '    print("Error:", error)\n'
                    "finally:\n"
                    '    print("Fin del registro")'
                ),
                salida="Error: La nota debe estar entre 0 y 20\nFin del registro",
                explicacion=(
                    "La función detecta el dato inválido y lanza la excepción. Quien "
                    "la llama decide qué hacer, aquí mostrar el mensaje. finally se "
                    "ejecuta en cualquier caso."
                ),
            ),
        ),
        ejercicios=(
            Ejercicio(
                id="exc-facil",
                nivel="Fácil",
                titulo="División segura",
                enunciado=(
                    "Escribe dividir_seguro(a, b), que devuelva a / b, o None si b "
                    "es cero. Usa try/except, no un if."
                ),
                plantilla="def dividir_seguro(a, b):\n    pass\n",
                funcion="dividir_seguro",
                casos=(
                    CasoPrueba((10, 2), 5.0),
                    CasoPrueba((7, 2), 3.5),
                    CasoPrueba((0, 5), 0.0),
                    CasoPrueba((1, 0), None),
                ),
            ),
            Ejercicio(
                id="exc-medio",
                nivel="Medio",
                titulo="Convertir solo lo válido",
                enunciado=(
                    "Escribe convertir_enteros(valores), que reciba una lista de "
                    "valores de cualquier tipo y devuelva una lista con los que se "
                    "pudieron convertir con int(), en el mismo orden. Ignora los "
                    "demás: int('x') lanza ValueError e int(None) lanza TypeError."
                ),
                plantilla="def convertir_enteros(valores):\n    pass\n",
                funcion="convertir_enteros",
                casos=(
                    CasoPrueba(([],), []),
                    CasoPrueba((["1", "2"],), [1, 2]),
                    CasoPrueba((["1", "x", "3"],), [1, 3]),
                    CasoPrueba((["7", None, "hola", 4],), [7, 4]),
                    CasoPrueba(([None, []],), []),
                ),
            ),
            Ejercicio(
                id="exc-dificil",
                nivel="Difícil",
                titulo="Retiro de una cuenta",
                enunciado=(
                    "Define la excepción SaldoInsuficienteError, que herede de "
                    "Exception, y escribe retirar(saldo, monto), que devuelva el "
                    "saldo tras el retiro. Si monto ≤ 0, lanza ValueError. Si monto "
                    "supera el saldo, lanza SaldoInsuficienteError."
                ),
                plantilla=(
                    "class SaldoInsuficienteError(Exception):\n"
                    "    pass\n"
                    "\n"
                    "\n"
                    "def retirar(saldo, monto):\n"
                    "    pass\n"
                ),
                funcion="retirar",
                casos=(
                    CasoPrueba((100, 30), 70),
                    CasoPrueba((100, 100), 0),
                    CasoPrueba((100, 0), lanza="ValueError"),
                    CasoPrueba((100, -5), lanza="ValueError"),
                    CasoPrueba((50, 80), lanza="SaldoInsuficienteError"),
                ),
            ),
        ),
    ),
}

