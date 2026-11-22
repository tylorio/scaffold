# 07. Clasificador y protocolo de evaluación

- Fase: F7 / Prompt P7
- Fecha: 2026-11-10
- Entrada: `01-requisitos.md` (RF-05 a RF-13, RNF-01, RNF-02), `02-escenarios.md` (ESC-01 a ESC-05, ESC-12, ESC-13), `03-riesgos-spikes.md` (RT-01, RT-02, RT-03, RT-08, RV-01, RV-02, RV-07, RV-08, RV-10; SP-01 a SP-07), `06-datos-privacidad.md` (corpus, retención), `05-componentes-interfaces.md` (A4–A8, versionado §7).
- Decisión registrada en `adr/ADR-003-clasificador.md`.
- Estado: **protocolo previo a los spikes**. Los valores marcados [PENDIENTE: SP-xx] se rellenan con el resultado del spike indicado; el protocolo no cambia, cambian los números.
- Actualizado el 2026-11-21 con las decisiones del asesor (`docs/decisiones/decisiones-asesor-2026-11-21.md`):
  - D7: validación de reglas.
  - D8: `ia_editado`.
  - D9: el clasificador queda sin rasgos de historial.
  - D10: FP ≤ 0,15 y sensibilidad ≥ 0,60.
  - D12: no se usan repositorios de compañeros antes del CEI.
- Actualizado de nuevo el 2026-11-21 con R3 (modo exploratorio y sus consecuencias) y R4 (salida `indeterminado`) (`docs/decisiones/decisiones-asesor-2026-11-21b.md`).

## 0. Dos preguntas distintas (regla del prompt)

| Pregunta | Qué mide | Evidencia que aporta este protocolo | Evidencia que **no** aporta y de dónde sale |
| --- | --- | --- | --- |
| **Exactitud del clasificador**: ¿distingue código escrito por un estudiante sin IA de código producido por un asistente? | Capacidad de separar dos procedencias en un corpus etiquetado por procedencia | AUROC, F1, FP a θ, calibración, generalización a asistentes y tareas no vistos, por concepto y por longitud (§5, §8) | Nada sobre dependencia. Un clasificador perfecto solo dice "este fragmento parece de asistente" |
| **Validez del constructo**: ¿el IDC mide dependencia hacia asistentes de IA? | Si la proporción de código "probablemente delegado" se relaciona con la dependencia tal como la define el plan (8.2: delegación sostenida de funciones cognitivas) | **Ninguna directa.** Solo la triangulación del plan: HE1 (IDC vs. autorreporte), HE2 (IDC vs. desempeño sin IA) y la revisión de sesgo por calidad (SP-03, RV-02) | Falta: una medida independiente de dependencia que no sea autorreporte; la distinción entre uso puntual y delegación sostenida; la estabilidad del IDC en el tiempo; el caso del código de IA editado y comprendido por el estudiante (RV-07). El plan (9.4) lo reconoce: "esa delegación es evidencia de dependencia solo cuando se acompaña de un bajo desempeño sin IA" |

Consecuencia práctica: este archivo garantiza que el **número** sea reproducible y honesto sobre su error; **no** puede garantizar que el número signifique dependencia. Eso lo decide el análisis de HE1 y HE2 con la interpretación prerregistrada en el plan 9.5, y así debe decirse en la tesis.

## 1. Especificación del corpus

### 1.1 Fuentes

| ID | Fuente | Clase | Papel | Estado |
| --- | --- | --- | --- | --- |
| C1 | **Sesión de etiquetado controlado** (plan 9.4): personas fuera de la muestra resuelven tareas de los tres conceptos, mitad sin IA y mitad con IA, en sesión supervisada, cada una en un repositorio Git con un commit por tarea | Humano (sin IA) e IA-sesión (con IA) | **Conjunto de referencia**: la única fuente que se parece al código de los participantes. Conjunto de prueba obligatorio | Diseño en §1.3; rendimiento [PENDIENTE: SP-02] |
| C2 | **Generación directa por asistentes** sobre los mismos enunciados de C1, con los asistentes que declaren los participantes (RF-03) y varios estilos de prompt | IA | Amplía la clase IA a bajo costo; permite "dejar un asistente fuera" | Asistentes [PENDIENTE: lista tras el cuestionario; mientras tanto, los más usados según el autor, marcados como provisionales] |
| C3 | **Código de IA editado a mano**: en C1, las tareas "con IA" producen código que el estudiante puede modificar; se guarda la salida cruda del asistente (C2-equivalente) y la versión final entregada | `ia_editado` (tercera etiqueta) | Mide el caso realista; se evalúa aparte (§5) | **Se excluye del entrenamiento** y se evalúa aparte con las dos lecturas (§5). Lo decidió el autor el 2026-11-10 y lo confirmó el asesor (D8). La lectura principal es que **sigue siendo delegación** si el núcleo lo escribió el asistente |
| C4 | **Conjuntos públicos** de código humano vs. IA en Python [VERIFICAR: AIGCodeSet y MultiAIGCD, basados en Project CodeNet; existencia, licencia, lenguaje, asistentes incluidos, formato] | Según el conjunto | Solo **aumento del entrenamiento**. Nunca en prueba; nunca como única fuente. Se evalúa si ayudan (SP-01 configuraciones a/b/c) | [VERIFICAR licencias antes de descargar] |
| C5 | Código del propio autor anterior a 2022 y proyectos académicos propios | Humano | Aumento menor de la clase humana con estilo local | Opcional; declarar si se usa |

