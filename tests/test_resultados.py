"""Archivo resultados-v1, perfiles local/nube y auditoría (pieza 8b, ADR-001)."""
import copy
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from analisis.models import (
    Analisis,
    Asignacion,
    Auditoria,
    Configuracion,
    Congelacion,
    Fragmento,
    Importacion,
    Participante,
    ResultadoConcepto,
)
from analisis.persistencia import congelar_asignacion
from analisis.resultados import (
    ArchivoInvalido,
    construir_resultados,
    exportar_resultados,
    importar_resultados,
)
from analisis.servicios.conceptos import CONCEPTOS
from analisis.servicios.resultados import validar_documento, validar_sin_datos_prohibidos

RAIZ = Path(__file__).resolve().parent.parent
CODIGO_SECRETO = "def funcion_del_estudiante(x):\n    return x  # Autor: Ana"


def con_diagnostico(codigo):
    participante = Participante.objects.create(
        codigo=codigo, repositorio=r"C:\Users\Ana\proyecto", hashes_correos=["a" * 64],
    )
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="demo-v1", modelo_es_demo=True, n_fragmentos=9, n_ia=6,
        idc_global=2 / 3, commit_head="f" * 40, version_reglas="conceptos-v1",
        version_rasgos="rasgos-v2", archivos_con_error=["src/roto.py"],
    )
    for concepto in CONCEPTOS:
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=2, idc=2 / 3,
            estado="debil",
        )
    Fragmento.objects.create(
        analisis=analisis, archivo="src/tarea.py", nombre="funcion_del_estudiante",
        codigo=CODIGO_SECRETO, linea_inicio=1, linea_fin=2, lineas=2, complejidad=1,
        conceptos=["recursion"], insercion_commit=40, p_ia=0.9,
    )
    return participante


@pytest.fixture
def congelada(db):
    for codigo in ("P01", "P02", "P03"):
        con_diagnostico(codigo)
    config = Configuracion.obtener()
    config.modo = "confirmatorio"
    config.save()
    congelar_asignacion(semilla_base=11, usuario="investigador")


def vaciar_como_portal_nuevo():
    """Simula la base vacía del portal: el mismo proceso de prueba, otra base."""
    Participante.objects.all().delete()
    Congelacion.objects.all().delete()


# Validadores puros

@pytest.mark.parametrize("texto, motivo", [
    ("https://github.com/ana/tareas", "una URL"),
    ("ana.perez@usil.pe", "un correo"),
    (r"C:\Users\Ana\proyecto", "una ruta"),
    ("/home/ana/tareas/", "una ruta"),
    ("tarea.py", "una ruta"),
    ("f" * 40, "un hash"),
    ("def f(x):\n    return x", "código"),
    ("import os", "código"),
])
def test_detecta_datos_prohibidos(texto, motivo):
    errores = validar_sin_datos_prohibidos({"campo": texto})
    assert any(motivo in e for e in errores)


def test_tambien_revisa_las_claves():
    assert validar_sin_datos_prohibidos({"src/tarea.py": 1})


@pytest.mark.django_db
def test_un_documento_real_pasa_los_dos_filtros(congelada):
    documento = construir_resultados()
    assert validar_documento(documento) == []
    assert validar_sin_datos_prohibidos(documento) == []


@pytest.mark.django_db
@pytest.mark.parametrize("cambio, error", [
    (lambda d: d["participantes"][0].update(codigo_fuente="x"), "campo no permitido"),
    (lambda d: d["participantes"][0].pop("asignacion"), "falta"),
    (lambda d: d["participantes"][0].update(codigo="Ana Perez"), "código anónimo"),
    (lambda d: d["participantes"][0]["conceptos"][0].update(condicion="otra"), "valor no permitido"),
    (lambda d: d["participantes"][0].update(n_ia=True), "tipo inválido"),
    (lambda d: d.update(esquema="resultados-v0"), "resultados-v1"),
])
def test_la_estructura_es_cerrada(congelada, cambio, error):
    documento = copy.deepcopy(construir_resultados())
    cambio(documento)
    assert any(error in e for e in validar_documento(documento))


# Exportar (local)

@pytest.mark.django_db
def test_exportar_exige_la_asignacion_congelada(tmp_path):
    con_diagnostico("P01")
    with pytest.raises(CommandError) as error:
        call_command("exportar_resultados", "--salida", str(tmp_path / "r.json"))
    assert error.value.returncode == 13


