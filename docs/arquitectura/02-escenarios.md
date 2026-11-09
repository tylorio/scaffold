# 02. Atributos de calidad y escenarios

- Fase: F2 / Prompt P2
- Fecha: 2026-11-09
- Entrada: `docs/arquitectura/01-requisitos.md` (RF, RNF, restricciones y huecos). Los umbrales con origen en el plan se citan; los demás van como [PENDIENTE] con un rango propuesto.

## 1. Árbol de utilidad

Prioridad = (importancia para el objetivo del estudio, dificultad de lograrlo). A = alta, M = media, B = baja. La importancia se juzga por cuántas hipótesis dependen del atributo (matriz de 01-requisitos, sección 6); la dificultad, por el esfuerzo para un solo desarrollador en las semanas 1–6.

| Atributo | Refinamiento | Escenario (resumen) | Prioridad (imp., dif.) |
| --- | --- | --- | --- |
| **Validez y exactitud del clasificador** | Exactitud global | F1 ≥ 0,70 en conjunto de prueba (RNF-01) | (A, A) |
| | Falsos positivos | Código humano marcado como IA al umbral θ (RNF-02) | (A, A) |
| | Generalización | Rendimiento con un asistente de IA no visto en entrenamiento | (A, A) |
| | Calibración | P(IA) = 0,7 significa ≈ 70 % de fragmentos IA (PR-05) | (M, M) |
| | Validez de las reglas de concepto | Un fragmento recursivo se asigna a recursión | (A, B) |
| **Privacidad y seguridad del código** | Anonimato | Cero datos personales directos en el sistema (RNF-05) | (A, B) |
| | Confidencialidad | Datos cifrados en reposo (RNF-06) | (A, M) |
| | Borrado | Retiro de un participante y cierre del estudio (RNF-07) | (A, B) |
| | Aislamiento de ejecución | Código del estudiante no sale de su caja (RNF-08) | (A, A) |
| | Control de acceso | Roles estudiante / investigador / experto (RF-28) | (A, B) |
| | Mínimo envío a terceros | Qué sale hacia un LLM, si se usa (RF-16 [PENDIENTE]) | (A, M) |
| **Reproducibilidad** | Determinismo del IDC | Mismo commit + modelo + parámetros ⇒ mismo IDC (RNF-03) | (A, B) |
| | Versionado de artefactos | Modelo, θ, λ, m, reglas de concepto y banco de ejercicios versionados (RF-11, RF-33) | (A, B) |
| | Reproducibilidad del entrenamiento | Misma semilla y corpus ⇒ mismas métricas (RF-12) | (M, B) |
| **Trazabilidad** | Fragmento → IDC | Descomponer cualquier IDC en sus fragmentos y probabilidades (RNF-04) | (A, B) |
| | Asignación → condición → puntaje | De cada puntaje por concepto saber si el concepto fue reforzado y por qué (RF-15, RF-23, RF-27) | (A, B) |
| | Integridad del diseño | La asignación no cambia tras el sorteo; el control no se abre antes del postest (RF-15, RF-19, RNF-15) | (A, B) |
| **Simplicidad y mantenibilidad** | Operable por una persona | Instalación y despliegue desde cero (RNF-13) | (A, M) |
| | Cobertura de la lógica de cálculo | Pruebas automatizadas de extracción, conceptos, IDC y asignación (RNF-13) | (A, B) |
| | Alcance acotado | Nada fuera de 01-requisitos sección 5 | (A, B) |
| **Costo** | Nube | Dentro del crédito de Azure for Students (RNF-14) | (M, B) |
| | LLM | Costo por participante si se usa un LLM [PENDIENTE] | (M, M) |
| **Disponibilidad y rendimiento** | Diagnóstico de 25 repositorios | Tiempo por repositorio (RNF-09) | (M, B) |
| | Intervención | Disponible en el horario acordado (RNF-10) | (M, B) |
| | Retroalimentación de ejercicios | Tiempo desde el envío hasta el resultado (RF-17) | (M, B) |
| **Usabilidad** | Dedicación acotada | Refuerzo usable en 1–2 h/semana [PENDIENTE] (RNF-12) | (M, M) |
| | Comprensión del IDC | El estudiante entiende que es una estimación (RF-32) | (M, B) |

