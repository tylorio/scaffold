# Respuestas del asesor a las consultas del 22 de noviembre

**Proyecto:** Sistema de detección de dependencia hacia código generado por IA con refuerzo personalizado (tesis de Juan Pablo Zavala Valle, USIL)
**Responde a:** *Consultas al asesor tras implementar sus decisiones* (P1–P10)
**Complementa a:** `decisiones-asesor-2026-11-21.md` (D1–D18) y `decisiones-asesor-2026-11-21b.md` (R1–R5, D19–D21, S1), que no se modifican
**Fecha:** 22 de noviembre de 2026
**Ubicación sugerida:** `docs/decisiones/decisiones-asesor-2026-11-22.md`

---

## 0. Resumen

Buen avance: las piezas 1 a 6 del camino crítico están hechas, con 439 pruebas en verde. Las diez opciones que tomaste están bien razonadas. Confirmo siete; **cambio tres (P7, P8 y P10)** y agrego precisiones en P5 y P6. Todos los cambios son pequeños y deben quedar hechos **antes de SP-06**, porque P7 y P8 cambian qué fragmentos entran en cada concepto.

| N.º | Punto | Respuesta |
|---|---|---|
| P1 | HE4 en los casos B y C | **Confirmo**: HE4 = desempeño en los conceptos reforzados. El caso A se reporta además como subgrupo |
| P2 | Métricas de D1 | **Confirmo**: complejidad media por función; líneas de toda la solución |
| P3 | HE2b | **Confirmo**: HE2a = autorreporte (confirmatoria siempre); HE2b = IDC global |
| P4 | Triviales y sensibilidad | **Confirmo**: el mismo conjunto de fragmentos para v1 y para la definición amplia |
| P5 | Ausente frente a sin respuesta | **Confirmo**, con una precisión sobre qué análisis pierde a cada ausente |
| P6 | Adherencia | **Confirmo**: intentados ÷ liberados, con una definición precisa de "intentado" |
| P7 | Nombres en estructuras de datos | Nodos en inglés: **confirmo**. Clase contenedora: **cambiar** a una lista bilingüe |
| P8 | Recursión sobre atributo | **Cambiar**: exigir un atributo de nodo |
| P9 | Sin historial Git | **Confirmo**: queda excluido, y se avisa en la convocatoria |
| P10 | Umbrales provisionales | Solapamiento: **confirmo**. Índice por historial: **cambiar** el método |

---

## 1. Puntos que afectan la medición o el análisis

### P1. HE4 se calcula sobre los conceptos reforzados — Confirmo

- **Variable operativa de HE4:** puntaje promedio de los conceptos **reforzados** de cada participante, en el pretest y el postest. Se calcula para toda la muestra, igual que HE5.
- **Análisis adicional:** HE4 restringido al caso A en modo confirmatorio, reportado como subgrupo. Es el caso en el que "reforzado" coincide con "débil", y conecta el resultado con la lógica del sistema.
- **Redacción para el plan (8.3 y la hipótesis):** *"HE4: en los conceptos reforzados, los estudiantes obtienen un desempeño mayor en el postest que en el pretest. En el caso A, los conceptos reforzados son conceptos débiles; en los casos B y C, son conceptos elegibles asignados por sorteo."*

### P2. Métricas de calidad de D1 — Confirmo

- **Complejidad:** media por función, calculada igual para la solución y para la referencia (es coherente con el plan, 8.3.2).
- **Líneas:** líneas de código de toda la solución, sin líneas en blanco ni comentarios.
- **Nota para la tesis:** con la media, un estudiante que descompone su solución en funciones auxiliares no se penaliza, mientras que una función monolítica más compleja que la referencia sí. Es el comportamiento deseado, porque descomponer es buena práctica. Escríbelo en la definición del indicador.

### P3. HE2b — Confirmo

- **HE2a:** HE2 con la dependencia autorreportada. Es **confirmatoria en los dos modos**.
- **HE2b:** HE2 con el **IDC global**, lo que el plan llama "análisis complementario". En modo exploratorio pasa a exploratoria, junto con HE1.
- Usa estos dos nombres en el código, la exportación y la tesis.

### P4. Triviales y análisis de sensibilidad — Confirmo

