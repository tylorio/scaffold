"""Pieza 10: base para el análisis (D17), exclusión (D15), retiro y cierre (D13),
consentimiento e informe personal."""
import csv
import io
import json
from datetime import date

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse

from analisis.estudio import CierreNoPermitido, cerrar_estudio, exportar_estudio
from analisis.models import (
    Analisis,
    Asignacion,
    Auditoria,
    Congelacion,
    Fragmento,
    Participante,
    ResultadoConcepto,
)
from analisis.participacion import CambioNoPermitido, excluir, incluir, retirar
from analisis.persistencia import (
    FueraDeLaMuestra,
    SinConsentimiento,
    ejecutar_analisis,
    estado_congelacion,
)
from analisis.resultados import construir_resultados, importar_resultados
from analisis.servicios.conceptos import CONCEPTOS, ESTRUCTURAS, EXCEPCIONES, RECURSION
from analisis.servicios.estudio import (
    AUSENTE,
    PRESENTE,
    SIN_CORREGIR,
    CalificacionesInvalidas,
    Registro,
    Situacion,
    estado_del_momento,
    etapas_del_flujo,
    forma_del_momento,
    hipotesis_que_lo_usan,
    leer_calificaciones,
    resumir_q,
)
from conftest import material
from pruebas.models import PuntajeItem
from refuerzo.acceso import ParticipanteRetirado, generar_codigo_acceso
from refuerzo.administracion import liberar_control
from refuerzo.models import AperturaRefuerzo, IntentoEjercicio

ITEMS = {RECURSION: "T1", ESTRUCTURAS: "T2", EXCEPCIONES: "T3"}


# Reglas de inclusión (P5), sin base de datos

def situacion(pre=PRESENTE, post=PRESENTE, caso="A", modo="confirmatorio", control=1, idc=True):
    return Situacion(True, idc, pre, post, 2, control, caso, modo)


def test_con_las_dos_pruebas_entra_en_todo():
    assert all(hipotesis_que_lo_usan(situacion()).values())


def test_ausente_en_el_pretest_solo_queda_en_he1():
    usa = hipotesis_que_lo_usan(situacion(pre=AUSENTE))
    assert [h for h, v in usa.items() if v] == ["HE1"]


def test_ausente_en_el_postest_conserva_he1_y_he2():
    usa = hipotesis_que_lo_usan(situacion(post=AUSENTE))
    assert [h for h, v in usa.items() if v] == ["HE1", "HE2a", "HE2b"]


def test_sin_corregir_cuenta_como_dato_faltante():
    assert not hipotesis_que_lo_usan(situacion(post=SIN_CORREGIR))["HG"]


def test_el_subgrupo_de_he4_es_el_caso_a_confirmatorio():
    assert not hipotesis_que_lo_usan(situacion(caso="B"))["HE4_casoA"]
    assert not hipotesis_que_lo_usan(situacion(modo="exploratorio"))["HE4_casoA"]
    assert hipotesis_que_lo_usan(situacion(caso="B"))["HE4"]  # P1: toda la muestra


def test_he5_exige_un_concepto_de_control():
    assert not hipotesis_que_lo_usan(situacion(control=0))["HE5"]


def test_he2b_exige_el_idc_global():
    usa = hipotesis_que_lo_usan(situacion(idc=False))
    assert usa["HE2a"] and not usa["HE2b"]


def test_estado_del_momento():
    assert estado_del_momento([]) == SIN_CORREGIR
    assert estado_del_momento(["ausente"] * 3) == AUSENTE
    assert estado_del_momento(["ok", "sin_respuesta", "ilegible"]) == PRESENTE


def test_forma_segun_el_orden():
    assert [forma_del_momento("AB", m) for m in ("pre", "post")] == ["A", "B"]
    assert [forma_del_momento("BA", m) for m in ("pre", "post")] == ["B", "A"]


# Rúbrica Q

CALIFICACIONES = """participante,concepto,momento,calificador,Q
P01,recursion,pre,1,12
P01,recursion,pre,2,"14,5"
P01,recursion,post,1,18
"""


def test_q_es_el_promedio_de_los_calificadores():
    notas = leer_calificaciones(CALIFICACIONES)
    assert resumir_q(notas[("P01", RECURSION, "pre")]) == {
        "Q": 13.25, "Q_cal1": 12.0, "Q_cal2": 14.5, "n_calificadores": 2,
    }
    assert resumir_q(notas[("P01", RECURSION, "post")])["n_calificadores"] == 1
    assert resumir_q(None)["Q"] is None