Nunca entran al corpus: repositorios de los participantes del estudio (serían a la vez entrenamiento y objeto de medición: fuga directa y violación del consentimiento) ni código de compañeros sin consentimiento específico para el corpus (06 §6, checklist).

### 1.2 Etiquetas

- Por **procedencia**, no por juicio de un evaluador (plan 9.4): `humano` = escrito en sesión sin IA; `ia` = salida de un asistente sin editar (C2 y salida cruda de C1-con-IA); `ia_editado` = salida de asistente modificada por una persona (C3).
- Metadatos por muestra (JSONL, una línea por fragmento): `id`, `fuente` (C1…C5), `etiqueta`, `autor_id` (código de la persona o nombre del asistente+versión), `tarea_id`, `concepto_previsto`, `asistente`, `estilo_prompt`, `fecha`, `insercion_commit` (líneas añadidas en el commit que introdujo la función; `null` si no hay historial), `hash_normalizado`, `codigo`.
- El corpus es un **archivo inmutable** con hash SHA-256 (06 §1.1, 05 §7). Cada cambio produce un archivo nuevo.

### 1.3 Diseño de la sesión de etiquetado (C1)

| Elemento | Especificación |
| --- | --- |
| Participantes | Personas fuera de la muestra (quedan excluidas del estudio, plan 9.1.2) con consentimiento específico para el corpus (06 §6). Número [PENDIENTE: SP-02; orientativo 10–15] |
| Tareas | 6 enunciados, 2 por concepto, diseñados para producir 2–3 funciones cada uno; cada enunciado tiene una versión A y B de dificultad equivalente para contrabalancear [PENDIENTE: validar que cada enunciado produce fragmentos del concepto previsto; SP-05] |
| Asignación de condición | Cada persona hace 3 tareas sin IA y 3 con IA (una por concepto en cada condición); el orden y qué tareas van con IA se contrabalancean con un cuadrado latino, para que cada tarea aparezca en ambas condiciones y el efecto de orden se reparta |
| Condición "sin IA" | Supervisada; sin asistentes, sin búsqueda; documentación local permitida [PENDIENTE] |
| Condición "con IA" | La persona usa el asistente que declara usar habitualmente; se le pide **guardar la salida cruda** del asistente (pegar en `crudo/`) antes de editarla; el entregable final va a `final/` |
| Historial | Cada persona trabaja en un repositorio Git propio con un commit por tarea como mínimo (el supervisor lo verifica). Así `insercion_commit` existe y refleja el comportamiento real: pegar la salida de un asistente produce inserciones grandes. Ya no alimenta al clasificador (D9). Sirve para **validar el índice por historial**: ¿las inserciones grandes corresponden a las tareas hechas con IA? |
| Duración | ≤ 20 min por tarea; sesión de 2 h [PENDIENTE: SP-02] |
| Rendimiento esperado | ≥ 5 fragmentos no triviales por persona, concepto y clase [PENDIENTE: SP-02] |

### 1.4 Generación de la clase IA (C2)

| Dimensión | Valores |
| --- | --- |
| Asistentes | Los declarados por los participantes en el cuestionario (RF-03), en las versiones vigentes en la fecha de generación [PENDIENTE]. Registrar nombre, versión o fecha y modo (chat, autocompletado, agente). Mínimo 3 asistentes distintos para poder "dejar uno fuera" [PENDIENTE: SP-01] |
| Estilos de prompt | (P1) enunciado literal; (P2) "resuélvelo como lo haría un estudiante de segundo año, en español, sin docstrings"; (P3) "resuélvelo con comentarios explicativos"; (P4) enunciado más un intento parcial erróneo para que lo corrija. Registrar el texto exacto de cada prompt |
| Repeticiones | 2 por asistente y estilo (temperatura por defecto); descartar salidas idénticas por hash normalizado |
| Tamaño orientativo | 6 tareas × 3–4 asistentes × 4 estilos × 2 = 144–192 salidas, ~300–450 fragmentos [PENDIENTE: SP-01] |
| Lo que no se hace | Pedir al asistente que "imite a un humano" para engañar al clasificador: eso mide otra cosa. Si se quiere medir evasión, es un análisis aparte y declarado |

