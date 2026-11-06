import pytest

from analisis.servicios.conceptos import ESTRUCTURAS, RECURSION
from analisis.servicios.extraccion import ErrorSintaxis, extraer_funciones


def nombres(fuente):
    return [f.nombre for f in extraer_funciones(fuente)]


def test_extrae_funcion_simple_con_sus_datos():
    fuente = "x = 1\n\ndef suma(a, b):\n    return a + b\n"
    [fragmento] = extraer_funciones(fuente, "mod.py")
    assert fragmento.archivo == "mod.py"
    assert fragmento.nombre == "suma"
    assert fragmento.codigo == "def suma(a, b):\n    return a + b"
    assert (fragmento.linea_inicio, fragmento.linea_fin) == (3, 4)
    assert fragmento.lineas == 2
    assert fragmento.complejidad == 1


def test_extrae_metodos_con_nombre_calificado_y_sin_sangria():
    fuente = "class A:\n    def f(self):\n        return 1\n"
    [fragmento] = extraer_funciones(fuente)
    assert fragmento.nombre == "A.f"
    assert fragmento.codigo.startswith("def f(self):")


def test_extrae_async_anidadas_y_clases_anidadas():
    fuente = (
        "async def a():\n    pass\n"
        "def b():\n    def c():\n        pass\n"
        "class D:\n    class E:\n        def f(self):\n            pass\n"
    )
    assert nombres(fuente) == ["a", "b", "b.c", "D.E.f"]


def test_extrae_funciones_dentro_de_condicionales():
    fuente = "if True:\n    def a():\n        pass\n"
    assert nombres(fuente) == ["a"]


def test_incluye_decoradores_en_el_codigo():
    fuente = "@staticmethod\ndef f():\n    pass\n"
    [fragmento] = extraer_funciones(fuente)
    assert fragmento.linea_inicio == 1
    assert fragmento.codigo.startswith("@staticmethod")


def test_cadena_multilinea_pegada_al_margen_no_rompe_el_metodo():
    fuente = 'class A:\n    def f(self):\n        return """\ntexto\n"""\n'
    [fragmento] = extraer_funciones(fuente)
    assert fragmento.codigo.startswith("def f(self):")
    assert "texto" in fragmento.codigo


def test_complejidad_cuenta_las_ramas():
    fuente = (
        "def f(x):\n"
        "    if x > 0:\n        return 1\n"
        "    elif x < 0:\n        return -1\n"
        "    return 0\n"
    )
    assert extraer_funciones(fuente)[0].complejidad == 3


def test_archivo_sin_funciones_no_da_fragmentos():
    assert extraer_funciones("x = 1\n") == []


def test_archivo_invalido_lanza_error_propio():
    with pytest.raises(ErrorSintaxis):
        extraer_funciones("def roto(:\n    pass\n", "malo.py")


def test_guarda_los_conceptos_detectados():
    fuente = "def f(n):\n    return f(n - 1)\n\ndef g(l):\n    l.append(1)\n"
    fragmentos = extraer_funciones(fuente)
    assert fragmentos[0].conceptos == {RECURSION}
    assert fragmentos[1].conceptos == {ESTRUCTURAS}