Los cinco atributos de mayor prioridad, en orden: (1) validez y exactitud del clasificador, (2) privacidad y seguridad, (3) reproducibilidad, (4) trazabilidad e integridad del diseño, (5) simplicidad y mantenibilidad. El costo queda sexto porque con 25 usuarios y sin LLM es bajo; sube si se adopta un LLM.

## 2. Escenarios de los cinco atributos prioritarios

### 2.1 Validez y exactitud del clasificador

| ID | Fuente del estímulo | Estímulo | Entorno | Respuesta esperada | Medida de la respuesta |
| --- | --- | --- | --- | --- | --- |
| ESC-01 | Investigador | Entrena el clasificador con el corpus etiquetado (RF-12) | Semana 7, piloto; corpus humano/IA de los tres conceptos | El sistema reporta precisión, sensibilidad y F1 por validación cruzada estratificada y en un conjunto de prueba separado por autor | F1 ≥ 0,70 en el conjunto de prueba (plan 9.4). Si no: activa RF-13 |
| ESC-02 | Corpus de prueba | Fragmentos escritos por estudiantes sin IA | Umbral θ calibrado | Pocos fragmentos humanos clasificados como IA | Tasa de falsos positivos al umbral θ ≤ [PENDIENTE: propuesta 0,15; rango 0,10–0,20]. Justificación: un falso positivo refuerza un concepto que el estudiante domina y contamina HE4; el plan (9.6) dice que la probabilidad no es prueba |
| ESC-03 | Asistente de IA no incluido en el entrenamiento | Fragmentos generados por ese asistente para los mismos enunciados | Evaluación "dejar un asistente fuera", **solo si el corpus incluye varios asistentes**; si no, se declara como limitación | El F1 no se desploma frente a modelos no vistos | Caída de F1 ≤ [PENDIENTE: propuesta 0,10 puntos respecto al F1 con todos los asistentes]. El plan no lo exige; lo exige la limitación declarada en 5 ("los asistentes cambian de estilo entre versiones") |
| ESC-04 | Investigador | Valida las reglas de concepto con una muestra etiquetada a mano (RF-05) | Muestra de fragmentos de repositorios reales de la USIL | Cada fragmento queda en los conceptos que un docente le asignaría | Concordancia regla–humano ≥ [PENDIENTE: propuesta 0,90 por concepto; el plan no fija valor]. Sin esto, el IDC por concepto mide otra cosa |
| ESC-05 | Investigador | Fija θ en el piloto (RF-11) | Probabilidades del clasificador sobre el conjunto de prueba | θ se elige con un criterio explícito (p. ej., FP ≤ umbral de ESC-02) y queda registrado con su justificación | θ documentado; curva de FP/sensibilidad adjunta. Si las probabilidades no están calibradas (PR-05), se declara |

### 2.2 Privacidad y seguridad del código

