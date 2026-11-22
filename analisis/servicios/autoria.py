"""Filtro por autor (D19): en un repositorio grupal solo se analiza lo del participante.

Se guarda únicamente un HMAC-SHA256 con sal de los correos que el participante
declara. Los correos de otros autores se hashean en memoria para compararlos y
nunca se guardan, ni en claro ni hasheados.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Iterable


def hash_correo(correo: str, sal: str) -> str:
    return hmac.new(
        sal.encode("utf-8"), correo.strip().lower().encode("utf-8"), hashlib.sha256
    ).hexdigest()


def hashes_de_correos(correos: Iterable[str], sal: str) -> list[str]:
    return sorted({hash_correo(c, sal) for c in correos})


@dataclass(frozen=True)
class FiltroAutor:
    hashes: frozenset[str]
    sal: str = field(repr=False)

    def es_propio(self, correo: str | None) -> bool:
        return correo is not None and hash_correo(correo, self.sal) in self.hashes
