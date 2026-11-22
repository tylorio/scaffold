from django.db import models

from analisis.models import Participante
from analisis.servicios.conceptos import NOMBRES_CONCEPTOS

from .servicios.corrector import AUSENTE, ILEGIBLE, OK, SIN_RESPUESTA


class PuntajeItem(models.Model):
    """Corrección automática de un ítem T. Solo vive en el almacén local.

    No guarda nada de la asignación: quien califica no debe conocerla (D3).
    """

    MOMENTOS = [("pre", "Pretest"), ("post", "Postest")]
    ESTADOS = [
        (OK, "Corregido"), (SIN_RESPUESTA, "Sin respuesta"), (ILEGIBLE, "Ilegible"),
        (AUSENTE, "Ausente"),
    ]

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="puntajes",
    )
    momento = models.CharField(max_length=4, choices=MOMENTOS)
    forma = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B")])
    item = models.CharField(max_length=2, choices=[("T1", "T1"), ("T2", "T2"), ("T3", "T3")])
    concepto = models.CharField(max_length=20, choices=list(NOMBRES_CONCEPTOS.items()))
    banco_version = models.CharField(max_length=40)
    estado = models.CharField(max_length=13, choices=ESTADOS)
    casos_pasados = models.PositiveIntegerField(null=True)  # vacío si está ausente
    casos_total = models.PositiveIntegerField()
    t_pct = models.FloatField(null=True)  # vacío si está ausente: dato faltante, no cero
    cc_sol = models.FloatField(null=True)
    lin_sol = models.PositiveIntegerField(null=True)
    n_funciones = models.PositiveIntegerField(null=True)
    cc_ref = models.FloatField()
    lin_ref = models.PositiveIntegerField()
    corregido_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["participante__codigo", "momento", "item"]
        constraints = [
            models.UniqueConstraint(
                fields=["participante", "momento", "item"], name="un_puntaje_por_item",
            ),
        ]
