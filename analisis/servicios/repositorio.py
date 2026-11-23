"""Lectura de repositorios Git y de carpetas locales.

Las URL se clonan en un directorio temporal que se borra al terminar: un clon
incluye el historial, y el historial trae nombres y correos reales.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import tokenize
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Iterator
from urllib.parse import urlsplit

from git import GitCommandError, InvalidGitRepositoryError, Repo
from pydriller import Repository

DIRECTORIOS_EXCLUIDOS = frozenset({
    ".git", ".venv", "venv", "env", "__pycache__", "site-packages",
    "node_modules", "build", "dist", ".tox", ".mypy_cache", ".pytest_cache",
    "migrations",
})
CARPETAS_DE_PRUEBAS = frozenset({"test", "tests", "pruebas"})
_URL =re.compile(r"^(https?|ssh|git|file)://", re.IGNORECASE)
_SCP = re.compile(r"^[\w.-]+@[\w.-]+:.+")


class OrigenInvalido(Exception):
    """La ruta o URL del repositorio no se puede usar."""


class ErrorRepositorio(Exception):
    """El repositorio existe pero no se pudo clonar o leer."""


@dataclass(frozen=True)
class ArchivoFuente:
    ruta: str  # relativa al repositorio y con "/"; nunca una ruta absoluta
    contenido: bytes


def es_url(origen: str) -> bool:
    return bool(_URL.match(origen) or _SCP.match(origen))


def _en_carpeta_excluida(ruta: str) -> bool:
    return not DIRECTORIOS_EXCLUIDOS.isdisjoint(PurePath(ruta).parts)


def es_archivo_de_pruebas(ruta: str) -> bool:
    """Las pruebas no miden el concepto. Siguen contando en el tamaño de inserción."""
    *carpetas, nombre = PurePath(ruta).parts
    return (
        not CARPETAS_DE_PRUEBAS.isdisjoint(carpetas)
        or nombre.startswith("test_")
        or nombre.endswith("_test.py")
        or nombre == "conftest.py"
    )


def resolver_ruta(origen: str, base: Path | None = None) -> Path:
    ruta = Path(origen).expanduser()
    if not ruta.is_absolute():
        ruta = (base or Path.cwd()) / ruta
    return ruta.resolve()


def _validar_url(origen: str) -> None:
    """Rechaza lo que dejaría un secreto en la base de datos."""
    try:
        partes = urlsplit(origen)
    except ValueError as error:
        raise OrigenInvalido("La URL no tiene un formato válido.") from error
    if "@" in partes.netloc or partes.query or partes.fragment:
        raise OrigenInvalido(
            "La URL no debe incluir usuario, token ni parámetros: quedarían "
            "guardados en la base de datos."
        )


def validar_origen(origen: str, base: Path | None = None) -> None:
    origen = origen.strip()
    if not origen:
        raise OrigenInvalido("Indica una ruta local o una URL.")
    if es_url(origen):
        if _URL.match(origen):
            _validar_url(origen)
        return
    if not resolver_ruta(origen, base).is_dir():
        raise OrigenInvalido(f"No existe la carpeta: {origen}")


def decodificar(contenido: bytes) -> str:
    """Decodifica respetando la declaración `coding` y el BOM, como Python."""
    codificacion, _ = tokenize.detect_encoding(io.BytesIO(contenido).readline)
    return contenido.decode(codificacion)


class CarpetaLocal:
    """Carpeta sin historial Git: no hay tamaño de inserción disponible."""

    tiene_historial = False
    commit_head = ""
    n_autores = None

    def __init__(self, ruta: Path):
        self.ruta = ruta

    def archivos(self) -> Iterator[ArchivoFuente]:
        for raiz, carpetas, nombres in os.walk(self.ruta):
            carpetas[:] = sorted(c for c in carpetas if c not in DIRECTORIOS_EXCLUIDOS)
            for nombre in sorted(nombres):
                if nombre.endswith(".py"):
                    ruta = Path(raiz) / nombre
                    relativa = ruta.relative_to(self.ruta).as_posix()
                    if not es_archivo_de_pruebas(relativa):
                        yield ArchivoFuente(relativa, ruta.read_bytes())

    def insercion_commit(self, archivo: str, inicio: int, fin: int) -> int | None:
        return None

    def commit_de(self, archivo: str, inicio: int, fin: int) -> str | None:
        return None

    def correo_autor(self, archivo: str, inicio: int, fin: int) -> str | None:
        return None

    def inserciones_por_linea(self, archivo: str, inicio: int, fin: int) -> list[int]:
        return []


class RepositorioGit:
    """Analiza el contenido de HEAD, no los cambios sin confirmar."""

    tiene_historial = True

    def __init__(self, ruta: Path, repo: Repo):
        self.ruta = ruta
        self._repo = repo
        self.commit_head = repo.head.commit.hexsha
        self._inserciones: dict[str, int] | None = None
        self._commits_de_archivo: dict[str, list[str]] = {}
        self._autores: set[str] = set()  # solo en memoria: se guarda la cantidad
        self._correo_de_commit: dict[str, str] = {}  # solo en memoria, para D19

    @property
    def n_autores(self) -> int:
        """Correos distintos en las líneas leídas. Depende de `insercion_commit`.

        Sirve para detectar repositorios que no son individuales. Una persona con
        dos correos cuenta como dos, así que es un aviso y no una prueba.
        """
        return len(self._autores)

    def archivos(self) -> Iterator[ArchivoFuente]:
        for elemento in self._repo.head.commit.tree.traverse():
            if elemento.type != "blob" or not elemento.path.endswith(".py"):
                continue
            if (
                elemento.mode == 0o120000
                or _en_carpeta_excluida(elemento.path)
                or es_archivo_de_pruebas(elemento.path)
            ):
                continue
            yield ArchivoFuente(elemento.path, elemento.data_stream.read())

    def _cargar_inserciones(self) -> dict[str, int]:
        """Líneas añadidas a archivos .py en cada commit.

        Se mide por commit y no por archivo para que un pegado grande repartido
        en varios archivos se vea como lo que es, y para sobrevivir a renombres.
        Las carpetas excluidas no cuentan: subir un entorno virtual junto al
        código no es escribir miles de líneas.
        """
        if self._inserciones is None:
            self._inserciones = {}
            commits = Repository(
                str(self.ruta), only_modifications_with_file_types=[".py"]
            ).traverse_commits()
            for commit in commits:
                self._inserciones[commit.hash] = sum(
                    archivo.added_lines
                    for archivo in commit.modified_files
                    if (ruta := archivo.new_path or "").endswith(".py")
                    and not _en_carpeta_excluida(ruta)
                )
        return self._inserciones

    def _commits_por_linea(self, archivo: str) -> list[str]:
        """Commit que escribió cada línea.

        `-w` ignora los cambios de espacios, y `-M` y `-C` siguen al código movido,
        para que reformatear o reorganizar no pase por escribirlo de nuevo.
        """
        if archivo not in self._commits_de_archivo:
            commits: list[str] = []
            try:
                blame = self._repo.blame("HEAD", archivo, w=True, M=True, C=True)
                for commit, lineas in blame or []:
                    commits.extend([commit.hexsha] * len(lineas))
                    correo = commit.author.email.lower()
                    self._autores.add(correo)
                    self._correo_de_commit[commit.hexsha] = correo
            except GitCommandError:
                commits = []
            self._commits_de_archivo[archivo] = commits
        return self._commits_de_archivo[archivo]

    def commit_de(self, archivo: str, inicio: int, fin: int) -> str | None:
        """Commit que aportó la mayoría de las líneas del fragmento."""
        lineas = self._commits_por_linea(archivo)[inicio - 1 : fin]
        return Counter(lineas).most_common(1)[0][0] if lineas else None

    def correo_autor(self, archivo: str, inicio: int, fin: int) -> str | None:
        """Correo del autor del commit mayoritario. Solo para compararlo en memoria."""
        commit = self.commit_de(archivo, inicio, fin)
        return None if commit is None else self._correo_de_commit.get(commit)

    def insercion_commit(self, archivo: str, inicio: int, fin: int) -> int | None:
        """Tamaño del commit que aportó la mayoría de las líneas del fragmento."""
        commit = self.commit_de(archivo, inicio, fin)
        return None if commit is None else self._cargar_inserciones().get(commit)

    def inserciones_por_linea(self, archivo: str, inicio: int, fin: int) -> list[int]:
        """Tamaño del commit que escribió cada línea del fragmento (índice por historial)."""
        inserciones = self._cargar_inserciones()
        return [
            inserciones[commit]
            for commit in self._commits_por_linea(archivo)[inicio - 1 : fin]
            if commit in inserciones
        ]


def _abrir_local(ruta: Path) -> tuple[CarpetaLocal | RepositorioGit, Repo | None]:
    if not (ruta / ".git").exists():
        return CarpetaLocal(ruta), None
    try:
        repo = Repo(ruta)
    except InvalidGitRepositoryError:
        return CarpetaLocal(ruta), None
    if not repo.head.is_valid():  # repositorio sin commits
        repo.close()
        return CarpetaLocal(ruta), None
    return RepositorioGit(ruta, repo), repo


@contextmanager
def abrir_repositorio(
    origen: str, base: Path | None = None, temporal: Path | None = None,
) -> Iterator[CarpetaLocal | RepositorioGit]:
    """Abre una ruta o clona una URL. Los clones desaparecen al salir del `with`.

    `temporal` es dónde se clona: el almacén cifrado, para que el código de los
    estudiantes no pase por la carpeta temporal del sistema, que no está cifrada.
    """
    origen = origen.strip()
    validar_origen(origen, base)

    if not es_url(origen):
        lector, repo = _abrir_local(resolver_ruta(origen, base))
        try:
            yield lector
        finally:
            if repo is not None:
                repo.close()
        return

    if temporal is not None:
        Path(temporal).mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="idc_clon_", dir=temporal, ignore_cleanup_errors=True
    ) as carpeta:
        destino = Path(carpeta) / "repo"
        try:
            Repo.clone_from(
                origen, destino, env={"GIT_TERMINAL_PROMPT": "0"}
            ).close()
        except GitCommandError as error:
            raise ErrorRepositorio(
                "No se pudo clonar el repositorio. Revisa la URL y que sea "
                "accesible sin credenciales."
            ) from error
        lector, repo = _abrir_local(destino)
        try:
            yield lector
        finally:
            if repo is not None:
                repo.close()