| ID | Fuente del estímulo | Estímulo | Entorno | Respuesta esperada | Medida de la respuesta |
| --- | --- | --- | --- | --- | --- |
| ESC-06 | Investigador | Registra un participante y su repositorio (RF-01) | Operación normal | El sistema rechaza nombres, correos y URLs con usuario o token; guarda solo el código anónimo y una referencia al repositorio sin identificadores personales | 0 datos personales directos en la base (RNF-05), verificado por una búsqueda automática de patrones (correo, `C:\Users\<nombre>`, usuario de GitHub) |
| ESC-07 | Atacante o acceso indebido al servidor | Copia el almacenamiento | Servidor en la nube | Los datos de participantes no son legibles sin la clave | 100 % de las tablas y archivos con código o puntajes cifrados en reposo (RNF-06; plan 9.6). Mecanismo decidido (2026-11-09): cifrado del volumen o de la base gestionado por la plataforma, más respaldo cifrado; **no** cifrado por campo. Con ADR-001, el código solo está en el almacén local del investigador; el portal no lo tiene. Detalle en F6/F9 |
| ESC-08 | Estudiante | Envía como solución un programa que intenta leer archivos del servidor, abrir una conexión de red o consumir toda la memoria (RF-17) | Ejecución de ejercicios | El programa no accede a nada fuera de su caja, se corta a tiempo y el sistema sigue operativo | 0 accesos exitosos a red o a archivos del servidor; terminación en ≤ [PENDIENTE: propuesta 5 s de CPU y 256 MB]; verificado con una batería de pruebas hostiles (RNF-08) |
| ESC-09 | Estudiante | Solicita retirarse (RF-30) | Durante el estudio | El sistema elimina repositorio clonado, fragmentos, probabilidades, IDC, asignación, intentos y aperturas del participante | 0 registros con su código tras el borrado, verificado por consulta; plazo ≤ [PENDIENTE: propuesta 7 días] |
| ESC-10 | Docente de curso o tercero | Intenta ver el IDC de un estudiante (RF-28) | Operación normal | Acceso denegado; no existe vista con IDC de otros para el rol estudiante ni rol "docente" | 0 rutas accesibles sin el rol investigador; probado con pruebas de autorización por rol |
| ESC-11 | Sistema | Envía texto a un LLM externo para generar explicaciones (RF-16) | **No aplica mientras rija ADR-001 (sin LLM, decidido 2026-11-09)**; se conserva por si la decisión cambia | Solo sale lo mínimo: nombre del concepto y, si hace falta, un fragmento con identificadores, comentarios y rutas anonimizados | 0 fragmentos sin anonimizar enviados; el consentimiento menciona el envío a terceros (plan 9.6) |

### 2.3 Reproducibilidad

| ID | Fuente del estímulo | Estímulo | Entorno | Respuesta esperada | Medida de la respuesta |
| --- | --- | --- | --- | --- | --- |
| ESC-12 | Investigador | Repite el análisis de un repositorio en el mismo commit con la misma versión del modelo y los mismos θ, λ, m (RF-11, RF-33) | Semana 14–16, auditoría | Mismo IDC global, mismos IDC por concepto, mismos conceptos débiles | Coincidencia exacta en el 100 % de los casos (RNF-03) |
| ESC-13 | Investigador | Reentrena el modelo con el mismo corpus y la misma semilla (RF-12) | Máquina del investigador | Mismas métricas y mismas predicciones | Diferencia de F1 = 0; predicciones idénticas en el conjunto de prueba |
| ESC-14 | Investigador | Cambia θ o el modelo después del diagnóstico | Semanas 9–13 | Los análisis ya hechos conservan sus valores originales; el cambio solo afecta a análisis nuevos y queda registrado | 0 análisis históricos alterados; cada análisis muestra su versión de modelo y parámetros |
| ESC-15 | Investigador | Exporta los datos para el análisis estadístico (RF-27) | Semana 14 | La exportación es idéntica si se repite sobre los mismos datos e incluye versión del modelo y parámetros por fila | Dos exportaciones consecutivas son byte a byte iguales (salvo marca de tiempo) |

### 2.4 Trazabilidad e integridad del diseño

