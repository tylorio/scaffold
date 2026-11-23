# Decisiones del asesor (23 de noviembre de 2026)

**Responde a:** *Lo que necesitamos para terminar* (23 de noviembre de 2026, versión 0.11.0)
**Numeración:** sigue la de los documentos anteriores (D1 a D21).
**Nota del investigador (2026-11-23):** en esta copia se omitieron, por D21, las frases que describen los ítems de la prueba. Lo demás está igual que el original.

## 1. Confirmaciones que pediste

### D22. Umbral de la alarma de solapamiento: confirmado en 0,20, como filtro y no como veredicto

Confirmo 0,20. La alarma no bloquea ni aprueba nada por sí sola: todo par marcado va a los jueces (D23), y solo ellos deciden si un ejercicio se cambia.

Antes de enviarte los bloques nuevos medí el parecido de enunciados por mi cuenta. Usé TF-IDF con coseno, que no es necesariamente tu métrica, así que tus números pueden variar un poco. Espero que tu alarma marque estos pares:

| Ítem | Ejercicio | Parecido (mi medida) | Mi lectura |
|---|---|---|---|
| A/T2 y B/T2 | `rec-s3-2-e3` (`combinaciones_suma`) | 0,24 y 0,23 | Falsa alarma: comparten "lista", "devuelve" y "ordenada" [omitido en esta copia: describe un ítem de la prueba (D21); el original está junto al banco, en el almacén] |
| A/T1 | `rec-s3-2-e1` (`subconjuntos`) | 0,20 | Falsa alarma: comparten "lista" y "elementos" |

Mantén el umbral en 0,20 después de integrar estos bloques, aunque marque más pares: revisar un par de más les cuesta a los jueces un minuto, y un solapamiento que se escapa invalida un ítem de la prueba.

**Agrega una segunda alarma sobre las soluciones.** El parecido de enunciados detecta palabras compartidas, no tareas compartidas. Lo que de verdad importa es si la solución de un bloque sirve, cambiando nombres, para resolver un ítem. Para medirlo, normalicé las soluciones (nombres a `ID`, literales a `LIT`) y comparé trigramas de tokens con Jaccard:

| Ítem | Ejercicio | Parecido de soluciones | Qué hice |
|---|---|---|---|
| A/T3 y B/T3 | `exc-s3-1-e3`, primera versión (`procesar_lotes`) | 0,33 | **Lo cambié.** Su solución tenía la misma forma que la de T3 [omitido en esta copia: describe un ítem de la prueba (D21); el original está junto al banco, en el almacén], aunque el enunciado no se pareciera (0,13). Ahora el ejercicio es `resumen(lotes)` y trata de en qué nivel se captura el error, que es el tema del bloque |
| A/T3 y B/T3 | `exc-s4-1-e3` (`procesar_inscripciones`) | 0,32 | Lo dejé, pero va a los jueces [omitido en esta copia: describe un ítem de la prueba (D21); el original está junto al banco, en el almacén] |
| A/T3 y B/T3 | `exc-s2-1-e1` (`validar_nota`) | 0,32 | Lo dejé: comparte solo un modismo, no la tarea [omitido en esta copia: describe un ítem de la prueba (D21); el original está junto al banco, en el almacén] |

Esta segunda alarma encontró lo que la primera no veía. Propongo calibrarla igual que la primera (tu método de P10): mídela con los tres solapamientos del prototipo, que ya conoces, y fija el umbral un poco por debajo del menor de ellos. Mientras no tengas esos datos, usa 0,30 como valor provisional.

### D23. Los jueces revisan los pares marcados con la pregunta 4

Sí. Los jueces revisan con la pregunta 4 de su lista ("¿Alguno de estos ítems, o uno equivalente, aparece en el banco de refuerzo?") estos pares:

- los 3 que marcó tu alarma: A/T3 y B/T3 con `ed-s1-2-e3`, y B/T2 con `ed-s2-2-e1`;
- los que marque tu alarma con los bloques nuevos (espero al menos los dos de D22);
- los que marque la alarma de soluciones, si la implementas antes de la validación; si no, por lo menos `exc-s4-1-e3` y `exc-s2-1-e1` con T3.

Para que las respuestas sean comparables, cada juez clasifica cada par en una de tres categorías:

| Respuesta | Qué significa | Qué se hace |
|---|---|---|
| Misma tarea | Quien resolvió el ejercicio del bloque podría reutilizar su solución en el ítem cambiando nombres | Se reemplaza el ejercicio del bloque |
| Misma habilidad, otra tarea | Practican lo mismo, pero la solución de uno no resuelve el otro | Se deja. Es lo que debe hacer un refuerzo |
| Sin relación | — | Se deja |

Basta con que uno de los jueces responda "misma tarea" para reemplazar el ejercicio. Reemplazar un ejercicio del bloque cuesta poco; reemplazar un ítem de la prueba, después del piloto, cuesta mucho.

### Valores provisionales (§1 de tu documento)

Siguen como están (intervalo incierto o muy incierto, ECE ≤ 0,10, caída LOAO ≤ 0,10, 5 s por envío) hasta que lleguen los datos de SP-03 y de la pieza 7. Los confirmaremos o corregiremos en un documento nuevo.

## 2. Decisiones nuevas que salen de esta entrega

### D24. C2 usa tres estilos de instrucción, no cuatro

`07-ml-evaluacion.md` §1.4 tiene cuatro estilos (P1 a P4). Pasan a ser los tres de `enunciados-sesion-etiquetado-v1.md` §4: **B** (breve), **C** (enunciado completo) y **E** (como estudiante).

