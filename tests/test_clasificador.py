import math

import pytest

from analisis.servicios.caracteristicas import (
    NOMBRES_CARACTERISTICAS,
    extraer_caracteristicas,
)
from analisis.servicios.clasificador import ModeloNoDisponible, cargar_modelo
from analisis.servicios.entrenamiento import (
    Muestra,
    cargar_corpus,
    entrenar_modelo,
    guardar_modelo,
)
from crear_corpus_demo import generar_corpus

ESTILO_IA = '''def calculate_total_sum(numbers_list: list[int]) -> int:
    """Calcula la suma de los valores.

    Args:
        numbers_list (list[int]): Valores de entrada.

    Returns:
        int: Resultado.
    """
    # Inicializa el acumulador
    total_sum = 0
    for current_value in numbers_list:
        total_sum += current_value
    return total_sum'''

ESTILO_HUMANO = "def s1(l):\n    t=0\n    for i in l:\n        t+=i\n    return t"


def caracteristica(nombre, codigo, insercion=None):
    vector = extraer_caracteristicas(codigo, insercion)
    return vector[NOMBRES_CARACTERISTICAS.index(nombre)]


def muestras_demo():
    return [
        Muestra(m["codigo"], m["etiqueta"], m["insercion_commit"])
        for m in generar_corpus(por_clase=40)
    ]


def test_vector_tiene_una_entrada_por_caracteristica():
    assert len(extraer_caracteristicas(ESTILO_IA, 10)) == len(NOMBRES_CARACTERISTICAS)


def test_detecta_docstring_y_type_hints():
    assert caracteristica("tiene_docstring", ESTILO_IA) == 1.0
    assert caracteristica("tiene_docstring", ESTILO_HUMANO) == 0.0
    assert caracteristica("proporcion_type_hints", ESTILO_IA) == 1.0
    assert caracteristica("proporcion_type_hints", ESTILO_HUMANO) == 0.0


def test_densidad_de_comentarios():
    codigo = "def f():\n    # uno\n    x = 1  # dos\n    return x"
    assert caracteristica("densidad_comentarios", codigo) == 0.5


def test_longitud_de_identificadores():
    assert caracteristica("longitud_media_identificadores", "def ab(cd):\n    return cd") == 2.0


def test_uniformidad_baja_con_estilos_mezclados():
    mezclado = "def miFuncion(otra_cosa):\n    a = 'x'\n    b = \"y\"\n    return a"
    assert caracteristica("uniformidad_estilo", mezclado) < 1.0
    assert caracteristica("uniformidad_estilo", ESTILO_IA) == 1.0


def test_insercion_ausente_queda_como_nan():
    assert math.isnan(caracteristica("log_insercion_commit", ESTILO_IA, None))
    assert caracteristica("log_insercion_commit", ESTILO_IA, 0) == 0.0


def test_codigo_invalido_no_rompe_la_extraccion():
    assert len(extraer_caracteristicas("def roto(:")) == len(NOMBRES_CARACTERISTICAS)


def test_corpus_demo_es_reproducible_y_balanceado():
    corpus = generar_corpus(por_clase=20)
    assert corpus == generar_corpus(por_clase=20)
    assert sum(m["etiqueta"] for m in corpus) == 20


def test_todo_el_corpus_demo_es_python_valido():
    import ast
    for muestra in generar_corpus(por_clase=100):
        ast.parse(muestra["codigo"])


def test_entrena_y_clasifica_con_probabilidades_validas(tmp_path):
    paquete = entrenar_modelo(muestras_demo(), version="prueba", es_demo=True)
    ruta = tmp_path / "modelo.joblib"
    guardar_modelo(paquete, ruta)

    modelo = cargar_modelo(ruta)
    assert modelo.version == "prueba"
    assert modelo.es_demo is True

    p_ia, p_humano = modelo.predecir([
        {"codigo": ESTILO_IA, "insercion_commit": 80},
        {"codigo": ESTILO_HUMANO, "insercion_commit": 5},
    ])
    assert 0.0 <= p_humano < p_ia <= 1.0


def test_clasifica_fragmentos_sin_historial():
    paquete = entrenar_modelo(muestras_demo(), version="prueba", es_demo=True)
    from analisis.servicios.clasificador import ModeloCargado
    modelo = ModeloCargado(paquete["pipeline"], "prueba", True)
    [p_ia] = modelo.predecir([{"codigo": ESTILO_IA, "insercion_commit": None}])
    assert 0.0 <= p_ia <= 1.0


def test_predecir_sin_fragmentos_devuelve_lista_vacia():
    paquete = entrenar_modelo(muestras_demo(), version="prueba", es_demo=True)
    from analisis.servicios.clasificador import ModeloCargado
    assert ModeloCargado(paquete["pipeline"], "prueba", True).predecir([]) == []


def test_entrenar_exige_las_dos_clases():
    with pytest.raises(ValueError):
        entrenar_modelo([Muestra("def f(): pass", 1)], version="x", es_demo=True)


def test_el_corpus_se_reemplaza_con_un_jsonl(tmp_path):
    ruta = tmp_path / "corpus.jsonl"
    ruta.write_text(
        '{"codigo": "def f(): pass", "etiqueta": 1, "insercion_commit": null}\n\n'
        '{"codigo": "def g(): pass", "etiqueta": 0}\n',
        encoding="utf-8",
    )
    assert cargar_corpus(ruta) == [
        Muestra("def f(): pass", 1, None),
        Muestra("def g(): pass", 0, None),
    ]


def test_modelo_inexistente_da_error_claro(tmp_path):
    with pytest.raises(ModeloNoDisponible):
        cargar_modelo(tmp_path / "no_existe.joblib")