- La trivialidad se decide con v1 y **el conjunto de fragmentos es el mismo** para las dos definiciones. Así, la comparación aísla el efecto de la definición.
- **Para la tesis:** declarar que la definición amplia cambia la asignación de conceptos de los fragmentos ya incluidos, pero no la inclusión.

### P5. Ausente frente a ítem sin respuesta — Confirmo, con una precisión

- Ítem faltante en una carpeta entregada: **0 %** (`sin_respuesta`). Lo mismo para un ítem Q en blanco: 0 en la rúbrica.
- Participante sin carpeta: **ausente** y dato faltante, nunca cero.
- **Precisión sobre los análisis:**
  - **Ausente en el pretest:** queda fuera de todo lo que use la prueba (HG, HE2, HE4, HE5). Si completó el cuestionario y el análisis del repositorio, **sigue en HE1**.
  - **Ausente en el postest:** queda fuera de HG, HE4 y HE5 (análisis de casos completos), pero **conserva sus datos del pretest para HE1 y HE2**.
  - Reportar en el Capítulo V un **diagrama de flujo de participantes**: convocados → incluidos → con pretest → con postest, con los motivos de pérdida en cada paso.
  - No se imputan datos.

### P6. Adherencia — Confirmo

- **Principal:** ejercicios **intentados** ÷ ejercicios liberados. **Secundaria:** resueltos ÷ liberados.
- **Definición de "intentado":** al menos **un envío ejecutado** de una solución a ese ejercicio. Abrir el material no cuenta, y varios envíos al mismo ejercicio cuentan como uno.
- El análisis de sensibilidad "adherencia < 50 %" usa la medida principal.

---

## 2. Reglas de asignación de conceptos

> **Versión.** Ninguna regla se ha aplicado todavía a datos reales, así que los ajustes de P7 y P8 entran en **`conceptos-v1`** (no hace falta una v2). A partir de SP-06 la versión queda congelada y cualquier cambio posterior abre una versión nueva.

### P7. Nombres en estructuras de datos

**Nodos enlazados — Confirmo.** Se aceptan los nombres en español e inglés: `siguiente`, `anterior`, `izquierda`, `izquierdo`, `derecha`, `derecho`, `next`, `prev`, `left`, `right`. Agregar también `hijo`, `hijos`, `children`, `padre` y `parent`, que son comunes en árboles.

**Clase contenedora — Cambiar.** Dejar fuera los nombres en español contradice tu propia observación de que muchos estudiantes nombran en un idioma y otros en otro, y crea un sesgo sistemático según cómo programe cada uno. La lista cerrada pasa a ser:

| Operación | Nombres que cuentan |
|---|---|
| Pila | `push`, `pop`, `peek`, `apilar`, `desapilar`, `cima`, `tope` |
| Cola | `enqueue`, `dequeue`, `encolar`, `desencolar`, `frente` |
| Protocolo de contenedor | `__len__`, `__iter__`, `__getitem__`, `__contains__` |

Sigue siendo una lista cerrada: solo cuentan estos nombres. La anotación de D7 medirá si falta alguno.

### P8. Recursión sobre atributo — Cambiar

**Problema.** Con la regla actual, la delegación (`guardar` → `self.repositorio.guardar()`) cuenta como recursión. Ese patrón es **muy frecuente** en los proyectos orientados a objetos de la carrera (servicios, repositorios, capas de Django), así que el falso positivo no sería marginal: inflaría el concepto de recursión justo en los proyectos más grandes.

**Regla nueva.** La llamada `self.<atributo>.<método>()` cuenta como recursión solo si se cumplen **las dos** condiciones:

1. `<método>` tiene el mismo nombre que el método que lo contiene, y
2. `<atributo>` es un **atributo de nodo**: un nombre de la lista de P7 (`izquierda`, `derecha`, `siguiente`, `hijo`, `left`, `right`, `next`, `children`, etc.) **o** un atributo al que, dentro de la misma clase, se le asigna una instancia de esa misma clase (`self.izquierda = Nodo(...)` dentro de `class Nodo`).

También cuenta la iteración sobre una colección de nodos con el mismo método (`for h in self.hijos: h.recorrer()`).

