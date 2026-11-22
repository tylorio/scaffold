from django.db import migrations, models

MODOS = [
    ("confirmatorio", "Confirmatorio (F1 ≥ 0,70)"),
    ("exploratorio", "Exploratorio (F1 < 0,70)"),
]
CASOS = [
    ("A", "A: entre los débiles"),
    ("B", "B: entre los calculables"),
    ("C", "C: entre los tres conceptos"),
]
ORDENES = [("AB", "Pretest A, postest B"), ("BA", "Pretest B, postest A")]


def descartar_asignaciones_anteriores(apps, schema_editor):
    """Las asignaciones previas se sortearon al primer análisis, sin casos ni orden.

    ADR-004 las invalida: la asignación se sortea de nuevo al congelar.
    """
    apps.get_model("analisis", "Asignacion").objects.all().delete()
    apps.get_model("analisis", "ResultadoConcepto").objects.update(reforzado=False)


class Migration(migrations.Migration):

    dependencies = [
        ("analisis", "0006_versiones_e_indice_historial"),
    ]

    operations = [
        migrations.RunPython(descartar_asignaciones_anteriores, migrations.RunPython.noop),
        migrations.RemoveField(model_name="analisis", name="fase"),
        migrations.RemoveField(model_name="asignacion", name="comparable"),
        migrations.AddField(
            model_name="asignacion", name="caso",
            field=models.CharField(choices=CASOS, default="", max_length=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="asignacion", name="modo",
            field=models.CharField(choices=MODOS, default="", max_length=13),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="asignacion", name="orden",
            field=models.CharField(choices=ORDENES, default="", max_length=2),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="asignacion", name="semilla",
            field=models.BigIntegerField(),
        ),
        migrations.AddField(
            model_name="configuracion", name="modo",
            field=models.CharField(blank=True, choices=MODOS, max_length=13),
        ),
        migrations.CreateModel(
            name="Congelacion",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                )),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("semilla_base", models.BigIntegerField()),
                ("modo", models.CharField(choices=MODOS, max_length=13)),
                ("tamano_bloque", models.PositiveSmallIntegerField()),
            ],
            options={"verbose_name": "congelación", "verbose_name_plural": "congelación"},
        ),
    ]
