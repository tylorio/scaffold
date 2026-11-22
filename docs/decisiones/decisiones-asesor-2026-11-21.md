# Decisiones del asesor sobre el informe de avance

**Proyecto:** Sistema de detección de dependencia hacia código generado por IA con refuerzo personalizado (tesis de Juan Pablo Zavala Valle, USIL)
**Responde a:** Informe de avance para el asesor, 10 de noviembre de 2026 (sección 5)
**Fecha de las decisiones:** 21 de noviembre de 2026
**Uso:** este documento se agrega al repositorio (sugerido: `docs/decisiones/decisiones-asesor-2026-11-21.md`) y se cita como fuente cuando un requisito, ADR o sección del plan dependa de alguna de estas decisiones. Si una decisión cambia, se registra un documento nuevo; este no se edita.

---

## 1. Resumen

- **18 decisiones**, todas cerradas para el desarrollo. Ninguna bloquea la construcción del sistema.
- **Fuente de verdad del plan:** `docs/plan/plan.md` (la versión alineada con el código). Se mantiene la numeración de hipótesis de `plan.md`.
- **Pendientes administrativos (no bloquean el código):**
  - D14: obtener **por escrito** la autorización sobre el alojamiento de datos codificados en Azure.
  - D13: plazo de conservación de los CSV agregados, que fija el CEI-USIL.

---

## 2. Tabla de decisiones