@pytest.mark.parametrize("fila, mensaje", [
    ("P01,recursion,pre,1,21", "0 a 20"),
    ("P01,recursion,pre,3,10", "1 o 2"),
    ("P01,magia,pre,1,10", "concepto"),
    ("P01,recursion,durante,1,10", "pre o post"),
    ("P01,recursion,pre,1,diez", "no son números"),
    ("P01,recursion,pre,1,10\nP01,recursion,pre,1,11", "repetida"),
])
def test_calificaciones_invalidas(fila, mensaje):
    with pytest.raises(CalificacionesInvalidas, match=mensaje):
        leer_calificaciones("participante,concepto,momento,calificador,Q\n" + fila)


def test_calificaciones_sin_columnas():
    with pytest.raises(CalificacionesInvalidas, match="columnas"):
        leer_calificaciones("codigo,nota\nP01,10\n")


# Flujo

def test_las_etapas_del_flujo_suman():
    registros = [
        Registro("", False, True, True, PRESENTE, PRESENTE),
        Registro("", False, True, True, PRESENTE, AUSENTE),
        Registro("", False, True, True, AUSENTE, SIN_CORREGIR),
        Registro("etiquetado", False, True, False, SIN_CORREGIR, SIN_CORREGIR),
        Registro("", True, False, False, SIN_CORREGIR, SIN_CORREGIR),
        Registro("", False, False, False, SIN_CORREGIR, SIN_CORREGIR),
    ]
    etapas = {(e, d): n for e, n, d in etapas_del_flujo(registros, convocados=10)}
    assert etapas[("convocados", "dato del investigador")] == 10
    assert etapas[("registrados", "con consentimiento")] == 6
    assert etapas[("excluidos", "etiquetado")] == 1
    assert etapas[("retirados", "datos borrados")] == 1
    assert etapas[("sin_diagnostico", "sin análisis válido o sin asignación")] == 1
    assert etapas[("incluidos", "con asignación congelada")] == 3
    assert etapas[("sin_pretest", AUSENTE)] == 1
    assert etapas[("con_pretest", "")] == 2
    assert etapas[("sin_postest", AUSENTE)] == 1
    assert etapas[("con_postest", "")] == 1


# Datos de prueba con base

def participante_con(codigo, reforzados=(RECURSION, ESTRUCTURAS), caso="A", orden="AB",
                     congelar=True):
    participante = Participante.objects.create(
        codigo=codigo, repositorio=f"C:/repos/{codigo}-secreto",
        consentimiento_en=date(2026, 11, 20), consentimiento_version="v1",
    )
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=9, n_ia=6,
        idc_global=6 / 9, commit_head="abc123def456",
    )
    for concepto in CONCEPTOS:
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=2, idc=2 / 3,
            estado="debil", reforzado=concepto in reforzados,
        )
    Fragmento.objects.create(
        analisis=analisis, archivo="tarea.py", nombre="f", codigo="def f():\n    return 'marca_xq9'\n",
        linea_inicio=1, linea_fin=2, lineas=2, complejidad=1, p_ia=0.9,
    )
    if congelar:
        if not Congelacion.objects.exists():
            Congelacion.objects.create(semilla_base=7, modo="confirmatorio", tamano_bloque=4)
        Asignacion.objects.create(
            participante=participante, analisis_base=analisis, semilla=11,
            debiles=list(CONCEPTOS), reforzados=list(reforzados),
            control=[c for c in CONCEPTOS if c not in reforzados],
            caso=caso, orden=orden, modo="confirmatorio",
        )
    return participante


def puntajes(participante, momento, forma, estado="ok", t_pct=75.0):
    for concepto, item in ITEMS.items():
        ausente = estado == "ausente"
        PuntajeItem.objects.create(
            participante=participante, momento=momento, forma=forma, item=item,
            concepto=concepto, banco_version="v1", estado=estado,
            casos_pasados=None if ausente else 3, casos_total=4,
            t_pct=None if ausente else t_pct, cc_sol=None if ausente else 2.0,
            lin_sol=None if ausente else 6, n_funciones=None if ausente else 1,
            cc_ref=2.0, lin_ref=5,
        )


def leer(carpeta, nombre):
    return list(csv.DictReader(io.StringIO((carpeta / nombre).read_text(encoding="utf-8"))))


# Consentimiento y exclusión

@pytest.mark.django_db
def test_sin_consentimiento_no_se_analiza():
    participante = Participante.objects.create(codigo="P01", repositorio="x", hashes_correos=["h"])
    with pytest.raises(SinConsentimiento):
        ejecutar_analisis(participante)


