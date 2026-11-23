"""Revisión del almacén local cifrado (08 §3.4, docs/almacen-cifrado.md)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

OK, FALTA, AVISO = "OK", "FALTA", "AVISO"


@dataclass(frozen=True)
class Revision:
    estado: str
    mensaje: str


def _dentro(ruta: Path, carpeta: Path) -> bool:
    try:
        Path(ruta).resolve().relative_to(Path(carpeta).resolve())
        return True
    except ValueError:
        return False


def _define(env: Path, clave: str) -> bool:
    if not env.is_file():
        return False
    return any(
        linea.strip().partition("=")[0].strip() == clave
        for linea in env.read_text(encoding="utf-8").splitlines()
    )


def estado_bitlocker(almacen: Path) -> str | None:
    """'On' u 'Off' según BitLocker; None si no se pudo consultar (pide administrador)."""
    unidad = Path(almacen).resolve().drive
    if not unidad:
        return None
    try:
        proceso = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-BitLockerVolume -MountPoint '{unidad}' -ErrorAction Stop).ProtectionStatus"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    estado = proceso.stdout.strip()
    return estado if proceso.returncode == 0 and estado in ("On", "Off") else None


def revisar_almacen(
    almacen: Path | None, base_datos: Path, datos: Path, raiz: Path, bitlocker: str | None,
) -> list[Revision]:
    if almacen is None:
        return [Revision(FALTA, (
            "IDC_ALMACEN no está definido: la base y los datos están en la carpeta del "
            "proyecto, sin cifrar. Sigue docs/almacen-cifrado.md."
        ))]
    revisiones = []

    def anotar(condicion, si, no, estado_no=FALTA):
        revisiones.append(Revision(OK, si) if condicion else Revision(estado_no, no))

    anotar(not _dentro(almacen, raiz), "El almacén está fuera del repositorio.",
           "El almacén está dentro del repositorio: podría terminar en Git.")
    anotar(_dentro(base_datos, almacen), "La base de datos está en el almacén.",
           f"La base de datos está fuera del almacén ({base_datos}).")
    anotar(_dentro(datos, almacen), "La carpeta datos/ está en el almacén.",
           f"La carpeta de datos está fuera del almacén ({datos}).")
    anotar(_define(almacen / ".env", "IDC_SAL_CORREOS"),
           "La sal de los correos está en el .env del almacén.",
           "Falta IDC_SAL_CORREOS en el .env del almacén.")
    anotar(not _define(raiz / ".env", "IDC_SAL_CORREOS"),
           "El .env del proyecto no guarda la sal.",
           "La sal también está en el .env del proyecto, que no está cifrado: bórrala de ahí.",
           AVISO)
    anotar(not (raiz / "db.sqlite3").exists(),
           "No queda una base sin cifrar en el proyecto.",
           "Queda db.sqlite3 en el proyecto, sin cifrar: muévela al almacén o bórrala.",
           AVISO)
    restos = raiz / "datos"
    anotar(not (restos.is_dir() and any(restos.iterdir())),
           "No quedan datos sin cifrar en el proyecto.",
           "Queda la carpeta datos/ en el proyecto, sin cifrar: muévela al almacén o bórrala.",
           AVISO)
    if bitlocker == "On":
        revisiones.append(Revision(OK, "BitLocker protege la unidad del almacén."))
    elif bitlocker == "Off":
        revisiones.append(Revision(FALTA, "BitLocker no protege la unidad del almacén."))
    else:
        unidad = Path(almacen).resolve().drive or "<unidad>"
        revisiones.append(Revision(AVISO, (
            "No se pudo comprobar BitLocker sin permisos de administrador. Compruébalo con "
            f"«manage-bde -status {unidad}» en una PowerShell de administrador."
        )))
    return revisiones
