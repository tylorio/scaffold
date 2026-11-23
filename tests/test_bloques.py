"""Pieza 9: bloques por semana, IDC oculto, lista de espera y soluciones sin código."""
import copy
import csv
import hashlib
import io
import json
from datetime import date, timedelta

import pytest
from django.core.management import CommandError, call_command
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
from analisis.servicios.conceptos import CONCEPTOS, ESTRUCTURAS, EXCEPCIONES, RECURSION
from conftest import bloques_listos, material
from refuerzo.administracion import (
    AccionNoPermitida,
    cargar_bloques,
    fijar_inicio,
    liberar_control,
    validar_bloque,
)
from refuerzo.models import AperturaRefuerzo, BloqueRefuerzo, IntentoEjercicio
from refuerzo.servicios import banco
from refuerzo.servicios.adherencia import calcular
from refuerzo.servicios.contenido import PLANTILLAS
from refuerzo.servicios.ejecutor import NO_DISPONIBLE, ResultadoEjecucion

HOY = date(2026, 12, 7)


def ejemplo(concepto=RECURSION):
    return next(b for b in banco.bloques_de_ejemplo() if b["concepto"] == concepto)


def otro_bloque(semana, orden=1, concepto=RECURSION, version=1):
    bloque = copy.deepcopy(ejemplo(concepto))
    bloque.update(id=f"{concepto}-s{semana}-{orden}", semana=semana, orden=orden,
                  version=version, titulo=f"Semana {semana}")
    return bloque


# Banco (sin base de datos)

@pytest.mark.parametrize("hoy, semana", [
    (HOY - timedelta(days=1), 0),
    (HOY, 1),
    (HOY + timedelta(days=6), 1),
    (HOY + timedelta(days=7), 2),
    (HOY + timedelta(days=27), 4),
    (HOY + timedelta(days=60), 9),  # pasada la intervención todo sigue abierto
])
def test_semana_contada_desde_el_inicio(hoy, semana):
    assert banco.semana_de(hoy, HOY) == semana


def test_sin_inicio_no_hay_semana():
    assert banco.semana_de(HOY, None) == 0


def test_los_bloques_de_ejemplo_son_validos_y_conservan_las_plantillas():
    bloques = banco.bloques_de_ejemplo()
    assert {b["concepto"] for b in bloques} == set(CONCEPTOS)
    for contenido in bloques:
        assert banco.validar(contenido) == []
        bloque = banco.desde_json(contenido)
        assert bloque.ejercicios == PLANTILLAS[contenido["concepto"]].ejercicios
        assert bloque.ejemplos == PLANTILLAS[contenido["concepto"]].ejemplos


def test_el_ejemplo_sobrevive_al_json():
    contenido = json.loads(json.dumps(ejemplo(EXCEPCIONES)))
    bloque = banco.desde_json(contenido)
    assert bloque.ejercicio("exc-dificil").casos[2].lanza == "ValueError"


@pytest.mark.parametrize("cambio, mensaje", [
    (lambda b: b.pop("version"), "faltan version"),
    (lambda b: b.update(concepto="magia"), "concepto desconocido"),
    (lambda b: b.update(semana=5), "semana"),
    (lambda b: b.update(orden=3), "orden"),
    (lambda b: b.update(version=0), "versión"),
    (lambda b: b.update(ejemplos=[]), "ejemplo resuelto"),
    (lambda b: b["ejercicios"].append(dict(b["ejercicios"][0])), "id distintos"),
    (lambda b: b["ejercicios"][0].update(casos=[]), "sin casos"),
])
def test_bloques_invalidos(cambio, mensaje):
    bloque = copy.deepcopy(ejemplo())
    cambio(bloque)
    assert any(mensaje in e for e in banco.validar(bloque))


def test_la_huella_cambia_con_el_contenido():
    bloque = copy.deepcopy(ejemplo())
    original = banco.huella(bloque)
    assert banco.huella(copy.deepcopy(bloque)) == original
    bloque["explicacion"][0] += " Más."
    assert banco.huella(bloque) != original


def test_ranuras_faltantes_de_los_ocho_bloques():
    faltan = banco.ranuras_faltantes([(RECURSION, 1, 1), (RECURSION, 1, 2)])
    assert len(faltan[RECURSION]) == 6
    assert (1, 1) not in faltan[RECURSION]
    assert len(faltan[ESTRUCTURAS]) == 8


def test_la_introduccion_no_cita_el_analisis():
    for concepto in CONCEPTOS:
        texto = banco.introduccion(concepto)
        assert "IDC" not in texto and "IA" not in texto
        assert "funciones" not in texto


