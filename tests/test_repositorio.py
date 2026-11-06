import os
import tempfile
from pathlib import Path

import pytest
from git import Actor, Repo

from analisis.servicios.clasificador import ModeloCargado
from analisis.servicios.entrenamiento import Muestra, entrenar_modelo
from analisis.servicios.flujo import analizar_repositorio
from analisis.servicios.idc import Parametros
from analisis.servicios.repositorio import (
    CarpetaLocal,
    ErrorRepositorio,
    OrigenInvalido,
    RepositorioGit,
    abrir_repositorio,
    decodificar,
    es_archivo_de_pruebas,
    es_url,
    validar_origen,
)
from crear_corpus_demo import generar_corpus

AUTOR = Actor("Persona Real", "persona@example.invalid")


@pytest.fixture(scope="module")
def modelo():
    muestras = [
        Muestra(m["codigo"], m["etiqueta"], m["insercion_commit"])
        for m in generar_corpus(por_clase=30)
    ]
    paquete = entrenar_modelo(muestras, version="prueba", es_demo=True)
    return ModeloCargado(paquete["pipeline"], "prueba", True)


@pytest.fixture
def repo_git(tmp_path):
    """Repositorio con un commit de 3 líneas y otro de 30 líneas."""
    ruta = tmp_path / "repo"
    ruta.mkdir()
    with Repo.init(ruta) as repo:
        (ruta / "pequeno.py").write_text(
            "def a():\n    x = 1\n    return x\n", encoding="utf-8"
        )
        repo.index.add(["pequeno.py"])
        repo.index.commit("uno", author=AUTOR, committer=AUTOR)

        cuerpo = "def b():\n" + "    x = 1\n" * 28 + "    return x\n"
        (ruta / "grande.py").write_text(cuerpo, encoding="utf-8")
        repo.index.add(["grande.py"])
        repo.index.commit("dos", author=AUTOR, committer=AUTOR)
    return ruta


@pytest.mark.parametrize("origen", [
    "https://github.com/x/y.git",
    "http://example.com/y",
    "git@github.com:x/y.git",
    "ssh://git@host/y.git",
])
def test_reconoce_urls(origen):
    assert es_url(origen)


@pytest.mark.parametrize("origen", ["demo_repo", r"C:\repos\tarea", "./tarea"])
def test_rutas_locales_no_son_urls(origen):
    assert not es_url(origen)


def test_rechaza_urls_con_credenciales():
    with pytest.raises(OrigenInvalido):
        validar_origen("https://usuario:token@github.com/x/y.git")


@pytest.mark.parametrize("origen", [
    "https://github.com/x/y.git?token=SECRETO",
    "https://github.com/x/y.git?access_token=SECRETO&ref=main",
    "https://github.com/x/y.git#SECRETO",
    "https://:SECRETO@github.com/x/y.git",
])
def test_rechaza_urls_que_guardarian_secretos(origen):
    with pytest.raises(OrigenInvalido):
        validar_origen(origen)


def test_url_mal_formada_da_error_propio():
    with pytest.raises(OrigenInvalido):
        validar_origen("https://[github.com/x/y.git")


def test_rechaza_carpeta_inexistente(tmp_path):
    with pytest.raises(OrigenInvalido):
        validar_origen(str(tmp_path / "no_existe"))


def test_acepta_ruta_relativa_a_la_base(tmp_path):
    (tmp_path / "tarea").mkdir()
    validar_origen("tarea", tmp_path)


def test_decodifica_latin1_declarado():
    contenido = "# -*- coding: latin-1 -*-\nx = 'ñ'\n".encode("latin-1")
    assert "ñ" in decodificar(contenido)


def test_carpeta_sin_git_lee_python_y_omite_entornos(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "c.py").write_text("z = 3\n", encoding="utf-8")

    with abrir_repositorio(str(tmp_path)) as lector:
        assert isinstance(lector, CarpetaLocal)
        rutas = [a.ruta for a in lector.archivos()]
        assert lector.insercion_commit("a.py", 1, 1) is None
    assert rutas == ["a.py", "sub/b.py"]


def test_git_lee_head_y_no_los_cambios_sin_confirmar(repo_git):
    (repo_git / "sin_confirmar.py").write_text("def z():\n    pass\n", encoding="utf-8")
    with abrir_repositorio(str(repo_git)) as lector:
        assert isinstance(lector, RepositorioGit)
        rutas = {a.ruta for a in lector.archivos()}
    assert rutas == {"pequeno.py", "grande.py"}