@pytest.mark.django_db
def test_el_archivo_no_lleva_codigo_ni_identificadores(congelada, tmp_path):
    salida = tmp_path / "resultados.json"
    call_command("exportar_resultados", "--salida", str(salida), stdout=io.StringIO())
    texto = salida.read_text(encoding="utf-8")
    for prohibido in ("funcion_del_estudiante", "Ana", "src/", "tarea.py", "f" * 40, "a" * 64,
                      '"repositorio"', '"hashes_correos"', '"commit_head"', '"fragmentos"',
                      '"archivos_con_error"'):
        assert prohibido not in texto
    documento = json.loads(texto)
    assert [p["codigo"] for p in documento["participantes"]] == ["P01", "P02", "P03"]
    assert Auditoria.objects.filter(accion=Auditoria.EXPORTAR).exists()


@pytest.mark.django_db
def test_si_un_dato_parece_prohibido_no_se_escribe_nada(congelada, tmp_path):
    Analisis.objects.update(modelo_version=r"C:\modelos\demo")
    salida = tmp_path / "r.json"
    with pytest.raises(CommandError) as error:
        call_command("exportar_resultados", "--salida", str(salida))
    assert error.value.returncode == 8
    assert not salida.exists()


# Importar (nube)

@pytest.mark.django_db
def test_ida_y_vuelta_entre_local_y_nube(congelada, settings):
    texto = exportar_resultados("investigador")
    esperado = {
        a.participante.codigo: (a.analisis_base.analisis_id, a.reforzados, a.control, a.caso, a.orden)
        for a in Asignacion.objects.select_related("participante", "analisis_base")
    }
    vaciar_como_portal_nuevo()
    settings.PERFIL = "nube"

    importacion, nuevos = importar_resultados(texto, "investigador")

    assert (nuevos, importacion.n_participantes) == (3, 3)
    for asignacion in Asignacion.objects.select_related("participante", "analisis_base"):
        a = asignacion
        assert (a.analisis_base.analisis_id, a.reforzados, a.control, a.caso, a.orden) == (
            esperado[a.participante.codigo]
        )
        reforzados = {c.concepto for c in a.analisis_base.conceptos.all() if c.reforzado}
        assert reforzados == set(a.reforzados)
    assert not Fragmento.objects.exists()
    assert set(Participante.objects.values_list("repositorio", flat=True)) == {""}
    assert set(Analisis.objects.values_list("commit_head", flat=True)) == {""}
    assert all(p.hashes_correos == [] for p in Participante.objects.all())
    assert Congelacion.objects.get().semilla_base == 11
    assert Auditoria.objects.filter(accion=Auditoria.IMPORTAR).count() == 1


@pytest.mark.django_db
def test_importar_es_idempotente(congelada):
    primero = exportar_resultados("investigador")
    documento = json.loads(primero)
    documento["generado"] = "2030-01-01T00:00:00+00:00"  # otra exportación, mismos datos
    segundo = json.dumps(documento)
    vaciar_como_portal_nuevo()
    importar_resultados(primero, "investigador")
    assert importar_resultados(primero, "investigador")[1] == 0
    assert importar_resultados(segundo, "investigador")[1] == 0
    assert Participante.objects.count() == 3
    assert Importacion.objects.count() == 2


@pytest.mark.django_db
def test_otro_diagnostico_para_el_mismo_codigo_se_rechaza(congelada):
    texto = exportar_resultados("investigador")
    vaciar_como_portal_nuevo()
    importar_resultados(texto, "investigador")
    documento = json.loads(texto)
    documento["participantes"][0]["analisis_id"] = "00000000-0000-4000-8000-000000000000"
    with pytest.raises(ArchivoInvalido, match="otro diagnóstico"):
        importar_resultados(json.dumps(documento), "investigador")


@pytest.mark.django_db
def test_otra_congelacion_se_rechaza(congelada):
    texto = exportar_resultados("investigador")
    vaciar_como_portal_nuevo()
    importar_resultados(texto, "investigador")
    documento = json.loads(texto)
    documento["congelacion"]["semilla_base"] = 999
    with pytest.raises(ArchivoInvalido, match="otra asignación"):
        importar_resultados(json.dumps(documento), "investigador")


