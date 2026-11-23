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


class IntentoAcceso(models.Model):
    """Cada intento de entrar al portal, para bloquear a quien prueba códigos al azar.

    La IP se guarda solo como hash y los registros se borran a las 24 h (08 §3.2).
    """

    ip_hash = models.CharField(max_length=64, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    exito = models.BooleanField(default=False)
    participante = models.ForeignKey(
        Participante, null=True, on_delete=models.SET_NULL, related_name="+",
    )


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