### 1.5 Tamaños orientativos y equilibrio

| Conjunto | Humano | IA | `ia_editado` | Nota |
| --- | --- | --- | --- | --- |
| C1 sesión | 60–120 fragmentos | 60–120 (salida cruda) | 60–120 | [PENDIENTE: SP-02] |
| C2 generado | — | 300–450 | — | [PENDIENTE] |
| C4 público | según conjunto | según conjunto | — | [VERIFICAR] |
| **Prueba final** (solo C1, por autor) | ≥ 40 | ≥ 40 | ≥ 40 | Mínimo para que el F1 tenga un intervalo útil [PENDIENTE: justificar con el bootstrap de §5] |

Desequilibrio de clases: se corrige con pesos de clase en el entrenamiento, no con sobremuestreo (evita duplicados sintéticos que inflan métricas). Se reporta siempre la prevalencia del conjunto de prueba.

### 1.6 Control de duplicados y fuga

| Control | Cómo |
| --- | --- |
| Duplicado exacto | `hash_normalizado`: código sin espacios, sin comentarios, sin docstrings, identificadores canonizados (`v1, v2…`, `f1…`); se conserva una muestra por hash |
| Casi duplicado | Similitud de Jaccard sobre trigramas de tokens ≥ 0,90 [PENDIENTE: umbral] → conservar una; se aplica entre todas las fuentes, en especial entre C2 (repeticiones del mismo asistente) y entre C4 y C1 |
| Fuga por tarea | Un enunciado de C1 no puede estar en C4; se comprueba por similitud de enunciados y de soluciones |
| Fuga por participante | Ningún participante del estudio aporta al corpus |
| Fuga por historial | `insercion_commit` se calcula por muestra desde su propio repositorio; nunca se copia entre muestras |

### 1.7 Licencias y consentimiento

- C1 y C3: consentimiento específico de la sesión (06 §6) con cláusula sobre conservación del corpus [PENDIENTE].
- C2: términos de uso de cada asistente respecto a reutilizar sus salidas en investigación [VERIFICAR por asistente].
- C4: licencia de cada conjunto y de Project CodeNet [VERIFICAR]; registrar la cita exacta en la tesis.

## 2. Rasgos candidatos por familia

Cada rasgo tiene una hipótesis de por qué separa las clases. Los que no la tengan no entran. Todos se calculan por fragmento (05, A5) y se versionan en `RASGOS_VERSION`.

### 2.1 Estilo y superficie (los 7 del prototipo que se conservan + candidatos)

| Rasgo | Por qué debería aportar | Estado |
| --- | --- | --- |
| Densidad de comentarios | Los asistentes comentan con regularidad; los estudiantes, poco o nada, salvo que el curso lo exija | Existe |
| Docstring presente | Casi constante en salidas de asistentes; raro en código académico | Existe |
| Proporción de anotaciones de tipo | Igual que docstring | Existe |
| Longitud media de identificadores | Asistentes: nombres descriptivos largos; estudiantes: `x`, `aux`, `lista2` | Existe |
| Uniformidad de estilo (nombres y comillas) | Asistentes son consistentes; humanos mezclan | Existe |
| Complejidad ciclomática | Asistentes tienden a funciones cortas y planas | Existe |
| Líneas | Interactúa con las demás; necesario para el reporte por longitud | Existe |
| ~~log(inserción por commit)~~ | **Sale del clasificador (D9)** y pasa al índice por historial (§2.4) | Existe; se elimina del vector en F10 |
| **Idioma de identificadores y comentarios** (proporción de palabras en inglés) | En la USIL los estudiantes nombran en español o espanglish; los asistentes tienden al inglés salvo que se les pida lo contrario (estilo P2 lo controla) | Candidato; riesgo: cursos que exigen inglés |
| Nombres de una letra fuera de bucles | Marca de estudiante | Candidato |
| Longitud máxima de línea y violaciones de PEP 8 | Asistentes casi no las cometen | Candidato |
| Excepciones genéricas (`except:` o `except Exception`) vs. específicas | Asistentes usan excepciones específicas; estudiantes, genéricas | Candidato; relevante al concepto `excepciones` |
| f-strings vs. concatenación / `%` / `.format` | Asistentes actuales prefieren f-strings | Candidato |

### 2.2 Estructura (AST)