def test_carpeta_con_json_roto(tmp_path):
    (tmp_path / "a.json").write_text("{", encoding="utf-8")
    with pytest.raises(banco.BloqueInvalido):
        banco.cargar_carpeta(tmp_path)


def test_carpeta_con_ids_repetidos(tmp_path):
    for nombre in ("a.json", "b.json"):
        (tmp_path / nombre).write_text(json.dumps(ejemplo()), encoding="utf-8")
    with pytest.raises(banco.BloqueInvalido, match="mismo id"):
        banco.cargar_carpeta(tmp_path)


# Adherencia (P6)

def test_varios_envios_al_mismo_ejercicio_cuentan_como_uno():
    medida = calcular(
        {"e1", "e2", "e3", "e4"},
        [("e1", True, False), ("e1", True, True), ("e2", True, False)],
    )
    assert (medida.intentados, medida.resueltos) == (2, 1)
    assert medida.principal == 0.5 and medida.secundaria == 0.25


def test_un_envio_no_ejecutado_o_de_algo_no_liberado_no_cuenta():
    medida = calcular({"e1"}, [("e1", False, False), ("e9", True, True)])
    assert (medida.intentados, medida.resueltos) == (0, 0)


def test_sin_liberados_no_hay_adherencia():
    assert calcular(set(), []).principal is None


# Carga y validación


@pytest.mark.django_db
def test_un_bloque_nuevo_queda_sin_validar_y_se_audita():
    resumen = cargar_bloques([ejemplo()], "investigador")
    bloque = BloqueRefuerzo.objects.get()
    assert resumen.nuevos == [bloque.id] and not bloque.validado
    assert Auditoria.objects.get(accion=Auditoria.CARGAR_BLOQUE).detalle["version"] == 1


@pytest.mark.django_db
def test_recargar_lo_mismo_no_cambia_nada():
    cargar_bloques([ejemplo()], "investigador")
    BloqueRefuerzo.objects.update(validado=True)
    resumen = cargar_bloques([ejemplo()], "investigador")
    assert resumen.sin_cambios == ["recursion-ejemplo"]
    assert BloqueRefuerzo.objects.get().validado


@pytest.mark.django_db
def test_cambiar_el_contenido_sin_subir_la_version_se_rechaza():
    cargar_bloques([ejemplo()], "investigador")
    cambiado = copy.deepcopy(ejemplo())
    cambiado["titulo"] = "Otro"
    with pytest.raises(banco.BloqueInvalido, match="versión"):
        cargar_bloques([otro_bloque(2), cambiado], "investigador")
    # Todo o nada: el bloque bueno del mismo lote tampoco entró.
    assert list(BloqueRefuerzo.objects.values_list("id", flat=True)) == ["recursion-ejemplo"]


@pytest.mark.django_db
def test_una_version_nueva_pierde_la_validacion():
    cargar_bloques([otro_bloque(2)], "investigador")
    validar_bloque("recursion-s2-1", 1, 3, "investigador")
    nueva = otro_bloque(2, version=2)
    nueva.update(titulo="Corregido")
    assert cargar_bloques([nueva], "investigador").actualizados == ["recursion-s2-1"]
    bloque = BloqueRefuerzo.objects.get()
    assert (bloque.version, bloque.validado, bloque.n_jueces) == (2, False, None)


@pytest.mark.django_db
def test_dos_bloques_no_comparten_semana_y_orden():
    cargar_bloques([ejemplo()], "investigador")
    with pytest.raises(banco.BloqueInvalido, match="ya es de recursion-ejemplo"):
        cargar_bloques([otro_bloque(1, 1)], "investigador")


@pytest.mark.django_db
def test_validar_exige_la_version_vista_y_los_jueces():
    cargar_bloques([otro_bloque(2)], "investigador")
    with pytest.raises(AccionNoPermitida, match="versión 1"):
        validar_bloque("recursion-s2-1", 2, 3, "investigador")
    with pytest.raises(AccionNoPermitida, match="jueces"):
        validar_bloque("recursion-s2-1", 1, 0, "investigador")
    validar_bloque("recursion-s2-1", 1, 3, "investigador")
    registro = Auditoria.objects.get(accion=Auditoria.VALIDAR_BLOQUE)
    assert registro.detalle["n_jueces"] == 3 and registro.objeto == "recursion-s2-1"


@pytest.mark.django_db
def test_los_bloques_de_ejemplo_no_se_pueden_validar():
    """Se solapan con la prueba real (orientación del asesor, 2026-11-22)."""
    cargar_bloques([ejemplo()], "investigador")
    with pytest.raises(AccionNoPermitida, match="bloque de ejemplo"):
        validar_bloque("recursion-ejemplo", 1, 3, "investigador")
    assert not BloqueRefuerzo.objects.get().validado


