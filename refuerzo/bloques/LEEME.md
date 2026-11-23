# Bloques de refuerzo (D20)

Un archivo JSON por bloque: 8 por concepto (2 por semana durante 4 semanas), 24 en total.
Se cargan con `python manage.py cargar_bloques` y se entregan solo después de registrar
en Gestión que los jueces los validaron (HE3). El formato está en el README, sección
"Bloques de refuerzo".

Cambiar un bloque ya cargado exige subir su `version`; la versión nueva vuelve a
quedar sin validar.
