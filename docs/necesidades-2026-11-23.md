# Lo que necesitamos para terminar (23 de noviembre de 2026)

**Responde a:** *Contenido desarrollado y orientación del asesor* (22 de noviembre de 2026)
**Estado del sistema:** versión 0.11.0, 685 pruebas automáticas en verde.

## 1. Lo que ya quedó integrado de su entrega

| Contenido | Estado |
|---|---|
| Formas A y B (T1 a T3) | En el almacén, fuera de Git. Las 6 soluciones de referencia pasan sus 60 casos con el corrector del sistema |
| 8 bloques de estructuras de datos | Cargables. Las 24 soluciones pasan sus 120 casos con el mismo ejecutor que usarán los estudiantes, y cada ejemplo resuelto devuelve el resultado que muestra |
| Bloques del prototipo | Retirados: el sistema ya no permite validarlos ni cargarlos en el portal |
| Valores provisionales | Aplicados: el informe dice «estimación incierta» si el intervalo mide entre 0,3 y 0,5, y «muy incierta» si mide más; ECE ≤ 0,10; caída LOAO ≤ 0,10; 5 s por envío |

**Sobre los nombres de campo:** no coincidían con los del sistema, pero en vez de convertir sus archivos adapté el sistema para que lea **su formato tal cual**. Puede seguir escribiendo los bloques exactamente igual.

## 2. Un hallazgo que necesita su confirmación

La alarma de solapamiento (D21) tenía un umbral de 0,5 de parecido de enunciado y **no detectaba ninguno** de los tres solapamientos que usted identificó entre la prueba y los bloques del prototipo. Medí los parecidos con el banco real:

| Pares | Parecido de enunciado |
|---|---|
| Los 3 solapamientos que usted identificó (en las dos formas) | 0,20 a 0,29 |
| Todos los demás pares | 0,15 como máximo |

Siguiendo su método de P10 (calibrar con el primer banco real y dejar el umbral bajo), lo fijé en **0,20**. Con los 8 bloques nuevos marca 3 pares:

| Ítem | Ejercicio del bloque | Parecido |
|---|---|---|
| A/T3 y B/T3 | `ed-s1-2-e3` (`agrupar_por_valor`) | 0,24 y 0,25 |
| B/T2 | `ed-s2-2-e1` (`es_creciente`) | 0,21 |

A mi juicio son falsas alarmas: comparten palabras de instrucción («escribe», «recibe», «lista», «valores»), no la tarea.

**Necesito que confirme:**
1. el umbral de 0,20, que revisaremos cuando lleguen los bloques de recursión y excepciones;
2. que los jueces revisen estos 3 pares con la pregunta 4 de su lista.

## 3. Lo que necesitamos del asesor

En el orden de prioridad que usted propuso:

| # | Entrega | Detalle |
|---|---|---|
| 1 | **8 bloques de excepciones** | Mismo formato que los de estructuras de datos, **con su archivo de soluciones** (`soluciones_excepciones.py`) |
| 2 | **8 bloques de recursión** | Igual, con `soluciones_recursion.py` |
| 3 | **6 enunciados de la sesión de etiquetado** | 2 por concepto, con 2 o 3 funciones cada uno, distintos de la prueba y de los bloques. Incluir las tres instrucciones fijas para C2 |
| 4 | **Consentimientos y convocatoria** | El consentimiento del estudio y el de la sesión de etiquetado, ambos con versión `v1`. La convocatoria debe exigir el repositorio con historial Git y los correos de commit |
| 5 | **Confirmaciones** | El umbral de solapamiento (§2) y, cuando lleguen los datos de SP-03 y de la pieza 7, los valores provisionales de §1 |

**Para que cada bloque pase la verificación automática** (lo que ya cumplen los de estructuras de datos):
- 3 ejercicios en orden `facil`, `medio`, `dificil`, con `id` de hasta 20 caracteres que no se repitan entre bloques;
- el código del ejemplo termina con la llamada que muestra y su resultado en un comentario;
- una solución por ejercicio en el archivo de soluciones, con el mismo nombre de función;
- sin diccionarios con claves numéricas en los casos;
- sin los temas que su orientación marca como isomorfos de la prueba.

## 4. Lo que necesita hacer el investigador

| # | Tarea | Para qué | Para cuándo |
|---|---|---|---|
| 1 | Elegir **de 5 a 10 repositorios** para SP-06 (propios o públicos de cursos), con sus correos de commit | Saber si m = 5 deja suficientes conceptos calculables | Antes de la semana 4 |
| 2 | Completar y **enviar el correo al CEI** (autorización escrita de Azure y plazo de conservación) | D14 y D13 | Antes del despliegue |
| 3 | **Crear el almacén cifrado** y mover ahí el banco de la prueba y el zip de la entrega del asesor | El banco real hoy está sin cifrar en la máquina | Cuanto antes |
| 4 | Conseguir a la **segunda persona que anote** para SP-05 | κ ≥ 0,70 por concepto (D7) | Después de SP-06 |
| 5 | Organizar a los **jueces**: formas A y B, 24 bloques y los 3 pares de §2 | HE3 y D21 | Antes de la semana 9 |
| 6 | Organizar la **sesión de etiquetado** y la generación de C2, cuando estén los enunciados | Corpus para la pieza 7 | Antes de la semana 7 |
| 7 | Pasar las **fechas reales** de cada semana del estudio | Cronograma y fecha de inicio de la intervención | Cuanto antes |
| 8 | Definir la **suscripción y región de Azure** | Despliegue (F9) | Antes de la semana 9 |

## 5. Lo que hago yo cuando llegue cada cosa

| Llega | Hago |
|---|---|
| Repositorios | SP-06: fragmentos por concepto, tiempo de análisis e informe para el asesor |
| Bloques nuevos | Integrarlos, verificarlos con sus soluciones y correr la alarma de solapamiento |
| Anotaciones | SP-05: kappa, concordancia regla–consenso y congelar `conceptos-v1` |
| Corpus | Pieza 7: evaluación por autor, calibración, θ y decisión go/no-go |
| Autorización y Azure | F9: despliegue del portal y del ejecutor, y verificar la red interna y la IP detrás del proxy |
| Fechas | Cronograma contra la semana 9 |

## 6. Camino crítico

```text
Repositorios ──► SP-06 ──► SP-05 ──► reglas congeladas ─┐
Enunciados ──► sesión de etiquetado + C2 ──► pieza 7 ──► go/no-go (sem. 7) ──► congelación ──► pretest
Bloques de excepciones y recursión ──► jueces ──► validación ──────────────────────────────► semana 9
Autorización CEI ──► F9 (Azure) ──────────────────────────────────────────────────────────► semana 9
```

Lo que más destraba hoy son **los repositorios para SP-06** (pueden cambiar m y los criterios de inclusión) y **los bloques de excepciones**.