| Rasgo | Por qué debería aportar |
| --- | --- |
| Profundidad máxima de anidamiento | Asistentes aplanan con retornos tempranos; estudiantes anidan |
| Proporción de nodos por tipo (comprehensions, `lambda`, `with`, `try`, `enumerate/zip/any/all`) | Asistentes usan idioms de Python; estudiantes, bucles explícitos |
| Nodos de AST por línea (densidad) | Compacidad idiomática |
| Retornos tempranos y número de `return` | Patrón de asistente |
| Uso de `else` tras `for`/`try`, `finally` | Raro en estudiantes |
| Repetición estructural (subárboles idénticos dentro del fragmento) | Estudiantes copian-pegan bloques; asistentes factorizan |

### 2.3 Perplejidad (condicional a SP-07)

| Rasgo | Por qué debería aportar | Condición |
| --- | --- | --- |
| Perplejidad media por token bajo un modelo de lenguaje de código pequeño en CPU [VERIFICAR: qué modelo cabe en CPU con licencia abierta; no se nombra ninguno para no inventar] | El texto generado por un modelo es más probable bajo otro modelo de lenguaje que el texto humano; es la base de los detectores de texto de IA | Solo si SP-01 queda entre 0,60 y 0,75 de F1 y SP-07 muestra ≥ +0,05 con ≤ 2 s por fragmento |
| Variabilidad de la perplejidad entre líneas (*burstiness*) | Los humanos alternan líneas muy predecibles y muy raras; los asistentes son uniformes | Igual |
| Riesgos | El modelo pequeño puede estar entrenado con código similar a C4 (contaminación); la perplejidad en español puede confundir idioma con procedencia; costo de cómputo en la máquina del investigador | Declarar en el ADR si se adopta |

### 2.4 Historial de commits: índice de delegación por historial, fuera del clasificador

**D9: estos rasgos no entran al clasificador.** Forman un **índice de delegación por historial** que se calcula aparte por participante. Es una medida exploratoria para HE1 que se reporta en modo GO y en el plan B. Como el clasificador mide el producto (estilo y estructura) y el índice mide el proceso, los dos son medidas independientes que se pueden triangular con el autorreporte.

| Rasgo | Por qué debería indicar delegación | Limitación |
| --- | --- | --- |
| log(líneas añadidas en el commit que introdujo la función) | Pegar una salida de asistente produce inserciones grandes de golpe; escribir a mano, inserciones pequeñas e iterativas | Castiga a quien trabaja mucho y sube todo junto (03, RT-07); por eso es un rasgo, no una regla |
| Número de commits que modificaron la función después de crearla | El código propio se retoca; el pegado, menos | Requiere `blame` por línea; costo medido en SP-06 |
| Proporción del archivo que entró en el mismo commit | Igual que el primero, normalizado | — |
| Tiempo entre el commit anterior y el de inserción (si hay historial denso) | Inserción grande tras poco tiempo = pegado | Historial académico suele ser escaso (plan 5) |
| **Ausencia de historial** | Si el repositorio no tiene historial útil, el índice no se calcula para ese participante y queda vacío, no imputado | Se reporta cuántos participantes quedan sin índice |

Nota de validez: los rasgos de historial son los únicos que miden **proceso** y no **superficie**, y los que menos dependen del estilo del asistente del momento (plan 5: "los asistentes cambian de estilo entre versiones"). Con D9 dejan de compensar dentro del clasificador el sesgo por calidad (RV-02). Por eso el reporte de falsos positivos por tercil de calidad (§5, §6.1) es obligatorio, no opcional.

Definición operativa del índice, fijada por el asesor (P10, `docs/decisiones/decisiones-asesor-2026-11-22.md`) y versionada como `historial-v1`. Se reportan dos medidas continuas:
- la **proporción de líneas propias** del participante que entraron en commits de **30 o más líneas**, calculada línea por línea con `git blame`, con sensibilidad a 15 y 60;
- la **media de log(1 + tamaño de inserción)** de sus fragmentos, que no usa umbral.

El umbral de 30 se fija *a priori* y así se declara en la tesis. **No** se calibra con la sesión de etiquetado: allí se pidió un commit por tarea, así que el tamaño de inserción es artificial por diseño.

### 2.5 Selección de rasgos

Se parte de la línea base (§2.1, los 7 rasgos existentes sin historial). Cada familia nueva se añade en bloque y se mantiene solo si mejora el AUROC en validación por autor en ≥ 0,01 [PENDIENTE] sin empeorar la calibración. Se reporta la importancia por permutación por familia, no por rasgo individual, para no sobreinterpretar con un corpus pequeño.

## 3. Modelos candidatos y criterio