| # | Tema (sección del informe) | Decisión | Implicación en el código | Estado |
|---|---|---|---|---|
| D1 | Puntaje por concepto y compuesto (5.1) | Ver la sección 3.1. Se fija por escrito antes del pretest. | No cambia el modelo de datos: se guardan los valores crudos por ítem y la solución de referencia de cada ítem por forma. La fórmula vive en el script de análisis, con versión. | Aprobada |
| D2 | Participantes sin dos conceptos débiles (5.2) | Regla de asignación escalonada (sección 3.2). Todos los participantes entran en el control intrasujeto. m se mantiene en 5. | Implementar los casos A, B y C en el módulo de asignación y guardar el caso de cada participante junto con la semilla. | Aprobada |
| D3 | Regla de sorteo (5.3, ADR-002) | Aprobada. El sorteo se hace después del diagnóstico y antes del pretest, con semilla registrada. Los calificadores no conocen la asignación. | Congelar la asignación con marca de tiempo anterior al pretest. La asignación no aparece en ninguna salida que vea un calificador. | Aprobada |
| D4 | Concepto de control | Lista de espera: el material del concepto de control se desbloquea después del postest. | Estado "desbloqueado tras el postest" para el concepto de control. | Aprobada |
| D5 | Definición de "estructuras de datos" (5.4) | Lista cerrada (sección 3.3). Validación por tres vías: sílabo del curso de Estructuras de Datos de la USIL y currículo ACM/IEEE, jueces expertos (V de Aiken) y anotación (κ). Se agrega un análisis de sensibilidad con una definición amplia. | Reescribir la regla de ED como versión 1, versionada. Calcular también el IDC con la definición amplia para el análisis de sensibilidad. | Aprobada |
| D6 | Resto de los casos límite (5.4) | Se aprueba la tabla del informe (sección 3.3), salvo la corrección sobre las comprensiones de lista. | Detectar la recursión mutua y la recursión sobre un atributo (mismo nombre de método invocado sobre un atributo). | Aprobada |
| D7 | Validación de las reglas de concepto | Ronda de calibración con 20 fragmentos. Luego 150 fragmentos con muestreo estratificado (al menos 30 positivos esperados por concepto). Acuerdo entre anotadores: κ de Cohen ≥ 0.70 por concepto. Reglas frente al consenso: precisión y recall por concepto. | Script de muestreo estratificado según la salida de las reglas y exportación ciega para los anotadores. | Aprobada |
| D8 | Código de IA editado a mano (5.5) | Se excluye del entrenamiento y se evalúa aparte. Lectura principal: **sigue siendo delegación** si el núcleo lo escribió el asistente. Se reportan las dos lecturas. | Etiqueta separada en el corpus ("IA editado") y métrica separada en la evaluación. | Aprobada |
| D9 | Rasgos de historial en el clasificador (sección 4 del informe) | Se **quita** el tamaño de inserción por commit de las características del clasificador, que queda solo con estilo y estructura. El índice de delegación por historial se calcula aparte, como medida exploratoria para HE1. | Eliminar la característica 8 del vector del clasificador y crear un cálculo independiente del índice por historial. | Aprobada |
| D10 | Umbrales del clasificador (5.7) | F1 ≥ 0.70 (según `plan.md`); tasa de falsos positivos al umbral θ ≤ 0.15; sensibilidad ≥ 0.60. θ se calibra en validación y la evaluación final se hace una sola vez en el conjunto de prueba. Los falsos positivos se reportan por nivel de calidad del código. | Criterio go/no-go en el protocolo F7 y reporte de falsos positivos estratificado por calidad. | Aprobada para el piloto |
| D11 | IDC durante la intervención (5.8) | El estudiante no ve su IDC en las semanas 9–12, solo los conceptos que trabaja. El IDC con su intervalo aparece en el informe personal al final. | El portal no muestra el IDC hasta después del postest. | Aprobada |
| D12 | Spikes antes del comité (5.6.1) | No se usan repositorios de compañeros antes de la aprobación del CEI-USIL. Solo código propio, generado o de conjuntos públicos. | SP-05 y SP-06 con repositorios públicos o propios. | Aprobada |
| D13 | Conservación de datos (5.6.2) | El código y todo lo derivado de los repositorios se elimina al terminar el análisis de datos. Los CSV agregados con código anónimo y sin código fuente se conservan como datos de investigación por el plazo que fije el CEI-USIL. | Borrado por participante (retiro) y borrado masivo al cierre. Exportación de CSV sin código fuente. | Aprobada; plazo pendiente del CEI |
| D14 | Alojamiento en Azure y Ley N.° 29733 (5.6.3) | Autorizado verbalmente. **Obtener la autorización por escrito** (correo o constancia) para el Anexo F y la sección de ética. Por buena práctica, la tabla de correspondencia código–nombre se mantiene solo en la máquina del investigador, cifrada. Se cita la Ley N.° 29733 en el plan. | La tabla de correspondencia nunca se sube al portal. La región de Azure es un parámetro de configuración documentado. | Aprobada; falta la evidencia escrita |
| D15 | Consentimiento de la sesión de etiquetado (5.6.4) | Documento aparte, presentado en la misma solicitud al CEI-USIL. Sus participantes quedan fuera de la muestra. | Marca de exclusión para los participantes del etiquetado y del piloto. | Aprobada |
| D16 | Equivalencia de las formas A y B (5.1) | Ítems isomorfos validados por los jueces. En el piloto: diferencia de medias menor que 1 punto y correlación entre formas reportada. En el estudio: la forma se usa como covariable. | Guardar la forma y el orden (A→B o B→A) de cada participante. | Aprobada |
| D17 | Exportación para el análisis | HE5 se analiza con t pareada (análisis principal) y con un modelo mixto como respaldo (sección 3.4). | CSV en formato largo (sección 3.4). | Aprobada |
| D18 | Numeración de hipótesis | Se mantiene la numeración de `plan.md`. | La matriz de trazabilidad de F1 sigue válida. | Aprobada |

---

## 3. Detalle de las decisiones

### 3.1 D1 — Fórmula del puntaje

Para cada concepto *k* (recursión, estructuras de datos, manejo de excepciones):

