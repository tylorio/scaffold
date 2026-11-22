"""Prueba de desempeño: banco A/B, corrector de T1–T3 y control de solapamiento."""
import csv
import io
import json
import shutil
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from analisis.models import Analisis, Asignacion, Configuracion, Participante, ResultadoConcepto
from analisis.persistencia import congelar_asignacion
from analisis.servicios.conceptos import CONCEPTOS
from pruebas.models import PuntajeItem
from pruebas.servicios.banco import BancoInvalido, cargar_bancos
from pruebas.servicios.calidad import metricas_calidad
from pruebas.servicios.corrector import (
    ILEGIBLE,
    OK,
    SIN_RESPUESTA,
    corregir_item,
    verificar_referencias,
)
from pruebas.servicios.exportacion import COLUMNAS_PUNTAJES, PROHIBIDAS
from pruebas.servicios.solapamiento import (
    material_de_refuerzo,
    pares_sospechosos,
    similitud_enunciados,
    similitud_soluciones,
)

EJEMPLO = Path(__file__).resolve().parent.parent / "pruebas" / "banco_ejemplo"


@pytest.fixture(scope="module")
def bancos():
    return cargar_bancos(EJEMPLO)


@pytest.fixture
def copia_banco(tmp_path):
    destino = tmp_path / "banco"
    shutil.copytree(EJEMPLO, destino)
    return destino


def modificar(carpeta, forma, cambio):
    ruta = carpeta / f"forma_{forma}.json"
    dato = json.loads(ruta.read_text(encoding="utf-8"))
    cambio(dato)
    ruta.write_text(json.dumps(dato), encoding="utf-8")


# Banco

def test_el_banco_de_ejemplo_es_valido_y_sus_referencias_pasan(bancos):
    assert set(bancos) == {"A", "B"}
    verificar_referencias(bancos, tiempo_limite=20)


def test_las_formas_evaluan_los_mismos_conceptos(bancos):
    for banco in bancos.values():
        assert [(i.item, i.concepto) for i in banco.items] == list(zip(("T1", "T2", "T3"), CONCEPTOS))


def test_falta_un_item(copia_banco):
    modificar(copia_banco, "B", lambda d: d["items"].pop(1))
    with pytest.raises(BancoInvalido, match="T1, T2 y T3"):
        cargar_bancos(copia_banco)


def test_item_con_el_concepto_equivocado(copia_banco):
    modificar(copia_banco, "A", lambda d: d["items"][0].update(concepto="excepciones"))
    with pytest.raises(BancoInvalido, match="A/T1"):
        cargar_bancos(copia_banco)


def test_referencia_que_no_pasa_sus_casos(copia_banco):
    def romper(dato):
        dato["items"][0]["referencia"] = "def contar(lista, x):\n    return 0\n"
    modificar(copia_banco, "A", romper)
    with pytest.raises(BancoInvalido, match="supera 2 de 4"):
        verificar_referencias(cargar_bancos(copia_banco), tiempo_limite=20)


def test_archivo_ausente(tmp_path):
    with pytest.raises(BancoInvalido, match="No se pudo leer"):
        cargar_bancos(tmp_path)


# Calidad y corrección

def test_metricas_de_calidad():
    codigo = (
        "def f(n):\n    # comentario\n    if n:\n        return 1\n    return 0\n\n"
        "def g():\n    return 2\n"
    )
    metricas = metricas_calidad(codigo)
    # 6 líneas de código: el comentario y la línea en blanco no cuentan.
    assert (metricas.cc, metricas.lineas, metricas.n_funciones) == (1.5, 6, 2)


def test_metricas_de_codigo_invalido():
    assert metricas_calidad("def roto(:") is None


def test_solucion_correcta(bancos):
    item = bancos["A"].item("T1")
    resultado = corregir_item(item.referencia, item, tiempo_limite=20)
    assert (resultado.estado, resultado.t_pct) == (OK, 100.0)
    assert (resultado.cc_sol, resultado.lin_sol) == (resultado.cc_ref, resultado.lin_ref)


def test_solucion_parcial(bancos):
    item = bancos["A"].item("T1")
    resultado = corregir_item("def contar(lista, x):\n    return 0\n", item, tiempo_limite=20)
    assert (resultado.casos_pasados, resultado.casos_total, resultado.t_pct) == (2, 4, 50.0)


