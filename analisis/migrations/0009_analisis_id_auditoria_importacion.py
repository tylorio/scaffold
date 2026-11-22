import uuid

from django.db import migrations, models


def dar_uuid_a_cada_analisis(apps, schema_editor):
    # Un default callable se evalúa una sola vez en AddField: cada fila necesita el suyo.
    for analisis in apps.get_model("analisis", "Analisis").objects.all():
        analisis.analisis_id = uuid.uuid4()
        analisis.save(update_fields=["analisis_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("analisis", "0008_indice_historial_continuo"),
    ]

    operations = [
        migrations.AddField(
            model_name="analisis", name="analisis_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(dar_uuid_a_cada_analisis, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="analisis", name="analisis_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.CreateModel(
            name="Auditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.CharField(max_length=150)),
                ("accion", models.CharField(choices=[
                    ("congelar", "Congelar la asignación"),
                    ("reanalizar", "Reemplazar un diagnóstico"),
                    ("exportar_resultados", "Exportar resultados"),
                    ("importar_resultados", "Importar resultados"),
                ], max_length=30)),
                ("objeto", models.CharField(blank=True, max_length=100)),
                ("detalle", models.JSONField(default=dict)),
            ],
            options={"ordering": ["-fecha", "-id"], "verbose_name_plural": "auditoría"},
        ),
        migrations.CreateModel(
            name="Importacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.CharField(max_length=150)),
                ("esquema", models.CharField(max_length=20)),
                ("hash_archivo", models.CharField(max_length=64, unique=True)),
                ("n_participantes", models.PositiveIntegerField()),
                ("generado", models.CharField(max_length=40)),
            ],
            options={
                "ordering": ["-fecha", "-id"], "verbose_name": "importación",
                "verbose_name_plural": "importaciones",
            },
        ),
    ]