```
P_k = 0.5 × (T_k / 5) + 0.5 × Q_k − Pen_k          (escala 0–20; mínimo 0)

T_k   = porcentaje de casos de prueba superados en el ítem T de k (0–100)
Q_k   = puntaje de la rúbrica de comprensión del ítem Q de k (0–20; promedio de dos calificadores)
Pen_k = penalización por calidad (0 a 2 puntos), solo si T_k > 0:
        +1 si complejidad_ciclomática(sol) > complejidad_ciclomática(ref_k) + 2
        +1 si líneas(sol) > 2 × líneas(ref_k)

Compuesto:  D = (P_recursión + P_estructuras + P_excepciones) / 3
```

- La penalización se compara con la **solución de referencia de cada ítem**, no con un umbral absoluto.
- El Cap. V reporta por separado las tres dimensiones: corrección (T), comprensión (Q) y calidad (penalización).
- **Análisis de sensibilidad:** HG y HE4 recalculadas con Pen_k = 0.
- Los jueces expertos opinan sobre los pesos en la ficha de validación. La versión final se fija antes del pretest.

### 3.2 D2 — Regla de asignación escalonada

Definiciones: un concepto es **calculable** si tiene al menos m = 5 fragmentos atribuidos al participante. Es **débil** si es calculable y su IDC es mayor o igual que λ.

| Caso | Condición | Conjunto elegible para el sorteo |
|---|---|---|
| A | 2 o más conceptos débiles | Los conceptos débiles |
| B | Menos de 2 débiles y 2 o más calculables | Los conceptos calculables |
| C | Menos de 2 calculables | Los 3 conceptos |

En todos los casos se sortean **hasta 2 reforzados y al menos 1 de control** dentro del conjunto elegible. El conjunto elegible siempre tiene al menos 2 conceptos.

- La comparación de HE5 usa los **puntajes de la prueba**, que existen para los 3 conceptos en todos los participantes. Por eso nadie queda fuera de HE5.
- Se reporta cuántos participantes quedaron en cada caso. Análisis exploratorio: ¿la ganancia en el concepto reforzado es mayor en el caso A?
- **Frase para el plan (8.3.1, nota, o 9.2):** *"Entre los conceptos elegibles de cada participante, los conceptos reforzados (hasta dos) y el de control (al menos uno) se seleccionan por sorteo con semilla registrada antes del pretest, de modo que la asignación sea independiente del nivel inicial de cada concepto. Son elegibles los conceptos débiles; si hay menos de dos, los conceptos calculables, y si estos también son menos de dos, los tres conceptos evaluados."*
- **Limitación para declarar:** el concepto de mayor IDC puede quedar como control y recibir su refuerzo recién después del postest.

### 3.3 D5 y D6 — Guía de asignación de conceptos

**Principio:** el concepto se asigna cuando escribir el fragmento exige haber aplicado el concepto, no cuando la sintaxis solo lo roza.

**Estructuras de datos (versión 1).** El fragmento cuenta como ED si contiene al menos uno de estos elementos:

1. Un diccionario o conjunto construido **y consultado**: `d[k] = v`, `k in d`, `k in s`, `.get`, `.setdefault`.
2. Una comprensión de **diccionario** o de **conjunto**.
3. Ordenación o búsqueda: `sort`, `sorted`, `bisect`, `heapq`.
4. `collections`: `deque`, `Counter`, `defaultdict`.
5. Colecciones anidadas (lista de listas, diccionario de listas, etc.).
6. Aritmética de índices sobre **listas**: `a[i]`, `a[i + 1]`, intercambios `a[i], a[j] = a[j], a[i]`.
7. Operaciones de pila o cola: `pop`, `appendleft`.
8. Una clase contenedora propia: métodos `push`, `pop`, `__len__`, `__iter__`, o nodos enlazados (`self.siguiente`, `self.izquierda`, `self.derecha`).

**No cuentan como ED:**
- `append` usado solo para acumular dentro de un bucle;
- la **comprensión de lista** (equivale a acumular con `append`);
- indexar o rebanar **cadenas** (`s[0]`, `s[1:3]`);
- `return a, b` y el desempaquetado;
- leer el resultado de una biblioteca (`requests.get(url)["datos"]`).

