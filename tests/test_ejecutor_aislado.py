"""SP-04: el código malicioso no escapa del ejecutor aislado (08 §2.4, ADR-005).

Necesita el motor de Docker. No corre con `pytest` a secas: se lanza con
`python -m pytest -m docker`. Construye la imagen la primera vez.
"""
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.docker

RAIZ = Path(__file__).resolve().parent.parent
IMAGEN = "idc-ejecutor-prueba"
TOKEN = "token-de-prueba-que-no-debe-filtrarse"

# Las mismas opciones que se usan en el despliegue (08 §2.1-§2.2).
OPCIONES = [
    "--read-only", "--tmpfs", "/tmp:rw,size=16m,mode=1777",
    "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
    "--memory", "512m", "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "128",
    "-e", f"IDC_EJECUTOR_TOKEN={TOKEN}",
]


def docker(*argumentos, **opciones):
    return subprocess.run(["docker", *argumentos], capture_output=True, text=True, **opciones)


@pytest.fixture(scope="session", autouse=True)
def imagen():
    if docker("info").returncode != 0:
        pytest.skip("El motor de Docker no está corriendo.")
    construccion = docker("build", "-q", "-f", "ejecutor/Dockerfile", "-t", IMAGEN, ".", cwd=RAIZ)
    assert construccion.returncode == 0, construccion.stderr
    return IMAGEN


def ejecutar(codigo, esperado="ok", tiempo=3, extra=()):
    """Corre una petición en un contenedor nuevo, sin red, como proceso 1."""
    peticion = {
        "codigo": codigo, "funcion": "f", "tiempo_limite_s": tiempo,
        "casos": [{"args": [], "esperado": esperado, "lanza": None}],
    }
    proceso = docker(
        "run", "--rm", "-i", "--network", "none", *OPCIONES, *extra, IMAGEN,
        "python", "-I", "/app/servidor.py", "--una-vez",
        input=json.dumps(peticion), timeout=60,
    )
    assert proceso.returncode == 0, proceso.stderr
    respuesta = json.loads(proceso.stdout)
    assert respuesta["estado"] == 200  # el servidor siempre sobrevive y responde
    return respuesta


def obtenido(respuesta):
    return respuesta["casos"][0]["obtenido"] if respuesta["casos"] else respuesta["error"]


def test_una_solucion_normal_funciona():
    respuesta = ejecutar("def f():\n    return 'ok'\n")
    assert respuesta["pasados"] == 1
    assert respuesta["procesos_restantes"] == 0


def test_1_sin_conexion_de_red():
    codigo = (
        "def f():\n    import socket\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=2)\n    return 'conecto'\n"
    )
    respuesta = ejecutar(codigo)
    assert respuesta["pasados"] == 0
    assert "conecto" not in obtenido(respuesta)


def test_2_sin_resolucion_de_nombres():
    codigo = "def f():\n    import socket\n    return socket.gethostbyname('example.com')\n"
    assert ejecutar(codigo)["pasados"] == 0


@pytest.mark.parametrize("ruta", ["/app/intruso.py", "/etc/intruso", "/usr/local/intruso"])
def test_3_no_escribe_fuera_de_tmp(ruta):
    codigo = f"def f():\n    open({ruta!r}, 'w').write('x')\n    return 'escribio'\n"
    respuesta = ejecutar(codigo)
    assert respuesta["pasados"] == 0
    assert "escribio" not in obtenido(respuesta)


def test_4_no_ve_las_variables_de_entorno_ni_el_token():
    codigo = "def f():\n    import os\n    return repr(dict(os.environ))\n"
    respuesta = ejecutar(codigo)
    assert TOKEN not in json.dumps(respuesta)
    assert "IDC_EJECUTOR_TOKEN" not in json.dumps(respuesta)


def test_4b_no_lee_el_entorno_del_servidor_por_proc():
    codigo = "def f():\n    return open('/proc/1/environ').read()\n"
    assert TOKEN not in json.dumps(ejecutar(codigo))


