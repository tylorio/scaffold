"""Flujo web completo con el cliente de pruebas de Django."""
import csv
import io
from pathlib import Path

import pytest
from django.db.models import RestrictedError
from django.urls import reverse
from git import Actor, Repo

from analisis.models import (
    Analisis,
    Asignacion,
    Configuracion,
    Participante,
    ResultadoConcepto,
)
from analisis.servicios.conceptos import (
    ESTRUCTURAS,
    EXCEPCIONES,
    NOMBRES_CONCEPTOS,
    RECURSION,
)
from analisis.servicios.entrenamiento import Muestra, entrenar_modelo, guardar_modelo
from analisis.servicios.idc import Parametros, repartir_conceptos
from crear_corpus_demo import generar_corpus
from refuerzo.models import AperturaRefuerzo, IntentoEjercicio
from refuerzo.servicios.contenido import PLANTILLAS

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


def test_configuracion_y_servicio_usan_los_mismos_valores_por_defecto():
    config, parametros = Configuracion(), Parametros()
    assert (config.theta, config.lambda_valor, config.m) == (
        parametros.theta, parametros.lambda_, parametros.m,
    )


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
    assert "completado" not in html
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


# Asignación y fases

@pytest.fixture
def todo_debil():
    """θ = 0 hace que todo cuente como IA, y m = 1 evalúa los tres conceptos."""
    config = Configuracion.obtener()
    config.theta, config.m = 0, 1
    config.save()


def agregar_funcion(repositorio, nombre="tarea_nueva"):
    ruta = repositorio / f"{nombre}.py"
    ruta.write_text(f"def {nombre}(l):\n    l.append(1)\n", encoding="utf-8")
    with Repo(repositorio) as repo:
        repo.index.add([ruta.name])
        autor = Actor("Persona Real", "persona@example.invalid")
        repo.index.commit(nombre, author=autor, committer=autor)


def analizar(client, codigo="P01"):
    return client.post(reverse("analisis:analizar", args=[codigo]), follow=True)


def asignacion_de(codigo="P01"):
    return Asignacion.objects.get(participante__codigo=codigo)


def test_primer_analisis_es_pre_y_crea_la_asignacion(client, participante, todo_debil):
    assert participante.fase_siguiente == "pre"
    analizar(client)

    analisis = participante.ultimo_analisis
    asignacion = asignacion_de()
    assert analisis.fase == "pre"
    assert asignacion.analisis_base == analisis
    assert len(asignacion.reforzados) == 2
    assert len(asignacion.control) == 1
    assert asignacion.comparable
    assert asignacion.debiles == [RECURSION, ESTRUCTURAS, EXCEPCIONES]
    guardados = {c.concepto for c in analisis.conceptos.all() if c.reforzado}
    assert guardados == set(asignacion.reforzados)


def test_la_semilla_guardada_reproduce_la_asignacion(client, participante, todo_debil):
    analizar(client)
    asignacion = asignacion_de()
    reparto = repartir_conceptos(asignacion.debiles, asignacion.semilla)
    assert list(reparto.reforzados) == asignacion.reforzados
    assert list(reparto.control) == asignacion.control


def test_post_conserva_la_asignacion_aunque_cambien_los_debiles(
    client, participante, repositorio, todo_debil
):
    analizar(client)
    asignacion = asignacion_de()
    agregar_funcion(repositorio)
    config = Configuracion.obtener()
    config.theta = 1  # ya nada cuenta como IA: ningún concepto sería débil
    config.save()

    analizar(client)

    analisis = participante.ultimo_analisis
    assert analisis.fase == "post"
    assert Asignacion.objects.count() == 1
    assert asignacion_de().semilla == asignacion.semilla
    assert {c.concepto for c in analisis.conceptos.all() if c.reforzado} == set(
        asignacion.reforzados
    )
    assert not analisis.conceptos.filter(estado="debil").exists()


def test_post_mide_solo_el_codigo_nuevo(client, participante, repositorio, todo_debil):
    analizar(client)
    agregar_funcion(repositorio)
    analizar(client)
    analisis = participante.ultimo_analisis
    assert [f.nombre for f in analisis.fragmentos.all()] == ["tarea_nueva"]


def test_post_sin_codigo_nuevo_avisa_y_no_guarda(client, participante, todo_debil):
    analizar(client)
    html = analizar(client).content.decode()
    assert "No hay funciones nuevas" in html
    assert Analisis.objects.count() == 1


def test_post_sin_historial_avisa_y_no_guarda(client, tmp_path, todo_debil):
    (tmp_path / "a.py").write_text("def f(l):\n    l.append(1)\n", encoding="utf-8")
    Participante.objects.create(codigo="P02", repositorio=str(tmp_path))
    analizar(client, "P02")
    html = analizar(client, "P02").content.decode()
    assert "sin historial Git" in html
    assert Analisis.objects.count() == 1


def test_borrar_la_asignacion_permite_volver_a_empezar(client, participante, todo_debil):
    analizar(client)
    asignacion_de().delete()
    analizar(client)
    assert participante.ultimo_analisis.fase == "pre"
    assert Asignacion.objects.count() == 1


def test_no_se_puede_borrar_el_analisis_base(client, participante, todo_debil):
    analizar(client)
    with pytest.raises(RestrictedError):
        participante.ultimo_analisis.delete()


def test_borrar_el_participante_borra_todo(client, participante, todo_debil):
    analizar(client)
    participante.delete()
    assert not Analisis.objects.exists()
    assert not Asignacion.objects.exists()


