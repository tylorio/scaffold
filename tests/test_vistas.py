"""Flujo web completo con el cliente de pruebas de Django."""
import csv
import io
import math
from datetime import date
from pathlib import Path

import pytest
from django.conf import settings as ajustes
from django.db.models import RestrictedError
from django.urls import reverse
from git import Actor, Repo

from analisis.models import (
    Analisis,
    Asignacion,
    Configuracion,
    Congelacion,
    Participante,
    ResultadoConcepto,
)
from conftest import material
from analisis.servicios.autoria import hash_correo, hashes_de_correos
from analisis.servicios.conceptos import (
    ESTRUCTURAS,
    EXCEPCIONES,
    NOMBRES_CONCEPTOS,
    RECURSION,
)
from analisis.servicios.entrenamiento import Muestra, entrenar_modelo, guardar_modelo
from analisis.servicios.idc import (
    Parametros,
    derivar_semilla,
    repartir_conceptos,
    sortear_orden,
)
from crear_corpus_demo import generar_corpus
from refuerzo.models import AperturaRefuerzo, IntentoEjercicio

pytestmark = pytest.mark.django_db

FUNCIONES = """
def recursiva(n):
    return recursiva(n - 1)


def con_lista(l):
    l.sort()


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


CORREO = "persona@example.invalid"
OTRA_PERSONA = Actor("Otra Persona", "otra@example.invalid")


def crear_participante(codigo, repositorio, correos=(CORREO,)):
    return Participante.objects.create(
        codigo=codigo, repositorio=repositorio,
        hashes_correos=hashes_de_correos(correos, ajustes.SAL_CORREOS),
        consentimiento_en=date(2026, 11, 20), consentimiento_version="v1",
    )


def commitear(carpeta, archivo, contenido, autor=Actor("Persona Real", CORREO)):
    (carpeta / archivo).write_text(contenido, encoding="utf-8")
    with Repo.init(carpeta) as repo:
        repo.index.add([archivo])
        repo.index.commit(archivo, author=autor, committer=autor)


@pytest.fixture
def participante(repositorio):
    return crear_participante(codigo="P01", repositorio=str(repositorio))


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
        "correos": "Persona@Example.invalid, segundo@example.invalid",
        "consentimiento_en": "2026-11-20", "consentimiento_version": "v1",
    })
    assert respuesta.status_code == 302
    participante = Participante.objects.get(codigo="P02")
    assert participante.hashes_correos == hashes_de_correos(
        [CORREO, "segundo@example.invalid"], ajustes.SAL_CORREOS
    )
    assert "example" not in repr(Participante.objects.filter(pk=participante.pk).values())


@pytest.mark.parametrize("correos", ["", "no-es-un-correo"])
def test_rechaza_participante_sin_correos_validos(client, repositorio, correos):
    respuesta = client.post(reverse("analisis:lista"), {
        "codigo": "P02", "repositorio": str(repositorio), "correos": correos,
    })
    assert respuesta.status_code == 200
    assert not Participante.objects.exists()


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
    participante = crear_participante(codigo="P02", repositorio=str(tmp_path))

    respuesta = client.post(reverse("analisis:analizar", args=["P02"]), follow=True)
    html = respuesta.content.decode()

    assert "No se encontraron funciones Python" in html
    assert "completado" not in html
    assert participante.ultimo_analisis is None


def test_analizar_solo_funciones_triviales_no_guarda(client, tmp_path):
    commitear(tmp_path, "a.py", "def f():\n    return 1\n")
    crear_participante(codigo="P02", repositorio=str(tmp_path))

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


def test_analizar_guarda_versiones_e_indice_por_historial(client, participante):
    client.post(reverse("analisis:analizar", args=["P01"]))
    analisis = participante.ultimo_analisis
    assert (analisis.version_reglas, analisis.version_rasgos) == ("conceptos-v1", "rasgos-v2")
    # Las 3 funciones (9 líneas) entraron en un único commit chico, bajo los tres umbrales.
    insercion = analisis.fragmentos.first().insercion_commit
    assert insercion < 15
    assert (analisis.indice_historial, analisis.indice_historial_15) == (0.0, 0.0)
    assert analisis.media_log_insercion == pytest.approx(math.log1p(insercion))
    assert (analisis.n_lineas_con_historial, analisis.n_con_historial) == (9, 3)
    assert (analisis.umbral_historial, analisis.version_historial) == (30, "historial-v1")
    [fila] = filas_csv(client)
    assert (fila["indice_historial"], fila["indice_historial_60"]) == ("0.0", "0.0")
    assert fila["media_log_insercion"] != ""
    assert fila["version_reglas"] == "conceptos-v1"


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
    crear_participante(codigo="P02", repositorio=str(tmp_path))

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
    crear_participante(codigo="P09", repositorio=r"Z:\no\existe")
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


# Diagnóstico y congelación de la asignación (D2, D3, R2, R3, R5)

@pytest.fixture
def todo_debil():
    """θ = 0 hace que todo cuente como IA, y m = 1 evalúa los tres conceptos."""
    config = Configuracion.obtener()
    config.theta, config.m = 0, 1
    config.save()


def analizar(client, codigo="P01"):
    return client.post(reverse("analisis:analizar", args=[codigo]), follow=True)


def fijar_modo(modo="confirmatorio"):
    config = Configuracion.obtener()
    config.modo = modo
    config.save()


def congelar(client, modo="confirmatorio"):
    fijar_modo(modo)
    return client.post(reverse("analisis:congelar"), follow=True)


def asignacion_de(codigo="P01"):
    return Asignacion.objects.get(participante__codigo=codigo)


def test_analizar_no_sortea(client, participante, todo_debil):
    analizar(client)
    assert not Asignacion.objects.exists()
    assert not participante.ultimo_analisis.conceptos.filter(reforzado=True).exists()
    url = material(client, RECURSION)
    assert client.get(url).status_code == 403  # sin congelar no hay material


def test_volver_a_analizar_reemplaza_el_diagnostico(client, participante, todo_debil):
    analizar(client)
    anterior = participante.ultimo_analisis.pk
    html = analizar(client).content.decode()
    assert Analisis.objects.count() == 1
    assert participante.ultimo_analisis.pk != anterior
    assert "Reemplaza al análisis anterior" in html


def test_no_se_puede_congelar_sin_modo(client, participante, todo_debil):
    analizar(client)
    html = client.get(reverse("analisis:congelar")).content.decode()
    assert "Fija el modo" in html
    client.post(reverse("analisis:congelar"))
    assert not Congelacion.objects.exists()


def test_no_se_puede_congelar_si_falta_un_diagnostico(client, participante, repositorio):
    crear_participante(codigo="P02", repositorio=str(repositorio))
    analizar(client)
    html = congelar(client).content.decode()
    assert "Sin diagnóstico: P02" in html
    assert not Congelacion.objects.exists()


def test_la_pagina_de_congelar_muestra_que_va_a_pasar(client, participante, todo_debil):
    analizar(client)
    fijar_modo()
    html = client.get(reverse("analisis:congelar")).content.decode()
    assert "una sola vez" in html
    assert "Caso A, entre los débiles:\n            1 participante." in html
    assert not Congelacion.objects.exists()  # mirar no congela


def test_congelar_sortea_conceptos_y_orden_de_todos(client, participante, repositorio, todo_debil):
    crear_participante(codigo="P02", repositorio=str(repositorio))
    analizar(client)
    analizar(client, "P02")

    congelar(client)

    [hecha] = Congelacion.objects.all()
    assert (hecha.modo, hecha.tamano_bloque) == ("confirmatorio", 4)
    asignaciones = list(Asignacion.objects.order_by("participante__codigo"))
    assert [a.caso for a in asignaciones] == ["A", "A"]
    assert sorted(a.orden for a in asignaciones) == ["AB", "BA"]
    for a in asignaciones:
        assert (len(a.reforzados), len(a.control)) == (2, 1)
        guardados = {c.concepto for c in a.analisis_base.conceptos.all() if c.reforzado}
        assert guardados == set(a.reforzados)


def test_la_semilla_base_reproduce_la_asignacion(client, participante, todo_debil):
    from analisis.persistencia import _resultado_idc
    analizar(client)
    congelar(client)
    base, asignacion = Congelacion.objects.get().semilla_base, asignacion_de()
    reparto = repartir_conceptos(
        _resultado_idc(asignacion.analisis_base),
        derivar_semilla(base, "conceptos", "P01"), asignacion.modo,
    )
    assert (list(reparto.reforzados), list(reparto.control)) == (
        asignacion.reforzados, asignacion.control,
    )
    assert asignacion.semilla == reparto.semilla
    assert sortear_orden(["P01"], base)["P01"] == asignacion.orden


def test_modo_exploratorio_omite_el_caso_a(client, participante, todo_debil):
    analizar(client)
    congelar(client, "exploratorio")
    assert (asignacion_de().caso, asignacion_de().modo) == ("B", "exploratorio")


def test_despues_de_congelar_no_se_puede_reanalizar(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    html = analizar(client).content.decode()
    assert "ya está congelada" in html
    assert Analisis.objects.count() == 1
    assert "Volver a analizar" not in client.get(reverse("analisis:lista")).content.decode()


def test_no_se_congela_dos_veces(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    congelar(client)
    assert Congelacion.objects.count() == 1
    assert Asignacion.objects.count() == 1


def test_el_modo_no_cambia_despues_de_congelar(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    client.post(reverse("analisis:configuracion"), {
        "theta": 0, "lambda_valor": 0.5, "m": 1, "modo": "exploratorio",
    })
    assert Configuracion.obtener().modo == "confirmatorio"


def test_lo_que_va_despues_de_congelar_lo_exige(client, participante, todo_debil):
    from analisis.persistencia import NoSePuedeCongelar, exigir_asignacion_congelada
    analizar(client)
    with pytest.raises(NoSePuedeCongelar):
        exigir_asignacion_congelada()
    congelar(client)
    assert exigir_asignacion_congelada() == Congelacion.objects.get()


def test_comando_congelar_asignacion(participante, client, todo_debil):
    from django.core.management import CommandError, call_command
    analizar(client)
    with pytest.raises(CommandError) as falta_modo:
        call_command("congelar_asignacion")
    assert falta_modo.value.returncode == 10
    fijar_modo()
    salida = io.StringIO()
    call_command("congelar_asignacion", "--semilla-base", "123", stdout=salida)
    assert Congelacion.objects.get().semilla_base == 123
    assert "P01  caso A" in salida.getvalue()
    with pytest.raises(CommandError) as repetida:
        call_command("congelar_asignacion")
    assert repetida.value.returncode == 11


def test_sin_historial_no_se_puede_comprobar_la_autoria(client, tmp_path, todo_debil):
    (tmp_path / "a.py").write_text("def f(l):\n    l.sort()\n", encoding="utf-8")
    crear_participante(codigo="P02", repositorio=str(tmp_path))
    html = analizar(client, "P02").content.decode()
    assert "sin historial Git" in html
    assert not Analisis.objects.exists()


# Filtro por autor (D19)

def test_solo_se_analizan_las_funciones_del_participante(client, participante, repositorio):
    commitear(
        repositorio, "del_companero.py",
        "def ajena(l):\n    l.sort()\n\n\ndef otra_ajena(n):\n    return otra_ajena(n - 1)\n",
        autor=OTRA_PERSONA,
    )
    analizar(client)
    analisis = participante.ultimo_analisis
    assert set(analisis.fragmentos.values_list("nombre", flat=True)) == {
        "recursiva", "con_lista", "con_try",
    }
    assert analisis.n_fragmentos_otros_autores == 2
    assert analisis.n_autores == 2


def test_no_se_guardan_correos_de_terceros_ni_sus_hashes(
    client, participante, repositorio
):
    commitear(repositorio, "del_companero.py", "def ajena(l):\n    l.sort()\n",
              autor=OTRA_PERSONA)
    analizar(client)
    huella_ajena = hash_correo(OTRA_PERSONA.email, ajustes.SAL_CORREOS)
    guardado = repr(list(Participante.objects.values())) + repr(
        list(Analisis.objects.values())
    ) + repr(list(participante.ultimo_analisis.fragmentos.values()))
    exportado = "".join(
        client.get(reverse(nombre)).content.decode()
        for nombre in ("analisis:exportar", "analisis:exportar_analisis")
    )
    for texto in (guardado, exportado):
        assert "otra@example" not in texto
        assert "Otra Persona" not in texto
        assert huella_ajena not in texto


def test_participante_sin_correos_declarados_no_se_analiza(client, repositorio):
    Participante.objects.create(
        codigo="P05", repositorio=str(repositorio), consentimiento_en=date(2026, 11, 20),
    )
    html = analizar(client, "P05").content.decode()
    assert "no tiene correos de commit declarados" in html
    assert not Analisis.objects.exists()


def test_si_ningun_correo_coincide_avisa_cuantas_se_descartaron(client, repositorio):
    crear_participante(codigo="P06", repositorio=str(repositorio),
                       correos=("nadie@example.invalid",))
    html = analizar(client, "P06").content.decode()
    assert "Se descartaron 3 funciones de otros autores" in html
    assert not Analisis.objects.exists()


def test_no_se_puede_borrar_el_analisis_base(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    with pytest.raises(RestrictedError):
        participante.ultimo_analisis.delete()


def test_borrar_el_participante_borra_todo(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    participante.delete()
    assert not Analisis.objects.exists()
    assert not Asignacion.objects.exists()


def test_con_un_solo_concepto_calculable_se_sortea_entre_los_tres(client, tmp_path):
    commitear(tmp_path, "a.py", "def f(l):\n    l.sort()\n")
    config = Configuracion.obtener()
    config.theta, config.m = 0, 1
    config.save()
    crear_participante(codigo="P02", repositorio=str(tmp_path))
    analizar(client, "P02")

    congelar(client)

    asignacion = asignacion_de("P02")
    assert asignacion.caso == "C"
    assert set(asignacion.reforzados) | set(asignacion.control) == {
        RECURSION, ESTRUCTURAS, EXCEPCIONES,
    }


def test_detalle_muestra_caso_orden_y_control(client, participante, todo_debil):
    analizar(client)
    assert "pendiente" in client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    congelar(client)
    asignacion = asignacion_de()
    control = NOMBRES_CONCEPTOS[asignacion.control[0]]
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "A: entre los débiles" in html
    assert f"<strong>Control:</strong>\n        {control}" in html
    assert asignacion.get_orden_display() in html
    assert "ya no se puede repetir" in html


def test_el_concepto_de_control_queda_bloqueado(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    url = material(client, asignacion_de().control[0])
    assert client.get(url).status_code == 403


def test_abrir_el_material_registra_una_apertura(client, participante):
    analisis_con(participante, {RECURSION})
    url = material(client, RECURSION)
    client.get(url)
    apertura = AperturaRefuerzo.objects.get()
    assert (apertura.participante, apertura.concepto) == (participante, RECURSION)


def test_volver_tras_enviar_no_cuenta_como_apertura(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = material(client, RECURSION)
    client.post(url, {"ejercicio": "rec-facil", "codigo": "x = 1"}, follow=True)
    assert not AperturaRefuerzo.objects.exists()


def test_el_intento_de_abrir_el_control_queda_registrado_como_bloqueado(client, participante):
    analisis_con(participante, {RECURSION})
    client.get(material(client, EXCEPCIONES))
    apertura = AperturaRefuerzo.objects.get()
    assert (apertura.concepto, apertura.permitida, apertura.motivo) == (
        EXCEPCIONES, False, AperturaRefuerzo.CONCEPTO_BLOQUEADO,
    )
    assert apertura.bloque_id == f"{EXCEPCIONES}-ejemplo"


# Exportación

def filas_de(client, url):
    respuesta = client.get(url)
    assert respuesta["Content-Type"].startswith("text/csv")
    return list(csv.DictReader(io.StringIO(respuesta.content.decode())))


def filas_csv(client):
    return filas_de(client, reverse("analisis:exportar"))


def test_exporta_cada_concepto_con_su_condicion(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    asignacion = asignacion_de()

    filas = filas_de(client, reverse("analisis:exportar_analisis"))

    assert len(filas) == 3
    condicion = {f["concepto"]: f["condicion"] for f in filas}
    assert condicion[asignacion.control[0]] == "control"
    assert condicion[asignacion.reforzados[0]] == "reforzado"
    assert {(f["caso"], f["orden"], f["modo"]) for f in filas} == {
        ("A", asignacion.orden, "confirmatorio"),
    }
    assert {f["semilla"] for f in filas} == {str(asignacion.semilla)}
    assert filas[0]["idc"] != ""
    assert filas[0]["idc_ic_inf"] != ""


def test_antes_de_congelar_el_csv_no_tiene_condicion(client, participante, todo_debil):
    analizar(client)
    filas = filas_de(client, reverse("analisis:exportar_analisis"))
    assert {(f["condicion"], f["caso"]) for f in filas} == {("", "")}


def test_exporta_intentos_numerados_con_su_condicion(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = material(client, RECURSION)
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
    client.get(material(client, RECURSION))
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


def test_csv_por_participante_incluye_caso_orden_y_control(client, participante, todo_debil):
    analizar(client)
    congelar(client)
    [fila] = filas_csv(client)
    asignacion = asignacion_de()
    assert (fila["caso"], fila["orden"], fila["modo"]) == ("A", asignacion.orden, "confirmatorio")
    assert fila["conceptos_control"] == asignacion.control[0]


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
    respuesta = client.get(material(client, RECURSION))
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Suma de dígitos" in html
    assert "Factorial" in html


def test_concepto_no_reforzado_queda_bloqueado(client, participante):
    analisis_con(participante, {RECURSION})
    respuesta = client.get(material(client, EXCEPCIONES))
    assert respuesta.status_code == 403
    assert "División segura" not in respuesta.content.decode()


def test_no_se_puede_enviar_a_un_concepto_no_reforzado(client, participante):
    analisis_con(participante, {RECURSION})
    respuesta = client.post(
        material(client, EXCEPCIONES),
        {"ejercicio": "exc-facil", "codigo": "x = 1"},
    )
    assert respuesta.status_code == 403
    assert not IntentoEjercicio.objects.exists()


def test_participante_sin_analisis_no_tiene_refuerzo(client, participante):
    url = material(client, RECURSION)
    assert client.get(url).status_code == 403


def test_concepto_inexistente_da_404(client, participante):
    url = material(client, "magia")
    assert client.get(url).status_code == 404


def test_enviar_solucion_ejecuta_y_muestra_el_resultado(client, participante, settings):
    settings.TIEMPO_LIMITE_EJERCICIO = 20
    analisis_con(participante, {RECURSION})
    url = material(client, RECURSION)
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
    url = material(client, RECURSION)
    solucion = "def suma_digitos(n):\n    return sum(int(c) for c in str(n))\n"
    respuesta = client.post(
        url, {"ejercicio": "rec-facil", "codigo": solucion}, follow=True
    )
    html = respuesta.content.decode()
    assert "4 de 4 pruebas pasadas" in html
    assert "No detectamos" in html


def test_ejercicio_inexistente_da_404(client, participante):
    analisis_con(participante, {RECURSION})
    url = material(client, RECURSION)
    assert client.post(url, {"ejercicio": "nada", "codigo": ""}).status_code == 404
