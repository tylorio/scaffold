# 01. Requisitos y trazabilidad

- Fase: F1 / Prompt P1
- Fecha: 2026-11-09
- Fuente: `docs/plan/plan.md` (secciones 1.3, 5, 6, 8.1, 8.2, 8.3, 9.1 a 9.7). Cuando se cita una sección, es de ese archivo.
- Lectura previa: `docs/arquitectura/00-estado-actual.md`.

Nota sobre la numeración: el prompt pide leer "9.1 a 9.4"; en el plan la metodología va de 9.1 a 9.7 (9.4 calibración, 9.5 análisis, 9.6 ética, 9.7 cronograma). Se leyeron todas.

Nota sobre el alcance del sistema: el plan dice en 9.5 que "las respuestas del cuestionario y los puntajes de las pruebas se registrarán en una base de datos codificada, a la que se incorporarán los IDC que exporte el sistema". Es decir, el plan **no exige** que el cuestionario ni la prueba de desempeño se administren dentro del sistema; exige que el sistema exporte sus datos de forma que puedan unirse por código anónimo. Por eso los requisitos del módulo 3 y del cuestionario tienen prioridad Should o Could y estaban marcados [PENDIENTE].

**Decisión (2026-11-09, revisión de F2 y F4, ADR-001):** el cuestionario y la prueba se aplican fuera del sistema (RF-26 → Won't); el sistema corrige T1–T3 por lotes en local (RF-24, RF-25); el juicio de expertos se recoge en una ficha externa y el investigador registra el resultado (RF-20 → Should, RF-21 → Won't); hay dos roles, investigador y estudiante (RF-28). Las propuestas PR-01 y PR-04 pasan a ser RF-34 y RF-35; PR-03 queda descartada.

## 1. Actores y casos de uso

Actores según el plan:

| Actor | Quién es en el plan | Sección |
| --- | --- | --- |
| Estudiante (participante) | Estudiante de Ingeniería de Software o de Sistemas de la USIL, identificado solo por código anónimo | 9.1, 9.6 |
| Investigador | El autor del estudio; único con acceso a la tabla código–nombre | 9.6 |
| Experto (juez) | Entre 3 y 5 docentes de programación y de metodología que validan instrumentos y recursos | 9.3 |
| Administrador | El plan no lo distingue del investigador (un solo investigador). Se conserva como rol técnico para configuración y borrado; lo ejerce el investigador. | — |