@pytest.mark.django_db
def test_los_bloques_de_ejemplo_no_se_cargan_en_el_portal(settings):
    settings.PERFIL = "nube"
    with pytest.raises(CommandError) as error:
        call_command("cargar_bloques", "--ejemplo")
    assert error.value.returncode == 17
    assert not BloqueRefuerzo.objects.exists()


@pytest.mark.django_db
def test_comando_cargar_bloques(tmp_path):
    salida = io.StringIO()
    call_command("cargar_bloques", "--ejemplo", stdout=salida)
    assert "Nuevos: 3" in salida.getvalue()
    with pytest.raises(CommandError) as error:
        call_command("cargar_bloques", "--carpeta", str(tmp_path))
    assert error.value.returncode == 19
    (tmp_path / "x.json").write_text(json.dumps({"id": "x"}), encoding="utf-8")
    with pytest.raises(CommandError) as error:
        call_command("cargar_bloques", "--carpeta", str(tmp_path))
    assert error.value.returncode == 19


# Lo que ve el estudiante

def diagnostico(codigo="P01", reforzados=(RECURSION,)):
    participante = Participante.objects.create(codigo=codigo, repositorio="")
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=9, n_ia=6,
        idc_global=0.6667,
    )
    for concepto in CONCEPTOS:
        ResultadoConcepto.objects.create(
            analisis=analisis, concepto=concepto, n_fragmentos=3, n_ia=2, idc=0.6667,
            estado="debil", reforzado=concepto in reforzados,
        )
    Asignacion.objects.create(
        participante=participante, analisis_base=analisis, semilla=1, debiles=list(CONCEPTOS),
        reforzados=list(reforzados), control=[c for c in CONCEPTOS if c not in reforzados],
        caso="A", orden="AB", modo="confirmatorio",
    )
    return participante


@pytest.fixture
def ejecucion_falsa(monkeypatch):
    """Evita levantar un proceso por envío; el resultado lo fija cada prueba."""
    resultado = {"valor": ResultadoEjecucion(4, 4, [{"entrada": "(0,)", "paso": True}])}
    monkeypatch.setattr(
        "refuerzo.views.ejecutar_solucion", lambda *a, **k: resultado["valor"],
    )
    return resultado


def fijar_inicio_hace(dias):
    configuracion = Configuracion.obtener()
    configuracion.inicio_intervencion = timezone.localdate() - timedelta(days=dias)
    configuracion.save()


@pytest.mark.django_db
def test_el_portal_no_muestra_el_idc(cliente_anonimo):
    diagnostico()
    url = material(cliente_anonimo, RECURSION)
    paginas = (reverse("estudiante:inicio"), reverse("estudiante:concepto", args=[RECURSION]), url)
    for pagina in paginas:
        html = cliente_anonimo.get(pagina).content.decode()
        assert "IDC" not in html
        assert "0,67" not in html and "0.67" not in html


@pytest.mark.django_db
def test_un_bloque_sin_validar_no_existe_para_el_estudiante(client):
    diagnostico()
    url = material(client, RECURSION)
    BloqueRefuerzo.objects.update(validado=False)
    assert client.get(url).status_code == 404
    assert not AperturaRefuerzo.objects.exists()
    lista = client.get(reverse("estudiante:concepto", args=[RECURSION])).content.decode()
    assert "recursion-ejemplo" not in lista


@pytest.mark.django_db
def test_los_bloques_se_liberan_por_semana(client):
    diagnostico()
    url = material(client, RECURSION)
    cargar_bloques([otro_bloque(2)], "investigador")
    BloqueRefuerzo.objects.update(validado=True)
    semana_2 = reverse("estudiante:bloque", args=[RECURSION, "recursion-s2-1"])

    respuesta = client.get(semana_2)
    assert respuesta.status_code == 403
    apertura = AperturaRefuerzo.objects.get()
    assert (apertura.permitida, apertura.motivo, apertura.bloque_id) == (
        False, AperturaRefuerzo.SEMANA_FUTURA, "recursion-s2-1",
    )
    lista = client.get(reverse("estudiante:concepto", args=[RECURSION])).content.decode()
    assert "Semana 2" not in lista and "próximos bloques" in lista

    fijar_inicio_hace(7)
    assert client.get(semana_2).status_code == 200
    assert client.get(url).status_code == 200  # la semana 1 sigue abierta