- **Sale P3** ("con comentarios explicativos"). La densidad de comentarios y la presencia de docstrings son rasgos del clasificador. Si le pedimos comentarios al asistente, el clasificador aprende a reconocer nuestra instrucción, no al asistente.
- **Sale P4** ("corregir un intento parcial erróneo"). La salida mezcla un intento que escribimos nosotros con lo que escribe el asistente, así que la etiqueta de autor no queda limpia. Es más cercano a C3 que a C2.
- **Entra B**, porque es la forma más común en que se pide código con prisa y la que deja al asistente más libre en estilo.

El tamaño orientativo pasa a 6 tareas × 3 a 4 asistentes × 3 estilos × 2 repeticiones = **108 a 144 salidas**. Actualiza la tabla de 07 §1.4.

### D25. En la sesión de etiquetado, el bloque sin IA va siempre primero

`07` §1.3 dice que el orden se contrabalancea con un cuadrado latino. Lo cambio en un punto: **qué tarea va con IA** y **el orden de los conceptos** se siguen contrabalanceando (tabla de §2 del documento de la sesión), pero la **condición** tiene un orden fijo: primero sin IA, luego con IA.

Si alguien resuelve una recursión con IA y luego la otra sin IA, su código "humano" llega influido por lo que acaba de ver del asistente, y la etiqueta `humano` es la base de todo el corpus. El costo es que el cansancio cae siempre sobre la condición con IA. Eso afecta poco, porque en esa condición el código lo escribe sobre todo el asistente. Se declara como limitación.

### D26. Un solo texto por enunciado de la sesión (sin versiones A y B)

`07` §1.3 pide una versión A y una B de cada enunciado para contrabalancear. Con la tabla de asignación de D25, cada enunciado ya aparece la mitad de las veces con IA y la otra mitad sin IA, que es lo que las versiones buscaban. Dos versiones duplicarían el trabajo de SP-05 (comprobar que cada enunciado produce funciones del concepto previsto) sin ganar nada. Actualiza 07 §1.3.

### D27. En la sesión, los commits se hacen con una identidad de sesión

Cada repositorio de la sesión se configura con `S07` y `s07@sesion.local`, no con el nombre ni el correo de la persona. Así el corpus no contiene correos personales y `autor_id` es directamente el código de sesión. El supervisor lo deja configurado antes de empezar (§3 del documento de la sesión).

### D28. Consentimientos v1

Los dos consentimientos y la convocatoria van en versión `v1` con los campos `[PENDIENTE]` marcados. Cubren todo lo que piden 06 §6 y 08 §5, incluido lo que me pediste destacar: la entrega del repositorio **con historial Git** (en el consentimiento, en los requisitos y con instrucciones para comprobarlo en la convocatoria) y los **correos de commit** con el filtro por autor.

Hay tres puntos que el CEI tiene que conocer. Agrégalos al correo que ya tienes preparado (`correo-CEI-autorizacion-azure.md`) o envíalos junto con la solicitud:

1. **Retiro después de congelar el corpus.** El consentimiento de la sesión dice que, si alguien se retira después de la congelación, su código se borra pero no se puede quitar del modelo ya entrenado. Es la verdad técnica y es mejor que el CEI la acepte o la objete ahora.
2. **Repositorios grupales.** Solo se analizan las funciones del participante, pero el clon que se guarda en el almacén incluye el código de sus compañeros, que no firmaron nada. Hasta el fin del análisis ese código queda cifrado y no se analiza. Pregunta si eso es aceptable o si hace falta avisar a los compañeros.
3. **Conservación del corpus de la sesión.** La opción "también para investigaciones futuras" (§6 del consentimiento de la sesión) necesita un plazo y la conformidad del comité.

## 3. Notas para integrar los bloques

- **16 bloques nuevos** (8 de excepciones y 8 de recursión), 48 ejercicios y 240 casos, en el mismo formato que los de estructuras de datos. Verifiqué los casos como lo hace el corrector: pasan por JSON, no hay diccionarios con claves numéricas y los `lanza` usan solo excepciones de Python (`ValueError`, `TypeError`, `ZeroDivisionError`, `TimeoutError`, `RuntimeError`).
- **Funciones auxiliares repetidas.** En `soluciones_excepciones.py` algunas funciones y clases auxiliares aparecen en más de un ejercicio (`precio_valido`, `inscribir`, `CupoLleno`, `AlumnoDuplicado`). Las dejé idénticas a propósito y comprobé que el **módulo completo**, importado de una vez, pasa los 120 casos. Si las cambias en un ejercicio, cámbialas en todos.
- **Tres ejercicios dependen del límite de 5 s.** `fib_memo(70)`, `caminos_memo(15, 15)` y `particiones(60)` no terminan a tiempo sin memoización, y eso es parte del ejercicio: el enunciado dice que deben responder en menos de un segundo. Si cambias el límite del ejecutor, avísame para revisarlos.
- **Restricciones que las pruebas no comprueban.** Algunos enunciados dicen "sin bucles", "sin usar `max`" o "sin `**`". Las pruebas solo miran el resultado, así que una solución sin recursión también pasa. No propongo revisar el AST: el refuerzo no es una evaluación, y una regla que rechaza soluciones correctas frustra más de lo que enseña. Que los jueces opinen si los enunciados lo dicen con suficiente claridad.
- **La profundidad de recursión** de los casos no pasa de 70 llamadas, muy por debajo del límite de Python.