def test_sin_respuesta_cuenta_como_cero(bancos):
    resultado = corregir_item(None, bancos["B"].item("T3"))
    assert (resultado.estado, resultado.t_pct, resultado.cc_sol) == (SIN_RESPUESTA, 0.0, None)
    assert resultado.cc_ref > 0


def test_solucion_ilegible(bancos):
    resultado = corregir_item("def nota_valida(:", bancos["B"].item("T3"))
    assert (resultado.estado, resultado.t_pct, resultado.lin_sol) == (ILEGIBLE, 0.0, None)


def test_el_csv_no_tiene_columnas_de_la_asignacion():
    assert not set(COLUMNAS_PUNTAJES) & PROHIBIDAS


# Corrección de una sesión, con la asignación congelada

def participante_con_diagnostico(codigo):
    participante = Participante.objects.create(codigo=codigo, repositorio="x")
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=9, n_ia=9,
    )
    for concepto in CONCEPTOS:
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=3, idc=1.0,
            estado="debil",
        )
    return participante


@pytest.fixture
def muestra_congelada(db):
    for codigo in ("P01", "P02"):
        participante_con_diagnostico(codigo)
    config = Configuracion.obtener()
    config.modo = "confirmatorio"
    config.save()
    congelar_asignacion(semilla_base=7)
    return {a.participante.codigo: a for a in Asignacion.objects.select_related("participante")}


def entregar(carpeta, codigo, bancos, forma, items=("T1", "T2", "T3"), contenido=None):
    destino = carpeta / codigo
    destino.mkdir(parents=True, exist_ok=True)
    for item in items:
        texto = contenido if contenido is not None else bancos[forma].item(item).referencia
        (destino / f"{item}.py").write_text(texto, encoding="utf-8")


def corregir(momento, soluciones, salida, **extra):
    salida_texto = io.StringIO()
    call_command(
        "corregir_prueba", "--momento", momento, "--soluciones", str(soluciones),
        "--salida", str(salida), "--banco", str(EJEMPLO), stdout=salida_texto, **extra,
    )
    return salida_texto.getvalue()


def leer_csv(ruta):
    return list(csv.DictReader(io.StringIO(ruta.read_text(encoding="utf-8"))))


@pytest.mark.django_db
def test_corregir_exige_la_asignacion_congelada(tmp_path):
    participante_con_diagnostico("P01")
    (tmp_path / "sol").mkdir()
    with pytest.raises(CommandError) as error:
        corregir("pre", tmp_path / "sol", tmp_path / "p.csv")
    assert error.value.returncode == 13


@pytest.mark.parametrize("momento, posicion", [("pre", 0), ("post", 1)])
def test_cada_participante_se_corrige_con_su_forma(
    muestra_congelada, bancos, tmp_path, momento, posicion
):
    assert {a.orden for a in muestra_congelada.values()} == {"AB", "BA"}
    for codigo, asignacion in muestra_congelada.items():
        entregar(tmp_path / "sol", codigo, bancos, asignacion.orden[posicion])

    corregir(momento, tmp_path / "sol", tmp_path / "p.csv")

    for codigo, asignacion in muestra_congelada.items():
        puntajes = PuntajeItem.objects.filter(participante__codigo=codigo, momento=momento)
        assert {p.forma for p in puntajes} == {asignacion.orden[posicion]}
        assert [p.t_pct for p in puntajes] == [100.0] * 3


def test_el_csv_sale_en_formato_largo_y_sin_la_asignacion(muestra_congelada, bancos, tmp_path):
    for codigo, asignacion in muestra_congelada.items():
        entregar(tmp_path / "sol", codigo, bancos, asignacion.orden[0])
    corregir("pre", tmp_path / "sol", tmp_path / "p.csv")

    filas = leer_csv(tmp_path / "p.csv")
    assert list(filas[0]) == list(COLUMNAS_PUNTAJES)
    assert len(filas) == 6  # 2 participantes × 3 conceptos
    contenido = (tmp_path / "p.csv").read_text(encoding="utf-8")
    for asignacion in muestra_congelada.values():
        assert str(asignacion.semilla) not in contenido


