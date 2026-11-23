"""Acceso del investigador y del estudiante (pieza 8c, 08 §3)."""
import io
import json
import re
from datetime import timedelta

import pytest
from django.contrib.auth.hashers import check_password
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from analisis.models import (
    Analisis,
    Asignacion,
    Auditoria,
    Configuracion,
    Participante,
    ResultadoConcepto,
)
from analisis.persistencia import congelar_asignacion
from analisis.resultados import exportar_resultados
from analisis.servicios.conceptos import CONCEPTOS, ESTRUCTURAS, RECURSION
from refuerzo.acceso import (
    ALFABETO,
    LARGO,
    MAXIMO_FALLOS,
    SESION_ESTUDIANTE,
    generar_codigo_acceso,
)
from refuerzo.models import IntentoAcceso

pytestmark = pytest.mark.django_db


def con_diagnostico(codigo, reforzados):
    participante = Participante.objects.create(codigo=codigo, repositorio="")
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="demo-v1", modelo_es_demo=True, n_fragmentos=9, n_ia=6, idc_global=0.66,
    )
    for concepto in CONCEPTOS:
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=2, idc=0.66,
            estado="debil", reforzado=concepto in reforzados,
        )
    Asignacion.objects.create(
        participante=participante, analisis_base=analisis, semilla=1, debiles=list(CONCEPTOS),
        reforzados=list(reforzados), control=[c for c in CONCEPTOS if c not in reforzados],
        caso="A", orden="AB", modo="confirmatorio",
    )
    return participante


def entrar(cliente, codigo, acceso, ip="10.0.0.1"):
    return cliente.post(
        reverse("estudiante:acceso"), {"participante": codigo, "codigo": acceso},
        REMOTE_ADDR=ip,
    )


# Código de acceso

def test_el_codigo_se_genera_al_azar_y_solo_se_guarda_su_hash():
    participante = Participante.objects.create(codigo="P01", repositorio="")
    codigo = generar_codigo_acceso(participante, "investigador")
    participante.refresh_from_db()
    assert len(codigo) == LARGO and set(codigo) <= set(ALFABETO)
    assert codigo not in participante.codigo_acceso
    assert check_password(codigo, participante.codigo_acceso)
    assert Auditoria.objects.filter(accion=Auditoria.CODIGO_ACCESO, objeto="P01").exists()