| ID | Fuente del estímulo | Estímulo | Entorno | Respuesta esperada | Medida de la respuesta |
| --- | --- | --- | --- | --- | --- |
| ESC-16 | Asesor o revisor | Pregunta por qué un participante tiene IDC 0,60 en recursión | Semana 14–16 | El sistema muestra los fragmentos de recursión, la P(IA) de cada uno, θ y cuántos superan θ (RNF-04) | 100 % de los IDC descomponibles hasta el fragmento |
| ESC-17 | Investigador | Consulta la condición de un concepto en un participante (RF-15) | Cualquier momento tras el diagnóstico | Devuelve reforzado / no reforzado / no débil, la fecha de la asignación y la regla o semilla que la produjo | 100 % de las asignaciones con fecha y justificación registrada |
| ESC-18 | Sistema o investigador | Intenta modificar la asignación después del sorteo (RNF-15) | Semanas 9–13 | La asignación es inmutable; cualquier cambio exige borrar y rehacer el diagnóstico, y queda en un registro de auditoría | 0 asignaciones modificadas en el período; registro de auditoría con cada rehecho |
| ESC-19 | Estudiante | Abre el refuerzo de su concepto no reforzado antes del postest (RF-19) | Semanas 9–12 | Acceso denegado y el intento queda registrado | 0 accesos al material de control antes de la fecha de liberación |
| ESC-20 | Investigador | Une IDC, condición por concepto y puntajes por concepto (RF-23, RF-27) | Semana 14 | Cada fila de la exportación tiene código anónimo, concepto, condición, IDC y puede unirse con los puntajes externos | 0 participantes sin correspondencia entre fuentes [depende del hueco 1 de 01-requisitos] |

### 2.5 Simplicidad y mantenibilidad

| ID | Fuente del estímulo | Estímulo | Entorno | Respuesta esperada | Medida de la respuesta |
| --- | --- | --- | --- | --- | --- |
| ESC-21 | Desarrollador (el autor) | Instala el sistema desde cero siguiendo el README | Máquina nueva con Windows o Linux | Sistema operativo con datos de prueba | ≤ [PENDIENTE: propuesta 30 min] y ≤ 10 pasos manuales |
| ESC-22 | Desarrollador | Corrige una regla de concepto o un rasgo del clasificador | Semana 7 (ajuste tras el piloto, plan 9.4) | Las pruebas automatizadas detectan regresiones en extracción, conceptos, IDC y asignación | Cobertura ≥ [PENDIENTE: propuesta 80 %] en los módulos de cálculo; suite completa en ≤ [PENDIENTE: propuesta 3 min] |
| ESC-23 | Cronograma | Final de la semana 6 (RNF-11) | Desarrollo | El módulo de análisis está operativo aunque el de refuerzo no lo esté (contingencia del plan 9.7) | Diagnóstico ejecutable sin el módulo 2 |
| ESC-24 | Desarrollador | Despliega una versión nueva | Semanas 7–13 | Un script de despliegue reproducible; CI automatizado solo para las pruebas (decidido 2026-11-09) | ≤ [PENDIENTE: propuesta 15 min]; ningún paso manual fuera del script |
| ESC-25 | Asesor | Pide reducir el alcance en la semana 5 | Desarrollo | Los módulos se pueden recortar sin romper el resto (análisis sin refuerzo; refuerzo sin juicio de expertos en línea) | Dependencias en un solo sentido entre módulos (se verifica en F5) |

## 3. Conflictos entre atributos y cómo resolverlos