@pytest.mark.django_db
def test_el_formulario_exige_el_consentimiento(client, tmp_path):
    respuesta = client.post(reverse("analisis:lista"), {
        "codigo": "P02", "repositorio": str(tmp_path), "correos": "a@example.invalid",
    })
    assert respuesta.status_code == 200
    assert not Participante.objects.exists()


@pytest.mark.django_db
def test_un_excluido_no_se_analiza_ni_entra_al_sorteo():
    participante = participante_con("P01", congelar=False)
    participante_con("P02", congelar=False)
    excluir(participante, Participante.ETIQUETADO, "investigador")
    with pytest.raises(FueraDeLaMuestra):
        ejecutar_analisis(participante)
    assert estado_congelacion().n_participantes == 1
    registro = Auditoria.objects.get(accion=Auditoria.EXCLUIR)
    assert (registro.objeto, registro.detalle["motivo"]) == ("P01", "etiquetado")


@pytest.mark.django_db
def test_motivo_de_exclusion_cerrado():
    with pytest.raises(CambioNoPermitido):
        excluir(participante_con("P01", congelar=False), "se llama Juan", "investigador")


@pytest.mark.django_db
def test_quitar_la_exclusion_tras_congelar_sin_asignacion_no_se_puede():
    fuera = participante_con("P01", congelar=False)
    excluir(fuera, Participante.PILOTO, "investigador")
    participante_con("P02")  # crea la congelación
    with pytest.raises(CambioNoPermitido, match="fuera del sorteo"):
        incluir(fuera, "investigador")
    dentro = Participante.objects.get(codigo="P02")
    excluir(dentro, Participante.NO_CUMPLE, "investigador")
    incluir(dentro, "investigador")  # conserva su asignación: puede volver
    assert not Participante.objects.get(codigo="P02").excluido


@pytest.mark.django_db
def test_excluir_desde_el_detalle(client):
    participante_con("P01", congelar=False)
    client.post(reverse("analisis:excluir", args=["P01"]), {"motivo": "piloto"})
    assert Participante.objects.get(codigo="P01").motivo_exclusion == "piloto"
    html = client.get(reverse("analisis:detalle", args=["P01"])).content.decode()
    assert "Participó en el piloto" in html and "Analizar repositorio" not in html


# Retiro

@pytest.mark.django_db
def test_el_retiro_borra_todo_y_deja_el_codigo(client):
    participante = participante_con("P01")
    puntajes(participante, "pre", "A")
    client.get(material(client, RECURSION))
    IntentoEjercicio.objects.create(
        analisis=participante.ultimo_analisis, concepto=RECURSION, bloque_id="b",
        bloque_version=1, ejercicio="e", longitud_codigo=1, hash_codigo="h", pasados=0, total=1,
    )
    generar_codigo_acceso(participante, "investigador")

    borrado = retirar(participante, "investigador")

    assert borrado == {"analisis": 1, "intentos": 1, "aperturas": 1, "puntajes": 3}
    participante.refresh_from_db()
    assert participante.retirado_en is not None
    assert (participante.repositorio, participante.hashes_correos, participante.codigo_acceso) == (
        "", [], "",
    )
    for modelo in (Analisis, Asignacion, Fragmento, PuntajeItem, AperturaRefuerzo, IntentoEjercicio):
        assert not modelo.objects.exists(), modelo.__name__
    registro = Auditoria.objects.get(accion=Auditoria.RETIRO)
    assert (registro.detalle["caso"], registro.detalle["orden"]) == ("A", "AB")
    # La sesión que tenía abierta ya no le sirve, ni puede pedir otro código.
    assert client.get(reverse("estudiante:inicio")).status_code == 302
    with pytest.raises(ParticipanteRetirado):
        generar_codigo_acceso(participante, "investigador")
    with pytest.raises(CambioNoPermitido):
        retirar(participante, "investigador")


@pytest.mark.django_db
def test_el_retiro_desde_gestion_pide_escribir_el_codigo(client):
    participante_con("P01")
    client.post(reverse("gestion:retiro", args=["P01"]), {"confirmo": "P02"})
    assert Participante.objects.get(codigo="P01").retirado_en is None
    client.post(reverse("gestion:retiro", args=["P01"]), {"confirmo": "P01"})
    assert Participante.objects.get(codigo="P01").retirado_en is not None
    assert "Retirado el" in client.get(reverse("gestion:panel")).content.decode()


@pytest.mark.django_db
def test_el_portal_no_vuelve_a_cargar_a_quien_se_retiro():
    participante_con("P01")
    texto = json.dumps(construir_resultados())
    retirado = Participante.objects.get(codigo="P01")
    retirar(retirado, "investigador")
    _, nuevos = importar_resultados(texto, "investigador")
    assert nuevos == 0 and not Analisis.objects.exists()