| Modelo | Por qué está | Hiperparámetros a explorar | Observación |
| --- | --- | --- | --- |
| **Línea base: regresión logística** con estandarización y pesos de clase | Interpretable (coeficientes por rasgo), estable con pocos datos, calibra bien | Regularización C ∈ {0,01, 0,1, 1, 10} | Si gana o queda a ≤ 0,02 AUROC del mejor, se elige |
| Bosque aleatorio | Captura interacciones (p. ej., docstring × idioma); robusto a escalas | `n_estimators` 300–500, `max_depth` {4, 8, None}, `min_samples_leaf` {2, 5, 10} | Probabilidades mal calibradas: exige calibración |
| Gradient boosting (histogramas, scikit-learn) | Suele ser el mejor en tabulares pequeños; trata `NaN` nativamente (historial ausente) | `learning_rate` {0,03, 0,1}, `max_iter` 100–300, `max_leaf_nodes` {7, 15} | Igual: calibrar |
| SVM con RBF | Referencia clásica para tabulares pequeños | C, γ en rejilla logarítmica | Solo si los anteriores decepcionan |
| **No candidatos** | Redes neuronales o ajuste fino de un modelo de código: no hay datos suficientes (cientos de muestras), no cabe en CPU ni en 6 semanas, y no es reproducible con la misma facilidad | — | ADR-003 |

Criterio de elección, en orden: (1) AUROC en validación cruzada por autor; (2) tasa de FP al θ elegido (§6); (3) error de calibración tras calibrar; (4) simplicidad: a igualdad (±0,02 AUROC), el más simple. Se elige **una vez**, con los datos de validación, antes de tocar el conjunto de prueba.

Calibración: `CalibratedClassifierCV` con partición por grupos (autor) y método Platt (sigmoide) por defecto; isotónica solo si hay ≥ 300 muestras de validación [PENDIENTE]. El modelo guardado es el calibrado; `ModeloCargado.calibrado = True`.

## 4. División de datos sin fuga

Principio: **la unidad de agrupación es el autor** (persona de C1 o asistente+versión de C2), y el conjunto de prueba se usa una sola vez.

| Nivel | Esquema | Para qué |
| --- | --- | --- |
| 0 | Eliminar duplicados y casi duplicados (§1.6) **antes** de dividir | Evitar que el mismo código caiga a ambos lados |
| 1 | **Prueba final**: 20 % de los autores de C1, elegidos con semilla fija, con sus fragmentos completos, estratificando por clase. Se congela y se guarda la lista de autores | El F1 que decide el go/no-go (§8) |
| 2 | **Validación cruzada por autor** (`GroupKFold`, 5 pliegues) sobre el 80 % restante, con búsqueda de hiperparámetros anidada (3 pliegues internos, también por autor) | Elegir modelo, rasgos y calibración sin tocar la prueba |
| 3 | **Por tarea** (`GroupKFold` con `tarea_id`) como análisis complementario | ¿Generaliza a enunciados no vistos? Un F1 mucho menor que en el nivel 2 indica que aprende la tarea, no la procedencia |
| 4 | **Dejar un asistente fuera** (LOAO): entrenar sin todas las muestras de un asistente, probar sobre ellas; repetir por asistente | Generalización a asistentes no vistos (ESC-03, RV-07). Requiere ≥ 3 asistentes [PENDIENTE: SP-01] |
| 5 | **Con y sin C4**: repetir los niveles 2 y 4 añadiendo los públicos solo al entrenamiento | ¿Aportan o perjudican? (RT-01, SP-01 configuraciones a/b/c) |
| 6 | **`ia_editado`** nunca en entrenamiento (decidido 2026-11-10); se evalúa en §5 con las dos lecturas | RV-07 |

Reglas duras: ningún fragmento de un autor en dos lados; `insercion_commit` se calcula antes de dividir y por repositorio propio; cualquier transformación aprendida (estandarización, imputación) se ajusta solo con el pliegue de entrenamiento (dentro de un `Pipeline`).

## 5. Métricas y reportes