def test_generar_otro_invalida_el_anterior(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    viejo = generar_codigo_acceso(participante, "investigador")
    nuevo = generar_codigo_acceso(participante, "investigador")
    assert entrar(cliente_anonimo, "P01", viejo).status_code == 200  # vuelve al formulario
    assert entrar(cliente_anonimo, "P01", nuevo).status_code == 302


def test_el_investigador_ve_el_codigo_una_sola_vez(client):
    Participante.objects.create(codigo="P01", repositorio="")
    respuesta = client.post(reverse("gestion:codigo_acceso", args=["P01"]))
    html = respuesta.content.decode()
    [mostrado] = re.findall(r"<code>([A-Z0-9]{10})</code>", html)
    assert check_password(mostrado, Participante.objects.get(codigo="P01").codigo_acceso)
    assert "Imprímelo ahora" in html
    assert "no-store" in respuesta["Cache-Control"]
    panel = client.get(reverse("gestion:panel")).content.decode()
    assert "Entregado" in panel
    hash_guardado = Participante.objects.get(codigo="P01").codigo_acceso
    assert hash_guardado not in panel


# Entrada del estudiante

def test_entra_con_sus_codigos_y_ve_sus_conceptos(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    codigo = generar_codigo_acceso(participante, "investigador")
    respuesta = entrar(cliente_anonimo, "p01", codigo.lower())  # tolera minúsculas
    assert respuesta.url == reverse("estudiante:inicio")
    html = cliente_anonimo.get(reverse("estudiante:inicio")).content.decode()
    assert "Abrir material" in html
    assert "Disponible después de la prueba final" in html
    assert "IDC" not in html and "0,66" not in html  # D11: sin IDC durante la intervención


def test_codigo_incorrecto(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    generar_codigo_acceso(participante, "investigador")
    respuesta = entrar(cliente_anonimo, "P01", "AAAAAAAAAA")
    assert "no son correctos" in respuesta.content.decode()
    assert SESION_ESTUDIANTE not in cliente_anonimo.session


def test_sin_codigo_generado_nadie_entra(cliente_anonimo):
    con_diagnostico("P01", {RECURSION})
    assert "no son correctos" in entrar(cliente_anonimo, "P01", "").content.decode()


def test_bloqueo_tras_diez_fallos_en_quince_minutos(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    codigo = generar_codigo_acceso(participante, "investigador")
    for _ in range(MAXIMO_FALLOS):
        entrar(cliente_anonimo, "P01", "ZZZZZZZZZZ")
    bloqueado = entrar(cliente_anonimo, "P01", codigo)  # ni con el código correcto
    assert bloqueado.status_code == 429
    assert entrar(Client(), "P01", codigo, ip="10.0.0.2").status_code == 302  # otra conexión

    IntentoAcceso.objects.update(fecha=timezone.now() - timedelta(minutes=16))
    assert entrar(cliente_anonimo, "P01", codigo).status_code == 302


def test_la_ip_no_se_guarda_en_claro_y_se_borra_a_las_24_horas(cliente_anonimo):
    con_diagnostico("P01", {RECURSION})
    entrar(cliente_anonimo, "P01", "ZZZZZZZZZZ", ip="203.0.113.7")
    assert "203.0.113.7" not in json.dumps(list(IntentoAcceso.objects.values()), default=str)
    IntentoAcceso.objects.update(fecha=timezone.now() - timedelta(hours=25))
    entrar(cliente_anonimo, "P01", "ZZZZZZZZZZ")
    assert IntentoAcceso.objects.count() == 1


def test_entrar_renueva_la_sesion(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    codigo = generar_codigo_acceso(participante, "investigador")
    cliente_anonimo.get(reverse("estudiante:acceso"))
    antes = cliente_anonimo.session.session_key
    entrar(cliente_anonimo, "P01", codigo)
    assert cliente_anonimo.session.session_key != antes


def test_salir_cierra_la_sesion_del_estudiante(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    entrar(cliente_anonimo, "P01", generar_codigo_acceso(participante, "investigador"))
    cliente_anonimo.post(reverse("estudiante:salir"))
    assert cliente_anonimo.get(reverse("estudiante:inicio")).status_code == 302


def test_el_formulario_de_acceso_exige_csrf():
    con_diagnostico("P01", {RECURSION})
    estricto = Client(enforce_csrf_checks=True)
    respuesta = estricto.post(reverse("estudiante:acceso"), {"participante": "P01", "codigo": "x"})
    assert respuesta.status_code == 403


# Lo que ve cada estudiante

def test_sin_sesion_no_hay_material(cliente_anonimo):
    con_diagnostico("P01", {RECURSION})
    for url in (reverse("estudiante:inicio"), reverse("estudiante:concepto", args=[RECURSION])):
        respuesta = cliente_anonimo.get(url)
        assert respuesta.status_code == 302
        assert respuesta.url == reverse("estudiante:acceso")


def test_cada_estudiante_solo_ve_su_propio_material(cliente_anonimo):
    con_diagnostico("P01", {RECURSION})
    p02 = con_diagnostico("P02", {ESTRUCTURAS})
    entrar(cliente_anonimo, "P02", generar_codigo_acceso(p02, "investigador"))
    assert cliente_anonimo.get(reverse("estudiante:concepto", args=[RECURSION])).status_code == 403
    assert cliente_anonimo.get(reverse("estudiante:concepto", args=[ESTRUCTURAS])).status_code == 200


def test_la_ruta_vieja_con_el_codigo_en_la_url_ya_no_existe(cliente_anonimo):
    con_diagnostico("P01", {RECURSION})
    assert cliente_anonimo.get("/refuerzo/P01/recursion/").status_code == 404


# Investigador

@pytest.mark.parametrize("nombre, argumentos", [
    ("analisis:lista", []),
    ("analisis:detalle", ["P01"]),
    ("analisis:configuracion", []),
    ("analisis:congelar", []),
    ("analisis:exportar", []),
    ("analisis:exportar_analisis", []),
    ("refuerzo:exportar_intentos", []),
    ("refuerzo:exportar_aperturas", []),
    ("gestion:panel", []),
])
def test_sin_sesion_de_investigador_se_pide_entrar(cliente_anonimo, nombre, argumentos):
    con_diagnostico("P01", {RECURSION})
    respuesta = cliente_anonimo.get(reverse(nombre, args=argumentos))
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("entrar"))


@pytest.mark.parametrize("nombre, argumentos", [
    ("analisis:analizar", ["P01"]),
    ("gestion:codigo_acceso", ["P01"]),
    ("gestion:importar", []),
])
def test_tampoco_se_puede_actuar_sin_sesion(cliente_anonimo, nombre, argumentos):
    con_diagnostico("P01", {RECURSION})
    respuesta = cliente_anonimo.post(reverse(nombre, args=argumentos))
    assert respuesta.status_code == 302
    assert Participante.objects.get(codigo="P01").codigo_acceso == ""


def test_una_sesion_de_estudiante_no_abre_lo_del_investigador(cliente_anonimo):
    participante = con_diagnostico("P01", {RECURSION})
    entrar(cliente_anonimo, "P01", generar_codigo_acceso(participante, "investigador"))
    assert cliente_anonimo.get(reverse("gestion:panel")).status_code == 302


def test_el_investigador_entra_con_su_contrasena(cliente_anonimo, django_user_model):
    django_user_model.objects.create_user("ana", password="clave-larga-de-prueba")
    respuesta = cliente_anonimo.post(
        reverse("entrar"), {"username": "ana", "password": "clave-larga-de-prueba"},
    )
    assert respuesta.status_code == 302
    assert cliente_anonimo.get(reverse("gestion:panel")).status_code == 200


# Importar desde la web (nube)

def preparar_archivo():
    for codigo in ("P01", "P02"):
        participante = Participante.objects.create(codigo=codigo, repositorio="")
        analisis = Analisis.objects.create(
            participante=participante, theta=0.5, lambda_valor=0.5, m=3,
            modelo_version="demo-v1", modelo_es_demo=True, n_fragmentos=9, n_ia=6,
            version_reglas="conceptos-v1", version_rasgos="rasgos-v2",
        )
        for concepto in CONCEPTOS:
            ResultadoConcepto.objects.create(
                analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=3, idc=1.0,
                estado="debil",
            )
    config = Configuracion.obtener()
    config.modo = "confirmatorio"
    config.save()
    congelar_asignacion(semilla_base=3)
    texto = exportar_resultados("investigador")
    Participante.objects.all().delete()
    from analisis.models import Congelacion
    Congelacion.objects.all().delete()
    return texto


def test_importar_desde_la_web_en_la_nube(client, settings):
    texto = preparar_archivo()
    settings.PERFIL, settings.LOCAL = "nube", False
    archivo = io.BytesIO(texto.encode("utf-8"))
    archivo.name = "resultados.json"
    respuesta = client.post(reverse("gestion:importar"), {"archivo": archivo}, follow=True)
    assert "2 participantes nuevos" in respuesta.content.decode()
    assert Participante.objects.count() == 2


def test_un_archivo_rechazado_se_explica_y_no_carga_nada(client, settings):
    settings.PERFIL, settings.LOCAL = "nube", False
    archivo = io.BytesIO(b'{"esquema": "resultados-v1", "codigo": "def f(): pass"}')
    archivo.name = "malo.json"
    respuesta = client.post(reverse("gestion:importar"), {"archivo": archivo}, follow=True)
    assert "Archivo rechazado" in respuesta.content.decode()
    assert not Participante.objects.exists()


def test_en_local_no_se_importa_desde_la_web(client):
    archivo = io.BytesIO(b"{}")
    archivo.name = "r.json"
    assert client.post(reverse("gestion:importar"), {"archivo": archivo}).status_code == 404
