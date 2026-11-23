"""Reglas de la base para el análisis (D17, P1, P3, P5), sin Django.

- Qué hipótesis usa a cada participante, según los momentos en que se presentó (P5).
- La unión con la rúbrica Q de los dos calificadores.
- Las etapas del diagrama de flujo de participantes.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from .conceptos import CONCEPTOS

MOMENTOS = ("pre", "post")
PRESENTE = "presente"
AUSENTE = "ausente"
SIN_CORREGIR = "sin_corregir"  # la prueba de ese momento todavía no se corrige

HIPOTESIS = ("HG", "HE1", "HE2a", "HE2b", "HE4", "HE4_casoA", "HE5")
Q_MAXIMO = 20


class CalificacionesInvalidas(Exception):
    pass


def estado_del_momento(estados_items: list[str]) -> str:
    """Un momento está presente si se entregó la carpeta, aunque falten ítems."""
    if not estados_items:
        return SIN_CORREGIR
    return AUSENTE if all(e == "ausente" for e in estados_items) else PRESENTE


@dataclass(frozen=True)
class Situacion:
    con_diagnostico: bool
    idc_global_calculable: bool
    pre: str
    post: str
    n_reforzados: int
    n_control: int
    caso: str
    modo: str


def hipotesis_que_lo_usan(s: Situacion) -> dict[str, bool]:
    """P5: análisis de casos completos, sin imputar.

    - Ausente en el pretest: fuera de todo lo que usa la prueba (HG, HE2, HE4, HE5).
      Sigue en HE1 si tiene el análisis del repositorio.
    - Ausente en el postest: fuera de HG, HE4 y HE5; conserva HE1 y HE2.

    HE1 y HE2a también exigen el cuestionario, que se aplica fuera del sistema: esa
    parte la comprueba quien une las dos bases.
    """
    pre = s.pre == PRESENTE
    ambos = pre and s.post == PRESENTE
    he4 = ambos and s.n_reforzados >= 1
    return {
        "HG": ambos,
        "HE1": s.con_diagnostico,
        "HE2a": pre,
        "HE2b": pre and s.idc_global_calculable,
        "HE4": he4,
        # P1: subgrupo donde "reforzado" coincide con "débil".
        "HE4_casoA": he4 and s.caso == "A" and s.modo == "confirmatorio",
        "HE5": he4 and s.n_control >= 1,
    }


def forma_del_momento(orden: str, momento: str) -> str:
    """AB: forma A en el pretest y B en el postest; BA, al revés (D16)."""
    if orden not in ("AB", "BA"):
        return ""
    return orden[0] if momento == "pre" else orden[1]


# Rúbrica Q

COLUMNAS_Q = ("participante", "concepto", "momento", "calificador", "Q")


def leer_calificaciones(texto: str) -> dict[tuple[str, str, str], dict[int, float]]:
    """CSV con una fila por participante, concepto, momento y calificador (1 o 2)."""
    lector = csv.DictReader(io.StringIO(texto.lstrip("﻿")))
    if lector.fieldnames is None or set(COLUMNAS_Q) - set(lector.fieldnames):
        raise CalificacionesInvalidas(f"Las columnas deben ser: {', '.join(COLUMNAS_Q)}.")
    notas: dict[tuple[str, str, str], dict[int, float]] = {}
    errores = []
    for numero, fila in enumerate(lector, start=2):
        clave = (fila["participante"].strip(), fila["concepto"].strip(), fila["momento"].strip())
        if clave[1] not in CONCEPTOS:
            errores.append(f"fila {numero}: concepto desconocido")
        if clave[2] not in MOMENTOS:
            errores.append(f"fila {numero}: el momento es pre o post")
        try:
            calificador = int(fila["calificador"])
            nota = float(fila["Q"].replace(",", "."))
        except ValueError:
            errores.append(f"fila {numero}: calificador o Q no son números")
            continue
        if calificador not in (1, 2):
            errores.append(f"fila {numero}: el calificador es 1 o 2")
        if not 0 <= nota <= Q_MAXIMO:
            errores.append(f"fila {numero}: Q va de 0 a {Q_MAXIMO}")
        if calificador in notas.get(clave, {}):
            errores.append(f"fila {numero}: nota repetida")
        notas.setdefault(clave, {})[calificador] = nota
    if errores:
        raise CalificacionesInvalidas("; ".join(errores[:10]))
    return notas


def resumir_q(notas: dict[int, float] | None) -> dict:
    """Q es el promedio de los calificadores que calificaron (D17)."""
    notas = notas or {}
    valores = list(notas.values())
    return {
        "Q": round(sum(valores) / len(valores), 4) if valores else None,
        "Q_cal1": notas.get(1),
        "Q_cal2": notas.get(2),
        "n_calificadores": len(valores),
    }


# Diagrama de flujo (P5)

@dataclass(frozen=True)
class Registro:
    motivo_exclusion: str
    retirado: bool
    con_diagnostico: bool
    con_asignacion: bool
    pre: str
    post: str


def etapas_del_flujo(
    registros: list[Registro], convocados: int | None = None,
) -> list[tuple[str, int, str]]:
    """(etapa, n, detalle). Registrados = incluidos + excluidos + retirados + sin diagnóstico."""
    filas: list[tuple[str, int, str]] = []
    if convocados is not None:
        filas.append(("convocados", convocados, "dato del investigador"))
    filas.append(("registrados", len(registros), "con consentimiento"))
    motivos: dict[str, int] = {}
    for r in registros:
        if r.motivo_exclusion and not r.retirado:
            motivos[r.motivo_exclusion] = motivos.get(r.motivo_exclusion, 0) + 1
    for motivo, n in sorted(motivos.items()):
        filas.append(("excluidos", n, motivo))
    filas.append(("retirados", sum(r.retirado for r in registros), "datos borrados"))
    activos = [r for r in registros if not r.motivo_exclusion and not r.retirado]
    filas.append((
        "sin_diagnostico", sum(not r.con_asignacion for r in activos),
        "sin análisis válido o sin asignación",
    ))
    incluidos = [r for r in activos if r.con_asignacion]
    filas.append(("incluidos", len(incluidos), "con asignación congelada"))
    for estado in (AUSENTE, SIN_CORREGIR):
        filas.append(("sin_pretest", sum(r.pre == estado for r in incluidos), estado))
    con_pre = [r for r in incluidos if r.pre == PRESENTE]
    filas.append(("con_pretest", len(con_pre), ""))
    for estado in (AUSENTE, SIN_CORREGIR):
        filas.append(("sin_postest", sum(r.post == estado for r in con_pre), estado))
    filas.append(("con_postest", sum(r.post == PRESENTE for r in con_pre), ""))
    return filas