@pytest.mark.django_db
def test_comando_retirar_participante():
    participante_con("P01")
    with pytest.raises(CommandError) as error:
        call_command("retirar_participante", "P01")
    assert error.value.returncode == 22
    call_command("retirar_participante", "P01", "--confirmo", "P01", stdout=io.StringIO())
    assert Participante.objects.get(codigo="P01").retirado_en is not None


# Informe personal (D11, RF-31, RF-34)

@pytest.mark.django_db
def test_el_informe_solo_se_abre_tras_el_postest(cliente_anonimo):
    participante_con("P01")
    material(cliente_anonimo, RECURSION)
    respuesta = cliente_anonimo.get(reverse("estudiante:informe"))
    assert respuesta.status_code == 403
    assert "0,67" not in respuesta.content.decode() and "0.67" not in respuesta.content.decode()

    liberar_control("investigador")
    html = cliente_anonimo.get(reverse("estudiante:informe")).content.decode()
    assert "estimación probabilística, no una prueba" in html
    assert "0.67" in html or "0,67" in html
    assert "estimación muy incierta" in html  # 2 de 3 funciones: intervalo muy ancho
    assert "modelo de demostración" in html
    assert "Ver mi informe" in cliente_anonimo.get(reverse("estudiante:inicio")).content.decode()


# Base para el análisis (D17)

@pytest.fixture
def muestra(db):
    p01 = participante_con("P01", orden="AB")
    puntajes(p01, "pre", "A", t_pct=50.0)
    puntajes(p01, "post", "B", t_pct=100.0)
    p02 = participante_con("P02", orden="BA", caso="B")
    puntajes(p02, "pre", "B")
    puntajes(p02, "post", "A", estado="ausente")
    participante_con("P03", orden="AB")  # sin corregir todavía
    excluido = participante_con("P04", congelar=False)
    excluir(excluido, Participante.ETIQUETADO, "investigador")
    retirar(participante_con("P05"), "investigador")


def test_formato_largo(muestra, tmp_path):
    notas = leer_calificaciones(CALIFICACIONES)
    exportar_estudio(tmp_path, "investigador", notas, convocados=8)
    filas = leer(tmp_path, "largo.csv")
    assert len(filas) == 3 * 3 * 2  # P01, P02 y P03 × 3 conceptos × 2 momentos
    assert {f["participante"] for f in filas} == {"P01", "P02", "P03"}

    p01 = {(f["concepto"], f["momento"]): f for f in filas if f["participante"] == "P01"}
    rec_pre = p01[(RECURSION, "pre")]
    assert (rec_pre["forma"], rec_pre["T_pct"], rec_pre["Q"], rec_pre["Q_cal2"]) == (
        "A", "50.0", "13.25", "14.5",
    )
    assert (rec_pre["reforzado"], p01[(EXCEPCIONES, "pre")]["reforzado"]) == ("1", "0")
    assert p01[(RECURSION, "post")]["forma"] == "B"

    p02_post = next(
        f for f in filas if f["participante"] == "P02" and f["momento"] == "post"
    )
    assert (p02_post["estado"], p02_post["T_pct"], p02_post["forma"]) == ("ausente", "", "A")
    p03 = next(f for f in filas if f["participante"] == "P03" and f["momento"] == "pre")
    assert (p03["estado"], p03["forma"], p03["T_pct"]) == ("sin_corregir", "A", "")


def test_participantes_e_hipotesis(muestra, tmp_path):
    exportar_estudio(tmp_path, "investigador")
    filas = {f["participante"]: f for f in leer(tmp_path, "participantes.csv")}
    assert set(filas) == {"P01", "P02", "P03"}
    assert (filas["P01"]["en_HG"], filas["P01"]["en_HE5"], filas["P01"]["en_HE4_casoA"]) == (
        "1", "1", "1",
    )
    assert (filas["P02"]["en_HG"], filas["P02"]["en_HE2a"], filas["P02"]["en_HE2b"]) == (
        "0", "1", "1",
    )
    assert (filas["P03"]["en_HE1"], filas["P03"]["en_HE2a"]) == ("1", "0")