| Métrica | Definición | Dónde se reporta | Umbral |
| --- | --- | --- | --- |
| AUROC | Área bajo la curva ROC; independiente de θ | Validación (nivel 2) y prueba | Informativo; sin umbral en el plan |
| Precisión, sensibilidad, F1 | A θ (§6) sobre la clase IA | Validación y **prueba** (plan 9.4) | **F1 ≥ 0,70 en prueba** (plan); **sensibilidad ≥ 0,60** (D10) |
| **Tasa de falsos positivos a θ** | Humanos clasificados como IA / humanos | Validación y prueba; **por tercil de calidad de estilo** (RV-02; obligatorio por D10) | **≤ 0,15** (D10) |
| Especificidad | 1 − FP | Igual | — |
| Brier | Error cuadrático de la probabilidad | Validación y prueba | Informativo |
| Error de calibración esperado (ECE, 10 intervalos) y curva de confiabilidad | ¿P(IA) = 0,7 ⇒ ≈ 70 % IA? | Antes y después de calibrar | ECE ≤ [PENDIENTE: 0,10; SP-03] |
| Caída de F1 en LOAO | F1 con todos − F1 dejando fuera el asistente peor | Nivel 4 | ≤ [PENDIENTE: 0,10; ESC-03] |
| Caída de F1 por tarea | Nivel 2 − nivel 3 | — | Informativo; si > 0,15 se declara |
| **Por concepto** | Todas las anteriores sobre los fragmentos de recursión / estructuras / excepciones | Validación y prueba | El F1 de ningún concepto queda por debajo de [PENDIENTE: 0,60] |
| **Por longitud** | Intervalos: ≤ 5, 6–15, 16–40, > 40 líneas | Validación | Los fragmentos muy cortos son casi inclasificables; justifica la definición de "trivial" (A3) |
| `ia_editado` | Dos lecturas. **Principal (D8):** se considera IA, y la proporción clasificada como IA es la sensibilidad en el caso realista. Secundaria: se considera humano, y esa misma proporción son falsos positivos | Prueba | Se reportan las dos; no decide el go/no-go |
| Intervalos de confianza | Bootstrap **por autor** (remuestrear autores con reemplazo, 1 000 réplicas, percentiles 2,5 y 97,5) para F1, FP y AUROC | Prueba | Si el intervalo inferior del F1 queda bajo 0,70, se dice |

## 6. Fijación de θ e intervalo del IDC

### 6.1 Procedimiento para θ (ESC-05, SP-03)

1. Obtener las probabilidades **calibradas fuera de pliegue** de la validación por autor (nivel 2): cada fragmento tiene una P(IA) producida por un modelo que no lo vio.
2. Para una rejilla de θ ∈ {0,50, 0,55, …, 0,95}: calcular FP, sensibilidad, F1 y sus intervalos por bootstrap de autores.
3. Elegir el **menor θ** tal que FP ≤ 0,15 **y** sensibilidad ≥ 0,60 (D10). Si no existe, los umbrales no se relajan por cuenta propia: se lleva al asesor la curva FP–sensibilidad (§8).
4. Comprobar FP por tercil de calidad de estilo (proxy de RV-02; los terciles salen de un índice simple: docstring + type hints + uniformidad). Si el FP del tercil superior supera al del inferior en más de [PENDIENTE: 0,10], θ no basta. Antes de fijarlo se revisan los rasgos de estilo y estructura; el historial ya no está disponible como contrapeso (D9).
5. Registrar θ en el modelo (`theta_recomendado`), en `Configuracion` y en el ADR; θ **no se vuelve a tocar** después del diagnóstico (ESC-14).
6. Reportar en prueba las métricas al θ fijado, una sola vez.

Por qué FP y no F1 decide θ: un falso positivo refuerza un concepto que el estudiante domina y contamina HE4; un falso negativo solo pierde un fragmento. El plan (9.6) insiste en que la probabilidad no es prueba; el umbral debe ser conservador hacia el estudiante (RT-03).

### 6.2 Intervalo del IDC

| Método | Qué captura | Dónde se usa |
| --- | --- | --- |
| **Wilson al 95 %** sobre n_ia / n (implementado, RF-34) | Incertidumbre de muestreo: pocos fragmentos | Interfaz, archivo de resultados, informe personal. Es la forma cerrada del bootstrap de fragmentos y se comporta bien con n pequeño y proporciones 0 o 1 |
| **Bootstrap de fragmentos** (2 000 réplicas, percentiles) | Lo mismo que Wilson, sin supuesto | Análisis estadístico (semana 14), como comprobación |
| **Bootstrap con propagación del clasificador**: en cada réplica, remuestrear fragmentos **y** sortear la etiqueta de cada uno como Bernoulli(P(IA) calibrada) en lugar de usar el corte a θ | Incertidumbre de muestreo **más** la del clasificador; produce un "IDC esperado" con intervalo | Análisis de sensibilidad de HE1/HE2 en la estadística; si cambia las conclusiones, se reporta. Exige calibración (§3), si no, no tiene sentido |

El intervalo que ve el estudiante y el que viaja al portal es Wilson; es explícito en el informe que no incluye el error del clasificador (ya lo advierte el prototipo).

## 7. Validación de las reglas de concepto (SP-05, ESC-04)