def test_repositorio_sin_commits_se_trata_como_carpeta(tmp_path):
    Repo.init(tmp_path).close()
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    with abrir_repositorio(str(tmp_path)) as lector:
        assert isinstance(lector, CarpetaLocal)


def test_insercion_es_el_tamano_del_commit_de_cada_funcion(repo_git):
    with abrir_repositorio(str(repo_git)) as lector:
        assert lector.insercion_commit("pequeno.py", 1, 3) == 3
        assert lector.insercion_commit("grande.py", 1, 30) == 30


@pytest.mark.parametrize("carpeta", [".venv", "venv/lib", "app/migrations", "build"])
def test_insercion_no_cuenta_carpetas_excluidas(tmp_path, carpeta):
    """Subir un entorno junto al código no debe hacerlo parecer un pegado grande."""
    excluida = tmp_path / carpeta
    excluida.mkdir(parents=True)
    (excluida / "lib.py").write_text("x = 1\n" * 500, encoding="utf-8")
    (tmp_path / "tarea.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    with Repo.init(tmp_path) as repo:
        repo.index.add([f"{carpeta}/lib.py", "tarea.py"])
        repo.index.commit("todo junto", author=AUTOR, committer=AUTOR)

    with abrir_repositorio(str(tmp_path)) as lector:
        assert lector.insercion_commit("tarea.py", 1, 2) == 2


def confirmar(repo, ruta, texto, mensaje, autor=AUTOR):
    destino = Path(repo.working_tree_dir) / ruta
    destino.write_text(texto, encoding="utf-8")
    repo.index.add([ruta])
    repo.index.commit(mensaje, author=autor, committer=autor)


def test_insercion_ignora_cambios_de_solo_espacios(tmp_path):
    """Reindentar no es escribir el código de nuevo."""
    otra = "def otra():\n" + "    y = 2\n" * 28 + "    return y\n"
    with Repo.init(tmp_path) as repo:
        confirmar(repo, "m.py", "def a():\n  x = 1\n  return x\n", "original")
        confirmar(
            repo, "m.py", "def a():\n    x = 1\n    return x\n\n" + otra, "reformatea"
        )

    with abrir_repositorio(str(tmp_path)) as lector:
        assert lector.insercion_commit("m.py", 1, 3) == 3


def test_insercion_sigue_al_codigo_movido_entre_archivos(tmp_path):
    movida = (
        "def calcular_promedio_ponderado(notas_del_curso, pesos_del_curso):\n"
        "    acumulado_total = 0\n"
        "    for nota_actual, peso_actual in zip(notas_del_curso, pesos_del_curso):\n"
        "        acumulado_total += nota_actual * peso_actual\n"
        "    return acumulado_total / sum(pesos_del_curso)\n"
    )
    resto = "def otra():\n" + "    y = 2\n" * 40 + "    return y\n"
    with Repo.init(tmp_path) as repo:
        confirmar(repo, "a.py", movida + "\nz = 1\n", "original")
        destino = Path(repo.working_tree_dir) / "a.py"
        destino.write_text("z = 1\n", encoding="utf-8")
        repo.index.add(["a.py"])
        confirmar(repo, "b.py", resto + "\n" + movida, "reorganiza")

    inicio = len(resto.splitlines()) + 2
    with abrir_repositorio(str(tmp_path)) as lector:
        assert lector.insercion_commit("b.py", inicio, inicio + 4) == 7


def test_cuenta_autores_sin_exponer_sus_datos(tmp_path, modelo):
    otra_persona = Actor("Otra Persona", "OTRA@example.invalid")
    cuerpo = "def {}():\n    x = 1\n    return x\n"
    with Repo.init(tmp_path) as repo:
        confirmar(repo, "a.py", cuerpo.format("a"), "uno")
        confirmar(repo, "b.py", cuerpo.format("b"), "dos", otra_persona)

    datos = analizar_repositorio(str(tmp_path), modelo)

    assert datos.n_autores == 2
    assert "OTRA@example" not in repr(datos)
    assert "Otra Persona" not in repr(datos)


def test_mismo_autor_con_mayusculas_distintas_cuenta_una_vez(tmp_path, modelo):
    cuerpo = "def {}():\n    x = 1\n    return x\n"
    with Repo.init(tmp_path) as repo:
        confirmar(repo, "a.py", cuerpo.format("a"), "uno")
        confirmar(
            repo, "b.py", cuerpo.format("b"), "dos",
            Actor("Persona Real", AUTOR.email.upper()),
        )
    assert analizar_repositorio(str(tmp_path), modelo).n_autores == 1


def test_carpeta_sin_git_no_tiene_autores(tmp_path, modelo):
    (tmp_path / "a.py").write_text(
        "def f():\n    x = 1\n    return x\n", encoding="utf-8"
    )
    assert analizar_repositorio(str(tmp_path), modelo).n_autores is None


@pytest.mark.parametrize("ruta", [
    "test_a.py", "a_test.py", "conftest.py", "tests/a.py", "test/a.py",
    "pruebas/a.py", "app/tests/unidad/a.py",
])
def test_reconoce_archivos_de_pruebas(ruta):
    assert es_archivo_de_pruebas(ruta)


@pytest.mark.parametrize("ruta", [
    "a.py", "testing.py", "contest.py", "latest.py", "app/prueba.py", "test1.py",
])
def test_no_confunde_archivos_normales_con_pruebas(ruta):
    assert not es_archivo_de_pruebas(ruta)


@pytest.mark.parametrize("con_git", [False, True])
def test_flujo_omite_pruebas_y_funciones_triviales(tmp_path, modelo, con_git):
    real = "def real():\n    x = 1\n    return x\n"
    (tmp_path / "tests").mkdir()
    (tmp_path / "app.py").write_text(
        real + "\n\ndef trivial():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_app.py").write_text(
        "def test_real():\n    x = 1\n    assert x\n", encoding="utf-8"
    )
    if con_git:
        with Repo.init(tmp_path) as repo:
            repo.index.add(["app.py", "tests/test_app.py"])
            repo.index.commit("uno", author=AUTOR, committer=AUTOR)

    datos = analizar_repositorio(str(tmp_path), modelo)

    assert [c.fragmento.nombre for c in datos.fragmentos] == ["real"]
    assert datos.resultado.n_fragmentos == 1
    assert datos.n_triviales == 1


def test_flujo_sobre_repositorio_git(repo_git, modelo):
    datos = analizar_repositorio(str(repo_git), modelo, Parametros())
    assert datos.tiene_historial
    assert len(datos.commit_head) == 40
    por_nombre = {c.fragmento.nombre: c for c in datos.fragmentos}
    assert por_nombre["a"].insercion_commit == 3
    assert por_nombre["b"].insercion_commit == 30
    assert all(0 <= c.p_ia <= 1 for c in datos.fragmentos)


def test_flujo_omite_archivos_invalidos_y_los_reporta(tmp_path, modelo):
    (tmp_path / "ok.py").write_text(
        "def f():\n    x = 1\n    return x\n", encoding="utf-8"
    )
    (tmp_path / "roto.py").write_text("def f(:\n", encoding="utf-8")
    (tmp_path / "binario.py").write_bytes(b"\xff\xfe\x00\x00def")

    datos = analizar_repositorio(str(tmp_path), modelo)
    assert [c.fragmento.nombre for c in datos.fragmentos] == ["f"]
    assert set(datos.archivos_con_error) == {"roto.py", "binario.py"}


def test_flujo_sin_funciones_no_falla(tmp_path, modelo):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    datos = analizar_repositorio(str(tmp_path), modelo)
    assert datos.fragmentos == []
    assert datos.resultado.idc_global is None


def test_url_se_clona_y_el_clon_desaparece(repo_git, modelo):
    url = repo_git.as_uri()  # file:///...
    antes = set(Path(tempfile.gettempdir()).glob("idc_clon_*"))

    datos = analizar_repositorio(url, modelo)

    assert {c.fragmento.nombre for c in datos.fragmentos} == {"a", "b"}
    assert datos.tiene_historial
    assert set(Path(tempfile.gettempdir()).glob("idc_clon_*")) == antes


def test_url_inaccesible_da_error_propio(tmp_path):
    url = (tmp_path / "no_existe").as_uri()
    with pytest.raises(ErrorRepositorio):
        with abrir_repositorio(url):
            pass


def test_el_resultado_no_contiene_autores(repo_git, modelo):
    datos = analizar_repositorio(str(repo_git), modelo)
    texto = repr(datos)
    assert "Persona Real" not in texto
    assert "persona@example" not in texto
    assert os.fspath(repo_git) not in texto