| ID | Actor | Objetivo | Precondición | Resultado |
| --- | --- | --- | --- | --- |
| CU-01 | Investigador | Dar de alta a un participante con código anónimo y su repositorio | Consentimiento informado firmado (9.6) | Participante registrado sin datos personales |
| CU-02 | Investigador | Comprobar los criterios de inclusión del repositorio (≥ 10 commits, ≥ 5 funciones propias en Python) | CU-01 | Participante marcado como elegible o no (9.1.2) |
| CU-03 | Estudiante | Declarar qué asistentes de IA usa (pregunta de datos generales) | CU-01 | Lista de asistentes para construir la clase «IA» del corpus (9.4) |
| CU-04 | Investigador | Entrenar y evaluar el clasificador con el corpus etiquetado | Corpus humano/IA disponible (9.4) | Modelo versionado con precisión, sensibilidad y F1; decisión F1 ≥ 0,70 |
| CU-05 | Investigador | Calibrar θ y λ en la prueba piloto | CU-04, datos del piloto (9.3, 9.7) | Parámetros vigentes registrados |
| CU-06 | Investigador | Analizar el repositorio de un participante (diagnóstico, semana 8) | CU-02 elegible, modelo vigente | IDC global, IDC por concepto, conceptos débiles (8.3.1, 9.4) |
| CU-07 | Investigador | Asignar conceptos reforzados y no reforzados | CU-06 | Máximo 2 reforzados y al menos 1 sin reforzar por estudiante (9.2) |
| CU-08 | Investigador | Generar los recursos de refuerzo de un concepto | CU-07 | Explicación, ejemplos resueltos y ejercicios con casos de prueba (9.3) |
| CU-09 | Experto | Validar un recurso de refuerzo | CU-08 | Calificación ordinal en pertinencia, claridad, corrección técnica y adecuación al nivel (9.3); insumo de la V de Aiken (HE3) |
| CU-10 | Estudiante | Usar el refuerzo de un concepto reforzado | CU-09 aprobado; semanas 9–12 | Retroalimentación por casos de prueba; uso registrado (9.3, 9.7) |
| CU-11 | Estudiante | Intentar abrir el refuerzo de un concepto no reforzado | CU-07 | Acceso denegado hasta después del postest (9.2) |
| CU-12 | Investigador | Liberar el refuerzo de los conceptos no reforzados | Postest tomado (semana 13) | Estudiante accede a todo el material (9.2) |
| CU-13 | Investigador | Registrar los puntajes del pretest y del postest por participante, forma e ítem | Prueba aplicada en sesión supervisada | Puntajes T1–T3, Q1–Q3, métricas de calidad y compuesto 0–20 (8.3.2, 8.1.1) [PENDIENTE: dentro o fuera del sistema] |
| CU-14 | Investigador | Exportar la base de datos codificada para el análisis estadístico | Datos de O₁ y O₂ | Tabla por código anónimo unible con cuestionario y pruebas (9.5) |
| CU-15 | Estudiante | Recibir su informe personal de diagnóstico | Estudio concluido | Informe individual (9.1.2) |
| CU-16 | Estudiante | Retirarse del estudio | CU-01 | Todos sus datos eliminados (9.6) |
| CU-17 | Administrador | Eliminar todos los datos al concluir el estudio | Análisis terminado (semana 16) | Sistema sin datos de participantes (9.6) |
| CU-18 | Estudiante | Responder el cuestionario diagnóstico de 12 ítems | CU-01 | Respuestas Likert 1–5 por código (8.3.1) [PENDIENTE: dentro o fuera del sistema] |

## 2. Requisitos funcionales

Prioridad MoSCoW: M = Must, S = Should, C = Could, W = Won't (en este estudio). Módulo: 1 análisis, 2 refuerzo, 3 pruebas, P plataforma.

### Módulo 1: análisis de código

| ID | Requisito | Prior. | Mód. | Origen en el plan |
| --- | --- | --- | --- | --- |
| RF-01 | El sistema debe registrar a cada participante únicamente con un código anónimo y la referencia a su repositorio Git, sin nombre, correo ni otro dato personal. | M | 1 | 9.6; 9.1.2 (unidad de análisis) |
| RF-02 | El sistema debe comprobar en el repositorio los criterios de inclusión: al menos 10 commits y al menos 5 funciones propias en Python, e informar el resultado. | S | 1 | 9.1.2 (criterios de inclusión) |
| RF-03 | El sistema debe registrar los asistentes de programación basados en IA que declara cada participante, para definir con qué asistentes se genera la clase «IA» del corpus. | S | 1 | 9.4 ("los que los participantes declaren usar") |
| RF-04 | El sistema debe extraer de cada repositorio cada función o método Python como unidad de análisis («fragmento»). | M | 1 | 9.4 |
| RF-05 | El sistema debe asignar cada fragmento a cero o más conceptos mediante reglas sobre el AST: recursión (la función se llama a sí misma), estructuras de datos (opera sobre listas, diccionarios, conjuntos o clases contenedoras) y manejo de excepciones (try/except o raise). | M | 1 | 9.4; 8.3.1 (indicador IDC por concepto) |
| RF-06 | El sistema debe calcular para cada fragmento características de estilo, nomenclatura, comentarios y complejidad y, cuando el historial lo permita, el tamaño de las inserciones por commit. | M | 1 | 9.4; 5 (precisión del módulo) |
| RF-07 | El sistema debe estimar para cada fragmento la probabilidad de haber sido generado por IA con un clasificador scikit-learn entrenado con el corpus etiquetado por procedencia. | M | 1 | 9.4; OE1; PE1 |
| RF-08 | El sistema debe calcular el IDC global de un participante como el número de fragmentos con probabilidad de IA ≥ θ dividido por el número de fragmentos analizados. | M | 1 | 8.3.1 (indicador) |
| RF-09 | El sistema debe calcular el IDC por concepto con la misma fórmula sobre los fragmentos de ese concepto, y solo cuando haya al menos m fragmentos del concepto; en caso contrario debe marcarlo como no calculable. | M | 1 | 8.3.1; 9.4 (último párrafo) |
| RF-10 | El sistema debe identificar los conceptos débiles de cada participante a partir del IDC por concepto y del umbral λ, sin usar el pretest. | M | 1 | 9.2 (control de la regresión a la media); 9.3 (calibración de λ) |
| RF-11 | El sistema debe permitir configurar θ, λ y m, y guardar con cada análisis los valores usados y la versión del modelo. | M | 1 | 9.3 y 9.7 (calibración en la semana 7); 4 (replicabilidad) |
| RF-12 | El sistema debe entrenar el clasificador con un corpus de dos clases etiquetadas por procedencia (humano: sesiones supervisadas sin IA; IA: soluciones de asistentes a los mismos enunciados), evaluarlo con validación cruzada estratificada y reportar precisión, sensibilidad y F1 en un conjunto de prueba. | M | 1 | 9.4 |
| RF-13 | Si el F1 en el conjunto de prueba es menor que 0,70, el sistema debe marcar el IDC como medida exploratoria y asignar los conceptos a reforzar de forma aleatoria por estudiante, manteniendo al menos un concepto sin reforzar. | M | 1 | 9.4 (plan de contingencia) |
| RF-14 | El sistema debe producir la ficha de registro automatizado de cada participante: IDC global, IDC por concepto, número de fragmentos por concepto y conceptos débiles. | M | 1 | 9.3 (tabla de instrumentos) |

