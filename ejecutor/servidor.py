"""Servidor del ejecutor aislado (ADR-005). Solo biblioteca estándar; corre en Linux.

Recibe una solución y sus casos por HTTP interno, la ejecuta en un proceso hijo con
límites del sistema y devuelve el resultado. Cuatro reglas lo protegen del código
que ejecuta:

- Corre como proceso 1 del contenedor. Linux no entrega a ese proceso las señales
  que le envían otros procesos del mismo espacio, salvo las que tenga manejadas, y
  este servidor no maneja ninguna. El código del estudiante no puede matarlo.
- Atiende un envío a la vez y, al terminar cada uno, mata y recoge cualquier
  proceso que haya quedado. Así no sobreviven procesos huérfanos ni zombis.
- Cada envío corre en una sesión propia, en una carpeta temporal propia, con
  entorno vacío y límites de CPU, memoria, procesos, archivos y tiempo.
- Exige un token compartido con el portal (IDC_EJECUTOR_TOKEN).

Modos: `python -I servidor.py` atiende HTTP en el puerto 8080;
`python -I servidor.py --una-vez` lee una petición por stdin y responde por stdout
(lo usan las pruebas de aislamiento, SP-04).
"""
import hmac
import json
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CORREDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corredor.py")
MAXIMO_CODIGO = 20_000
MAXIMO_RESPUESTA = 64 * 1024
TIEMPO_POR_DEFECTO = 5.0
TIEMPO_MAXIMO = 10.0
ESPERA_TURNO = 15.0  # segundos que una petición espera su turno antes de un 503

LIMITES = {  # 08 §2.2
    "RLIMIT_CPU": 5,
    "RLIMIT_AS": 256 * 1024 * 1024,
    "RLIMIT_NPROC": 64,
    "RLIMIT_FSIZE": 1024 * 1024,
    "RLIMIT_NOFILE": 32,
}

_turno = threading.Lock()


class PeticionInvalida(Exception):
    pass


def validar_peticion(dato: object) -> dict:
    if not isinstance(dato, dict):
        raise PeticionInvalida("La petición debe ser un objeto JSON.")
    codigo, funcion, casos = dato.get("codigo"), dato.get("funcion"), dato.get("casos")
    if not isinstance(codigo, str) or not isinstance(funcion, str) or not isinstance(casos, list):
        raise PeticionInvalida("Faltan codigo, funcion o casos.")
    if len(codigo.encode("utf-8")) > MAXIMO_CODIGO:
        raise PeticionInvalida("El código supera los 20 KB.")
    tiempo = dato.get("tiempo_limite_s", TIEMPO_POR_DEFECTO)
    if not isinstance(tiempo, (int, float)) or not 0 < tiempo <= TIEMPO_MAXIMO:
        raise PeticionInvalida("tiempo_limite_s debe estar entre 0 y 10.")
    return {"codigo": codigo, "funcion": funcion, "casos": casos, "tiempo": float(tiempo)}


def token_valido(recibido: str | None, esperado: str | None) -> bool:
    return bool(esperado) and recibido is not None and hmac.compare_digest(recibido, esperado)


def proteger_memoria() -> None:
    """El hijo corre con el mismo usuario: sin esto podría leer /proc/1/environ (el token).

    Un proceso no volcable deja su entorno y su memoria en /proc solo para root.
    """
    import ctypes

    PR_SET_DUMPABLE = 4
    if ctypes.CDLL(None, use_errno=True).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0:
        sys.exit("No se pudo proteger la memoria del ejecutor.")


def es_proceso_1() -> bool:
    """La limpieza mata todo proceso ajeno: solo es segura dentro de su contenedor."""
    return os.getpid() == 1


def _otros_procesos() -> list[int]:
    yo = os.getpid()
    return [int(p) for p in os.listdir("/proc") if p.isdigit() and int(p) not in (1, yo)]


def _limpiar_procesos() -> int:
    """Mata y recoge todo proceso que no sea el servidor. Devuelve cuántos quedan."""
    if not es_proceso_1():
        raise RuntimeError("El ejecutor solo limpia procesos siendo el proceso 1 de su contenedor.")
    for _ in range(50):
        restantes = _otros_procesos()
        for pid in restantes:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
        if not restantes:
            return 0
        time.sleep(0.02)
    return len(_otros_procesos())