@pytest.mark.django_db
def test_antes_del_inicio_no_hay_bloques(client):
    diagnostico()
    url = material(client, RECURSION)
    fijar_inicio_hace(-3)
    assert client.get(url).status_code == 403
    assert "empieza el" in client.get(reverse("estudiante:inicio")).content.decode()


@pytest.mark.django_db
def test_la_apertura_registra_bloque_y_version(client):
    diagnostico()
    client.get(material(client, RECURSION))
    apertura = AperturaRefuerzo.objects.get()
    assert (apertura.bloque_id, apertura.bloque_version, apertura.permitida) == (
        "recursion-ejemplo", 1, True,
    )


@pytest.mark.django_db
def test_la_solucion_no_se_guarda(client, ejecucion_falsa):
    diagnostico()
    url = material(client, RECURSION)
    codigo = "def suma_digitos(n):\n    # firma_unica_del_estudiante\n    return 0\n"
    respuesta = client.post(url, {"ejercicio": "rec-facil", "codigo": codigo})
    assert "firma_unica_del_estudiante" in respuesta.content.decode()  # solo en esta respuesta

    intento = IntentoEjercicio.objects.get()
    assert intento.longitud_codigo == len(codigo)
    assert intento.hash_codigo == hashlib.sha256(codigo.encode()).hexdigest()
    assert (intento.bloque_id, intento.bloque_version) == ("recursion-ejemplo", 1)
    guardado = json.dumps(list(IntentoEjercicio.objects.values()), default=str)
    assert "firma_unica_del_estudiante" not in guardado
    assert not hasattr(intento, "codigo")

    # Al volver a abrir el bloque aparece la plantilla, no la solución.
    html = client.get(url).content.decode()
    assert "firma_unica_del_estudiante" not in html
    assert "4 de 4 pruebas pasadas" in html


@pytest.mark.django_db
def test_con_el_ejecutor_caido_el_envio_no_cuenta_como_intentado(client, ejecucion_falsa):
    diagnostico()
    ejecucion_falsa["valor"] = ResultadoEjecucion(0, 4, error=NO_DISPONIBLE)
    client.post(material(client, RECURSION), {"ejercicio": "rec-facil", "codigo": "x"})
    assert IntentoEjercicio.objects.get().ejecutado is False


# Lista de espera (D4)

@pytest.mark.django_db
def test_liberar_el_control_abre_todos_los_conceptos(client):
    diagnostico()
    url_control = material(client, EXCEPCIONES)
    assert client.get(url_control).status_code == 403
    liberar_control("investigador")
    assert client.get(url_control).status_code == 200
    html = client.get(reverse("estudiante:inicio")).content.decode()
    assert "Disponible después de la prueba final" not in html
    assert Auditoria.objects.filter(accion=Auditoria.LIBERAR_CONTROL).count() == 1


@pytest.mark.django_db
def test_liberar_exige_inicio_y_no_se_repite():
    with pytest.raises(AccionNoPermitida, match="inicio"):
        liberar_control("investigador")
    fijar_inicio(HOY, "investigador")
    liberar_control("investigador")
    with pytest.raises(AccionNoPermitida, match="ya está liberado"):
        liberar_control("investigador")
    with pytest.raises(AccionNoPermitida, match="terminó"):
        fijar_inicio(HOY, "investigador")


@pytest.mark.django_db
def test_gestion_libera_solo_con_confirmacion(client):
    fijar_inicio(HOY, "investigador")
    client.post(reverse("gestion:liberar"))
    assert Configuracion.obtener().control_liberado_en is None
    client.post(reverse("gestion:liberar"), {"confirmo": "si"})
    assert Configuracion.obtener().control_liberado_en is not None


@pytest.mark.django_db
def test_gestion_fija_el_inicio_y_valida_bloques(client):
    client.post(reverse("gestion:inicio_intervencion"), {"fecha": "2026-12-07"})
    assert Configuracion.obtener().inicio_intervencion == HOY
    cargar_bloques([otro_bloque(2)], "investigador")
    html = client.get(reverse("gestion:panel")).content.decode()
    assert "Registrar validación" in html and "faltan 7 de 8" in html
    client.post(
        reverse("gestion:validar_bloque", args=["recursion-s2-1"]),
        {"version": "1", "n_jueces": "3"},
    )
    bloque = BloqueRefuerzo.objects.get()
    assert (bloque.validado, bloque.n_jueces, bloque.validado_por) == (True, 3, "investigador")


# Exportaciones

def filas(client, nombre):
    respuesta = client.get(reverse(nombre))
    return list(csv.DictReader(io.StringIO(respuesta.content.decode())))