### Módulo 2: refuerzo personalizado

| ID | Requisito | Prior. | Mód. | Origen en el plan |
| --- | --- | --- | --- | --- |
| RF-15 | El sistema debe asignar a cada participante como máximo dos conceptos reforzados y dejar al menos uno sin reforzar, elegidos entre los débiles; la asignación debe quedar registrada y no cambiar durante la intervención. | M | 2 | 9.2 (control intrasujeto); nota en 8.3.1 |
| RF-16 | El sistema debe generar, para cada concepto reforzado, un recurso con una explicación breve del concepto, ejemplos resueltos y ejercicios graduados en Python con casos de prueba automáticos. | M | 2 | 9.3 ("Refuerzo académico"); OE3 |
| RF-17 | El sistema debe ejecutar la solución que envía el estudiante contra los casos de prueba del ejercicio y devolverle retroalimentación. | M | 2 | 9.3 ("casos de prueba automáticos que retroalimentan") |
| RF-18 | El sistema debe registrar el uso del refuerzo por participante y concepto: accesos, intentos y resultados, con fecha. | M | 2 | 9.7 (producto de las semanas 9–12: "Registro de uso del refuerzo") |
| RF-19 | El sistema debe impedir que un participante acceda al refuerzo de sus conceptos no reforzados hasta después del postest, y permitirlo después. | M | 2 | 9.2 ("Al terminar el postest, los participantes recibirán también el refuerzo de los conceptos no reforzados") |
| RF-20 | El sistema debe registrar, por recurso de refuerzo, el resultado de la validación de los expertos (validado / no validado, fecha, número de jueces). Las calificaciones en pertinencia, claridad, corrección técnica y adecuación al nivel se recogen en una ficha externa (plan 9.3), no en el sistema. | S | 2 | 9.3 ("Validadores"); HE3. Decidido 2026-11-09 (simplificación de la revisión F2). |
| RF-21 | ~~Calcular la V de Aiken en el sistema.~~ Se calcula fuera, con el resto de la estadística (9.5). | W | 2 | 8.1.2 (HE3); 9.5. Decidido 2026-11-09. |
| RF-22 | El sistema debe entregar a los estudiantes solo recursos validados por los expertos. | S | 2 | OE3 ("validados por juicio de expertos"); 9.3 (validación en la semana 7, antes del refuerzo) |

