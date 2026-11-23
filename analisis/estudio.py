"""Base para el análisis estadístico (D17) y cierre del estudio (D13). Solo en local.

`exportar_estudio` escribe en una carpeta:

- `largo.csv`: una fila por participante × concepto × momento (D17), con T y Q.
- `participantes.csv`: una fila por participante incluido, con el IDC global, el
  índice por historial y en qué hipótesis entra (P1, P3, P5).
- `flujo.csv`: las etapas del diagrama de flujo de participantes (P5).
- `LEEME.txt`: qué es cada archivo y las reglas de inclusión.

Ningún archivo lleva código, rutas, URLs, correos ni hashes de commit.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Auditoria, Fragmento, Participante
from .persistencia import exigir_asignacion_congelada
from .servicios.conceptos import CONCEPTOS
from .servicios.estudio import (
    HIPOTESIS,
    MOMENTOS,
    Registro,
    Situacion,
    estado_del_momento,
    etapas_del_flujo,
    forma_del_momento,
    hipotesis_que_lo_usan,
    resumir_q,
)
from .servicios.exportacion import csv_de_filas
from .servicios.idc import intervalo_wilson

COLUMNAS_LARGO = (
    "participante", "concepto", "momento", "forma", "orden", "estado", "T_pct",
    "Q", "Q_cal1", "Q_cal2", "n_calificadores", "cc_sol", "cc_ref", "lin_sol", "lin_ref",
    "reforzado", "condicion", "caso", "modo", "idc_concepto", "idc_lo", "idc_hi",
    "n_fragmentos", "estado_concepto", "semilla", "version_reglas", "version_modelo",
    "modelo_es_demo", "theta", "lambda", "m", "banco_version",
)
COLUMNAS_PARTICIPANTES = (
    "participante", "caso", "orden", "modo", "n_reforzados", "n_control",
    "idc_global", "idc_global_lo", "idc_global_hi", "n_fragmentos", "n_ia", "n_autores",
    "indice_historial", "indice_historial_15", "indice_historial_60",
    "media_log_insercion", "pre", "post",
    *(f"en_{h}" for h in HIPOTESIS),
)
COLUMNAS_FLUJO = ("etapa", "n", "detalle")

LEEME = """Base para el análisis del estudio IDC (D17). Generada el {fecha}.

largo.csv: una fila por participante x concepto x momento.
  estado: ok, sin_respuesta e ilegible valen como dato (0 % si no hay respuesta);
  ausente y sin_corregir son datos faltantes, nunca cero (P5). No se imputa.
  Q es el promedio de los calificadores; Q_cal1 y Q_cal2 sirven para el ICC.
  reforzado = 1 si el concepto se reforzó. HE4 usa los reforzados de toda la muestra
  (P1); el subgrupo del caso A es en_HE4_casoA en participantes.csv.
  HE5: Delta_reforzado - Delta_control por participante (t pareada o Wilcoxon);
  respaldo: Delta ~ reforzado + concepto + (1 | participante).

participantes.csv: una fila por participante incluido (con asignación congelada).
  HE2a usa la dependencia autorreportada, del cuestionario, que se une por el código
  del participante. HE2b usa idc_global. En modo exploratorio, HE1 y HE2b son
  exploratorias (P3, R3).
  en_<hipótesis> = 1 si el participante entra en ese análisis según P5. HE1 y HE2a
  exigen además el cuestionario: compruébalo al unir las bases.

flujo.csv: etapas del diagrama de flujo de participantes (Capítulo V).
  registrados = incluidos + excluidos + retirados + sin_diagnostico.