| Conflicto | Dónde choca | Resolución propuesta |
| --- | --- | --- |
| **Exactitud vs. costo de cómputo** | Rasgos de perplejidad con un modelo de código en CPU (CLAUDE.md) mejorarían ESC-01 pero encarecen y alargan ESC-21 y RNF-09 | Tratar la perplejidad como spike (F3): medir cuánto F1 aporta sobre los rasgos de estilo con el corpus real. Si aporta < [PENDIENTE] puntos, no se incluye. Decidir en F7 |
| **Exactitud vs. simplicidad** | Más rasgos, más modelos y calibración (PR-05) contra una persona en 6 semanas | Línea base simple primero (rasgos de estilo + modelo lineal o de árboles); cada añadido debe justificar su F1 en el corpus. El F1 ≥ 0,70 del plan es el criterio de parada, no "lo máximo posible" |
| **Trazabilidad vs. privacidad** | ESC-16 quiere ver los fragmentos; RNF-05/06 y el plan (9.6) quieren guardar lo mínimo | Guardar el fragmento cifrado mientras dura el estudio (necesario para ESC-16 y ESC-12), nunca el archivo completo ni la ruta con nombre; al concluir, borrar el código y conservar solo rasgos, probabilidades e IDC si el asesor pide auditoría posterior [PENDIENTE]. Detallar en F6 |
| **Privacidad vs. utilidad de un LLM** | Explicaciones personalizadas (RF-16) pedirían enviar código a un tercero (ESC-11) | Opción 1: banco curado sin LLM (cero envío; el prototipo ya lo hace). Opción 2: LLM solo con el nombre del concepto y el ejercicio, sin código del estudiante. Opción 3: LLM con fragmento anonimizado. Recomiendo la 1 para el estudio y, si quieres personalización, la 2; la 3 añade consentimiento específico y costo. Decidir [PENDIENTE] antes de F4 |
| **Seguridad del aislamiento vs. tiempo del desarrollador** | ESC-08 exige una caja (contenedor sin red, límites) que cuesta días | Mínimo seguro: contenedor sin red, usuario sin privilegios, sistema de archivos de solo lectura, límites de tiempo y memoria; probado con una batería hostil (F8). Si no cabe, segunda opción: los ejercicios de refuerzo (RF-17) se corrigen en la máquina del investigador por lotes, no en el servidor público; riesgo residual declarado |
| **Reproducibilidad vs. LLM** | Un LLM no es determinista; ESC-12 y ESC-15 exigen resultados estables | Si hay LLM, el contenido generado se guarda una vez, lo revisan los expertos (RF-20) y lo que se entrega es el texto guardado, no una regeneración. El IDC nunca pasa por un LLM |
| **Rendimiento vs. simplicidad** | Analizar un repositorio puede tardar minutos (RNF-09); una cola de trabajos resuelve el bloqueo pero añade un componente | (Recomendación hecha para F4.) **Resuelto en ADR-001:** el análisis corre en local, por lotes, desde la línea de comandos; el portal no tiene tareas largas ni gestor de colas. Solo queda un límite de tiempo por clonado en el comando local |
| **Integridad del diseño vs. flexibilidad** | ESC-18 quiere asignaciones inmutables; el investigador puede necesitar rehacer un diagnóstico (p. ej., cambio de modelo demo a real) | Rehacer = borrar la asignación con registro de auditoría y volver a diagnosticar; nunca editar. Antes de la semana 8 es libre; después, cada rehecho se reporta en el informe |

---

**Supuestos**
- Los cinco atributos prioritarios se juzgaron por el número de hipótesis que dependen de ellos y por el tiempo disponible; el asesor puede reordenarlos.
- El costo es bajo mientras no haya LLM ni GPU.
- La "batería de pruebas hostiles" de ESC-08 es realizable en 1–2 días.

**Decisiones que debes tomar**
1. Umbrales [PENDIENTE] que más pesan: tasa de falsos positivos (ESC-02), concordancia de reglas de concepto (ESC-04) y caída de F1 ante asistentes no vistos (ESC-03). Llévalos al asesor y al piloto. **Sigue abierta.**
2. ~~Uso de LLM~~ Decidido 2026-11-09: sin LLM (ADR-001).
3. Qué se conserva del código al concluir el estudio (conflicto trazabilidad vs. privacidad). **Sigue abierta: F6 y asesor.**

**Riesgos**
- Si el corpus real no permite medir ESC-02 y ESC-03 (pocos asistentes, pocos autores), los umbrales quedarán sin verificar y el IDC se usará sin conocer sus falsos positivos.
- El aislamiento de ESC-08 es el escenario más caro en tiempo y el más grave si falla.
- Los umbrales propuestos son míos, no del plan; si se copian al plan sin validarlos, se convierten en cifras inventadas.

**Siguiente paso**
- Revisión de fase de 01 y 02 (plantilla del protocolo). Luego `/clear` y P3 (riesgos y spikes), que debe convertir ESC-01 a ESC-05 y ESC-08 en spikes con criterio de éxito y fracaso.