### Módulo 3: pruebas de desempeño (alcance decidido el 2026-11-09)

El plan aplica la prueba "en sesión supervisada y sin asistentes de IA" (8.2) y corrige Q1–Q3 "con rúbrica" (8.3.2). Lo único que describe como automático es la métrica de calidad y el porcentaje de casos de prueba de T1–T3. **Decisión:** la prueba se aplica fuera del sistema; el sistema corrige T1–T3 **por lotes, en local** (núcleo de análisis, ADR-001), sobre las soluciones recogidas en la sesión; Q1–Q3 y el cuestionario quedan fuera.

| ID | Requisito | Prior. | Mód. | Origen en el plan |
| --- | --- | --- | --- | --- |
| RF-23 | La base de datos codificada externa debe registrar por participante, momento (pretest/postest) y forma (A/B): el porcentaje de casos superados en T1, T2 y T3; el puntaje 0–20 de Q1, Q2 y Q3; la complejidad ciclomática media y la longitud media de las funciones; y el puntaje compuesto 0–20. Los puntajes deben quedar separados por concepto. El sistema aporta sus columnas mediante RF-24, RF-25 y RF-27. | M | 3 (externo) | 8.3.2 (operacionalización); 8.1.1 (puntaje compuesto 0–20); 9.5 (base de datos codificada); HE4 y control intrasujeto (por concepto) |
| RF-24 | El sistema debe ejecutar, por lotes y en local, los casos de prueba de las soluciones de T1–T3 y calcular el porcentaje de casos superados por participante, momento y forma. | S | 3 | 8.3.2 ("Porcentaje de casos de prueba superados"); ADR-001 |
| RF-25 | El sistema debe calcular, por lotes y en local, sobre las soluciones de T1–T3 la complejidad ciclomática media por función y la longitud media de las funciones. | S | 3 | 8.3.2 ("métrica automática sobre las soluciones"); ADR-001 |
| RF-26 | ~~Aplicar el cuestionario diagnóstico en el sistema.~~ Se aplica fuera, en un formulario con el código anónimo como campo obligatorio, y se registra en la base codificada (9.5). | W | 3 | 8.3.1; 9.3; 9.5. Decidido 2026-11-09. |

### Plataforma

| ID | Requisito | Prior. | Mód. | Origen en el plan |
| --- | --- | --- | --- | --- |
| RF-27 | El sistema debe exportar una tabla codificada por participante con: IDC global, IDC por concepto, conceptos débiles, reforzados y no reforzados, uso del refuerzo, versión del modelo y parámetros, unible por código anónimo con las respuestas del cuestionario y los puntajes de las pruebas. | M | P | 9.5 ("se incorporarán los IDC que exporte el sistema") |
| RF-28 | El sistema debe distinguir dos roles: estudiante (ve solo su refuerzo y su informe, entra con su código de acceso) e investigador (todo). Los expertos no tienen cuenta: validan en una ficha externa. Ningún docente de curso tiene acceso. | M | P | 9.6 ("no se compartirán con los docentes de los cursos"). Decidido 2026-11-09. |
| RF-29 | El sistema debe registrar, antes de analizar un repositorio, que el participante firmó el consentimiento informado (fecha y versión del documento), y permitir registrar su retiro. | S | P | 9.6; 9.1.2 (criterios de inclusión y exclusión) |
| RF-30 | El sistema debe eliminar todos los datos de un participante cuando se retira, y todos los datos del estudio cuando concluye. | M | P | 9.6 ("se eliminarán al concluir el estudio"); 9.1.2 (retiro) |
| RF-31 | El sistema debe generar para cada participante un informe personal de diagnóstico al final del estudio. | S | P | 9.1.2 ("cada participante recibirá al final su informe personal de diagnóstico") |
| RF-32 | El sistema debe presentar el IDC como una estimación probabilística y no como una prueba de uso de IA, y no debe producir vistas ni reportes orientados a detectar plagio o sancionar. | S | P | 9.6 ("el clasificador emite una probabilidad y no una prueba"); 5 |
| RF-33 | El sistema debe conservar lo necesario para reproducir cualquier IDC: fragmentos (o su representación), probabilidades, versión del modelo y parámetros θ, λ, m del análisis. | S | P | 4 (justificación metodológica: replicable); 9.4 |