def test_flujo_de_participantes(muestra, tmp_path):
    exportar_estudio(tmp_path, "investigador", convocados=8)
    etapas = {(f["etapa"], f["detalle"]): f["n"] for f in leer(tmp_path, "flujo.csv")}
    assert etapas[("convocados", "dato del investigador")] == "8"
    assert etapas[("registrados", "con consentimiento")] == "5"
    assert etapas[("excluidos", "etiquetado")] == "1"
    assert etapas[("retirados", "datos borrados")] == "1"
    assert etapas[("incluidos", "con asignación congelada")] == "3"
    assert etapas[("sin_pretest", "sin_corregir")] == "1"
    assert etapas[("sin_postest", "ausente")] == "1"
    assert etapas[("con_postest", "")] == "1"


def test_la_base_no_lleva_codigo_ni_rutas(muestra, tmp_path):
    exportar_estudio(tmp_path, "investigador")
    todo = "".join(p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
    for prohibido in ("secreto", "marca_xq9", "abc123", "C:/repos"):
        assert prohibido not in todo
    registro = Auditoria.objects.get(accion=Auditoria.EXPORTAR_ESTUDIO)
    assert set(registro.detalle["huellas"]) == {
        "largo.csv", "participantes.csv", "flujo.csv", "LEEME.txt",
    }


@pytest.mark.django_db
def test_comando_exportar_estudio(tmp_path):
    with pytest.raises(CommandError) as error:
        call_command("exportar_estudio", "--salida", str(tmp_path))
    assert error.value.returncode == 13  # sin congelación
    participante_con("P01")
    malas = tmp_path / "q.csv"
    malas.write_text("participante,concepto,momento,calificador,Q\nP01,recursion,pre,1,50\n",
                     encoding="utf-8")
    with pytest.raises(CommandError) as error:
        call_command("exportar_estudio", "--salida", str(tmp_path), "--calificaciones", str(malas))
    assert error.value.returncode == 20
    buenas = tmp_path / "q2.csv"
    buenas.write_text("participante,concepto,momento,calificador,Q\nP09,recursion,pre,1,10\n",
                      encoding="utf-8")
    salida = io.StringIO()
    call_command("exportar_estudio", "--salida", str(tmp_path / "base"),
                 "--calificaciones", str(buenas), stdout=salida)
    assert "P09" in salida.getvalue()  # nota de alguien que no está en la base
    assert (tmp_path / "base" / "largo.csv").exists()


@pytest.mark.django_db
def test_exportar_estudio_solo_en_local(settings, tmp_path):
    settings.PERFIL = "nube"
    with pytest.raises(CommandError) as error:
        call_command("exportar_estudio", "--salida", str(tmp_path))
    assert error.value.returncode == 17


# Cierre (D13)

def test_el_cierre_exige_exportar_antes(muestra):
    with pytest.raises(CierreNoPermitido):
        cerrar_estudio("investigador")


def test_el_cierre_borra_el_codigo_y_conserva_los_agregados(muestra, tmp_path):
    exportar_estudio(tmp_path, "investigador")
    borrado = cerrar_estudio("investigador")
    assert borrado["fragmentos"] == 4  # P01–P04; el de P05 se borró al retirarse
    assert not Fragmento.objects.exists()
    assert not Participante.objects.exclude(repositorio="").exists()
    assert not Participante.objects.exclude(hashes_correos=[]).exists()
    assert ResultadoConcepto.objects.exists() and PuntajeItem.objects.exists()
    assert Auditoria.objects.filter(accion=Auditoria.CIERRE).exists()


def test_comando_cerrar_pide_confirmar(muestra, tmp_path):
    exportar_estudio(tmp_path, "investigador")
    with pytest.raises(CommandError) as error:
        call_command("cerrar_estudio")
    assert error.value.returncode == 21
    assert Fragmento.objects.exists()
    call_command("cerrar_estudio", "--confirmo", "borrar-codigo", stdout=io.StringIO())
    assert not Fragmento.objects.exists()


@pytest.mark.parametrize("repositorio, carpeta", [
    ("C:/repos/P01", "C:/repos/P01"),
    ("https://github.com/x/y.git", None),
    ("git@github.com:x/y.git", None),
    ("", None),
])
def test_el_retiro_recuerda_borrar_la_carpeta_entregada(repositorio, carpeta):
    from analisis.participacion import carpeta_a_borrar
    assert carpeta_a_borrar(repositorio) == carpeta


@pytest.mark.django_db
def test_el_comando_de_retiro_nombra_la_carpeta_pero_no_la_audita():
    participante_con("P01")
    salida = io.StringIO()
    call_command("retirar_participante", "P01", "--confirmo", "P01", stdout=salida)
    assert "C:/repos/P01-secreto" in salida.getvalue()
    assert "secreto" not in json.dumps(list(Auditoria.objects.values("detalle")))