def test_5_bomba_de_procesos():
    codigo = (
        "def f():\n    import os\n    while True:\n"
        "        try:\n            os.fork()\n        except OSError:\n            pass\n"
    )
    respuesta = ejecutar(codigo, tiempo=3)
    assert respuesta["pasados"] == 0
    assert respuesta["procesos_restantes"] == 0


def test_6_bomba_de_memoria():
    codigo = "def f():\n    x = bytearray(2 * 1024 ** 3)\n    return 'reservo'\n"
    respuesta = ejecutar(codigo)
    assert respuesta["pasados"] == 0
    assert "reservo" not in obtenido(respuesta)


def test_7_bucle_infinito():
    respuesta = ejecutar("def f():\n    while True:\n        pass\n", tiempo=2)
    assert "límite" in respuesta["error"]
    assert respuesta["procesos_restantes"] == 0


def test_8_no_quedan_procesos_huerfanos():
    codigo = (
        "def f():\n    import os, time\n"
        "    if os.fork() == 0:\n        os.setsid()\n"
        "        if os.fork() == 0:\n            time.sleep(60)\n        os._exit(0)\n"
        "    return 'ok'\n"
    )
    respuesta = ejecutar(codigo)
    assert respuesta["procesos_restantes"] == 0


def test_9_no_escribe_archivos_grandes():
    codigo = (
        "def f():\n    with open('grande.bin', 'wb') as a:\n"
        "        a.write(b'0' * 100_000_000)\n    return 'escribio'\n"
    )
    respuesta = ejecutar(codigo)
    assert respuesta["pasados"] == 0
    assert "escribio" not in obtenido(respuesta)


def test_10_no_puede_matar_al_servidor():
    codigo = (
        "def f():\n    import os, signal\n"
        "    for s in (signal.SIGKILL, signal.SIGTERM, signal.SIGINT):\n"
        "        try:\n            os.kill(os.getppid(), s)\n            os.kill(1, s)\n"
        "        except OSError:\n            pass\n    return 'ok'\n"
    )
    ejecutar(codigo)  # la función ejecutar() ya exige que el servidor responda


def test_11_salida_enorme():
    codigo = "def f():\n    import os\n    os.write(1, b'x' * 10_000_000)\n    return 'ok'\n"
    respuesta = ejecutar(codigo)
    assert respuesta["pasados"] == 0


def test_el_servidor_se_niega_a_correr_sin_ser_proceso_1():
    proceso = docker(
        "run", "--rm", "--init", "--network", "none", *OPCIONES, IMAGEN, timeout=60,
    )
    assert proceso.returncode != 0
    assert "proceso 1" in proceso.stderr


def test_12_http_exige_token():
    nombre = f"idc-ejecutor-http-{int(time.time())}"
    arranque = docker(
        "run", "-d", "--rm", "--name", nombre, "-p", "127.0.0.1::8080", *OPCIONES, IMAGEN,
    )
    assert arranque.returncode == 0, arranque.stderr
    try:
        puerto = docker("port", nombre, "8080").stdout.strip().rsplit(":", 1)[-1]
        url = f"http://127.0.0.1:{puerto}"
        for _ in range(50):
            try:
                urllib.request.urlopen(url + "/salud", timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        cuerpo = json.dumps({
            "codigo": "def f():\n    return 'ok'\n", "funcion": "f",
            "casos": [{"args": [], "esperado": "ok", "lanza": None}],
        }).encode()

        def enviar(token):
            peticion = urllib.request.Request(
                url + "/ejecutar", data=cuerpo, method="POST",
                headers={"Content-Type": "application/json", **({"X-Token": token} if token else {})},
            )
            try:
                with urllib.request.urlopen(peticion, timeout=20) as respuesta:
                    return respuesta.status, json.loads(respuesta.read())
            except urllib.error.HTTPError as error:
                return error.code, None

        assert enviar(None)[0] == 401
        assert enviar("otro")[0] == 401
        estado, respuesta = enviar(TOKEN)
        assert (estado, respuesta["pasados"]) == (200, 1)
    finally:
        docker("rm", "-f", nombre)