### RF añadidos por propuestas aceptadas (2026-11-09)

| ID | Requisito | Prior. | Mód. | Origen |
| --- | --- | --- | --- | --- |
| RF-34 | El sistema debe mostrar y exportar cada IDC (global y por concepto) con su intervalo de confianza al 95 %, y señalar cuando el intervalo es demasiado ancho para interpretar el valor. | S | 1 | PR-01 aceptada; coherente con RF-32 y plan 9.6 (probabilidad, no prueba) |
| RF-35 | El sistema debe detectar si un repositorio tiene más de un autor de commits, avisarlo al investigador y exportarlo como variable, sin guardar los correos ni nombres de los autores. | S | 1 | PR-04 aceptada; plan 9.1.2 (repositorios "de sus proyectos") |

### Propuestas (no derivadas del plan; no son requisitos hasta que las apruebes)

| ID | Propuesta | Justificación | Riesgo si no se hace |
| --- | --- | --- | --- |
| PR-01 | Mostrar el IDC con un intervalo de confianza (el prototipo usa Wilson al 95 %). | Con m = 5 fragmentos, un IDC de 0,60 (3 de 5) tiene un intervalo de Wilson al 95 % de 0,23 a 0,88 (cálculo verificable); sin intervalo se sobreinterpreta. Coherente con RF-32. | Conceptos débiles asignados por ruido. |
| PR-02 | Aislar la ejecución del código de los estudiantes (RF-17, RF-24) en un entorno sin red y con límites de recursos. | Ejecutar código ajeno en el servidor del investigador es un riesgo técnico que el plan no menciona pero que RF-17 crea. | Pérdida o filtración de datos de todos los participantes. |
| PR-03 | Analizar el repositorio también después de la intervención (análisis "post", como hace el prototipo). | Permitiría ver si el IDC cambia; **no lo exige ninguna hipótesis**: el postest del plan es la prueba de desempeño, no un nuevo análisis del código. | Ninguno para el estudio. Es alcance extra: candidato a recorte en F10. |
| PR-04 | Avisar cuando un repositorio tenga más de un autor. | El plan supone repositorios individuales (9.1.2: "sus proyectos"); con varios autores, el IDC mezcla personas. | IDC inválido sin que nadie lo note. |
| PR-05 | Calibrar las probabilidades del clasificador antes de fijar θ. | θ solo tiene sentido como umbral de probabilidad si las probabilidades están calibradas. Afecta RF-08 y la fijación de θ en el piloto (9.4). | θ arbitrario; IDC sesgado. |

Estado tras la aprobación del 2026-11-09: **PR-01 aceptada** (RF-34); **PR-02 aceptada** (ya cubierta por RNF-08 y ESC-08); **PR-03 descartada** (ADR-001: el análisis ocurre una vez, en la semana 8); **PR-04 aceptada** (RF-35); **PR-05 condicionada** al resultado de SP-03 (03-riesgos-spikes).

## 3. Requisitos no funcionales

