# Lo que necesito para terminar (23 de noviembre de 2026)

**Estado:** versión 0.12.0, 759 pruebas en verde. Los 24 bloques, la prueba A/B y las dos alarmas de solapamiento están listos. Lo que falta depende de ti y del asesor.

## 1. Pedirle al asesor

Puedes reenviarle esta sección tal cual.

1. **El archivo que faltó.** El LEEME anuncia `soluciones_privadas/soluciones_sesion_etiquetado.py`, pero no venía en la entrega.
2. **Confirmar el `autor_id` de la sesión.** D27 dice que el `autor_id` es el código de sesión (S07). Pero la regla de etiquetado (§3 del documento de la sesión) pone el asistente como `autor_id` de las salidas crudas. Con el asistente, el código de una persona queda repartido entre dos autores, y la separación por autor de la prueba final (07 §4) deja de agrupar a cada persona. **Propuesta:** `autor_id` = código de sesión para todo lo que sale de la sesión, y el asistente en el campo `asistente`.
3. **Aprobar dos correcciones del consentimiento del estudio (v1)**, antes de enviarlo al CEI (§3 de este documento).
4. **Aprobar el cambio de dos comandos de la convocatoria** que no funcionan en Windows (§3).
5. **Revisar la pregunta 2 de D28** (repositorios grupales). El sistema solo guarda una copia del repositorio cuando el estudiante entrega la carpeta. Si entrega una URL, clona, analiza y borra el clon en el momento (§3).

## 2. Tus tareas

En orden de urgencia.

| # | Tarea | Cómo | Por qué urge |
|---|---|---|---|
| 1 | **Crear el almacén cifrado** | Sigue [almacen-cifrado.md](almacen-cifrado.md) §1 y §2. Después mueve a `Z:\entregas-asesor\` el zip `contenido-asesor-2026-11-22.zip` y la carpeta `docs/entregas-asesor/` | Hoy la prueba real (formas A y B, claves y ficha de los jueces) está **sin cifrar** en tu disco |
| 2 | **Repositorios para SP-06** | Entre 5 y 10 repositorios Python con historial Git, **tuyos o públicos de cursos**. Pásame una lista con «ruta o URL + correos de commit» (los saca `git shortlog -sne --all`) | Puede cambiar m y los criterios de inclusión; los resultados van al asesor antes de la semana 4 |
| 3 | **Corregir y enviar el correo al CEI** | Completa los `[COMPLETAR]` de `correo-CEI-autorizacion-azure.md` (está en el zip del 22). Agrega los 3 puntos de D28 con la corrección de §3.3 y adjunta los consentimientos ya corregidos | Sin la autorización escrita no hay despliegue en Azure, y sin consentimiento aprobado no hay convocatoria |
| 4 | **Jueces** | Entrégales la prueba (`datos/banco_prueba/prueba-desempeno-formas-A-B.md`), los 24 bloques y la ficha de pares (`datos/banco_prueba/pares-para-jueces-2026-11-23.csv`, 20 pares). Cada juez clasifica cada par como `misma_tarea`, `misma_habilidad` o `sin_relacion` (D23). Devuélveme la ficha llena | Validar antes de la semana 9 (HE3). Si un par sale `misma_tarea`, el asesor tiene que reemplazar ese ejercicio |
| 5 | **Segunda persona que anote (SP-05)** | Alguien con formación en programación que pueda anotar 170 fragmentos (20 de calibración y 150 de la muestra) | Sin ella no se congelan las reglas de concepto |
| 6 | **Sesión de etiquetado** | Con el consentimiento de la sesión aprobado: convoca de 10 a 16 personas (convocatoria, parte B) y sigue el protocolo de `datos/sesion_etiquetado/enunciados-sesion-etiquetado-v1.1.md` §3 | El corpus alimenta la pieza 7 y el go/no-go de la semana 7 |
| 7 | **Fechas reales del estudio** | Dime qué fecha corresponde a cada semana (sobre todo la 4, la 7, la 8, la 9 y la 13) | Para el cronograma y la fecha de inicio de la intervención |
| 8 | **Azure** | Qué suscripción usarás (por ejemplo, Azure for Students) y en qué región | Para el despliegue (F9) y para completar el consentimiento |

## 3. Correcciones a los documentos antes de enviarlos

### 3.1 Consentimiento del estudio, §3 («El portal web»)

**Dice:** «Las soluciones que escribes en los ejercicios se ejecutan automáticamente para corregirlas, durante unos segundos, y no se guardan; solo se guarda si el intento pasó o no.»

**Debe decir:** «Las soluciones que escribes en los ejercicios se ejecutan automáticamente para corregirlas, durante unos segundos. **No se guarda tu código**: solo su longitud, una huella que no permite recuperarlo y el resultado de cada caso de prueba.»

**Por qué:** es lo que el sistema guarda de verdad (longitud, SHA-256 y resultado por caso).

### 3.2 Consentimiento del estudio, §3 («Tu repositorio»)

**Agregar al final:** «Si nos das acceso por GitHub o GitLab, el sistema descarga el repositorio, lo analiza y borra esa copia en el momento. Si entregas la carpeta, la guardamos en el disco cifrado hasta terminar el análisis o hasta que te retires.»

**Por qué:** §6 promete borrar «la copia de tu repositorio», y esa copia solo existe si se entrega la carpeta.

### 3.3 Correo al CEI, punto 2 de D28 (repositorios grupales)

**Redacción propuesta:** «Solo se analizan y guardan las funciones del participante. Si el repositorio se entrega por enlace, el sistema lo descarga, lo analiza y lo borra en el momento. Si se entrega como carpeta, la carpeta completa, con el código de los compañeros, queda en el disco cifrado hasta el fin del análisis, sin analizarse. ¿Es aceptable, o hace falta avisar a los compañeros o pedir solo el enlace?»

### 3.4 Convocatoria, parte A («Antes de inscribirte, comprueba tu repositorio»)

| Dice | Debe decir | Por qué |
|---|---|---|
| `git log --oneline \| head` | `git log --oneline -5` | `head` no existe en PowerShell ni en cmd. El comando falla, y el estudiante puede creer que no tiene historial |
| `git log --format="%an <%ae>" \| sort -u` | `git shortlog -sne --all` | `sort -u` falla en cmd. `shortlog` da cada nombre y correo una sola vez, sin tuberías |

## 4. Qué hago yo cuando llegue cada cosa

| Llega | Hago |
|---|---|
| Repositorios | SP-06 e informe para el asesor |
| Ficha de los jueces llena | Reviso qué ejercicios hay que reemplazar y corro de nuevo las alarmas con los bloques corregidos |
| Anotaciones de SP-05 | Kappa, concordancia y congelar `conceptos-v1` |
| Corpus de la sesión y de C2 | Pieza 7: evaluación por autor, calibración, θ y go/no-go |
| Autorización y datos de Azure | F9: despliegue del portal y del ejecutor |
| Fechas | Cronograma contra la semana 9 |

## 5. Resumen

- **Hoy:** crear el almacén (1) y pasarme los repositorios (2).
- **Esta semana:** corregir los documentos (§3), enviar el correo al CEI (3) y pedirle al asesor lo de §1.
- **Antes de la semana 7:** sesión de etiquetado (6) y segunda persona que anote (5).
- **Antes de la semana 9:** validación de los jueces (4) y Azure (8).
