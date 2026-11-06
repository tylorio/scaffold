"""Flujo completo del análisis, sin Django: repositorio → fragmentos → IDC."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .clasificador import ModeloCargado
from .extraccion import ErrorSintaxis, Fragmento, extraer_funciones
from .idc import Parametros, ResultadoIDC, calcular_resultados
from .repositorio import abrir_repositorio, decodificar


@dataclass(frozen=True)
class FragmentoClasificado:
    fragmento: Fragmento
    insercion_commit: int | None
    p_ia: float


@dataclass(frozen=True)
class ResultadoAnalisis:
    fragmentos: list[FragmentoClasificado]
    resultado: ResultadoIDC
    commit_head: str
    tiene_historial: bool
    archivos_con_error: list[str] = field(default_factory=list)


def analizar_repositorio(
    origen: str,
    modelo: ModeloCargado,
    parametros: Parametros = Parametros(),
    base: Path | None = None,
) -> ResultadoAnalisis:
    with abrir_repositorio(origen, base) as repositorio:
        fragmentos: list[Fragmento] = []
        con_error: list[str] = []
        for archivo in repositorio.archivos():
            try:
                fragmentos.extend(
                    extraer_funciones(decodificar(archivo.contenido), archivo.ruta)
                )
            except (ErrorSintaxis, UnicodeDecodeError, SyntaxError):
                con_error.append(archivo.ruta)

        inserciones = [
            repositorio.insercion_commit(f.archivo, f.linea_inicio, f.linea_fin)
            for f in fragmentos
        ]
        commit_head = repositorio.commit_head
        tiene_historial = repositorio.tiene_historial

    probabilidades = modelo.predecir([
        {"codigo": f.codigo, "insercion_commit": i}
        for f, i in zip(fragmentos, inserciones)
    ])
    clasificados = [
        FragmentoClasificado(f, i, p)
        for f, i, p in zip(fragmentos, inserciones, probabilidades)
    ]
    resultado = calcular_resultados(
        ((c.p_ia, c.fragmento.conceptos) for c in clasificados), parametros
    )
    return ResultadoAnalisis(
        fragmentos=clasificados,
        resultado=resultado,
        commit_head=commit_head,
        tiene_historial=tiene_historial,
        archivos_con_error=con_error,
    )
