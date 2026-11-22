# Consultas al asesor tras implementar sus decisiones

**Proyecto:** Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software e Ingeniería de Sistemas de la USIL, 2026
**Autor:** Juan Pablo Zavala Valle
**Fecha:** 22 de noviembre de 2026
**Responde a:** `decisiones-asesor-2026-11-21.md` (D1–D18) y `decisiones-asesor-2026-11-21b.md` (R1–R5, D19–D21, S1)

---

## 1. Avance

Ya están construidas las seis primeras piezas del orden de trabajo que usted fijó (sección 4 del documento 21b). Cada una tiene sus pruebas automatizadas; en total pasan 439.

| Pieza | Qué quedó funcionando | Decisiones |
| --- | --- | --- |
| 1 | Clave secreta y `DEBUG` leídos del entorno; la clave anterior ya no se usa | S1 |
| 2 | Reglas de conceptos v1 con la lista cerrada de estructuras de datos, la salida `indeterminado`, la recursión mutua y sobre atributo, y la definición amplia para el análisis de sensibilidad | D5, D6, R4 |
| 3 | Filtro por autor: solo se analizan las funciones del participante; de su correo se guarda solo una huella (HMAC) | D19 |
| 4 | Clasificador solo con estilo y estructura; índice de delegación por historial calculado aparte | D9 |
| 5 | Asignación escalonada A/B/C, modo exploratorio, orden AB/BA por bloques, congelación única antes del pretest; sin análisis post | D2, D3, D16, R2, R3, R5 |
| 6 | Banco A/B de la prueba, corrector de T1–T3 con las métricas de D1, CSV sin datos de la asignación, control de solapamiento con el refuerzo | D1, D16, D17, D21 |

Al implementarlas surgieron **diez puntos** que sus decisiones no fijan del todo. En cada uno tomé una opción para no detener el trabajo, y está escrita en el código y en la documentación. Le pido que confirme cada una o la corrija.

**Cómo responder:** basta con una línea por punto, "Confirmo" o "Cambiar a…". Ninguno obliga a rehacer trabajo: todos se corrigen en el código en poco tiempo.

---

## 2. Puntos que afectan la medición o el análisis

Son los más importantes: cambian números de la tesis.

### P1. HE4 en los casos B y C

**Contexto.** HE4 dice "en los conceptos **débiles**…". Con la asignación escalonada (D2), en los casos B y C, y en todo el modo exploratorio, los conceptos reforzados pueden no ser débiles. Un participante del caso C puede no tener ningún concepto débil.

**Lo que propongo.** La variable operativa de HE4 pasa a ser el **desempeño en los conceptos reforzados**. En el caso A, en modo confirmatorio, coincide con los débiles, que es lo que dice el plan. Así HE4 se calcula para toda la muestra, igual que HE5.

**Alternativa.** Calcular HE4 solo con los participantes del caso A y reportar el resto como exploratorio. Es más fiel al texto actual, pero reduce el n.

**Efecto en el plan:** si confirma, hay que ajustar la redacción de HE4 o su operacionalización en 8.3.

### P2. Definición de las métricas de calidad de D1

**Contexto.** D1 compara "complejidad_ciclomática(sol)" y "líneas(sol)" con la solución de referencia, pero no dice cómo se miden cuando la solución tiene varias funciones.

**Lo que implementé:**
- **Complejidad:** la complejidad ciclomática **media por función**, que es lo que dice el plan en 8.3.2. Se calcula igual para la solución y para la referencia.
- **Líneas:** las líneas de código fuente de **toda la solución**, sin líneas en blanco ni comentarios.

**Alternativas.** La complejidad máxima en lugar de la media, o contar solo las líneas de la función pedida.

### P3. Qué es "HE2b"

**Contexto.** R3 dice que en modo exploratorio "HE1 y HE2b pasan a exploratorias". El plan solo tiene HE2.

**Lo que asumí.** HE2b es el análisis de HE2 con el **IDC global**, que el plan llama "análisis complementario" en la tabla de pruebas estadísticas. HE2 con el autorreporte sigue siendo confirmatoria en los dos modos.

### P4. Fragmentos triviales y análisis de sensibilidad

**Contexto.** Una función trivial (una sola sentencia sin ningún concepto) no cuenta para el IDC. "Sin ningún concepto" se decide con la regla **v1**. Por eso una función como `return [x * 2 for x in lista]` es trivial con v1, aunque la definición amplia la contaría como estructura de datos.

**Lo que implementé.** El conjunto de fragmentos es **el mismo** para las dos definiciones. La definición amplia solo cambia qué concepto tiene cada fragmento, no cuáles entran. Así la comparación de sensibilidad mide solo el efecto de la definición, no un cambio en la muestra de funciones.

### P5. Participante ausente frente a ítem sin respuesta