@pytest.mark.django_db
@pytest.mark.parametrize("cambio", [
    lambda d: d["participantes"][0].update(codigo_fuente=CODIGO_SECRETO),
    lambda d: d["sistema"].update(version="https://github.com/ana/x"),
    lambda d: d["participantes"][0]["versiones"].update(modelo="ana@usil.pe"),
])
def test_el_importador_rechaza_datos_prohibidos_y_no_crea_nada(congelada, cambio):
    documento = construir_resultados()
    cambio(documento)
    vaciar_como_portal_nuevo()
    with pytest.raises(ArchivoInvalido):
        importar_resultados(json.dumps(documento), "investigador")
    assert not Participante.objects.exists()
    assert not Importacion.objects.exists()


@pytest.mark.django_db
def test_comando_importar(congelada, settings, tmp_path):
    archivo = tmp_path / "r.json"
    archivo.write_text(exportar_resultados("investigador"), encoding="utf-8")
    vaciar_como_portal_nuevo()
    settings.PERFIL = "nube"
    salida = io.StringIO()
    call_command("importar_resultados", str(archivo), stdout=salida)
    assert "3 participantes nuevos" in salida.getvalue()
    archivo.write_text("{ roto", encoding="utf-8")
    with pytest.raises(CommandError) as error:
        call_command("importar_resultados", str(archivo))
    assert error.value.returncode == 16


# Perfiles

@pytest.mark.django_db
@pytest.mark.parametrize("comando, argumentos, perfil", [
    ("importar_resultados", ["x.json"], "local"),
    ("exportar_resultados", ["--salida", "x.json"], "nube"),
    ("congelar_asignacion", [], "nube"),
    ("corregir_prueba", ["--momento", "pre", "--soluciones", ".", "--salida", "x.csv"], "nube"),
    ("controlar_solapamiento", [], "nube"),
])
def test_cada_comando_solo_existe_en_su_perfil(settings, comando, argumentos, perfil):
    settings.PERFIL = perfil
    with pytest.raises(CommandError) as error:
        call_command(comando, *argumentos)
    assert error.value.returncode == 17


@pytest.mark.django_db
def test_reanalizar_y_congelar_quedan_en_la_auditoria(congelada):
    [congelar] = Auditoria.objects.filter(accion=Auditoria.CONGELAR)
    assert congelar.usuario == "investigador"
    assert congelar.detalle["n_participantes"] == 3


PERFIL_NUBE = """
import sys
import django
django.setup()
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
import config.urls, refuerzo.views, refuerzo.urls, pruebas.models
assert settings.PERFIL == "nube"
try:
    reverse("analisis:lista")
    sys.exit("las vistas de análisis existen en la nube")
except NoReverseMatch:
    pass
reverse("refuerzo:concepto", args=["P01", "recursion"])
html = render_to_string("base.html", {"perfil": "nube"})
assert "Participantes" not in html
cargados = sorted(m for m in ("git", "pydriller", "sklearn", "joblib") if m in sys.modules)
print(",".join(cargados))
"""


def entorno_nube(**extra):
    return {
        **os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_pruebas", "IDC_PERFIL": "nube",
        "IDC_EJECUTOR_URL": "http://ejecutor:8080", "IDC_EJECUTOR_TOKEN": "t", **extra,
    }


def test_el_perfil_nube_no_carga_git_ni_el_modelo():
    proceso = subprocess.run(
        [sys.executable, "-c", PERFIL_NUBE], cwd=RAIZ, env=entorno_nube(),
        capture_output=True, text=True,
    )
    assert proceso.returncode == 0, proceso.stderr
    assert proceso.stdout.strip() == "", f"La nube cargó: {proceso.stdout.strip()}"


def test_el_perfil_nube_no_arranca_sin_el_ejecutor_aislado():
    entorno = entorno_nube()
    entorno.pop("IDC_EJECUTOR_URL")
    entorno["IDC_EJECUTOR_URL"] = ""
    proceso = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"], cwd=RAIZ, env=entorno,
        capture_output=True, text=True,
    )
    assert proceso.returncode != 0
    assert "ejecutor aislado" in proceso.stderr


def test_el_perfil_nube_no_necesita_la_sal_de_los_correos():
    proceso = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"], cwd=RAIZ,
        env=entorno_nube(IDC_SAL_CORREOS=""), capture_output=True, text=True,
    )
    assert proceso.returncode == 0, proceso.stderr
