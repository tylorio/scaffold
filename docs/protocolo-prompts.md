# Protocolo de diseño de arquitectura: prompts para Claude Code

Cómo usar este archivo: copia cada bloque que está entre líneas de comillas triples (```text) y pégalo en Claude Code, en el orden indicado. Los bloques son independientes; cada uno lee archivos del repositorio y escribe su resultado en `docs/arquitectura/`.

> Nota de este repositorio (2026-11-09): el paso 0 ya está hecho. `CLAUDE.md` contiene el P0 **corregido** donde contradecía al plan (Django en lugar de FastAPI, alcance del módulo 3 y uso de LLM marcados [PENDIENTE], desarrollo en las semanas 1–6). El estado del prototipo existente y las brechas están en `docs/arquitectura/00-estado-actual.md`. Las secciones del plan sobre metodología van de 9.1 a 9.7 (no 9.1 a 9.4).

---

## 0. Preparación (una sola vez)

1. Crea esta estructura en la raíz del repositorio:

```text
mkdir -p docs/plan docs/arquitectura/adr
```

2. Convierte tu plan de investigación a Markdown (requiere pandoc) y guárdalo como fuente de verdad:

```text
pandoc "01_Plan_Trab_Investigación.docx" -t markdown --wrap=none -o docs/plan/plan.md
```

3. Crea el archivo `CLAUDE.md` en la raíz del repositorio con el contenido del bloque "P0" de la sección siguiente. Claude Code lo carga solo en cada sesión, así que ya no tienes que repetirlo.

4. Trabaja una fase por sesión: ejecuta `/clear` entre fases. Antes de pasar a la siguiente, revisa el archivo generado y usa la "Revisión de fase" (sección 3).

5. Orden obligatorio: P1 a P12. Las fases F4, F7 y F9 deben dejar un ADR en `docs/arquitectura/adr/`.

Mapa de fases y archivos de salida:

| Fase | Prompt | Archivo de salida |
| --- | --- | --- |
| F1 Requisitos | P1 | docs/arquitectura/01-requisitos.md |
| F2 Calidad | P2 | docs/arquitectura/02-escenarios.md |
| F3 Riesgos | P3 | docs/arquitectura/03-riesgos-spikes.md |
| F4 Estructura | P4 | docs/arquitectura/04-contexto-contenedores.md y adr/ADR-001 |
| F5 Componentes | P5 | docs/arquitectura/05-componentes-interfaces.md |
| F6 Datos | P6 | docs/arquitectura/06-datos-privacidad.md |
| F7 ML | P7 | docs/arquitectura/07-ml-evaluacion.md |
| F8 Seguridad y ética | P8 | docs/arquitectura/08-seguridad-etica.md |
| F9 Despliegue | P9 | docs/arquitectura/09-despliegue.md |
| F10 Construcción | P10 | docs/arquitectura/10-esqueleto-backlog.md |
| F11 Revisión | P11 | docs/arquitectura/11-revision.md |
| F12 Redacción | P12 | docs/arquitectura/12-redaccion-plan.md |

---

## 1. P0: contenido de CLAUDE.md

El P0 vigente es el archivo `CLAUDE.md` de la raíz. El texto original del protocolo se conserva aquí como referencia; las diferencias con el vigente están en `docs/arquitectura/00-estado-actual.md`, sección 6.

```text
# Contexto del proyecto

Eres un arquitecto de software senior y asesor metodológico. Me ayudas a diseñar la arquitectura del software que es el entregable de mi Plan de Trabajo de Investigación (Proyecto de Computación I, USIL). Responde siempre en español.

## Proyecto
Título: "Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software e Ingeniería de Sistemas de la USIL".

El sistema tiene tres módulos:
1. Análisis de código: analiza repositorios Git de proyectos académicos de los participantes, divide el código en fragmentos (función o clase), estima la probabilidad de que cada fragmento sea generado por IA, lo asigna a un concepto (recursión, estructuras de datos, manejo de excepciones) con reglas sobre el AST, y calcula el índice de dependencia conductual (IDC) global y por concepto.
2. Refuerzo personalizado: para los conceptos con mayor IDC, genera recursos de refuerzo (banco curado de ejercicios con tests + explicaciones personalizadas por un LLM). Los expertos revisan el material antes de entregarlo.
3. Pruebas pre/post: pruebas de desempeño en programación, formas A y B, con autocorrección y métricas de calidad (complejidad ciclomática, longitud de funciones).

## Diseño de la investigación (fijo, no lo cambies)
- Cuantitativa, aplicada, correlacional y exploratorio-aplicada; sin lenguaje causal.
- Pre/post de un solo grupo, n = 25 participantes (muestreo por conveniencia, convocar ~30). Intervención de 4 semanas.
- Hipótesis: HG (desempeño post > pre), HE1 (el IDC del sistema se relaciona con la dependencia autorreportada), HE2 (dependencia y desempeño se relacionan), HE3 (pertinencia del refuerzo por juicio de expertos), HE4 (mejora en conceptos débiles).
- Variable independiente: dependencia hacia asistentes de programación basados en IA (dimensiones cognitiva, afectiva, conductual). Variable dependiente: desempeño en programación (corrección funcional, calidad del código, comprensión conceptual).

## Restricciones
- Lenguaje de la solución y de los repositorios analizados: Python.
- Despliegue en Microsoft Azure con Azure for Students (crédito limitado; servicios y regiones disponibles por verificar).
- Unas 25 personas usuarias; sin necesidad de escala. Un solo desarrollador (estudiante con otros cursos y trabajo): priorizar la simplicidad.
- Plazo total aproximado: 16 semanas.
- Datos sensibles: código de estudiantes. Consentimiento informado, anonimato por código, Ley N.º 29733, aprobación del comité de ética. El IDC nunca se usa para calificar ni sancionar.

## Stack de partida (puedes cuestionarlo con argumentos)
Python 3.12, FastAPI + Pydantic + SQLAlchemy, PostgreSQL, ast + radon + GitPython/PyDriller, scikit-learn, transformers (CPU) para rasgos de perplejidad, LLM por API con salida estructurada, sandbox Docker sin red, Jinja2 + HTMX, pandas/scipy/pingouin para la estadística.

## Reglas de respuesta
1. No inventes datos, cifras, versiones, precios, límites ni referencias. Marca [VERIFICAR] lo que dependa de información actual y [PENDIENTE] lo que solo yo pueda decidir.
2. Ante cada decisión de diseño, presenta 2 o 3 alternativas con ventajas y desventajas, y recomienda una con su motivo.
3. Prefiere lo simple (por ejemplo, un monolito modular) a lo sofisticado. Si algo no cabe en 16 semanas, dímelo.
4. Cuando algo contradiga mi plan o decisiones anteriores, señálalo antes de continuar.
5. Termina cada respuesta con cuatro listas breves: supuestos, decisiones que debo tomar, riesgos y siguiente paso.
6. Diagramas en Mermaid; tablas en Markdown; sin relleno.

## Convenciones de trabajo en este repositorio
- La fuente de verdad del estudio es docs/plan/plan.md. No lo modifiques. Si algo lo contradice, gana el plan, salvo que yo indique otra cosa.
- Los artefactos de diseño se guardan en docs/arquitectura/ con nombre numerado (01-requisitos.md, 02-escenarios.md, ...). Las decisiones, en docs/arquitectura/adr/ (ADR-NNN-titulo.md).
- No escribas código de implementación hasta la fase F10. Antes de esa fase solo se admiten firmas, contratos y diagramas.
- Antes de crear o sobrescribir un archivo de docs/arquitectura/, lee los anteriores y mantén los mismos nombres, cifras y terminología.
- Si un archivo ya existe y tu cambio lo contradice, dímelo antes de sobrescribirlo.
```

---

## 2. Serie de prompts

### P1. Requisitos y trazabilidad (F1)

Salida: `docs/arquitectura/01-requisitos.md`. Aceptación: cada hipótesis y objetivo específico tiene al menos un RF; ningún RF sin origen en el plan.

```text
Tarea: levantar los requisitos del sistema a partir de mi plan de investigación.

ENTRADA
Lee docs/plan/plan.md completo, en especial: objetivos general y específicos, hipótesis, tabla de operacionalización y secciones 9.1 a 9.4.

ENTREGA (guárdala en docs/arquitectura/01-requisitos.md)
1. Actores y casos de uso (estudiante, investigador, experto/juez, administrador). Tabla: ID | actor | objetivo | precondición | resultado.
2. Requisitos funcionales (RF-01, RF-02, ...) redactados como "El sistema debe...". Cada uno con: prioridad MoSCoW, módulo (1 análisis, 2 refuerzo, 3 pruebas, plataforma) y el objetivo, hipótesis o indicador que lo exige.
3. Requisitos no funcionales (RNF-01, ...) medibles: qué, métrica, umbral. Si no puedes inferir un umbral, escribe [PENDIENTE] y propón un rango.
4. Restricciones técnicas, de tiempo, éticas y de costo.
5. Fuera de alcance: lo que NO se construirá en 16 semanas y por qué.
6. Matriz de trazabilidad: filas = HG, HE1 a HE4, objetivos específicos; columnas = RF que los habilitan. Señala huecos (hipótesis sin RF, RF sin origen).

REGLA: no agregues requisitos que no se deriven del plan. Si crees que falta uno, lístalo aparte como "propuesta" con su justificación.
```

### P2. Atributos de calidad y escenarios (F2)

Salida: `docs/arquitectura/02-escenarios.md`. Aceptación: al menos un escenario con métrica y umbral por atributo prioritario; los umbrales que dependan del asesor o del piloto van como [PENDIENTE].

```text
Tarea: determinar qué atributos de calidad gobiernan la arquitectura.

ENTRADA
Lee docs/arquitectura/01-requisitos.md.

ENTREGA (guárdala en docs/arquitectura/02-escenarios.md)
1. Árbol de utilidad: atributo -> refinamiento -> escenario, con prioridad (alta/media/baja) por importancia para el objetivo del estudio y por dificultad.
2. Considera como mínimo estos atributos: validez y exactitud del clasificador (en especial la tasa de falsos positivos), privacidad y seguridad del código de los estudiantes, reproducibilidad de los resultados (versión de modelo, semillas, datos), trazabilidad (de fragmento a puntaje), simplicidad y mantenibilidad para una sola persona, y costo.
3. Para los 5 atributos de mayor prioridad, escribe escenarios con el formato: fuente del estímulo | estímulo | entorno | respuesta esperada | medida de la respuesta (con umbral).
4. Señala los conflictos entre atributos (por ejemplo, exactitud vs. costo de cómputo) y cómo los resolverías.

REGLA: ningún umbral se inventa. Si depende de mi asesor, del piloto o de la literatura, márcalo [PENDIENTE] con el rango que propones y por qué.
```

### P3. Riesgos y spikes (F3)

Salida: `docs/arquitectura/03-riesgos-spikes.md`. Aceptación: cada riesgo alto tiene una mitigación concreta o un spike con criterio de éxito y de fracaso.

```text
Tarea: identificar lo que puede hacer fallar el proyecto y cómo comprobarlo antes de diseñar a fondo.

ENTRADA
Lee docs/arquitectura/01-requisitos.md y docs/arquitectura/02-escenarios.md.

ENTREGA (guárdala en docs/arquitectura/03-riesgos-spikes.md)
1. Registro de riesgos: ID | descripción | probabilidad | impacto | disparador | mitigación | dueño. Considera como mínimo: el clasificador no generaliza del código de competencia al código de cursos de la USIL; falsos positivos que perjudiquen a un estudiante; datos etiquetados insuficientes; costo o latencia del LLM; sandbox inseguro; consentimiento o ética; poco tiempo del desarrollador; el IDC no refleja dependencia real (validez de constructo).
2. Spikes: pregunta que responde | método (1 a 3 días) | criterio de éxito | criterio de fracaso | decisión de diseño que desbloquea.
3. Orden recomendado de ejecución de los spikes y por qué.

REGLA: separa los riesgos técnicos de los riesgos de validez científica; los segundos pueden obligar a cambiar el diseño de la investigación, no solo el software.
```

### P4. Contexto, contenedores y estilo arquitectónico (F4)

Salida: `docs/arquitectura/04-contexto-contenedores.md` y `docs/arquitectura/adr/ADR-001-estilo-arquitectonico.md`. Aceptación: la elección se justifica con los escenarios de P2; cada contenedor tiene responsabilidad, tecnología y al menos un consumidor.

```text
Tarea: proponer la estructura de alto nivel del sistema.

ENTRADA
Lee docs/arquitectura/01-requisitos.md, 02-escenarios.md y 03-riesgos-spikes.md.

ENTREGA (guárdala en docs/arquitectura/04-contexto-contenedores.md)
1. Diagrama C4 nivel 1 (contexto: personas y sistemas externos como GitHub, API de LLM, correo) en Mermaid.
2. Comparación de 3 estilos: (a) monolito modular con trabajos en segundo plano, (b) servicios separados por módulo, (c) CLI por lotes + portal mínimo. Evalúalos contra los escenarios de 02-escenarios.md y mi restricción de tiempo; recomienda uno.
3. Diagrama C4 nivel 2 (contenedores) del estilo elegido en Mermaid: cada contenedor con tecnología y responsabilidad en una línea; flechas con el protocolo.
4. Dónde corre cada tarea pesada (extracción de rasgos, perplejidad, generación con LLM) y si es síncrona o por lotes.
5. Crea además docs/arquitectura/adr/ADR-001-estilo-arquitectonico.md con el formato: contexto, decisión, alternativas descartadas, consecuencias, verificación.

REGLA: si recomiendas algo distinto del stack de partida de CLAUDE.md, explica el cambio y su costo en tiempo.
```

### P5. Componentes e interfaces (F5)

Salida: `docs/arquitectura/05-componentes-interfaces.md`. Aceptación: cada componente se puede implementar y probar por separado; las dependencias van en un solo sentido, sin ciclos.

```text
Tarea: diseñar los componentes internos y sus interfaces.

ENTRADA
Lee docs/arquitectura/04-contexto-contenedores.md, el ADR-001 y docs/arquitectura/01-requisitos.md.

ENTREGA (guárdala en docs/arquitectura/05-componentes-interfaces.md)
1. Para cada módulo (análisis, refuerzo, pruebas, plataforma): lista de componentes con una responsabilidad única cada uno.
2. Pipeline del módulo de análisis como etapas con entrada y salida tipadas: ingesta del repo -> filtrado de archivos -> parsing con ast -> extracción de fragmentos -> rasgos (estilo, estructura, perplejidad, historial de commits) -> probabilidad calibrada -> asignación de concepto -> IDC global y por concepto con intervalo.
3. Interfaces como firmas de Python con modelos Pydantic y, para la API, lista de endpoints (método, ruta, entrada, salida, errores). No escribas la implementación.
4. Diagrama de dependencias entre componentes (Mermaid) y verificación explícita de que no hay ciclos.
5. Diagrama de secuencia (Mermaid) del flujo completo: consentimiento -> carga del repo -> diagnóstico -> selección de conceptos -> generación y revisión del refuerzo -> entrega -> postest -> exportación de datos.
6. Qué se prueba con pruebas unitarias, de contrato y de integración en cada componente.

REGLA: define cómo se versiona cada artefacto que influye en un resultado (modelo, theta, reglas de concepto, banco de ejercicios) para poder reproducir cualquier puntaje.
```

### P6. Datos y privacidad (F6)

Salida: `docs/arquitectura/06-datos-privacidad.md`. Aceptación: ningún dato personal directo junto al código; se puede borrar todo lo de un participante; el consentimiento cubre cada uso.

```text
Tarea: diseñar el modelo de datos y las reglas de privacidad.

ENTRADA
Lee docs/arquitectura/05-componentes-interfaces.md y, en docs/plan/plan.md, el cuestionario de 12 ítems, los ítems de las pruebas y lo que diga del consentimiento y la ética.

ENTREGA (guárdala en docs/arquitectura/06-datos-privacidad.md)
1. Modelo entidad-relación en Mermaid (erDiagram): participante (solo código anónimo), repositorio, fragmento, rasgos, predicción, concepto, IDC, cuestionario y respuestas, pruebas A/B, intentos y puntajes, recursos de refuerzo, revisión de expertos, auditoría.
2. Diccionario de datos: campo | tipo | descripción | sensibilidad (pública, interna, personal, código de terceros).
3. Separación de identidades: dónde vive la tabla que relaciona nombre real con código anónimo y quién accede a ella.
4. Qué se almacena del código (archivo completo, fragmento, hash, solo rasgos) y por qué; cuánto tiempo; cómo se borra.
5. Qué se envía a APIs externas (LLM): cuál es el mínimo, cómo se anonimiza (nombres de variables, comentarios, rutas, correos) y qué debe decir el consentimiento.
6. Relación con la Ley N.º 29733 y con las exigencias del comité de ética: marca [VERIFICAR] lo que deba confirmarse con mi asesor o la universidad.

REGLA: si un dato no hace falta para una hipótesis o para operar el sistema, no se guarda.
```

### P7. Pipeline de ML y protocolo de evaluación (F7)

Salida: `docs/arquitectura/07-ml-evaluacion.md` y un ADR. Aceptación: el protocolo se puede ejecutar sin ambigüedad; hay un plan B si el clasificador no alcanza el umbral.

```text
Tarea: diseñar el clasificador y su evaluación como un protocolo científico reproducible.

ENTRADA
Lee docs/arquitectura/01-requisitos.md, 02-escenarios.md, 03-riesgos-spikes.md y 06-datos-privacidad.md.

CONTEXTO DE DATOS
Existen conjuntos públicos de código humano vs. IA en Python (por ejemplo AIGCodeSet y MultiAIGCD, basados en Project CodeNet), pero son de problemas tipo concurso, de una sola función y con modelos de IA más antiguos que los que usan mis compañeros. Además planeo una sesión de etiquetado controlado: cada participante resuelve tareas de los tres conceptos, la mitad sin IA y la mitad con IA, en sesión supervisada.

ENTREGA (guárdala en docs/arquitectura/07-ml-evaluacion.md)
1. Especificación del corpus: fuentes, etiquetas, cómo se generan las muestras de IA (varios LLMs actuales, estilos de prompt, código de IA editado a mano), tamaños orientativos [PENDIENTE], control de duplicados y licencias [VERIFICAR].
2. Rasgos candidatos por familia (estilo, AST, perplejidad con un modelo de código pequeño en CPU, historial de commits) y por qué cada uno debería aportar.
3. Modelos candidatos y una línea base simple; criterio para elegir.
4. Esquema de división de datos sin fuga: por estudiante o autor, por tarea, y "dejar un LLM fuera" para medir generalización a modelos no vistos.
5. Métricas: AUROC, F1, tasa de falsos positivos al umbral theta, calibración (curva y error de calibración), y reporte por concepto y por longitud de fragmento.
6. Procedimiento para fijar theta priorizando una tasa baja de falsos positivos, y cómo se calcula el intervalo del IDC (bootstrap).
7. Validación de las reglas de asignación de concepto con una muestra etiquetada a mano.
8. Criterio go/no-go del clasificador con umbrales propuestos [PENDIENTE] y plan B si no se cumple (por ejemplo, reportar el IDC como señal con incertidumbre, o apoyarse más en el historial de commits y el autorreporte).
9. Reproducibilidad: versionado de datos y modelo, semillas, entorno, registro de experimentos.

REGLA: separa lo que es evaluación del clasificador (exactitud) de lo que es validez del constructo (si el IDC mide dependencia); muéstrame qué evidencia aporta cada una y cuál falta.
```

### P8. Seguridad, ética y sandbox (F8)

Salida: `docs/arquitectura/08-seguridad-etica.md`. Aceptación: cada amenaza alta tiene una mitigación y una forma de verificarla.

```text
Tarea: asegurar el sistema y encuadrar su uso ético.

ENTRADA
Lee docs/arquitectura/04-contexto-contenedores.md, 05-componentes-interfaces.md y 06-datos-privacidad.md.

ENTREGA (guárdala en docs/arquitectura/08-seguridad-etica.md)
1. Modelo de amenazas STRIDE ligero por contenedor y por flujo de datos. Tabla: amenaza | activo | impacto | mitigación | cómo se verifica.
2. Diseño del sandbox para ejecutar código de estudiantes y de LLM: contenedor sin red, usuario sin privilegios, sistema de archivos de solo lectura, límites de CPU, memoria, procesos y tiempo, y limpieza posterior. Incluye las pruebas que demuestran que el aislamiento funciona.
3. Autenticación y autorización mínimas (códigos de invitación, roles estudiante e investigador), gestión de secretos y registro de accesos.
4. Controles éticos incorporados al diseño: el IDC se muestra siempre con su incertidumbre; no hay vistas con nombres reales para terceros; el participante puede ver sus datos y retirarse; el sistema no genera reportes con fines disciplinarios.
5. Checklist para el comité de ética: qué evidencia del diseño puedo adjuntar.

REGLA: si una mitigación supera el tiempo disponible, propón la opción mínima segura y dime qué riesgo residual queda.
```

### P9. Despliegue, CI/CD y costos (F9)

Salida: `docs/arquitectura/09-despliegue.md` y un ADR. Aceptación: el despliegue se reproduce desde cero con pasos listados; el costo cabe en el crédito disponible.

```text
Tarea: diseñar el despliegue y la operación mínima.

ENTRADA
Lee docs/arquitectura/04-contexto-contenedores.md, 05-componentes-interfaces.md y 08-seguridad-etica.md.

ENTREGA (guárdala en docs/arquitectura/09-despliegue.md)
1. Dos o tres alternativas de despliegue en Azure (por ejemplo Container Apps, App Service para contenedores, una máquina virtual con Docker Compose) comparadas por simplicidad, costo, aislamiento del sandbox y esfuerzo de operación; recomienda una.
2. Diagrama de despliegue en Mermaid: servicios, red, almacén de archivos, base de datos, gestión de secretos.
3. Entornos (local, desarrollo, producción), configuración por variables de entorno y estrategia de respaldo de la base de datos.
4. Pipeline en GitHub Actions: lint, pruebas, construcción de imagen, despliegue, y cómo se versionan imagen, modelo y banco de ejercicios.
5. Observabilidad mínima: qué se registra, dónde y cómo se evita registrar código o datos personales.
6. Estimación de costo mensual con supuestos explícitos (horas de cómputo, almacenamiento, llamadas al LLM). Marca [VERIFICAR] cada precio y límite de Azure for Students y de la API del LLM, y [PENDIENTE] el presupuesto disponible.
7. Plan de contingencia si el crédito se agota o un servicio no está disponible en mi región.

REGLA: no des precios de memoria; si no puedes verificarlos, di cómo calcularlos.
```

### P10. Esqueleto ejecutable y backlog (F10)

Salida: `docs/arquitectura/10-esqueleto-backlog.md`. Aceptación: el sprint 1 deja algo ejecutable de punta a punta; el clasificador queda validado antes de la fase de diagnóstico. Desde aquí sí se permite escribir código.

```text
Tarea: planificar la construcción para que lo más riesgoso se valide primero.

ENTRADA
Lee todos los archivos de docs/arquitectura/ (01 a 09) y docs/arquitectura/adr/.

ENTREGA (guárdala en docs/arquitectura/10-esqueleto-backlog.md)
1. Estructura de carpetas del repositorio (un árbol) y convenciones de nombres.
2. Walking skeleton: la secuencia mínima que une repo -> análisis -> IDC -> refuerzo -> prueba -> puntaje, con datos de juguete y componentes simulados. Lista de tareas para construirlo.
3. Backlog en sprints de 1 o 2 semanas, ordenado por riesgo (spikes y clasificador primero) y no por comodidad. Cada ítem: descripción | RF que cubre | estimación en horas | dependencias.
4. Calendario hacia atrás desde la fecha del diagnóstico: qué debe estar listo antes de la sesión de etiquetado, del piloto, del diagnóstico y del postest.
5. Definición de hecho (pruebas, documentación, revisión) y estrategia de pruebas por nivel.
6. Lo que recortarías primero si el tiempo no alcanza, y lo que nunca recortarías.

REGLA: si el plan no cabe en las semanas disponibles, dilo y propón el alcance reducido en lugar de comprimir las estimaciones. En esta fase todavía no escribas código: solo el plan; el código empieza cuando yo apruebe este archivo.
```

### P11. Revisión crítica del diseño (F11)

Salida: `docs/arquitectura/11-revision.md`. Aceptación: ningún hallazgo crítico abierto. Ejecútalo en una sesión nueva (`/clear`) para que el revisor no herede los sesgos del diseñador.

```text
Actúa como revisor externo exigente (ATAM ligero). No fuiste parte del diseño y tu trabajo es encontrar lo que está mal, no validarlo.

ENTRADA
Lee CLAUDE.md, docs/plan/plan.md, todos los archivos de docs/arquitectura/ (01 a 10) y los ADR.

REVISA Y REPORTA (guárdalo en docs/arquitectura/11-revision.md)
1. Incoherencias entre artefactos (nombres, cifras, supuestos, hipótesis sin requisito, requisito sin componente, componente sin prueba).
2. Escenarios de calidad sin soporte en la arquitectura y decisiones sin escenario que las justifique.
3. Puntos únicos de falla, sobre-ingeniería y partes que no caben en el tiempo disponible.
4. Riesgos éticos y de privacidad no cubiertos.
5. Validez científica: ¿el sistema mide lo que dice medir?, ¿el diseño permite contrastar cada hipótesis con los datos que produce?, ¿hay circularidad o fuga de datos?
6. Suposiciones optimistas sobre el clasificador, la muestra de 25 personas o el crédito de Azure.

FORMATO
Tabla: ID | hallazgo | evidencia (cita el archivo y la sección) | severidad (crítico, alto, medio, bajo) | fase a la que regresar | cambio propuesto.
Termina con los tres cambios que más reducen el riesgo de que el proyecto falle.

REGLA: no suavices. Si algo es crítico, dilo. No inventes problemas para llenar la tabla; si algo está bien, no lo menciones. No modifiques ningún otro archivo.
```

### P12. Redacción para el plan de investigación (F12)

Salida: `docs/arquitectura/12-redaccion-plan.md`. Aceptación: terminología idéntica a la del plan; ninguna cifra ni referencia inventada.

```text
Tarea: redactar para mi Plan de Trabajo de Investigación las secciones que describen el software.

ENTRADA
Lee docs/plan/plan.md (para respetar título, objetivos, variables y terminología) y todos los archivos de docs/arquitectura/ (04 a 11) y los ADR.

ENTREGA (guárdala en docs/arquitectura/12-redaccion-plan.md)
1. "Metodología de desarrollo del proyecto": enfoque general, fases, cómo se articula el desarrollo con la evaluación del estudio.
2. "Metodología de desarrollo de software": proceso (por ejemplo Scrum ligero para el software y CRISP-DM para el componente de ML), sprints, definición de hecho, pruebas y control de versiones. Justifica cada elección en una o dos frases.
3. "Artefactos esperados": resumen de la arquitectura de software esperada con los diagramas (contexto, contenedores, componentes, secuencia, datos, despliegue) en Mermaid, cada uno con un título y una frase de lectura. Menciona los requisitos de hardware/cómputo.
4. Una frase para cada sección del plan que dependa de esta arquitectura y deba ajustarse (limitaciones, consideraciones éticas, cronograma, presupuesto de servicios).
5. Referencias sugeridas para fundamentar las decisiones (por ejemplo C4, ADR, ATAM, CRISP-DM). Márcalas [VERIFICAR] y no inventes autores, años ni DOI.

ESTILO
Tercera persona e impersonal, registro académico, sin primera persona, sin notas del borrador, sin cifras que no estén en los artefactos. Usa exactamente los mismos nombres de módulos, variables e hipótesis del plan.
```

---

## 3. Plantillas

### Registro de decisión (ADR)

Una decisión por archivo en `docs/arquitectura/adr/`, numerada (`ADR-001-estilo-arquitectonico.md`).

```markdown
# ADR-NNN: [título corto de la decisión]

- Estado: propuesta | aceptada | reemplazada por ADR-NNN
- Fecha: AAAA-MM-DD
- Fase y prompt de origen: [F? / P?]

## Contexto
[Qué problema o fuerza obliga a decidir. Requisitos y escenarios que intervienen.]

## Decisión
[Lo que se decide, en una o dos frases.]

## Alternativas descartadas
| Alternativa | Por qué no |
| --- | --- |

## Consecuencias
[Qué se gana, qué se pierde, qué riesgos quedan, qué otros artefactos cambian.]

## Verificación
[Cómo sabré que fue buena decisión: escenario, métrica o spike.]
```

### Revisión de fase antes de aprobar

Pégalo al terminar cada fase, en la misma sesión, y no apruebes hasta que todas las respuestas sean sí o estén resueltas.

```text
Revisa el archivo que acabas de producir contra su criterio de salida y contra CLAUDE.md.
1. ¿Cumple el criterio de salida de esta fase? Cita la evidencia.
2. ¿Contradice alguna decisión fija de CLAUDE.md o un archivo anterior de docs/arquitectura/? Cuál.
3. ¿Hay alguna cifra, versión, precio o referencia que no se pueda sustentar? Márcala [VERIFICAR].
4. ¿Qué supuestos hiciste que yo no confirmé? Lístalos.
5. ¿Qué parte es más compleja de lo necesario para 25 usuarios y 16 semanas? Propón la versión más simple.
Responde con una tabla: pregunta | respuesta | acción recomendada. No modifiques archivos todavía.
```

### Propagación de un cambio

Cuando una decisión cambie (por ejemplo, otro estilo arquitectónico o un cambio en las hipótesis), actualiza CLAUDE.md y usa este prompt para saber qué más debe cambiar.

```text
Ha cambiado la siguiente decisión: [DESCRIBIR: antes -> después, y el motivo].

ENTRADA
Lee todos los archivos de docs/arquitectura/ y docs/arquitectura/adr/.

ENTREGA
1. Qué archivos quedan afectados y en qué secciones o líneas, citando el texto actual.
2. Para cada uno, el cambio exacto propuesto.
3. Qué escenarios, riesgos o ADR dejan de valer o deben reescribirse.
4. El orden en que conviene rehacer las fases y desde cuál prompt volver a empezar.
5. Un ADR nuevo que registre el cambio.

REGLA: no modifiques nada todavía, solo propón. No cambies decisiones que yo no mencioné.
```

---

## 4. Checklist final

- [x] CLAUDE.md creado y sus decisiones fijas coinciden con el plan vigente.
- [ ] Artefactos de F1 a F10 guardados en docs/arquitectura/ con número.
- [ ] Cada hipótesis y objetivo específico tiene al menos un RF en la matriz de P1.
- [ ] Hay un ADR por cada decisión de F4, F7 y F9.
- [ ] Los spikes de F3 se ejecutaron y sus resultados actualizaron el diseño.
- [ ] La revisión F11 no deja hallazgos críticos abiertos.
- [ ] Todos los [PENDIENTE] y [VERIFICAR] están resueltos o listados para el asesor.
- [ ] Los diagramas de Mermaid están exportados como imagen para el plan.
- [ ] El texto de P12 fue revisado por el asesor y es coherente con el resto del plan.
