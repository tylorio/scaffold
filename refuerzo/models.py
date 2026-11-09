from django.db import models

from analisis.models import Analisis, Participante, ResultadoConcepto


class AperturaRefuerzo(models.Model):
    """Cada vez que un participante abre el material: mide la exposición real."""

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="aperturas",
    )
    concepto = models.CharField(max_length=20, choices=ResultadoConcepto.CONCEPTOS)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "id"]


class IntentoEjercicio(models.Model):
    analisis = models.ForeignKey(
        Analisis, on_delete=models.CASCADE, related_name="intentos",
    )
    concepto = models.CharField(max_length=20, choices=ResultadoConcepto.CONCEPTOS)
    ejercicio = models.CharField(max_length=20)
    codigo = models.TextField()
    pasados = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    error = models.TextField(blank=True)
    casos = models.JSONField(default=list)
    usa_concepto = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
