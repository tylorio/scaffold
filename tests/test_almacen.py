"""Almacén local cifrado (pieza 8d, 08 §3.4)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command
from git import Actor, Repo

from analisis.almacen import AVISO, FALTA, OK, revisar_almacen
from analisis.servicios.repositorio import abrir_repositorio

RAIZ = Path(__file__).resolve().parent.parent

LEER_AJUSTES = """
import json, django
django.setup()
from django.conf import settings
print(json.dumps({
    "almacen": str(settings.ALMACEN), "base": str(settings.DATABASES["default"]["NAME"]),
    "datos": str(settings.DATOS_DIR), "modelo": str(settings.RUTA_MODELO),
    "banco": str(settings.BANCO_PRUEBA_DIR), "temporal": str(settings.CARPETA_TEMPORAL),
    "sal": settings.SAL_CORREOS,
}))
"""


def ajustes_con(almacen, modulo="config.settings"):
    entorno = {**os.environ, "DJANGO_SETTINGS_MODULE": modulo, "IDC_ALMACEN": str(almacen),
               "IDC_PERFIL": "local", "DJANGO_SECRET_KEY": "x" * 50, "PYTHONIOENCODING": "utf-8"}
    entorno.pop("IDC_SAL_CORREOS", None)
    return subprocess.run(
        [sys.executable, "-c", LEER_AJUSTES], cwd=RAIZ, env=entorno, capture_output=True,
        text=True, encoding="utf-8",
    )


def test_con_almacen_todo_va_dentro_y_la_sal_sale_de_su_env(tmp_path):
    (tmp_path / ".env").write_text("IDC_SAL_CORREOS=sal-del-almacen\n", encoding="utf-8")
    proceso = ajustes_con(tmp_path)
    assert proceso.returncode == 0, proceso.stderr
    ajustes = json.loads(proceso.stdout)
    for clave in ("base", "datos", "modelo", "banco", "temporal"):
        assert Path(ajustes[clave]).is_relative_to(tmp_path), clave
    # El .env del almacén manda sobre el del proyecto, aunque este también defina la sal.
    assert ajustes["sal"] == "sal-del-almacen"


def test_con_el_almacen_desmontado_no_arranca(tmp_path):
    proceso = ajustes_con(tmp_path / "no_montado")
    assert proceso.returncode != 0
    assert "no está montado" in proceso.stderr


def test_las_pruebas_nunca_usan_el_almacen_real(tmp_path):
    proceso = ajustes_con(tmp_path / "no_montado", modulo="config.settings_pruebas")
    assert proceso.returncode == 0, proceso.stderr
    assert json.loads(proceso.stdout)["almacen"] == "None"


def test_los_clones_van_a_la_carpeta_indicada(tmp_path):
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    with Repo.init(origen) as repo:
        repo.index.add(["a.py"])
        autor = Actor("Persona", "persona@example.invalid")
        repo.index.commit("a", author=autor, committer=autor)
    almacen_tmp = tmp_path / "almacen" / "tmp"
    with abrir_repositorio(origen.as_uri(), temporal=almacen_tmp) as repositorio:
        assert Path(repositorio.ruta).is_relative_to(almacen_tmp)
    assert list(almacen_tmp.iterdir()) == []  # el clon se borra al terminar


# Revisión

def almacen_listo(tmp_path):
    raiz, almacen = tmp_path / "proyecto", tmp_path / "almacen"
    raiz.mkdir()
    (almacen / "datos").mkdir(parents=True)
    (almacen / ".env").write_text("IDC_SAL_CORREOS=s\n", encoding="utf-8")
    (raiz / ".env").write_text("IDC_ALMACEN=Z:\\\n", encoding="utf-8")
    return raiz, almacen


def estados(revisiones):
    return [r.estado for r in revisiones]


def test_un_almacen_bien_armado_pasa_la_revision(tmp_path):
    raiz, almacen = almacen_listo(tmp_path)
    revisiones = revisar_almacen(almacen, almacen / "db.sqlite3", almacen / "datos", raiz, "On")
    assert set(estados(revisiones)) == {OK}


def test_sin_almacen_falta(tmp_path):
    [revision] = revisar_almacen(None, tmp_path / "db.sqlite3", tmp_path / "datos", tmp_path, None)
    assert revision.estado == FALTA


@pytest.mark.parametrize("problema, estado", [
    ("almacen_en_el_repositorio", FALTA),
    ("base_fuera", FALTA),
    ("sin_sal", FALTA),
    ("sal_en_el_proyecto", AVISO),
    ("base_vieja_en_el_proyecto", AVISO),
    ("datos_viejos_en_el_proyecto", AVISO),
    ("bitlocker_apagado", FALTA),
    ("bitlocker_sin_comprobar", AVISO),
])
def test_cada_problema_se_detecta(tmp_path, problema, estado):
    raiz, almacen = almacen_listo(tmp_path)
    base, bitlocker = almacen / "db.sqlite3", "On"
    if problema == "almacen_en_el_repositorio":
        almacen = raiz / "almacen"
        (almacen / "datos").mkdir(parents=True)
        (almacen / ".env").write_text("IDC_SAL_CORREOS=s\n", encoding="utf-8")
        base = almacen / "db.sqlite3"
    elif problema == "base_fuera":
        base = tmp_path / "otra" / "db.sqlite3"
    elif problema == "sin_sal":
        (almacen / ".env").unlink()
    elif problema == "sal_en_el_proyecto":
        (raiz / ".env").write_text("IDC_SAL_CORREOS=s\n", encoding="utf-8")
    elif problema == "base_vieja_en_el_proyecto":
        (raiz / "db.sqlite3").write_text("", encoding="utf-8")
    elif problema == "datos_viejos_en_el_proyecto":
        (raiz / "datos").mkdir()
        (raiz / "datos" / "corpus.jsonl").write_text("{}", encoding="utf-8")
    elif problema == "bitlocker_apagado":
        bitlocker = "Off"
    elif problema == "bitlocker_sin_comprobar":
        bitlocker = None
    revisiones = revisar_almacen(almacen, base, almacen / "datos", raiz, bitlocker)
    assert estado in estados(revisiones)


@pytest.mark.django_db
def test_el_comando_falla_si_no_hay_almacen(settings):
    settings.ALMACEN = None
    with pytest.raises(CommandError) as error:
        call_command("verificar_almacen")
    assert error.value.returncode == 18


@pytest.mark.django_db
def test_el_comando_solo_existe_en_local(settings):
    settings.PERFIL = "nube"
    with pytest.raises(CommandError) as error:
        call_command("verificar_almacen")
    assert error.value.returncode == 17
