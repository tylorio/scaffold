"""Corrige una sesión de la prueba y guarda los puntajes T."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from analisis.models import Asignacion
from analisis.persistencia import exigir_asignacion_congelada
from analisis.servicios.repositorio import decodificar
from refuerzo.servicios.ejecutor import EjecutorRemoto

from .models import PuntajeItem
from .servicios.banco import Banco
from .servicios.corrector import ILEGIBLE, corregir_item, resultado_ausente

MOMENTOS = ("pre", "post")


@dataclass
class Correccion:
    filas: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def hay_ilegibles(self) -> bool:
        return any(f["estado"] == ILEGIBLE for f in self.filas)


def forma_de(asignacion: Asignacion, momento: str) -> str:
    """AB: pretest con A y postest con B. BA: al revés (D16)."""
    return asignacion.orden[MOMENTOS.index(momento)]


def _leer(ruta: Path) -> str | None:
    if not ruta.is_file():
        return None
    try:
        return decodificar(ruta.read_bytes())
    except (UnicodeDecodeError, SyntaxError, LookupError):
        return "\0"  # no es texto Python: el corrector lo marcará ilegible


def corregir_momento(
    momento: str, soluciones: Path, bancos: dict[str, Banco], tiempo_limite: float = 5.0,
    remoto: EjecutorRemoto | None = None,
) -> Correccion:
    """Corrige `soluciones/<código>/T1.py…T3.py` con la forma que le tocó a cada uno.

    Exige la asignación congelada: sin ella no se sabe qué forma rindió cada
    participante, y además corregir el pretest antes de congelar abriría la puerta
    a que la prueba influya en el sorteo (D3).
    """
    if momento not in MOMENTOS:
        raise ValueError(f"Momento desconocido: {momento}")
    exigir_asignacion_congelada()
    soluciones = Path(soluciones)
    correccion = Correccion()
    asignaciones = list(
        Asignacion.objects.select_related("participante").order_by("participante__codigo")
    )
    codigos = {a.participante.codigo for a in asignaciones}
    if soluciones.is_dir():
        for carpeta in sorted(p for p in soluciones.iterdir() if p.is_dir()):
            if carpeta.name not in codigos:
                correccion.avisos.append(
                    f"{carpeta.name}: no es un participante con asignación; se ignoró."
                )
    for asignacion in asignaciones:
        participante = asignacion.participante
        carpeta = soluciones / participante.codigo
        ausente = not carpeta.is_dir()
        if ausente:
            correccion.avisos.append(
                f"{participante.codigo}: sin carpeta de soluciones; queda como ausente "
                "(dato faltante, no cero)."
            )
        forma = forma_de(asignacion, momento)
        banco = bancos[forma]
        for item in banco.items:
            if ausente:
                resultado = resultado_ausente(item)
            else:
                resultado = corregir_item(
                    _leer(carpeta / f"{item.item}.py"), item, tiempo_limite, remoto,
                )
            valores = {
                "forma": forma, "concepto": item.concepto, "banco_version": banco.version,
                "estado": resultado.estado, "casos_pasados": resultado.casos_pasados,
                "casos_total": resultado.casos_total, "t_pct": resultado.t_pct,
                "cc_sol": resultado.cc_sol, "lin_sol": resultado.lin_sol,
                "n_funciones": resultado.n_funciones, "cc_ref": resultado.cc_ref,
                "lin_ref": resultado.lin_ref,
            }
            PuntajeItem.objects.update_or_create(
                participante=participante, momento=momento, item=item.item,
                defaults=valores,
            )
            correccion.filas.append({
                "participante": participante.codigo, "momento": momento,
                "item": item.item, "T_pct": resultado.t_pct, **valores,
            })
    return correccion