**Pruebas que debes agregar:**
- `guardar` → `self.repositorio.guardar()`: **no** cuenta.
- `insertar` → `self.izquierda.insertar(x)`: **sí** cuenta.
- `recorrer` → `for h in self.hijos: h.recorrer()`: **sí** cuenta.

---

## 3. Puntos operativos

### P9. Repositorios sin historial Git — Confirmo

- Sin historial no se puede aplicar D19, así que **el repositorio queda excluido**. Es coherente con el criterio de inclusión.
- **Acción preventiva:** la convocatoria y el consentimiento deben decir claramente que el repositorio debe entregarse **con su historial** (enlace a GitHub o carpeta con `.git`), no como `.zip` del código. Si no, se van a perder participantes por algo evitable.
- Registrar el motivo de exclusión (`sin_historial`) para el diagrama de flujo de P5.

### P10. Umbrales provisionales

**Solapamiento (D21) — Confirmo el método.** Fijar los umbrales con los primeros bancos reales, revisando a mano los pares marcados. Como el control es una alarma y la decisión la toma una persona, conviene que los umbrales queden **bajos** (que marquen de más y no de menos).

**Índice por historial — Cambiar el método.** No calibres el umbral con la sesión de etiquetado: allí se pidió **un commit por tarea**, así que el tamaño de inserción es artificial por diseño. Es la misma razón por la que D9 sacó ese rasgo del clasificador. En su lugar:

- **Medida principal del índice (continua, sin umbral):** proporción de líneas propias del participante que entraron en commits de 30 o más líneas, **y** la media del logaritmo del tamaño de inserción de sus fragmentos. Se reportan las dos.
- **El umbral de 30 líneas** se mantiene como valor fijado *a priori* y se declara así en la tesis. Como análisis de sensibilidad, se repite con 15 y con 60.
- El índice es exploratorio (D9): no hace falta optimizarlo, solo fijarlo antes de ver los datos.

---

## 4. Pendientes de la sección 5

| Pendiente | Respuesta |
|---|---|
| Autorización escrita del alojamiento en Azure (D14) | Debe emitirla **quien dio la autorización verbal** (CEI-USIL u oficina correspondiente), no el asesor. Pedirla por correo, citando qué datos se alojan (solo códigos anónimos, asignación, IDC agregado y registros de uso), la región y que la tabla de correspondencia nunca sale de la máquina del investigador. La respuesta va al Anexo F. |
| Ítems reales de las formas A y B | Prioridad alta: sin ellos no hay validación de jueces, piloto ni pretest. Escribirlos en **pares isomorfos** (misma estructura y casos límite, distinto contexto y valores) sobre la plantilla del repositorio, y verificar el solapamiento (D21) contra el banco de refuerzo a medida que se escribe. |
| 24 bloques de refuerzo (D20) | Escribirlos en paralelo, concepto por concepto. Orden sugerido: estructuras de datos, excepciones y recursión. La recursión es la que menos participantes tendrán como calculable, pero igual puede salir reforzada en los casos B y C. |

---

## 5. Cambios a llevar al código y a los documentos

| Dónde | Cambio |
|---|---|
| `conceptos-v1` | P7 (lista bilingüe de contenedores y nodos con `hijo`/`children`/`padre`/`parent`); P8 (recursión sobre atributo solo con atributo de nodo); pruebas nuevas de P8 |
| Exportación y análisis | Nombres `HE2a` y `HE2b`; HE4 sobre los reforzados y subgrupo del caso A; estado `ausente` frente a `sin_respuesta`; motivos de exclusión para el diagrama de flujo |
| Pieza 9 (portal) | Adherencia con "intentado" = al menos un envío ejecutado; medida secundaria de resueltos |
| Índice por historial | Dos medidas continuas; umbral de 30 líneas fijado *a priori*, con sensibilidad a 15 y 60 |
| Convocatoria y consentimiento | Exigir el repositorio con su historial Git |
| `plan.md` (próxima versión) | Redacción de HE4 (P1); definición de las métricas de calidad (P2); HE2a y HE2b (P3); tratamiento de ausentes y diagrama de flujo (P5); definición de adherencia (P6); reglas de P7 y P8 en la guía de conceptos; índice por historial (P10) |