def test_un_solo_debil_se_marca_como_no_comparable(client, tmp_path):
    (tmp_path / "a.py").write_text("def f(l):\n    l.append(1)\n", encoding="utf-8")
    with Repo.init(tmp_path) as repo:
        repo.index.add(["a.py"])
        autor = Actor("Persona Real", "persona@example.invalid")
        repo.index.commit("uno", author=autor, committer=autor)
    config = Configuracion.obtener()
    config.theta, config.m = 0, 1
    config.save()
    Participante.objects.create(codigo="P02", repositorio=str(tmp_path))

    html = analizar(client, "P02").content.decode()

    asignacion = asignacion_de("P02")
    assert asignacion.reforzados == [ESTRUCTURAS]
    assert not asignacion.comparable
    assert "fuera de la comparación principal" in html


def test_detalle_muestra_fase_y_control(client, participante, todo_debil):
    analizar(client)
    control = NOMBRES_CONCEPTOS[asignacion_de().control[0]]
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "Fase: pre" in html
    assert f"<strong>Control:</strong>\n      {control}" in html
    assert "Analizar repositorio (post)" in html


def test_el_concepto_de_control_queda_bloqueado(client, participante, todo_debil):
    analizar(client)
    url = reverse("refuerzo:concepto", args=["P01", asignacion_de().control[0]])
    assert client.get(url).status_code == 403


def test_los_intentos_siguen_visibles_tras_el_post(
    client, participante, repositorio, todo_debil, settings
):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analizar(client)
    concepto = asignacion_de().reforzados[0]
    ejercicio = PLANTILLAS[concepto].ejercicios[0]
    url = reverse("refuerzo:concepto", args=["P01", concepto])
    client.post(url, {"ejercicio": ejercicio.id, "codigo": "marca_de_mi_intento = 1"})
    agregar_funcion(repositorio)
    analizar(client)

    assert "marca_de_mi_intento" in client.get(url).content.decode()


def test_abrir_el_material_registra_una_apertura(client, participante):
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    client.get(url)
    apertura = AperturaRefuerzo.objects.get()
    assert (apertura.participante, apertura.concepto) == (participante, RECURSION)


def test_volver_tras_enviar_no_cuenta_como_apertura(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    client.post(url, {"ejercicio": "rec-facil", "codigo": "x = 1"}, follow=True)
    assert not AperturaRefuerzo.objects.exists()


def test_el_control_bloqueado_no_registra_apertura(client, participante):
    analisis_con(participante, {RECURSION})
    client.get(reverse("refuerzo:concepto", args=["P01", EXCEPCIONES]))
    assert not AperturaRefuerzo.objects.exists()


# Exportación

def filas_de(client, url):
    respuesta = client.get(url)
    assert respuesta["Content-Type"].startswith("text/csv")
    return list(csv.DictReader(io.StringIO(respuesta.content.decode())))


def filas_csv(client):
    return filas_de(client, reverse("analisis:exportar"))


def test_exporta_cada_analisis_por_concepto_y_condicion(
    client, participante, repositorio, todo_debil
):
    analizar(client)
    agregar_funcion(repositorio)
    analizar(client)
    asignacion = asignacion_de()

    filas = filas_de(client, reverse("analisis:exportar_analisis"))

    assert len(filas) == 6
    assert [f["fase"] for f in filas] == ["pre"] * 3 + ["post"] * 3
    condicion = {(f["fase"], f["concepto"]): f["condicion"] for f in filas}
    assert condicion["pre", asignacion.control[0]] == "control"
    assert condicion["post", asignacion.reforzados[0]] == "reforzado"
    assert all(f["comparable"] == "1" for f in filas)
    assert {f["semilla"] for f in filas} == {str(asignacion.semilla)}
    assert filas[0]["idc"] != ""
    assert filas[0]["idc_ic_inf"] != ""


def test_exporta_intentos_numerados_con_su_condicion(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = reverse("refuerzo:concepto", args=["P01", RECURSION])
    for _ in range(2):
        client.post(url, {"ejercicio": "rec-facil", "codigo": "secreto_del_codigo = 1"})

    respuesta = client.get(reverse("refuerzo:exportar_intentos"))
    filas = list(csv.DictReader(io.StringIO(respuesta.content.decode())))

    assert [f["intento"] for f in filas] == ["1", "2"]
    assert filas[0]["codigo"] == "P01"
    assert filas[0]["ejercicio"] == "rec-facil"
    assert filas[0]["total"] == "4"
    assert "secreto_del_codigo" not in respuesta.content.decode()


def test_exporta_aperturas(client, participante):
    analisis_con(participante, {RECURSION})
    client.get(reverse("refuerzo:concepto", args=["P01", RECURSION]))
    [fila] = filas_de(client, reverse("refuerzo:exportar_aperturas"))
    assert (fila["codigo"], fila["concepto"]) == ("P01", RECURSION)


def test_los_csv_no_incluyen_datos_que_identifiquen(
    client, participante, repositorio, todo_debil
):
    analizar(client)
    commit = participante.ultimo_analisis.commit_head
    for nombre in ("analisis:exportar", "analisis:exportar_analisis"):
        contenido = client.get(reverse(nombre)).content.decode()
        assert commit not in contenido  # un commit público lleva al repositorio
        assert str(repositorio) not in contenido


def test_csv_por_participante_incluye_fase_y_control(client, participante, todo_debil):
    analizar(client)
    [fila] = filas_csv(client)
    assert fila["fase"] == "pre"
    assert fila["comparable"] == "1"
    assert fila["conceptos_control"] == asignacion_de().control[0]


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