@pytest.mark.django_db
def test_adherencia_intentados_sobre_liberados(client, ejecucion_falsa):
    diagnostico()
    url = material(client, RECURSION)
    ejecucion_falsa["valor"] = ResultadoEjecucion(1, 4)
    client.post(url, {"ejercicio": "rec-facil", "codigo": "a"})
    ejecucion_falsa["valor"] = ResultadoEjecucion(4, 4)
    client.post(url, {"ejercicio": "rec-facil", "codigo": "b"})
    ejecucion_falsa["valor"] = ResultadoEjecucion(0, 6)
    client.post(url, {"ejercicio": "rec-medio", "codigo": "c"})

    [fila] = filas(client, "refuerzo:exportar_adherencia")  # solo el concepto reforzado
    assert (fila["concepto"], fila["condicion"]) == (RECURSION, "reforzado")
    assert (fila["liberados"], fila["intentados"], fila["resueltos"]) == ("3", "2", "1")
    assert (fila["adherencia"], fila["adherencia_resueltos"]) == ("0.6667", "0.3333")


@pytest.mark.django_db
def test_la_practica_tras_el_postest_no_cuenta(client, ejecucion_falsa):
    diagnostico()
    url = material(client, RECURSION)
    liberar_control("investigador")
    client.post(url, {"ejercicio": "rec-facil", "codigo": "a"})
    [fila] = filas(client, "refuerzo:exportar_adherencia")
    assert fila["intentados"] == "0"
    [intento] = filas(client, "refuerzo:exportar_intentos")
    assert intento["tras_postest"] == "1"


@pytest.mark.django_db
def test_csv_de_intentos_sin_codigo_ni_hash(client, ejecucion_falsa):
    diagnostico()
    url = material(client, RECURSION)
    for codigo in ("secreto_del_codigo = 1", "secreto_del_codigo = 1", "otro = 2"):
        client.post(url, {"ejercicio": "rec-facil", "codigo": codigo})
    contenido = client.get(reverse("refuerzo:exportar_intentos")).content.decode()
    assert "secreto_del_codigo" not in contenido
    assert hashlib.sha256(b"otro = 2").hexdigest() not in contenido
    registros = list(csv.DictReader(io.StringIO(contenido)))
    assert [r["igual_al_anterior"] for r in registros] == ["0", "1", "0"]
    assert {(r["bloque"], r["version"]) for r in registros} == {("recursion-ejemplo", "1")}


@pytest.mark.django_db
def test_csv_de_aperturas_con_las_bloqueadas(client):
    diagnostico()
    client.get(material(client, RECURSION))
    client.get(material(client, EXCEPCIONES))
    registros = filas(client, "refuerzo:exportar_aperturas")
    assert [(r["concepto"], r["permitida"], r["motivo"]) for r in registros] == [
        (RECURSION, "1", ""), (EXCEPCIONES, "0", "concepto"),
    ]


@pytest.mark.django_db
def test_la_adherencia_exige_sesion_de_investigador(cliente_anonimo):
    respuesta = cliente_anonimo.get(reverse("refuerzo:exportar_adherencia"))
    assert respuesta.status_code == 302


@pytest.mark.django_db
def test_bloques_listos_no_duplica():
    bloques_listos()
    bloques_listos()
    assert BloqueRefuerzo.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_la_migracion_borra_el_codigo_y_conserva_longitud_y_hash():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    antes = [("refuerzo", "0003_intentos_de_acceso"), ("analisis", "0010_codigo_acceso")]
    despues = [("refuerzo", "0004_bloques_y_codigo_sin_guardar")]
    executor = MigrationExecutor(connection)
    executor.migrate(antes)
    viejas = executor.loader.project_state(antes).apps
    participante = viejas.get_model("analisis", "Participante").objects.create(
        codigo="P01", repositorio="",
    )
    analisis = viejas.get_model("analisis", "Analisis").objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=1, n_ia=1,
    )
    viejas.get_model("refuerzo", "IntentoEjercicio").objects.create(
        analisis=analisis, concepto=RECURSION, ejercicio="rec-facil", codigo="x = 1",
        pasados=0, total=4,
    )

    executor = MigrationExecutor(connection)
    executor.migrate(despues)
    nuevas = executor.loader.project_state(despues).apps
    intento = nuevas.get_model("refuerzo", "IntentoEjercicio").objects.get()
    assert (intento.longitud_codigo, intento.bloque_id) == (5, "recursion-ejemplo")
    assert intento.hash_codigo == hashlib.sha256(b"x = 1").hexdigest()
    assert not hasattr(intento, "codigo")
    MigrationExecutor(connection).migrate(
        MigrationExecutor(connection).loader.graph.leaf_nodes()
    )