| ID | Qué | Métrica | Umbral | Origen |
| --- | --- | --- | --- | --- |
| RNF-01 | Exactitud del clasificador | F1 en el conjunto de prueba, con validación cruzada estratificada; también precisión y sensibilidad | F1 ≥ 0,70 | 9.4 |
| RNF-02 | Falsos positivos (código humano marcado como IA) | Tasa de falsos positivos al umbral θ | [PENDIENTE] El plan no fija uno. Propuesta: ≤ 0,15, porque un falso positivo lleva a reforzar un concepto que el estudiante sí domina y el plan (9.6) insiste en que la probabilidad no es prueba. Rango razonable: 0,10–0,20; fijarlo en el piloto. | 9.4; 9.6 |
| RNF-03 | Reproducibilidad | Al repetir un análisis con la misma versión del modelo, los mismos parámetros y el mismo commit, el IDC coincide | 100 % de coincidencia | 4; RF-11; RF-33 |
| RNF-04 | Trazabilidad | Desde cada IDC se puede llegar a los fragmentos y a la probabilidad de cada uno | 100 % de los IDC | 9.4 (definición operativa); RF-33 |
| RNF-05 | Anonimato | Datos personales directos (nombre, correo, usuario de GitHub, rutas con nombre) almacenados en el sistema | 0 | 9.6 |
| RNF-06 | Confidencialidad en reposo | Datos de participantes cifrados en almacenamiento | 100 % de las tablas y archivos con código o puntajes | 9.6 ("se almacenarán cifrados") |
| RNF-07 | Borrado | Tiempo entre la solicitud de retiro y la eliminación efectiva; residuo tras el borrado final | [PENDIENTE] Propuesta: ≤ 7 días para el retiro; 0 registros al concluir | 9.6 |
| RNF-08 | Aislamiento de la ejecución de código ajeno | Capacidad del código del estudiante para acceder a red, al sistema de archivos del servidor o a procesos ajenos | [PENDIENTE] Propuesta: ninguna (sin red, sistema de archivos de solo lectura, límites de CPU, memoria y tiempo). El plan no lo exige; lo exige RF-17. | Derivado de RF-17 y RF-24 |
| RNF-09 | Tiempo de análisis por repositorio | Tiempo desde que se lanza el análisis hasta que hay IDC | [PENDIENTE] Propuesta: ≤ 5 min por repositorio con ≥ 10 commits, para analizar 25 repositorios en la semana 8 en una jornada | 9.7 (semana 8) |
| RNF-10 | Disponibilidad durante la intervención | Porcentaje de tiempo disponible en las semanas 8 a 13 | [PENDIENTE] Propuesta: ≥ 95 % en el horario acordado con los participantes | 9.1.2 (horarios acordados); 9.7 |
| RNF-11 | Plazo | Semana en la que el sistema está operativo | Final de la semana 6; contingencia: módulo de análisis solo, antes de la semana 8 | 9.7 |
| RNF-12 | Dedicación del estudiante al refuerzo | Horas por semana en el sistema | [PENDIENTE] El plan tiene "[COMPLETAR: horas por semana]" en 9.1.2. Propuesta: 1–2 h/semana, por las 4 semanas de intervención. | 9.1.2 |
| RNF-13 | Mantenibilidad para un solo desarrollador | Cobertura de pruebas automatizadas de la lógica de análisis e IDC; tiempo de instalación desde cero | [PENDIENTE] Propuesta: ≥ 80 % en los módulos de cálculo; instalación ≤ 30 min siguiendo el README | 1.3 (recursos); restricción de un desarrollador |
| RNF-14 | Costo | Gasto mensual en servicios en la nube | [PENDIENTE] Debe caber en el crédito de Azure for Students [VERIFICAR monto y servicios]. El plan no asigna presupuesto. | Restricción del autor (CLAUDE.md) |
| RNF-15 | Independencia del pretest | La selección de conceptos débiles no usa ningún dato del pretest | 0 dependencias | 9.2 |

## 4. Restricciones