def test_avisa_de_quien_no_entrego_y_de_carpetas_desconocidas(muestra_congelada, bancos, tmp_path):
    asignacion = muestra_congelada["P01"]
    entregar(tmp_path / "sol", "P01", bancos, asignacion.orden[0], items=("T1",))
    (tmp_path / "sol" / "P99").mkdir()

    salida = corregir("pre", tmp_path / "sol", tmp_path / "p.csv")

    assert "P02: sin carpeta de soluciones" in salida
    assert "P99: no es un participante" in salida
    estados = dict(
        PuntajeItem.objects.filter(participante__codigo="P01").values_list("item", "estado")
    )
    assert estados == {"T1": OK, "T2": SIN_RESPUESTA, "T3": SIN_RESPUESTA}
    assert not PuntajeItem.objects.filter(participante__codigo="P02").exists()


def test_una_solucion_ilegible_se_registra_y_se_avisa(muestra_congelada, bancos, tmp_path):
    forma = muestra_congelada["P01"].orden[0]
    entregar(tmp_path / "sol", "P01", bancos, forma, contenido="def roto(:")
    with pytest.raises(CommandError) as error:
        corregir("pre", tmp_path / "sol", tmp_path / "p.csv")
    assert error.value.returncode == 9
    assert PuntajeItem.objects.filter(estado=ILEGIBLE).count() == 3
    assert (tmp_path / "p.csv").exists()


def test_corregir_de_nuevo_reemplaza_los_puntajes(muestra_congelada, bancos, tmp_path):
    forma = muestra_congelada["P01"].orden[0]
    entregar(tmp_path / "sol", "P01", bancos, forma, contenido="x = 1\n")
    corregir("pre", tmp_path / "sol", tmp_path / "p.csv")
    entregar(tmp_path / "sol", "P01", bancos, forma)
    corregir("pre", tmp_path / "sol", tmp_path / "p.csv")
    puntajes = PuntajeItem.objects.filter(participante__codigo="P01")
    assert puntajes.count() == 3
    assert {p.t_pct for p in puntajes} == {100.0}


@pytest.mark.django_db
def test_banco_invalido_detiene_la_correccion(copia_banco, tmp_path):
    modificar(copia_banco, "B", lambda d: d["items"].pop())
    (tmp_path / "sol").mkdir()
    with pytest.raises(CommandError) as error:
        call_command(
            "corregir_prueba", "--momento", "pre", "--soluciones", str(tmp_path / "sol"),
            "--salida", str(tmp_path / "p.csv"), "--banco", str(copia_banco),
        )
    assert error.value.returncode == 14


# Solapamiento con el refuerzo (D21)

def test_similitudes():
    assert similitud_enunciados("Suma los dígitos de un número", "suma los digitos de un numero") == 1.0
    assert similitud_enunciados("Ordena una lista", "Valida una contraseña") == 0.0
    a = "def f(x):\n    return f(x - 1) if x else 0\n"
    b = "def g(y):\n    return g(y - 1) if y else 0\n"
    assert similitud_soluciones(a, b) == 1.0
    assert similitud_soluciones(a, "def roto(:") == 0.0


def test_el_banco_de_ejemplo_no_se_solapa_con_el_refuerzo(bancos):
    assert pares_sospechosos(bancos, material_de_refuerzo()) == []


def test_un_item_copiado_del_refuerzo_se_detecta(copia_banco):
    ejercicio = next(m for m in material_de_refuerzo() if m.id == "rec-facil")
    modificar(copia_banco, "A", lambda d: d["items"][0].update(enunciado=ejercicio.enunciado))
    salida = io.StringIO()
    with pytest.raises(CommandError) as error:
        call_command("controlar_solapamiento", "--banco", str(copia_banco), stdout=salida)
    assert error.value.returncode == 12
    assert "A/T1 ~ rec-facil  (enunciado" in salida.getvalue()


def test_sin_pares_el_comando_termina_bien():
    salida = io.StringIO()
    call_command("controlar_solapamiento", "--banco", str(EJEMPLO), stdout=salida)
    assert "Sin pares sospechosos" in salida.getvalue()