| Paso | Especificación |
| --- | --- |
| Muestra | Primero, una **ronda de calibración con 20 fragmentos**. Después, **150 fragmentos con muestreo estratificado** según la salida de las reglas: al menos 30 positivos esperados por concepto, más fragmentos que las reglas no asignan a ninguno, para medir omisiones (D7). Entran también los fragmentos con **indexación indeterminada** (R4), para medir cuántas listas reales esconden. Fuente: repositorios académicos **públicos o propios**, nunca de compañeros, hasta la aprobación del CEI (D12). Se guardan como conjunto dorado versionado |
| Guía de anotación | La guía de la sección 3.3 del documento del asesor (D5, D6):<br>• Estructuras de datos: lista cerrada de 8 elementos. No cuentan el `append` acumulativo, la comprensión de lista, la indexación de cadenas, el desempaquetado ni la lectura de resultados de bibliotecas.<br>• Recursión: directa, mutua y sobre atributo.<br>• Excepciones: todo `try/except` y todo `raise`.<br>Se entrega a los anotadores como un anexo de una página |
| Validación de la definición | Tres vías (D5): sílabo de Estructuras de Datos de la USIL y currículo ACM/IEEE; jueces expertos (V de Aiken por regla, en la ficha de validación); anotación (κ) |
| Limitación técnica | El elemento 6 de ED (aritmética de índices sobre **listas**, no sobre cadenas) exige saber el tipo, y el AST no lo dice. Propuesta: una heurística local. Cuenta como lista si la variable se asignó en la función desde un literal de lista, `list()`, `sorted()` o `.split()`, o si se le aplican métodos de lista. Si no se puede saber, la salida es **`indeterminado`** (aprobado en R4). No asigna el concepto, pero se cuenta en `n_indexacion_indeterminada` por fragmento y por participante, y entra en la muestra de anotación. Si resultan muchos, una regla v2 podrá usar las anotaciones de tipo de los parámetros; **no se implementa ahora** |
| Anotadores | Dos personas (autor y una segunda con formación en programación), a ciegas respecto a la salida de las reglas |
| Acuerdo entre anotadores | Kappa de Cohen por concepto; se exige **≥ 0,70** (D7); los desacuerdos se resuelven por discusión y se anota la decisión en la guía |
| Concordancia regla–consenso | Por concepto: precisión y recall de la regla frente al consenso (D7). El asesor no fijó un mínimo. Propuesta interna: ≥ 0,90 como objetivo para iterar la regla, no como criterio de rechazo [PENDIENTE] |
| Taxonomía de errores | Inferencia de tipos (cadenas indexadas), recursión mutua, `raise` trivial, métodos de clases contenedoras, funciones anidadas |
| Resultado | `conceptos-v1` congelada con su concordancia documentada. Se versiona también la **definición amplia** (`conceptos-v1-amplia`, que incluye el `append` acumulativo y las comprensiones de lista), para calcular el IDC dos veces en el análisis de sensibilidad (D5); el conjunto dorado pasa a ser prueba automatizada (05 §6): cualquier cambio de reglas que baje la concordancia falla |

## 8. Criterio go/no-go y plan B

Fecha límite: final de la **semana 7** (plan 9.4: "si no se alcanza en la semana 7, se ajustarán las características y el modelo; si aun así no se alcanza, el IDC se reportará solo como medida exploratoria").

| Resultado en el conjunto de prueba (una sola evaluación) | Decisión | Qué pasa |
| --- | --- | --- |
| F1 ≥ 0,70 **y** FP ≤ 0,15 **y** sensibilidad ≥ 0,60 (D10), con ECE ≤ [PENDIENTE] y (si hay ≥ 3 asistentes) caída LOAO ≤ [PENDIENTE] | **GO** | IDC operativo; conceptos débiles por IDC y λ; asignación escalonada (ADR-004) |
| F1 ≥ 0,70, pero ningún θ da FP ≤ 0,15 con sensibilidad ≥ 0,60, o el ECE es alto | **Consulta al asesor** | Se le lleva la curva FP–sensibilidad. Los umbrales de D10 no se relajan por cuenta propia |
| F1 ≥ 0,70 pero caída LOAO > umbral | **GO con advertencia** | IDC operativo; en la tesis se declara que no generaliza a asistentes no vistos y se recomienda interpretar HE1 con cautela |
| F1 < 0,70 tras un ajuste (rasgos o modelo) dentro de la semana 7 | **NO-GO** → plan B | Ver abajo |

Plan B (RF-13, plan 9.4, ADR-002):
1. Se fija `modo = exploratorio` **una sola vez**, en la configuración, antes de `congelar_asignacion`. Queda registrado en cada asignación y en el archivo de resultados, y el portal y el informe lo muestran (R3).
2. El IDC se reporta como **señal con incertidumbre**, siempre con intervalo y con el F1 obtenido. Consecuencias que deben escribirse en el plan **antes de ver los datos** (R3):
   - **HE1, HE2b y OE1 pasan a exploratorias**, porque dependen del IDC. HE2b es el análisis de HE2 con el IDC global, que el plan llama "análisis complementario" de HE2.
   - **HE4 y HE5 siguen siendo confirmatorias**, porque la asignación sigue siendo aleatoria.
