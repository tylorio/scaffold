"""Flujo web completo con el cliente de pruebas de Django."""
import csv
import io
from pathlib import Path

import pytest
from django.urls import reverse
from git import Actor, Repo

from analisis.models import Analisis, Configuracion, Participante, ResultadoConcepto
from analisis.servicios.conceptos import ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.entrenamiento import Muestra, entrenar_modelo, guardar_modelo
from crear_corpus_demo import generar_corpus
from refuerzo.models import IntentoEjercicio

pytestmark = pytest.mark.django_db

FUNCIONES = """
def recursiva(n):
    return recursiva(n - 1)


def con_lista(l):
    l.append(1)


def con_try():
    try:
        pass
    except ValueError:
        pass
"""


@pytest.fixture(scope="session")
def ruta_modelo(tmp_path_factory):
    muestras = [
        Muestra(m["codigo"], m["etiqueta"], m["insercion_commit"])
        for m in generar_corpus(por_clase=30)
    ]
    ruta = tmp_path_factory.mktemp("modelo") / "modelo.joblib"
    guardar_modelo(entrenar_modelo(muestras, version="prueba", es_demo=True), ruta)
    return ruta


@pytest.fixture(autouse=True)
def usar_modelo(settings, ruta_modelo):
    settings.RUTA_MODELO = ruta_modelo


@pytest.fixture
def repositorio(tmp_path):
    (tmp_path / "tarea.py").write_text(FUNCIONES, encoding="utf-8")
    with Repo.init(tmp_path) as repo:
        repo.index.add(["tarea.py"])
        autor = Actor("Persona Real", "persona@example.invalid")
        repo.index.commit("tarea", author=autor, committer=autor)
    return tmp_path


@pytest.fixture
def participante(repositorio):
    return Participante.objects.create(codigo="P01", repositorio=str(repositorio))


def analisis_con(participante, reforzados):
    """Crea un análisis con la asignación indicada, sin depender del modelo."""
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=9, n_ia=6,
        idc_global=2 / 3,
    )
    for concepto in (RECURSION, ESTRUCTURAS, EXCEPCIONES):
        reforzado = concepto in reforzados
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3,
            n_ia=3 if reforzado else 0, idc=1.0 if reforzado else 0.0,
            estado="debil" if reforzado else "no_debil", reforzado=reforzado,
        )
    return analisis


# Participantes

def test_registra_participante(client, repositorio):
    respuesta = client.post(reverse("analisis:lista"), {
        "codigo": "P02", "repositorio": str(repositorio),
    })
    assert respuesta.status_code == 302
    assert Participante.objects.filter(codigo="P02").exists()


@pytest.mark.parametrize("codigo", ["Juan Perez", "juanperez", "P1"])
def test_rechaza_codigos_que_no_son_anonimos(client, repositorio, codigo):
    respuesta = client.post(reverse("analisis:lista"), {
        "codigo": codigo, "repositorio": str(repositorio),
    })
    assert respuesta.status_code == 200
    assert not Participante.objects.exists()


def test_rechaza_url_con_token(client):
    client.post(reverse("analisis:lista"), {
        "codigo": "P03", "repositorio": "https://yo:secreto@github.com/x/y.git",
    })
    assert not Participante.objects.exists()


def test_aviso_de_modelo_demo_visible_en_todas_las_paginas(client, participante):
    for url in (reverse("analisis:lista"), reverse("analisis:configuracion")):
        assert "Modelo de demostración" in client.get(url).content.decode()


def test_sin_modelo_se_avisa_y_no_se_rompe(client, participante, settings, tmp_path):
    settings.RUTA_MODELO = tmp_path / "no_existe.joblib"
    assert "No hay modelo entrenado" in client.get(reverse("analisis:lista")).content.decode()
    respuesta = client.post(
        reverse("analisis:analizar", args=["P01"]), follow=True
    )
    assert "No existe el modelo" in respuesta.content.decode()
    assert not Analisis.objects.exists()


# Análisis

def test_analizar_guarda_y_muestra_resultados(client, participante):
    respuesta = client.post(reverse("analisis:analizar", args=["P01"]), follow=True)
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "IDC global" in html
    assert "recursiva" in html

    analisis = participante.ultimo_analisis
    assert analisis.n_fragmentos == 3
    assert analisis.tiene_historial
    assert analisis.conceptos.count() == 3
    assert analisis.fragmentos.get(nombre="recursiva").conceptos == [RECURSION]
    assert analisis.fragmentos.get(nombre="con_try").insercion_commit is not None


def test_analizar_sin_funciones_avisa_y_no_guarda(client, tmp_path):
    (tmp_path / "datos.py").write_text("x = 1\n", encoding="utf-8")
    participante = Participante.objects.create(codigo="P02", repositorio=str(tmp_path))

    respuesta = client.post(reverse("analisis:analizar", args=["P02"]), follow=True)
    html = respuesta.content.decode()

    assert "No se encontraron funciones Python" in html
    assert "Análisis completado" not in html
    assert participante.ultimo_analisis is None