def ejecutar(peticion: dict) -> dict:
    """Ejecuta una petición ya validada. Se llama con el turno tomado."""
    import subprocess

    inicio = time.monotonic()
    total = len(peticion["casos"])
    carga = json.dumps({k: peticion[k] for k in ("codigo", "funcion", "casos")})
    carpeta = tempfile.mkdtemp(prefix="envio_", dir="/tmp")
    try:
        salida_ruta = os.path.join(carpeta, "salida.json")
        with open(salida_ruta, "wb") as salida:
            # Sin preexec_fn, que puede trabarse con hilos: el corredor aplica sus
            # propios límites antes de leer el código del estudiante.
            proceso = subprocess.Popen(
                [sys.executable, "-I", CORREDOR, "--limites", json.dumps(LIMITES)],
                stdin=subprocess.PIPE, stdout=salida, stderr=subprocess.DEVNULL,
                cwd=carpeta, env={}, start_new_session=True, close_fds=True,
            )
            try:
                proceso.communicate(carga.encode("utf-8"), timeout=peticion["tiempo"])
                vencido = False
            except subprocess.TimeoutExpired:
                vencido = True
        restantes = _limpiar_procesos()
        with open(salida_ruta, "rb") as salida:
            texto = salida.read(MAXIMO_RESPUESTA + 1)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)

    respuesta = {"casos": [], "pasados": 0, "total": total, "error": None}
    if vencido:
        respuesta["error"] = (
            f"Se superó el límite de {peticion['tiempo']:g} s. "
            "Revisa si hay un bucle o una recursión que no termina."
        )
    elif len(texto) > MAXIMO_RESPUESTA:
        respuesta["error"] = "El programa produjo una salida demasiado grande."
    else:
        try:
            dato = json.loads(texto.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            dato = None
        if not isinstance(dato, dict):
            respuesta["error"] = "El programa terminó sin entregar un resultado."
        elif "error" in dato:
            respuesta["error"] = str(dato["error"])[:300]
        else:
            casos = [c for c in dato.get("casos", []) if isinstance(c, dict)][:total]
            respuesta["casos"] = casos
            respuesta["pasados"] = sum(1 for c in casos if c.get("paso") is True)
    respuesta["duracion_ms"] = int((time.monotonic() - inicio) * 1000)
    respuesta["procesos_restantes"] = restantes
    return respuesta


def atender(dato: object) -> tuple[int, dict]:
    try:
        peticion = validar_peticion(dato)
    except PeticionInvalida as error:
        return 400, {"error": str(error)}
    if not _turno.acquire(timeout=ESPERA_TURNO):
        return 503, {"error": "El ejecutor está ocupado; intenta de nuevo."}
    try:
        return 200, ejecutar(peticion)
    finally:
        _turno.release()


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, estado: int, cuerpo: dict) -> None:
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path == "/salud":
            self._responder(200, {"ok": True})
        else:
            self._responder(404, {"error": "No existe."})

    def do_POST(self):
        if self.path != "/ejecutar":
            return self._responder(404, {"error": "No existe."})
        if not token_valido(self.headers.get("X-Token"), os.environ.get("IDC_EJECUTOR_TOKEN")):
            return self._responder(401, {"error": "Token inválido."})
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > MAXIMO_CODIGO * 4:
            return self._responder(413, {"error": "Petición demasiado grande."})
        try:
            dato = json.loads(self.rfile.read(largo) or b"null")
        except ValueError:
            return self._responder(400, {"error": "JSON inválido."})
        self._responder(*atender(dato))

    def log_message(self, formato, *args):
        pass  # no registrar rutas ni cuerpos: pueden traer código de estudiantes


def main() -> None:
    if not es_proceso_1():
        sys.exit("El ejecutor debe correr como proceso 1 de su contenedor (ver ejecutor/Dockerfile).")
    proteger_memoria()
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # sin manejadores: nadie de dentro puede detenerlo
    if "--una-vez" in sys.argv:
        estado, cuerpo = atender(json.loads(sys.stdin.read() or "null"))
        sys.stdout.write(json.dumps({"estado": estado, **cuerpo}))
        return
    if not os.environ.get("IDC_EJECUTOR_TOKEN"):
        sys.exit("Falta IDC_EJECUTOR_TOKEN.")
    ThreadingHTTPServer(("0.0.0.0", 8080), Manejador).serve_forever()


if __name__ == "__main__":
    main()
