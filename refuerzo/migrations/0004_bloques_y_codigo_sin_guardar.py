"""Pieza 9: bloques de refuerzo (D20), aperturas bloqueadas y soluciones sin código.

Los intentos que ya existían pasan a llevar solo la longitud y el hash de su
código, y quedan asociados al bloque de ejemplo de su concepto (versión 1), que
es el material que tenían a la vista. Después se borra la columna del código.
"""
import hashlib

from django.db import migrations, models


def codigo_a_huella(apps, schema_editor):
    IntentoEjercicio = apps.get_model("refuerzo", "IntentoEjercicio")
    for intento in IntentoEjercicio.objects.all():
        intento.longitud_codigo = len(intento.codigo)
        intento.hash_codigo = hashlib.sha256(intento.codigo.encode("utf-8")).hexdigest()
        intento.bloque_id = f"{intento.concepto}-ejemplo"
        intento.bloque_version = 1
        intento.save(update_fields=[
            "longitud_codigo", "hash_codigo", "bloque_id", "bloque_version",
        ])


class Migration(migrations.Migration):

    dependencies = [
        ("analisis", "0010_codigo_acceso"),
        ("refuerzo", "0003_intentos_de_acceso"),
    ]

    operations = [
        migrations.CreateModel(
            name="BloqueRefuerzo",
            fields=[
                ("id", models.CharField(max_length=60, primary_key=True, serialize=False)),
                ("concepto", models.CharField(choices=[("recursion", "Recursión"), ("estructuras_datos", "Estructuras de datos"), ("excepciones", "Manejo de excepciones")], max_length=20)),
                ("semana", models.PositiveSmallIntegerField()),
                ("orden", models.PositiveSmallIntegerField()),
                ("version", models.PositiveIntegerField()),
                ("huella", models.CharField(max_length=64)),
                ("contenido", models.JSONField()),
                ("validado", models.BooleanField(default=False)),
                ("n_jueces", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("validado_en", models.DateTimeField(blank=True, null=True)),
                ("validado_por", models.CharField(blank=True, max_length=150)),
                ("cargado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["concepto", "semana", "orden"],
                "constraints": [models.UniqueConstraint(fields=("concepto", "semana", "orden"), name="un_bloque_por_ranura")],
            },
        ),
        migrations.AddField(
            model_name="aperturarefuerzo", name="bloque_id",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="aperturarefuerzo", name="bloque_version",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="aperturarefuerzo", name="permitida",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="aperturarefuerzo", name="motivo",
            field=models.CharField(blank=True, choices=[("concepto", "Concepto no reforzado antes del postest"), ("semana", "Bloque de una semana que aún no empieza")], max_length=10),
        ),
        migrations.AddField(
            model_name="intentoejercicio", name="bloque_id",
            field=models.CharField(default="", max_length=60), preserve_default=False,
        ),
        migrations.AddField(
            model_name="intentoejercicio", name="bloque_version",
            field=models.PositiveIntegerField(default=1), preserve_default=False,
        ),
        migrations.AddField(
            model_name="intentoejercicio", name="longitud_codigo",
            field=models.PositiveIntegerField(default=0), preserve_default=False,
        ),
        migrations.AddField(
            model_name="intentoejercicio", name="hash_codigo",
            field=models.CharField(default="", max_length=64), preserve_default=False,
        ),
        migrations.AddField(
            model_name="intentoejercicio", name="ejecutado",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(codigo_a_huella, migrations.RunPython.noop),
        migrations.RemoveField(model_name="intentoejercicio", name="codigo"),
    ]