3. La asignación sigue el **modo exploratorio de ADR-004**: no se aplica el caso A; se sortea entre los calculables si hay 2 o más y, si no, entre los 3 conceptos (aprobado en R3). Así el diseño pre/post y el control intrasujeto (HE4, HG) siguen siendo válidos y la selección sigue independiente del pretest.
4. Análisis complementario (decidido el 2026-11-10 y confirmado por el asesor en D9): un "índice de delegación por historial" basado solo en los rasgos de proceso (§2.4) como variable alternativa para HE1, declarado como exploratorio. Definición operativa [PENDIENTE: proponer en la estadística; p. ej., proporción de fragmentos cuyo commit de inserción supera un tamaño umbral]. Se calcula también en modo GO, como análisis de sensibilidad.
5. Se registra en un ADR nuevo la fecha, las métricas y la decisión.

El interruptor de plan B es una bandera, no un desarrollo: debe existir desde el primer sprint (RV-10).

## 9. Reproducibilidad

| Elemento | Cómo se garantiza |
| --- | --- |
| Corpus | Archivos JSONL inmutables con SHA-256 y un `manifiesto.json` (fuentes, fechas, asistentes, prompts, conteos); la lista de autores del conjunto de prueba se guarda con el corpus |
| Semillas | Una semilla global por experimento que fija: partición de prueba, `GroupKFold`, bootstrap, y el `random_state` de cada modelo; se registra en el modelo y en `experimentos.jsonl` |
| Entorno | `requirements.txt` con versiones fijadas [VERIFICAR al construir]; versión de Python; `pip freeze` guardado junto al modelo; CPU solamente; `n_jobs=1` en lo que afecte al orden de operaciones |
| Registro de experimentos | `datos/experimentos.jsonl`: una línea por entrenamiento o evaluación con fecha, etiqueta de Git del código, hash del corpus, partición, rasgos (`RASGOS_VERSION`), hiperparámetros, métricas con intervalos, θ elegido, ruta del modelo |
| Modelo | Paquete joblib con todos los metadatos de 05 §7; nunca se sobrescribe; `evaluar` reproduce las métricas del registro a partir del paquete y del corpus |
| Comandos | `entrenar`, `evaluar` (05 §3.3) con todos los argumentos explícitos; sin estado oculto |
| Prueba de reproducibilidad | Antes del go/no-go: ejecutar `entrenar` dos veces con la misma semilla y comparar métricas y predicciones (ESC-13); diferencia esperada: 0 |
| Lo que no es reproducible | Las salidas de los asistentes (C2): por eso se guardan, con fecha y versión, y no se regeneran |

---

**Supuestos**
- Los participantes de la sesión de etiquetado se consiguen fuera de la muestra y aceptan trabajar con Git (un commit por tarea).
- Hay al menos 3 asistentes distintos declarados; si no, LOAO no se puede hacer y se declara.
- Los conjuntos públicos existen con licencia utilizable; si no, el corpus es solo C1 + C2 + C5.
- La calibración con Platt es suficiente con cientos de muestras.

**Decisiones que debes tomar**
1. Resueltas por el asesor (2026-11-21): `ia_editado` (D8), clasificador sin historial (D9), FP y sensibilidad (D10), casos límite y guía (D5, D6), validación de reglas (D7).
2. Siguen pendientes los umbrales que rellenan los spikes: ECE máximo, caída en LOAO, F1 mínimo por concepto, casi duplicados y tope de la diferencia de FP entre terciles.
3. La definición operativa del índice por historial (umbral N de líneas; §2.4), antes del diagnóstico.
4. ~~Modo exploratorio~~ y ~~heurística de tipos~~: resueltos (R3, R4).

**Riesgos**
- El corpus de C1 puede quedar pequeño (RT-02): el conjunto de prueba por autor tendría intervalos tan anchos que el go/no-go sería un lanzamiento de moneda; SP-02 debe medirlo antes de la sesión real.
- Un F1 alto en C2 y bajo en C1 significa que el clasificador aprende "salida cruda de asistente", no "código con IA de un estudiante": por eso la prueba es solo C1.
- La perplejidad, si se adopta, introduce un modelo externo con posible contaminación y costo; SP-07 es la única puerta de entrada.

**Siguiente paso**
- Revisión de fase. Ejecutar SP-06 y SP-05 (un día cada uno) y SP-02 en cuanto haya enunciados; volver a este archivo para rellenar los [PENDIENTE] y actualizar el ADR-003. Después, F8 (seguridad, ética y sandbox), que no depende de los spikes salvo SP-04.