**Recursión:** cuenta la llamada a sí misma, la **recursión mutua** (`a` llama a `b` y `b` llama a `a`) y la **recursión sobre un atributo** (`self.izquierda.insertar(x)`, detectada como el mismo nombre de método invocado sobre un atributo).

**Manejo de excepciones:** cuentan `try/except` y `raise`, incluidos el `raise` en una función corta de validación y el `except:` vacío. El IDC mide dónde aparece el concepto; si está bien aplicado lo mide la prueba (T3).

**Otros:** los métodos de una clase contenedora propia cuentan como ED aunque tengan una sola línea. Las funciones anidadas se funden con la función que las contiene. Un fragmento puede pertenecer a varios conceptos.

**Validación de la definición:**
- Respaldo documental: sílabo del curso de Estructuras de Datos de la USIL y área *Fundamental Data Structures* del currículo ACM/IEEE.
- Jueces expertos: la guía se incluye en la ficha de validación (V de Aiken por regla).
- Anotación: D7 (κ ≥ 0.70).
- Sensibilidad: el IDC también se calcula con una definición amplia (que incluye `append` acumulativo y comprensiones de lista) y se compara qué conceptos resultan débiles.

### 3.4 D17 — Formato de exportación para el análisis

CSV en formato largo, **una fila por participante × concepto × momento**:

| Columna | Descripción |
|---|---|
| `participante` | Código anónimo (P01…) |
| `concepto` | recursion / estructuras / excepciones |
| `momento` | pre / post |
| `forma` | A / B |
| `orden` | AB / BA |
| `T_pct` | % de casos de prueba superados |
| `Q` | Rúbrica (0–20), promedio de los calificadores |
| `Q_cal1`, `Q_cal2` | Puntaje de cada calificador (para el ICC) |
| `cc_sol`, `cc_ref` | Complejidad ciclomática de la solución y de la referencia |
| `lin_sol`, `lin_ref` | Líneas de la solución y de la referencia |
| `reforzado` | 1 / 0 |
| `caso` | A / B / C |
| `idc_concepto` | IDC del concepto (vacío si no es calculable) |
| `idc_lo`, `idc_hi` | Intervalo de Wilson al 95 % |
| `n_fragmentos` | Fragmentos del concepto |
| `semilla` | Semilla del sorteo |
| `version_reglas`, `version_modelo`, `theta`, `lambda`, `m` | Trazabilidad del análisis |

Análisis de HE5:
- Principal: t pareada (o Wilcoxon) sobre Δ_reforzado − Δ_control por participante.
- Respaldo: modelo mixto `Δ ~ reforzado + concepto + (1 | participante)`.

---

## 4. Cambios que deben llevarse a `plan.md`

| Sección de `plan.md` | Cambio |
|---|---|
| 8.3.1 (nota) o 9.2 | Regla de sorteo y asignación escalonada (frase de la sección 3.2) |
| 8.1.1 / 9.5 | Fórmula del puntaje por concepto y del compuesto (D1), con el análisis de sensibilidad |
| 9.3 | Equivalencia de las formas A y B (D16); ítems isomorfos |
| 9.4 | Guía de conceptos (D5, D6); validación de las reglas (D7); clasificador solo con estilo y estructura e índice por historial como análisis complementario (D9); código de IA editado (D8); umbrales (D10) |
| 9.5 | Unificar el lenguaje no causal (eliminar "atribuir"); análisis de HE5 con modelo mixto de respaldo (D17) |
| 9.6 | Cifrado en reposo, borrado por retiro, conservación de datos (D13), Azure con evidencia escrita y cita de la Ley N.° 29733 (D14), consentimiento de la sesión de etiquetado (D15), lista de espera (D4), IDC oculto durante la intervención (D11) |
| 5 (limitaciones) | El concepto de mayor IDC puede quedar como control hasta el postest; el clasificador puede no generalizar a asistentes no vistos; definición operativa de ED |
| Índice | Corregir el índice para que el capítulo 9 muestre 9.1–9.7 |