def test_analizar_solo_funciones_triviales_no_guarda(client, tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    Participante.objects.create(codigo="P02", repositorio=str(tmp_path))

    respuesta = client.post(reverse("analisis:analizar", args=["P02"]), follow=True)

    assert "No se encontraron funciones Python" in respuesta.content.decode()
    assert not Analisis.objects.exists()


def test_detalle_muestra_intervalos_de_confianza(client, participante):
    analisis_con(participante, {RECURSION})
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "IC 95" in html
    assert "0,44" in html  # 3 de 3 fragmentos en recursión


def test_detalle_avisa_si_hay_varios_autores(client, participante):
    analisis = analisis_con(participante, {RECURSION})
    analisis.n_autores = 3
    analisis.save()
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "3 autores" in html


def test_detalle_no_avisa_con_un_autor(client, participante):
    analisis = analisis_con(participante, {RECURSION})
    analisis.n_autores = 1
    analisis.save()
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "autores" not in html


def test_analizar_guarda_autores_y_triviales(client, participante, repositorio):
    (repositorio / "extra.py").write_text("def g():\n    return 1\n", encoding="utf-8")
    with Repo(repositorio) as repo:
        repo.index.add(["extra.py"])
        autor = Actor("Persona Real", "persona@example.invalid")
        repo.index.commit("extra", author=autor, committer=autor)

    client.post(reverse("analisis:analizar", args=["P01"]))

    analisis = participante.ultimo_analisis
    assert (analisis.n_autores, analisis.n_triviales) == (1, 1)


def test_analizar_sin_funciones_nombra_los_archivos_ilegibles(client, tmp_path):
    (tmp_path / "roto.py").write_text("def f(:\n", encoding="utf-8")
    Participante.objects.create(codigo="P02", repositorio=str(tmp_path))

    respuesta = client.post(reverse("analisis:analizar", args=["P02"]), follow=True)

    assert "roto.py" in respuesta.content.decode()
    assert not Analisis.objects.exists()


def test_analizar_sin_funciones_conserva_el_analisis_anterior(client, participante):
    anterior = analisis_con(participante, [RECURSION])
    participante.repositorio = str(participante.repositorio) + "_vacio"
    Path(participante.repositorio).mkdir()
    participante.save()

    client.post(reverse("analisis:analizar", args=["P01"]))

    assert participante.ultimo_analisis == anterior


def test_analizar_guarda_los_parametros_usados(client, participante):
    config = Configuracion.obtener()
    config.theta = 0.7
    config.m = 1
    config.save()
    client.post(reverse("analisis:analizar", args=["P01"]))
    analisis = participante.ultimo_analisis
    assert (analisis.theta, analisis.m) == (0.7, 1)


def test_analizar_requiere_post(client, participante):
    assert client.get(reverse("analisis:analizar", args=["P01"])).status_code == 405


def test_repositorio_desaparecido_muestra_error(client):
    Participante.objects.create(codigo="P09", repositorio=r"Z:\no\existe")
    respuesta = client.post(reverse("analisis:analizar", args=["P09"]), follow=True)
    assert "No existe la carpeta" in respuesta.content.decode()


def test_no_se_guardan_datos_del_autor(client, participante):
    client.post(reverse("analisis:analizar", args=["P01"]))
    analisis = participante.ultimo_analisis
    guardado = repr(list(analisis.fragmentos.values())) + repr(
        Analisis.objects.filter(pk=analisis.pk).values().first()
    )
    assert "Persona Real" not in guardado
    assert "persona@example" not in guardado


def test_detalle_de_participante_sin_analisis(client, participante):
    assert client.get(reverse("analisis:detalle", args=["P01"])).status_code == 200


# Configuración

def test_guarda_la_configuracion(client):
    client.post(reverse("analisis:configuracion"), {
        "theta": "0.6", "lambda_valor": "0.4", "m": "5",
    })
    config = Configuracion.obtener()
    assert (config.theta, config.lambda_valor, config.m) == (0.6, 0.4, 5)


def test_rechaza_configuracion_fuera_de_rango(client):
    client.post(reverse("analisis:configuracion"), {
        "theta": "1.5", "lambda_valor": "0.4", "m": "0",
    })
    assert Configuracion.obtener().theta == 0.5


# Exportación

def filas_csv(client):
    respuesta = client.get(reverse("analisis:exportar"))
    assert respuesta["Content-Type"].startswith("text/csv")
    return list(csv.DictReader(io.StringIO(respuesta.content.decode())))


def test_exporta_datos_por_participante(client, participante):
    analisis_con(participante, {RECURSION, EXCEPCIONES})
    [fila] = filas_csv(client)
    assert fila["codigo"] == "P01"
    assert float(fila["idc_global"]) == pytest.approx(0.6667)
    assert fila["idc_recursion"] == "1.0"
    assert fila["idc_estructuras_datos"] == "0.0"
    assert fila["reforzado_recursion"] == "1"
    assert fila["reforzado_estructuras_datos"] == "0"
    assert fila["conceptos_reforzados"] == "recursion;excepciones"
    assert fila["modelo_es_demo"] == "1"


def test_exporta_intervalos_autores_y_triviales(client, participante):
    analisis = analisis_con(participante, {RECURSION})
    analisis.n_autores = 2
    analisis.n_triviales = 4
    analisis.save()
    [fila] = filas_csv(client)
    assert float(fila["idc_recursion_ic_inf"]) == pytest.approx(0.4385)
    assert float(fila["idc_recursion_ic_sup"]) == 1.0
    assert float(fila["idc_global_ic_inf"]) == pytest.approx(0.3542, abs=1e-4)
    assert float(fila["idc_global_ic_sup"]) == pytest.approx(0.8794, abs=1e-4)
    assert fila["n_autores"] == "2"
    assert fila["n_triviales"] == "4"


def test_exporta_sin_intervalo_si_no_hay_idc(client, participante):
    analisis = analisis_con(participante, {RECURSION})
    analisis.conceptos.filter(concepto=EXCEPCIONES).update(
        idc=None, estado="datos_insuficientes",
    )
    [fila] = filas_csv(client)
    assert fila["idc_excepciones_ic_inf"] == ""
    assert fila["idc_excepciones_ic_sup"] == ""


def test_exporta_solo_el_ultimo_analisis(client, participante):
    analisis_con(participante, {RECURSION})
    analisis_con(participante, {ESTRUCTURAS})
    [fila] = filas_csv(client)
    assert fila["conceptos_reforzados"] == "estructuras_datos"


def test_exporta_participante_sin_analisis(client, participante):
    [fila] = filas_csv(client)
    assert fila["codigo"] == "P01"
    assert fila["idc_global"] == ""


def test_exportacion_no_incluye_el_origen_del_repositorio(client, participante):
    analisis_con(participante, {RECURSION})
    assert participante.repositorio not in client.get(
        reverse("analisis:exportar")
    ).content.decode()


# Refuerzo

def test_concepto_reforzado_muestra_el_material(client, participante):
    analisis_con(participante, {RECURSION})
    respuesta = client.get(reverse("refuerzo:concepto", args=["P01", RECURSION]))
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Suma de dígitos" in html
    assert "Factorial" in html


def test_concepto_no_reforzado_queda_bloqueado(client, participante):
    analisis_con(participante, {RECURSION})
    respuesta = client.get(reverse("refuerzo:concepto", args=["P01", EXCEPCIONES]))
    assert respuesta.status_code == 403
    assert "División segura" not in respuesta.content.decode()


def test_no_se_puede_enviar_a_un_concepto_no_reforzado(client, participante):
    analisis_con(participante, {RECURSION})
    respuesta = client.post(
        reverse("refuerzo:concepto", args=["P01", EXCEPCIONES]),
        {"ejercicio": "exc-facil", "codigo": "x = 1"},
    )
    assert respuesta.status_code == 403
    assert not IntentoEjercicio.objects.exists()


def test_participante_sin_analisis_no_tiene_refuerzo(client, participante):
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    assert client.get(url).status_code == 403


def test_concepto_inexistente_da_404(client, participante):
    url = reverse("refuerzo:concepto", args=["P01", "magia"])
    assert client.get(url).status_code == 404


def test_enviar_solucion_ejecuta_y_muestra_el_resultado(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    solucion = (
        "def suma_digitos(n):\n"
        "    if n < 10:\n        return n\n"
        "    return n % 10 + suma_digitos(n // 10)\n"
    )
    respuesta = client.post(
        url, {"ejercicio": "rec-facil", "codigo": solucion}, follow=True
    )
    html = respuesta.content.decode()
    assert "4 de 4 pruebas pasadas" in html

    intento = IntentoEjercicio.objects.get()
    assert (intento.pasados, intento.total) == (4, 4)
    assert intento.usa_concepto is True


def test_aviso_si_la_solucion_no_usa_el_concepto(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    solucion = "def suma_digitos(n):\n    return sum(int(c) for c in str(n))\n"
    respuesta = client.post(
        url, {"ejercicio": "rec-facil", "codigo": solucion}, follow=True
    )
    html = respuesta.content.decode()
    assert "4 de 4 pruebas pasadas" in html
    assert "No detectamos" in html


def test_ejercicio_inexistente_da_404(client, participante):
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    assert client.post(url, {"ejercicio": "nada", "codigo": ""}).status_code == 404
