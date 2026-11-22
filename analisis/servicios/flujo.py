"""Flujo completo del análisis, sin Django: repositorio → fragmentos → IDC."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .clasificador import ModeloCargado
from .conceptos import ESTRUCTURAS
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
    n_autores: int | None = None
    n_triviales: int = 0
    resultado_amplio: ResultadoIDC | None = None  # conceptos-v1-amplia, para sensibilidad
    # Fragmentos sin estructuras de datos que tienen alguna indexación de tipo desconocido (R4).
    n_indexacion_indeterminada: int = 0


def analizar_repositorio(
    origen: str,
    modelo: ModeloCargado,
    parametros: Parametros = Parametros(),
    base: Path | None = None,
    desde_commit: str | None = None,
) -> ResultadoAnalisis:
    """Analiza el repositorio; con `desde_commit`, solo lo escrito después de él.

    Un análisis post sobre todo el repositorio repetiría el código del pre y el
    IDC casi no podría cambiar.
    """
    with abrir_repositorio(origen, base) as repositorio:
        extraidos: list[Fragmento] = []
        con_error: list[str] = []
        for archivo in repositorio.archivos():
            try:
                extraidos.extend(
                    extraer_funciones(decodificar(archivo.contenido), archivo.ruta)
                )
            except (ErrorSintaxis, UnicodeDecodeError, SyntaxError):
                con_error.append(archivo.ruta)

        if desde_commit:
            nuevos = repositorio.commits_desde(desde_commit)
            extraidos = [
                f for f in extraidos
                if repositorio.commit_de(f.archivo, f.linea_inicio, f.linea_fin) in nuevos
            ]

        fragmentos = [f for f in extraidos if not f.trivial]
        inserciones = [
            repositorio.insercion_commit(f.archivo, f.linea_inicio, f.linea_fin)
            for f in fragmentos
        ]
        commit_head = repositorio.commit_head
        tiene_historial = repositorio.tiene_historial
        n_autores = repositorio.n_autores

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
    resultado_amplio = calcular_resultados(
        ((c.p_ia, c.fragmento.conceptos_amplia) for c in clasificados), parametros
    )
    return ResultadoAnalisis(
        fragmentos=clasificados,
        resultado=resultado,
        commit_head=commit_head,
        tiene_historial=tiene_historial,
        archivos_con_error=con_error,
        n_autores=n_autores,
        n_triviales=len(extraidos) - len(fragmentos),
        resultado_amplio=resultado_amplio,
        n_indexacion_indeterminada=sum(
            1 for f in fragmentos
            if f.indexaciones_indeterminadas and ESTRUCTURAS not in f.conceptos
        ),
    )
