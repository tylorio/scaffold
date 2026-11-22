"""Ejecutor aislado sin Docker: validación, token y cliente del portal (ADR-005)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ejecutor import servidor
from refuerzo.servicios.contenido import PLANTILLAS
from refuerzo.servicios.ejecutor import NO_DISPONIBLE, EjecutorRemoto, ejecutar_solucion

EJERCICIO = PLANTILLAS["recursion"].ejercicios[0]


# Servidor: lo que se puede probar fuera del contenedor

@pytest.mark.parametrize("peticion, mensaje", [
    ([], "objeto JSON"),
    ({"codigo": "x", "casos": []}, "Faltan"),
    ({"codigo": "x" * 20_001, "funcion": "f", "casos": []}, "20 KB"),
    ({"codigo": "x", "funcion": "f", "casos": [], "tiempo_limite_s": 11}, "entre 0 y 10"),
    ({"codigo": "x", "funcion": "f", "casos": [], "tiempo_limite_s": "5"}, "entre 0 y 10"),
])
def test_rechaza_peticiones_invalidas(peticion, mensaje):
    estado, cuerpo = servidor.atender(peticion)
    assert estado == 400
    assert mensaje in cuerpo["error"]


def test_token():
    assert servidor.token_valido("abc", "abc")
    assert not servidor.token_valido("abd", "abc")
    assert not servidor.token_valido(None, "abc")
    assert not servidor.token_valido("", "")  # sin token configurado, nadie entra


def test_fuera_de_su_contenedor_no_arranca_ni_limpia():
    """La limpieza mata todo proceso ajeno: fuera del contenedor sería un desastre."""
    assert not servidor.es_proceso_1()
    with pytest.raises(SystemExit, match="proceso 1"):
        servidor.main()
    with pytest.raises(RuntimeError):
        servidor._limpiar_procesos()


# Cliente del portal frente a un ejecutor simulado

class FalsoEjecutor(BaseHTTPRequestHandler):
    recibido: dict = {}

    def do_POST(self):
        FalsoEjecutor.recibido = {
            "token": self.headers.get("X-Token"),
            "cuerpo": json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
        }
        cuerpo = json.dumps({
            "casos": [{"entrada": "5", "esperado": "5", "obtenido": "5", "paso": True}],
            "pasados": 1, "total": 4, "error": None,
        }).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def falso_ejecutor():
    servidor_http = ThreadingHTTPServer(("127.0.0.1", 0), FalsoEjecutor)
    hilo = threading.Thread(target=servidor_http.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor_http.server_address[1]}"
    servidor_http.shutdown()


def test_el_portal_envia_la_solucion_con_token_al_ejecutor(falso_ejecutor):
    remoto = EjecutorRemoto(falso_ejecutor, "secreto")
    resultado = ejecutar_solucion("def suma_digitos(n): return n", EJERCICIO, 3, remoto)
    assert (resultado.pasados, resultado.total, resultado.error) == (1, 4, "")
    assert FalsoEjecutor.recibido["token"] == "secreto"
    cuerpo = FalsoEjecutor.recibido["cuerpo"]
    assert (cuerpo["funcion"], cuerpo["tiempo_limite_s"]) == ("suma_digitos", 3)
    assert len(cuerpo["casos"]) == len(EJERCICIO.casos)


def test_ejecutor_caido_da_un_mensaje_claro():
    remoto = EjecutorRemoto("http://127.0.0.1:9", "secreto")  # puerto sin servicio
    resultado = ejecutar_solucion("def f(): pass", EJERCICIO, 1, remoto)
    assert (resultado.pasados, resultado.error) == (0, NO_DISPONIBLE)


def test_el_token_no_aparece_al_mostrar_la_conexion():
    assert "secreto" not in repr(EjecutorRemoto("http://x", "secreto"))


@pytest.mark.django_db
def test_la_vista_usa_el_ejecutor_configurado(client, settings, falso_ejecutor):
    from analisis.models import Analisis, Participante, ResultadoConcepto
    from refuerzo.models import IntentoEjercicio

    settings.EJECUTOR_URL, settings.EJECUTOR_TOKEN = falso_ejecutor, "secreto"
    participante = Participante.objects.create(codigo="P01", repositorio="x")
    analisis = Analisis.objects.create(
        participante=participante, theta=0.5, lambda_valor=0.5, m=3,
        modelo_version="prueba", modelo_es_demo=True, n_fragmentos=3, n_ia=3,
    )
    ResultadoConcepto.objects.create(
        analisis=analisis, concepto="recursion", n_fragmentos=3, n_ia=3, idc=1.0,
        estado="debil", reforzado=True,
    )
    client.post("/refuerzo/P01/recursion/", {"ejercicio": EJERCICIO.id, "codigo": "x = 1"})
    assert IntentoEjercicio.objects.get().pasados == 1
    assert FalsoEjecutor.recibido["token"] == "secreto"
