"""Filtro por autor (D19), sin Django."""
from git import Actor, Repo

from analisis.servicios.autoria import FiltroAutor, hash_correo, hashes_de_correos
from analisis.servicios.repositorio import abrir_repositorio

SAL = "sal-de-prueba"


def test_el_hash_no_contiene_el_correo_y_depende_de_la_sal():
    huella = hash_correo("persona@example.invalid", SAL)
    assert "persona" not in huella
    assert huella != hash_correo("persona@example.invalid", "otra-sal")


def test_normaliza_mayusculas_y_espacios():
    assert hash_correo("  Persona@Example.INVALID ", SAL) == hash_correo(
        "persona@example.invalid", SAL
    )


def test_hashes_sin_repetidos():
    assert len(hashes_de_correos(["a@x.invalid", "A@x.invalid", "b@x.invalid"], SAL)) == 2


def test_filtro_reconoce_solo_los_correos_declarados():
    filtro = FiltroAutor(frozenset(hashes_de_correos(["yo@x.invalid"], SAL)), SAL)
    assert filtro.es_propio("YO@x.invalid")
    assert not filtro.es_propio("otra@x.invalid")
    assert not filtro.es_propio(None)


def test_el_filtro_no_muestra_la_sal():
    assert SAL not in repr(FiltroAutor(frozenset(), SAL))


def test_repositorio_da_el_correo_del_commit_mayoritario(tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    with Repo.init(tmp_path) as repo:
        repo.index.add(["a.py"])
        autor = Actor("Otra Persona", "Otra@Example.invalid")
        repo.index.commit("a", author=autor, committer=autor)
    with abrir_repositorio(str(tmp_path)) as repositorio:
        assert repositorio.correo_autor("a.py", 1, 2) == "otra@example.invalid"


def test_carpeta_sin_historial_no_tiene_autor(tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    with abrir_repositorio(str(tmp_path)) as repositorio:
        assert repositorio.correo_autor("a.py", 1, 2) is None