| Tipo | Restricción | Origen |
| --- | --- | --- |
| Técnica | Lenguaje de la solución y del código analizado: Python. Clasificador en scikit-learn. Django como framework (ver `CLAUDE.md`). | 1.3; 2.2; 9.4 |
| Técnica | Los repositorios deben tener historial Git; el tamaño de inserción por commit solo existe "cuando el historial lo permite". | 5; 9.4 |
| Técnica | Los conceptos son exactamente tres: recursión, estructuras de datos, manejo de excepciones. | 2.2; 8.2 |
| Tiempo | 16 semanas en total; desarrollo en las semanas 1–6; validación y piloto en la 7; diagnóstico en la 8; refuerzo 9–12; postest 13; análisis 14–16. | 9.7 |
| Tiempo | Un solo desarrollador con otros cursos y trabajo. | CLAUDE.md |
| Ética | Aprobación del Comité de Ética de la USIL y autorización de la Facultad antes de recolectar datos; consentimiento informado; código anónimo; tabla código–nombre solo en poder del investigador; datos cifrados y eliminados al concluir; resultados no compartidos con docentes ni usados como evidencia de plagio. | 9.6; 9.3 (procedimiento) |
| Ética | Ley N.º 29733 de protección de datos personales [VERIFICAR: el plan no la cita; confirmar con el asesor si debe incluirse]. | CLAUDE.md |
| Ética | Participación voluntaria y sin incentivos. | 9.1.2 |
| Costo | Sin presupuesto asignado en el plan; crédito de Azure for Students [VERIFICAR]. | CLAUDE.md |
| Muestra | 25 participantes (convocar ~30); el sistema no necesita escalar más. | 9.1.2 |

## 5. Fuera de alcance

| Qué no se construye | Por qué |
| --- | --- |
| Inferencia causal o lenguaje de atribución en el software | Diseño preexperimental sin grupo de control (5; 9.2). El sistema reporta medidas, no conclusiones. |
| Análisis de código en lenguajes distintos de Python | Delimitación temática (2.2). |
| Detección de conceptos distintos de los tres definidos | Delimitación temática (2.2). |
| Detección de plagio, informes disciplinarios o vistas para docentes de curso | Prohibido por 9.6. |
| Corrección automática de Q1–Q3 (comprensión conceptual) | El plan los corrige con rúbrica (8.3.2); automatizarlo exigiría otro clasificador sin tiempo para validarlo. |
| Validación psicométrica del cuestionario dentro del sistema | Se hace con los datos del piloto en el análisis estadístico (9.5), fuera del sistema. |
| Medición de retención a largo plazo | Limitación declarada (5): el postest mide el efecto inmediato. |
| Escalado a toda la población de la USIL, integración con LMS o con GitHub Classroom | 25 usuarios; muestra por conveniencia (9.1.2). |
| Detección a nivel de línea o de commit individual | La unidad de análisis es la función o método (9.4). |
| Análisis post del repositorio | No lo exige ninguna hipótesis (ver PR-03). |

## 6. Matriz de trazabilidad

Filas: hipótesis y objetivos específicos. Columnas: RF que los habilitan. Los RF entre paréntesis son opcionales (S/C) o [PENDIENTE] de alcance.

| Hipótesis / objetivo | RF que la habilitan | Datos que necesita del sistema |
| --- | --- | --- |
| **HG** desempeño global post > pre | RF-15, RF-16, RF-17, RF-18, RF-19 (la intervención X); RF-23; RF-27 | Puntaje compuesto 0–20 en pre y post por participante; registro de que recibió el refuerzo |
| **HE1** IDC se relaciona con la dependencia autorreportada | RF-04 a RF-14 (IDC válido); RF-12, RF-13 (validez del clasificador); RF-27; (RF-26) | IDC global por participante unible por código con el total del cuestionario |
| **HE2** dependencia y desempeño pre se relacionan | RF-08, RF-27; RF-23; (RF-26) | Total del cuestionario y puntaje global del pretest; IDC global como complemento |
| **HE3** pertinencia del refuerzo por expertos | RF-16, RF-20 (resultado de la ficha externa), RF-22 | Calificaciones ordinales de 3–5 jueces por recurso y criterio (en la ficha externa); el sistema registra qué recursos quedaron validados |
| **HE4** mejora en conceptos débiles | RF-09, RF-10, RF-15 (qué conceptos son débiles y cuáles se refuerzan); RF-16 a RF-19; RF-23 (puntajes **por concepto**); RF-27 | Puntaje por concepto en pre y post; condición de cada concepto (reforzado / no reforzado) |
| **Control intrasujeto** (complementario a HE4) | RF-15, RF-19, RF-23, RF-27, RNF-15 | Ganancia por concepto reforzado vs. no reforzado |
| **OE1** módulo de análisis + relación con autorreporte | RF-01 a RF-14; RF-33 | Igual que HE1 |
| **OE2** relación dependencia–desempeño | Igual que HE2 | |
| **OE3** módulo de refuerzo validado por expertos | RF-15 a RF-22 | Igual que HE3 |
| **OE4** efecto del refuerzo pre/post en conceptos débiles | Igual que HE4 y control intrasujeto | |