Modo de la asignación: {modo}. Semilla base: {semilla}.
Versión del sistema: {version}.
"""


def _redondear(valor, digitos=4):
    return "" if valor is None else round(valor, digitos)


def _intervalo(n_ia, n):
    intervalo = intervalo_wilson(n_ia, n) if n else None
    return (None, None) if intervalo is None else intervalo


def _momentos(participante):
    puntajes = {}
    for p in participante.puntajes.all():
        puntajes.setdefault(p.momento, []).append(p)
    return puntajes, {
        m: estado_del_momento([p.estado for p in puntajes.get(m, [])]) for m in MOMENTOS
    }


def _filas(participantes, notas):
    largo, resumen = [], []
    for participante in participantes:
        asignacion = participante.asignacion
        analisis = asignacion.analisis_base
        conceptos = {c.concepto: c for c in analisis.conceptos.all()}
        puntajes, estados = _momentos(participante)
        for concepto in CONCEPTOS:
            resultado = conceptos.get(concepto)
            lo, hi = (
                _intervalo(resultado.n_ia, resultado.n_fragmentos)
                if resultado is not None and resultado.idc is not None else (None, None)
            )
            for momento in MOMENTOS:
                item = next(
                    (p for p in puntajes.get(momento, []) if p.concepto == concepto), None,
                )
                q = resumir_q(notas.get((participante.codigo, concepto, momento)))
                largo.append({
                    "participante": participante.codigo,
                    "concepto": concepto,
                    "momento": momento,
                    "forma": item.forma if item else forma_del_momento(asignacion.orden, momento),
                    "orden": asignacion.orden,
                    "estado": item.estado if item else estados[momento],
                    "T_pct": _redondear(item.t_pct if item else None, 2),
                    **{k: ("" if v is None else v) for k, v in q.items()},
                    "cc_sol": _redondear(item.cc_sol if item else None),
                    "cc_ref": _redondear(item.cc_ref if item else None),
                    "lin_sol": "" if item is None or item.lin_sol is None else item.lin_sol,
                    "lin_ref": item.lin_ref if item else "",
                    "reforzado": int(concepto in asignacion.reforzados),
                    "condicion": asignacion.condicion(concepto),
                    "caso": asignacion.caso,
                    "modo": asignacion.modo,
                    "idc_concepto": _redondear(resultado.idc if resultado else None),
                    "idc_lo": _redondear(lo),
                    "idc_hi": _redondear(hi),
                    "n_fragmentos": resultado.n_fragmentos if resultado else "",
                    "estado_concepto": resultado.estado if resultado else "",
                    "semilla": asignacion.semilla,
                    "version_reglas": analisis.version_reglas,
                    "version_modelo": analisis.modelo_version,
                    "modelo_es_demo": int(analisis.modelo_es_demo),
                    "theta": analisis.theta,
                    "lambda": analisis.lambda_valor,
                    "m": analisis.m,
                    "banco_version": item.banco_version if item else "",
                })
        situacion = Situacion(
            con_diagnostico=True,
            idc_global_calculable=analisis.idc_global is not None,
            pre=estados["pre"], post=estados["post"],
            n_reforzados=len(asignacion.reforzados), n_control=len(asignacion.control),
            caso=asignacion.caso, modo=asignacion.modo,
        )
        lo, hi = _intervalo(analisis.n_ia, analisis.n_fragmentos)
        resumen.append({
            "participante": participante.codigo,
            "caso": asignacion.caso,
            "orden": asignacion.orden,
            "modo": asignacion.modo,
            "n_reforzados": len(asignacion.reforzados),
            "n_control": len(asignacion.control),
            "idc_global": _redondear(analisis.idc_global),
            "idc_global_lo": _redondear(lo),
            "idc_global_hi": _redondear(hi),
            "n_fragmentos": analisis.n_fragmentos,
            "n_ia": analisis.n_ia,
            "n_autores": analisis.n_autores,
            "indice_historial": _redondear(analisis.indice_historial),
            "indice_historial_15": _redondear(analisis.indice_historial_15),
            "indice_historial_60": _redondear(analisis.indice_historial_60),
            "media_log_insercion": _redondear(analisis.media_log_insercion),
            "pre": estados["pre"],
            "post": estados["post"],
            **{f"en_{h}": int(v) for h, v in hipotesis_que_lo_usan(situacion).items()},
        })
    return largo, resumen


def _registros_del_flujo():
    registros = []
    for participante in Participante.objects.select_related("asignacion").prefetch_related(
        "puntajes", "analisis",
    ):
        _, estados = _momentos(participante)
        registros.append(Registro(
            motivo_exclusion=participante.motivo_exclusion,
            retirado=participante.retirado_en is not None,
            con_diagnostico=participante.ultimo_analisis is not None,
            con_asignacion=hasattr(participante, "asignacion"),
            pre=estados["pre"], post=estados["post"],
        ))
    return registros


def exportar_estudio(
    carpeta: Path, usuario: str, notas: dict | None = None, convocados: int | None = None,
) -> dict[str, str]:
    """Escribe los archivos y devuelve el SHA-256 de cada uno (queda en la auditoría)."""
    congelada = exigir_asignacion_congelada()
    notas = notas or {}
    incluidos = list(
        Participante.objects.filter(
            motivo_exclusion="", retirado_en__isnull=True, asignacion__isnull=False,
        )
        .select_related("asignacion__analisis_base")
        .prefetch_related("puntajes", "asignacion__analisis_base__conceptos")
        .order_by("codigo")
    )
    codigos = {p.codigo for p in incluidos}
    sobrantes = sorted({clave[0] for clave in notas} - codigos)
    largo, resumen = _filas(incluidos, notas)
    flujo = etapas_del_flujo(_registros_del_flujo(), convocados)
    archivos = {
        "largo.csv": csv_de_filas(COLUMNAS_LARGO, largo),
        "participantes.csv": csv_de_filas(COLUMNAS_PARTICIPANTES, resumen),
        "flujo.csv": csv_de_filas(
            COLUMNAS_FLUJO, ({"etapa": e, "n": n, "detalle": d} for e, n, d in flujo),
        ),
        "LEEME.txt": LEEME.format(
            fecha=timezone.now().isoformat(timespec="seconds"), modo=congelada.modo,
            semilla=congelada.semilla_base, version=settings.VERSION_SISTEMA,
        ),
    }
    carpeta.mkdir(parents=True, exist_ok=True)
    huellas = {}
    for nombre, contenido in archivos.items():
        datos = contenido.encode("utf-8")
        (carpeta / nombre).write_bytes(datos)
        huellas[nombre] = hashlib.sha256(datos).hexdigest()
    Auditoria.anotar(
        usuario, Auditoria.EXPORTAR_ESTUDIO, n_incluidos=len(incluidos),
        n_notas=len(notas), huellas=huellas,
    )
    return {"huellas": huellas, "sobrantes": sobrantes}


# Cierre (D13)

class CierreNoPermitido(Exception):
    pass


def cerrar_estudio(usuario: str) -> dict:
    """Borra el código y lo que lleva a los repositorios. Se conservan los agregados.

    Exige una exportación previa de la base, que es lo que se conserva. No se
    deshace: después ya no se puede analizar ni volver a leer un fragmento.
    """
    from refuerzo.models import IntentoAcceso

    ultima = Auditoria.objects.filter(accion=Auditoria.EXPORTAR_ESTUDIO).first()
    if ultima is None:
        raise CierreNoPermitido(
            "Primero exporta la base con exportar_estudio: es lo que se conserva."
        )
    from .participacion import carpeta_a_borrar

    # Las carpetas entregadas las borra el investigador; sus rutas no van a la auditoría.
    carpetas = sorted(filter(None, (
        carpeta_a_borrar(r) for r in Participante.objects.values_list("repositorio", flat=True)
    )))
    with transaction.atomic():
        borrado = {
            "fragmentos": Fragmento.objects.count(),
            "participantes_con_repositorio": Participante.objects.exclude(repositorio="").count(),
            "carpetas_entregadas": len(carpetas),
        }
        Fragmento.objects.all().delete()
        Participante.objects.update(repositorio="", hashes_correos=[], codigo_acceso="")
        IntentoAcceso.objects.all().delete()
        Auditoria.anotar(
            usuario, Auditoria.CIERRE, borrado=borrado,
            exportacion=ultima.fecha.isoformat(timespec="seconds"),
        )
    temporal = settings.CARPETA_TEMPORAL
    if temporal is not None and Path(temporal).is_dir():
        for hijo in Path(temporal).iterdir():  # clones que quedaron de una caída
            if hijo.is_dir():
                shutil.rmtree(hijo, ignore_errors=True)
            else:
                hijo.unlink()
    return {**borrado, "carpetas": carpetas}