**Lo que implementé:**
- Si un participante **entregó** su carpeta en la sesión pero le falta un ítem, ese ítem vale **0 %** (`sin_respuesta`).
- Si un participante **no tiene carpeta**, se considera ausente y no se registra ningún puntaje. Queda como dato faltante, no como cero.

### P6. Medición de la adherencia (D20)

**Contexto.** D20 dice: "ejercicios intentados (o resueltos; definir uno y registrarlo) ÷ ejercicios liberados".

**Lo que propongo.** La adherencia principal es **ejercicios intentados ÷ liberados**. "Resueltos ÷ liberados" se reporta como medida secundaria. El motivo es que la adherencia mide exposición a la intervención; si se midiera con los resueltos, se mezclaría con el desempeño, que es la variable dependiente.

*Esto todavía no está implementado: corresponde a la pieza 9.*

---

## 3. Puntos de las reglas de asignación de conceptos

### P7. Ampliaciones de la lista cerrada de estructuras de datos

D5 da ejemplos con nombres en español. Implementé así el elemento 8 de la lista:

| Elemento 8 | Lo implementado |
| --- | --- |
| Nodos enlazados | `self.siguiente`, `self.izquierda`, `self.derecha` **y también** `anterior`, `izquierdo`, `derecho` y sus equivalentes en inglés: `next`, `prev`, `left`, `right`. Muchos estudiantes nombran en inglés |
| Clase contenedora propia | Solo los métodos que nombra D5: `push`, `pop`, `__len__`, `__iter__`. **No** cuentan nombres en español como `apilar` o `encolar` |

¿Confirma las dos? La segunda deja fuera clases contenedoras con nombres en español; la anotación de D7 medirá cuántas.

### P8. Falso positivo conocido de la recursión sobre atributo

**Contexto.** D6 define la recursión sobre atributo como "el mismo nombre de método invocado sobre un atributo". Con esa regla, un método `guardar` que llama a `self.repositorio.guardar()` cuenta como recursión, aunque solo delega en otro objeto.

**Lo que implementé.** La regla tal como está en D6. Lo declaro como limitación, y la anotación de D7 medirá cuánto pesa. ¿Lo acepta así, o prefiere exigir además que la clase tenga atributos de nodo (`izquierda`, `siguiente`…)?

---

## 4. Puntos operativos

### P9. Repositorios sin historial Git

**Lo que implementé.** Sin historial Git no se puede saber de quién es cada función, así que **el análisis se rechaza** (D19). Es coherente con el criterio de inclusión, que ya exige un mínimo de commits. ¿Confirma que un repositorio entregado sin historial queda excluido?

### P10. Umbrales provisionales

Estos valores no los fija ninguna decisión. Los dejé marcados como provisionales, para fijarlos con datos antes del diagnóstico:

| Umbral | Valor provisional | Cómo propongo fijarlo |
| --- | --- | --- |
| Índice por historial: tamaño de inserción que cuenta como "grande" | 30 líneas | Con el corpus de la sesión de etiquetado: la mediana de inserción en las tareas hechas con IA |
| Control de solapamiento (D21): similitud de enunciados | 0,5 | Con los primeros bancos reales, revisando a mano los pares que marque |
| Control de solapamiento (D21): similitud de soluciones | 0,8 | Ídem |

¿Está de acuerdo con el método?

---

## 5. Pendientes de la sección anterior que siguen abiertos

- **Autorización escrita del alojamiento en Azure (D14).** Necesito su correo o una constancia para el Anexo F.
- **Ítems reales de las formas A y B.** El sistema ya los corrige. Falta escribir los ítems isomorfos, con su solución de referencia y sus casos de prueba, y que los validen los jueces. En el repositorio hay un banco de ejemplo que sirve de plantilla.
- **Los 24 bloques de refuerzo (D20).** Es trabajo de autoría que debe validarse antes de la semana 9.

---

## 6. Resumen para responder

| N.º | Punto | Mi propuesta |
| --- | --- | --- |
| P1 | HE4 en los casos B y C | Variable operativa: desempeño en los conceptos reforzados |
| P2 | Métricas de D1 | Complejidad media por función; líneas de código de toda la solución |
| P3 | HE2b | El análisis de HE2 con el IDC global |
| P4 | Triviales y sensibilidad | El mismo conjunto de fragmentos para v1 y para la definición amplia |
| P5 | Ausente frente a sin respuesta | Ítem faltante = 0 %; participante ausente = dato faltante |
| P6 | Adherencia | Intentados ÷ liberados; resueltos como dato secundario |
| P7 | Nombres en estructuras de datos | Nodos también en inglés; clase contenedora solo con los nombres de D5 |
| P8 | Recursión sobre atributo | Regla de D6 tal cual, con su falso positivo declarado como limitación |
| P9 | Sin historial Git | Excluido |
| P10 | Umbrales provisionales | Fijarlos con datos antes del diagnóstico, con los métodos de la tabla |