### Huecos detectados

| Hueco | Consecuencia | Dónde se resuelve |
| --- | --- | --- |
| HE1 y HE2 necesitan el total del cuestionario, que se registra **fuera** del sistema (RF-26 → Won't, decidido). La unión depende de que la base externa use el mismo código anónimo. | Riesgo de desalineación de códigos entre dos fuentes. | RF-27 debe fijar el formato exacto del código anónimo (el prototipo valida `^[A-Z]{1,3}\d{2,4}$`) como clave de unión, y el formulario externo debe validarlo igual. Detallar en F6. |
| HE4 y el control intrasujeto exigen puntajes **por concepto** en pre y post. El plan los define (T1/Q1 recursión, T2/Q2 estructuras, T3/Q3 excepciones) pero no dice cómo se agregan por concepto ni cómo se pondera corrección, calidad y comprensión en el compuesto 0–20. | Sin fórmula, RF-23 no se puede implementar ni verificar. | [PENDIENTE] Definir la fórmula del compuesto y del puntaje por concepto con el asesor; registrar en 06-datos. |
| RF-13 (modo exploratorio con asignación aleatoria) no tiene un criterio sobre **qué** conceptos son candidatos al azar cuando el IDC no es confiable (¿los tres?, ¿los que tengan ≥ m fragmentos?). | Ambigüedad en el plan B. | [PENDIENTE] Decidir en F3/F5. |
| Ningún RF cubre la **sesión de etiquetado controlado** (los participantes resuelven tareas con y sin IA para formar el corpus, 9.4). El plan la describe como procedimiento, no como función del sistema. | El corpus se construye a mano; RF-12 solo lo consume. | Confirmar que queda fuera del sistema; si no, añadir RF en F1 (propuesta). |
| RF-02 (criterio "5 funciones propias"): el plan no define "propias". | No se puede verificar automáticamente sin una definición. | [PENDIENTE] Propuesta: funciones no triviales en archivos que no sean de pruebas, escritas en commits del participante. |
| Todos los RF tienen origen en el plan; no hay RF sin origen. Las ideas sin origen están en "Propuestas". | — | — |

---

**Supuestos**
- La versión del plan exportada el 2026-11-09 es la vigente.
- "Base de datos codificada" (9.5) puede ser un archivo externo del investigador; el sistema no está obligado a albergar el cuestionario ni las pruebas.
- El administrador es el propio investigador.
- Los repositorios son individuales (un autor por repositorio).

**Decisiones que debes tomar**
1. ~~Alcance del módulo 3~~ Decidido: prueba fuera; T1–T3 corregidos por lotes en local.
2. ~~Cuestionario dentro o fuera~~ Decidido: fuera.
3. Fórmula del puntaje compuesto 0–20 y del puntaje por concepto (afecta RF-23 y HE4). **Sigue abierta: asesor.**
4. ~~Propuestas~~ Decidido: PR-01, PR-02, PR-04 aceptadas; PR-03 descartada; PR-05 condicionada a SP-03.
5. Si incluir la Ley N.º 29733 en el plan. **Sigue abierta: asesor.**

**Riesgos**
- Si el cuestionario y las pruebas quedan fuera, HE1, HE2 y HE4 dependen de unir tres fuentes por un código manual: un error de código invalida a un participante.
- Sin fórmula del compuesto, RF-23 no se puede cerrar y bloquea F6.
- RNF-02 (falsos positivos) no tiene umbral en el plan; es el que más afecta a los estudiantes.

**Siguiente paso**
- Aplicar la "Revisión de fase" a este archivo y aprobarlo; luego P2 (`02-escenarios.md`), que ya se ejecuta a continuación por tu indicación.
