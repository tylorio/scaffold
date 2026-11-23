# Bloques de refuerzo (D20)

Un archivo JSON por bloque: 8 por concepto (2 por semana durante 4 semanas), 24 en
total. El nombre del archivo es el `id` del bloque, por ejemplo
`estructuras_datos-s1-1.json`. El formato está en el README, sección «Bloques de
refuerzo».

Estado: los 24 bloques escritos (8 por concepto), con sus soluciones. Falta la validación de los jueces.

Antes de cargarlos:

1. Agrega la solución de cada ejercicio en `datos/soluciones_bloques/<concepto>.py`. Va al almacén, no a Git: el repositorio es público.
2. Corre `python -m pytest tests/test_contenido.py`.
3. Corre `python manage.py controlar_solapamiento` contra la prueba real.

Después, carga con `python manage.py cargar_bloques`. Los bloques se entregan solo
cuando registras en Gestión que los jueces los validaron (HE3). Cambiar un bloque ya
cargado exige subir su `version`, y la versión nueva vuelve a quedar sin validar.
