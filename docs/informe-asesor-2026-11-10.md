# Informe de avance para el asesor

**Proyecto:** Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software e Ingeniería de Sistemas de la USIL, 2026.
**Autor:** Juan Pablo Zavala Valle
**Fecha:** 10 de noviembre de 2026
**Propósito de este documento:** explicar qué está construido, qué decisiones de diseño ya tomé y cuáles necesito que usted valide antes de seguir. Las preguntas concretas están en la sección 5; el resto es contexto para que pueda responderlas con criterio.

---

## 1. Resumen en una página

**Qué existe.** Un prototipo funcional del sistema (Django y scikit-learn, como dice el plan en 1.3) que ya hace lo central del módulo de análisis: lee un repositorio Git, extrae cada función de Python, la asigna a uno o más de los tres conceptos (recursión, estructuras de datos, manejo de excepciones), estima la probabilidad de que sea código de IA, calcula el índice de dependencia conductual (IDC) global y por concepto con su intervalo de confianza, identifica los conceptos débiles y sortea cuáles se refuerzan y cuál queda de control. También tiene un módulo de refuerzo básico con ejercicios autocorregidos. Tiene 262 pruebas automatizadas que pasan.

**Qué no existe todavía.** El clasificador está entrenado con un corpus **sintético**: sus números solo demuestran que el flujo funciona, no dicen nada sobre ningún estudiante. Falta el corpus real (la sesión de etiquetado del plan, 9.4), la validación de las reglas de concepto, el aislamiento seguro de la ejecución de código, el despliegue en la nube, la autenticación y la exportación final.

**Qué hice después del prototipo.** Adopté un protocolo de diseño de arquitectura en doce fases, documentado en el repositorio, y completé siete: requisitos y trazabilidad con las hipótesis, atributos de calidad, riesgos, estructura del sistema, componentes e interfaces, datos y privacidad, y protocolo de evaluación del clasificador. Cada fase es un documento con decisiones justificadas; tres de ellas quedaron como registros formales de decisión (ADR).

**Qué necesito de usted.** Nueve decisiones que no son de software sino de diseño de la investigación o de ética (sección 5). Las tres más urgentes: la fórmula del puntaje de la prueba de desempeño por concepto, qué hacer con los participantes que no tengan dos conceptos débiles, y la definición operativa de "estructuras de datos" para las reglas de asignación de concepto.

---

## 2. Estado del prototipo

### 2.1 Lo que hace hoy, paso a paso

1. El investigador registra a un participante con su código anónimo (por ejemplo `P01`) y la ubicación de su repositorio.
2. El sistema clona o abre el repositorio, descarta archivos de pruebas y carpetas de entorno, y extrae **cada función o método** de Python como una unidad de análisis ("fragmento"). Las funciones triviales (un getter de una línea) se omiten y se cuentan.
3. Con reglas sobre el árbol sintáctico asigna cada fragmento a cero, uno o varios conceptos: se llama a sí misma → recursión; opera sobre listas, diccionarios, conjuntos o clases contenedoras → estructuras de datos; tiene `try/except` o `raise` → manejo de excepciones.
4. Calcula ocho características del fragmento (densidad de comentarios, docstring, anotaciones de tipo, longitud de identificadores, uniformidad de estilo, complejidad ciclomática, líneas y, si hay historial Git, el tamaño de la inserción en el commit que lo introdujo) y el clasificador devuelve una probabilidad de IA.
5. Calcula el **IDC global** (fragmentos con probabilidad ≥ θ ÷ fragmentos analizados) y el **IDC por concepto**, solo cuando el concepto tiene al menos *m* fragmentos (hoy *m* = 5). Cada IDC va con su intervalo de confianza de Wilson al 95 %.
6. Un concepto es **débil** si su IDC ≥ λ. Entre los débiles, sortea cuáles se refuerzan (máximo dos) y cuál queda de control (al menos uno), como pide el plan en 9.2. La asignación queda congelada con su semilla.
7. El estudiante abre el material de refuerzo de sus conceptos reforzados (explicación, ejemplos, ejercicios con casos de prueba que se corrigen automáticamente); el material del concepto de control está bloqueado.
8. Cada análisis guarda θ, λ, *m* y la versión del modelo con que se hizo, para poder reproducirlo. Se exportan tablas CSV por código anónimo, sin código fuente.

### 2.2 Lo que no hace, y por qué importa

| Falta | Consecuencia |
| --- | --- |
| Clasificador con corpus real | Es el corazón del estudio; hoy el modelo es de demostración. Depende de la sesión de etiquetado (plan 9.4). |
| Validación de las reglas de concepto con una muestra etiquetada a mano | Sin esto no sabemos si "IDC en recursión" mide recursión. |
| Aislamiento de la ejecución de código ajeno | Hoy las soluciones de los ejercicios corren con los permisos del servidor; es inaceptable fuera de una máquina controlada. Ya está diseñado; falta construirlo. |
| Autenticación y roles, cifrado, borrado por participante | Exigencias del plan 9.6; diseñadas, no construidas. |
| Despliegue en la nube | Diseñado a nivel de estructura; pendiente de verificar el crédito de Azure for Students. |

---

## 3. Cómo se diseñó la arquitectura

Seguí un protocolo de doce fases, una por documento, en el que la **fuente de verdad es el plan de investigación** (lo exporté a `docs/plan/plan.md` y no se modifica): si algo del diseño lo contradice, gana el plan. Cada fase lee las anteriores y debe citar la sección del plan que justifica cada requisito o decisión; lo que no se puede sustentar queda marcado como [PENDIENTE] (decisión del autor o del asesor) o [VERIFICAR] (dato externo).

| Fase | Documento | Qué contiene | Estado |
| --- | --- | --- | --- |
| F1 | `01-requisitos.md` | 18 casos de uso, 35 requisitos funcionales y 15 no funcionales, cada uno con su origen en el plan; matriz hipótesis ↔ requisitos con los huecos detectados | Hecho |
| F2 | `02-escenarios.md` | Atributos de calidad priorizados (exactitud del clasificador, privacidad, reproducibilidad, trazabilidad, simplicidad) con 25 escenarios medibles | Hecho |
| F3 | `03-riesgos-spikes.md` | 12 riesgos técnicos, 11 riesgos de validez científica, 7 experimentos cortos ("spikes") para resolverlos antes de construir | Hecho |
| F4 | `04-contexto-contenedores.md`, ADR-001 | Estructura del sistema y estilo arquitectónico | Hecho |
| F5 | `05-componentes-interfaces.md` | Componentes, pipeline tipado, interfaces, diagrama de secuencia de las 16 semanas, versionado | Hecho |
| F6 | `06-datos-privacidad.md`, ADR-002 | Modelo de datos, qué se guarda del código y dónde, borrado, consentimiento, Ley 29733 | Hecho |
| F7 | `07-ml-evaluacion.md`, ADR-003 | Corpus, rasgos, modelos, división sin fuga, métricas, fijación de θ, criterio go/no-go y plan B | Hecho como protocolo; los umbrales se rellenan con los spikes |
| F8 | Seguridad, ética y sandbox | — | Pendiente |
| F9 | Despliegue y costos | — | Pendiente |
| F10 | Plan de construcción (sprints) | — | Pendiente; a partir de aquí se escribe código nuevo |
| F11 | Revisión crítica externa | — | Pendiente |
| F12 | Redacción para el plan | — | Pendiente |

---

## 4. Decisiones ya tomadas que afectan al plan

Las tomé porque son de ingeniería o porque el plan ya las implicaba. Se las presento para que las conozca; si alguna le parece mal, se puede revertir con un registro de decisión nuevo.

| Decisión | Fundamento | Efecto en el plan |
| --- | --- | --- |
| **El análisis de repositorios se hace en mi computadora, por lotes; en la nube solo vive un portal mínimo de refuerzo.** | El plan (9.7) analiza los repositorios **una sola vez**, en la semana 8, y lo hago yo. El postest es la prueba de desempeño, no un nuevo análisis del código. Entonces el código de los estudiantes y las direcciones de sus repositorios **nunca salen de mi máquina**, que es lo que pide 9.6 ("solo en poder del investigador"). Al portal sube únicamente el IDC agregado y la asignación. | Ninguno en el texto; refuerza las consideraciones éticas. Se puede mencionar en limitaciones que el análisis no es "en línea". |
| **Sin modelos de lenguaje (LLM) en el sistema.** | El plan (9.3) no los menciona. Usarlos obligaría a enviar código de estudiantes a un tercero, encarece y hace irreproducible el material. El refuerzo es un banco curado que validan los expertos. | Ninguno. |
| **El cuestionario de 12 ítems y la prueba de desempeño se aplican fuera del sistema**; el sistema corrige automáticamente los ítems T1–T3 (casos de prueba y métricas de calidad) y exporta los puntajes. Q1–Q3 se corrigen con la rúbrica, a mano. | El plan (9.5) dice que cuestionario y puntajes "se registrarán en una base de datos codificada, a la que se incorporarán los IDC que exporte el sistema". | Ninguno; es lo que el plan ya describe. |
| **Los expertos validan en una ficha externa**; el sistema solo registra qué recursos quedaron validados. La V de Aiken se calcula en el análisis estadístico. | Son 3 a 5 docentes evaluando pocos recursos una vez; no justifica una interfaz. | Ninguno. |
| **Entre los conceptos débiles, los reforzados se eligen por sorteo** con semilla registrada (ADR-002). | El plan fija "máximo 2 reforzados, al menos 1 sin reforzar" pero no cómo elegir. Reforzar siempre los de mayor IDC haría que el control fuera sistemáticamente el "menos débil" y sesgaría la comparación reforzado vs. control por regresión a la media. | **Hay que escribir la regla** en 8.3.1 (nota) o 9.2, y declarar como limitación que puede quedar sin reforzar el concepto de mayor IDC hasta después del postest. |
| **No se guarda la URL ni la ruta del repositorio** (identifican al estudiante); **no se guarda el código de las soluciones de los ejercicios** en la nube (solo un hash); **los nombres de autor de los commits nunca se extraen**. | Principio: si un dato no sirve a una hipótesis ni a operar el sistema, no se guarda. | Fortalece 9.6. |
| **El código de IA que el estudiante editó a mano no se usa para entrenar el clasificador**; se evalúa aparte. | Decidir si "editar código de IA" es dependencia o comprensión es una cuestión del constructo; no quise que el modelo la decidiera por mí. | Ver pregunta 5.5. |
| **Se añade un "índice de delegación por historial"** (solo rasgos de proceso: tamaño de las inserciones por commit) como variable exploratoria para HE1. | Es el único indicador que mide *proceso* y no *estilo*; contrapesa el riesgo de que el clasificador marque como IA al estudiante ordenado. | Mención en 9.4 como análisis complementario [si usted lo aprueba]. |

---

## 5. Lo que necesito que decida

Ordenado por urgencia. Para cada punto: por qué es suyo y no mío, las opciones, y mi recomendación.

### 5.1 Fórmula del puntaje por concepto y del compuesto 0–20 (urgente: bloquea el modelo de datos)

El plan define los ítems (T1–T3: porcentaje de casos de prueba; Q1–Q3: 0–20 con rúbrica; complejidad ciclomática y longitud media como calidad) y dice que HG usa un "puntaje compuesto de 0 a 20" (8.1.1). Pero **no dice cómo se agregan** corrección, calidad y comprensión en ese compuesto, ni cómo se obtiene el **puntaje por concepto** que necesitan HE4 y el control intrasujeto (ganancia en el reforzado vs. ganancia en el control).

Mientras no exista la fórmula, el sistema guarda los valores crudos por ítem, así que nada se pierde. Propuesta de partida, para que la corrija:

- Puntaje del concepto *k* = media de (`pct_casos(Tk) / 5`, en escala 0–20) y (`Qk`, 0–20), menos una penalización acotada por calidad (por ejemplo, hasta 2 puntos si la complejidad media supera un umbral) [pesos a definir].
- Compuesto = media de los tres conceptos.

También falta cómo se comprobará la equivalencia de las formas A y B en el piloto (plan 9.3), con *n* de piloto pequeño.

### 5.2 Participantes sin dos conceptos débiles (urgente: afecta la potencia)

El control intrasujeto solo existe para quien tiene **al menos dos conceptos débiles** (uno reforzado, uno de control). Con *m* = 5 fragmentos mínimos por concepto, y dado que la recursión es rara en proyectos académicos, es probable que una parte de los 25 participantes tenga cero o un concepto calculable o débil. El cálculo de potencia de 9.1.2 (d ≥ 0,52 con n = 25) asume que los 25 entran en la comparación.

Opciones: (a) bajar *m* y aceptar intervalos más anchos; (b) cuando no hay dos débiles, asignar al azar entre los conceptos **calculables**, extendiendo la regla que 9.4 ya prevé para el caso exploratorio; (c) reportar la potencia alcanzada con los comparables (ya previsto en 9.1.2).

Mi recomendación: (b) como regla desde el inicio, con (c) como reporte. Lo mediré con un experimento corto (SP-06: distribución real de fragmentos por concepto en 5–10 repositorios académicos) antes de la semana 4; con ese dato podrá decidir.

### 5.3 Aprobar la regla de sorteo (ADR-002)

Descrita en la sección 4. Necesito su aprobación por escrito y una frase para el plan.

### 5.4 Definición operativa de los conceptos: casos límite (bloquea la validación de las reglas)

El plan define cada concepto en una línea (9.4). Para validar las reglas automáticas contra el juicio humano (dos personas etiquetan 150 fragmentos a ciegas; se mide el acuerdo entre ellas y con las reglas), necesito una **guía de anotación** que resuelva los fragmentos ambiguos. Si la guía no los fija, los anotadores discrepan y no se sabe si fallan las reglas o la definición. Y la decisión cambia el IDC: si indexar una cadena cuenta como "estructuras de datos", muchos fragmentos entran a ese concepto.

Principio que propongo: **el concepto se asigna cuando escribir el fragmento exige haber aplicado el concepto, no cuando la sintaxis lo roza.** Con ese principio:

| Caso | Mi propuesta | Razón |
| --- | --- | --- |
| Indexar una cadena (`s[0]`, `s[1:3]`) | No cuenta como estructuras de datos | No exige entender estructuras; es sintaxis básica |
| Leer un resultado de una biblioteca (`requests.get(url)["datos"]`) | No | No diseña ni manipula una estructura |
| `return a, b`, desempaquetado | No | Idioma del lenguaje, no el concepto |
| Lista usada solo para acumular (`res.append(x)` en un bucle) | **No** | Si cuenta, el 80 % de las funciones cae en "estructuras de datos" y el concepto deja de discriminar. Propongo definirlo como "**construye, transforma o consulta una colección con una operación distinta de añadir e iterar**": diccionarios como índice, conjuntos para pertenencia, ordenación, comprensiones, anidamiento, clases contenedoras |
| Recursión mutua (`a` llama a `b`, `b` a `a`) | Sí es recursión | Lo es por definición; mejoraré la regla para detectarla |
| Recursión sobre un atributo (`self.izquierda.insertar(x)`) | Sí | Caso típico de árboles |
| `raise` en una función corta que valida la entrada | Sí es manejo de excepciones | Lanzar la excepción correcta es parte del concepto en pregrado |
| `except:` vacío que silencia todo | Sí cuenta | El IDC mide dónde aparece el concepto, no si está bien hecho; la calidad la mide la prueba (T3). Mezclarlas confundiría la variable independiente con la dependiente |
| Métodos de una clase contenedora propia (`push`, `pop`) | Sí, aunque tengan una línea | Son el concepto en su forma más pura |
| Funciones anidadas | Se funden con la función que las contiene | Ya es así en el prototipo |

Lo que le pido: que **el docente de programación valide la definición operativa de "estructuras de datos"** (es la más difusa y la que más fragmentos captura) y que usted apruebe la tabla, para convertirla en la guía de anotación y citarla en el plan.

### 5.5 Código de IA editado a mano

En la sesión de etiquetado, cuando un estudiante usa IA puede modificar lo que el asistente le dio. Decidí **no usar ese código para entrenar** y evaluarlo aparte, reportando dos lecturas: qué porcentaje de ese código el clasificador marca como IA, interpretado como acierto (si editar sigue siendo delegación) o como falso positivo (si editar es comprender). Necesito que me diga cuál de las dos lecturas corresponde a la definición de dependencia del plan (8.2: "delegación sostenida de funciones cognitivas"). Mi lectura: sigue siendo delegación si el núcleo lo escribió el asistente.

### 5.6 Ética y datos

1. **Experimentos previos al comité.** Los spikes necesitan código real. Hasta la aprobación del comité pienso usar solo código mío, generado por asistentes y conjuntos públicos. ¿Puedo usar repositorios de compañeros voluntarios antes de la aprobación, con un consentimiento simple, o debo esperar? ¿Quien participe en un spike queda excluido de la muestra, como el piloto (9.1.2)?
2. **"Los datos se eliminarán al concluir el estudio" (9.6).** ¿Qué hito es "concluir": el informe final o la sustentación? ¿Los CSV agregados por código anónimo, sin código fuente, cuentan como datos a eliminar o como resultados a conservar? La tesis necesita al menos esos CSV. Esto debe quedar claro **antes** de redactar el consentimiento.
3. **Alojamiento en la nube.** El portal (solo códigos anónimos y agregados) iría en Microsoft Azure. ¿Alojar datos codificados sin nombre fuera del Perú cuenta como flujo transfronterizo según la Ley N.º 29733? ¿La universidad tiene lineamientos? El plan no cita la ley; ¿debe citarla?
4. **Consentimiento aparte para la sesión de etiquetado**, cuyos participantes aportan código al corpus y quedan fuera de la muestra. ¿Se tramita junto con el principal?

### 5.7 Umbrales que el plan no fija

El plan fija F1 ≥ 0,70. Propongo, para fijar en el piloto, no ahora: tasa de falsos positivos al umbral θ ≤ 0,15 (un falso positivo refuerza un concepto que el estudiante domina y contamina HE4; el plan 9.6 insiste en que la probabilidad no es prueba); sensibilidad mínima 0,60; concordancia de las reglas de concepto con el juicio humano ≥ 0,90; acuerdo entre anotadores ≥ 0,80. ¿Le parecen rangos razonables para llevarlos al piloto?

### 5.8 El estudiante no ve su IDC durante la intervención

Propongo que durante las semanas 9–12 el estudiante vea solo **qué conceptos trabaja**, no su IDC numérico; el valor con su intervalo e interpretación aparece en el informe personal al final (9.1.2). Razón: 9.6 pide no presentar la probabilidad como prueba, y un número a mitad de la intervención puede desmotivar o cambiar la conducta. ¿De acuerdo?

### 5.9 Ajustes de redacción en el plan

Al derivar los requisitos del plan encontré estos puntos para ajustar cuando corresponda:

- 1.3 y 9.7: el desarrollo ocupa las semanas 1–6; el diseño de arquitectura ya consumió parte de ese tiempo antes del inicio formal, lo que lo favorece.
- 9.2 dice "alcance correlacional y explicativo" y 9.5 habla de "atribuir" la mejora; en otros pasajes el diseño se describe sin lenguaje causal. Conviene unificar.
- 8.3.1 (nota) y 9.2: escribir la regla de sorteo.
- 9.4: mencionar el análisis complementario por historial, si lo aprueba.
- 9.6: añadir cifrado en reposo, borrado por retiro, alojamiento en nube de datos codificados y la región.
- 5 (limitaciones): el concepto de mayor IDC puede quedar sin reforzar hasta el postest; el clasificador puede no generalizar a asistentes no vistos.
- La numeración interna del capítulo 9 va de 9.1 a 9.7; el índice del documento dice 9.1 a 9.4.

---

## 6. Riesgos que debe conocer

| Riesgo | Por qué es serio | Qué estoy haciendo |
| --- | --- | --- |
| **Pocos participantes comparables** (5.2) | HE4 y el control intrasujeto pueden quedarse con *n* ≈ 10 | SP-06 antes de la semana 4; decisión suya sobre la regla |
| **Corpus de etiquetado pequeño** | Con pocos fragmentos de prueba, el F1 tendrá un intervalo tan ancho que el go/no-go de la semana 7 será poco informativo | Diseño de la sesión con 6 enunciados que producen 2–3 funciones cada uno, un commit por tarea, y un ensayo previo (SP-02) para medir cuántos fragmentos salen |
| **Validez del constructo** | Un clasificador perfecto solo dice "parece de asistente"; que eso sea dependencia lo decide HE1/HE2, y la correlación puede ser nula aunque el clasificador sea exacto. El plan ya lo prevé en 9.5 | Dejar escrita la interpretación antes de ver datos; nombrar el IDC como "delegación observada" ante los participantes |
| **Tiempo** | Una persona, seis semanas de desarrollo, con otros cursos | Orden por riesgo: corpus y clasificador antes que interfaz; recortes predefinidos; contingencia del plan 9.7 (semana 8 solo con el módulo de análisis) |
| **Falsos positivos sesgados** | Los rasgos de estilo pueden marcar como IA al estudiante ordenado; HE2 saldría distorsionada | Medir falsos positivos por nivel de calidad en el piloto; rasgos de historial como contrapeso |

---

## 7. Próximos pasos

| Cuándo | Qué | Necesita |
| --- | --- | --- |
| Esta semana | SP-06: distribución de fragmentos por concepto en repositorios académicos reales; SP-05: validación de reglas de concepto | Respuesta a 5.4 (guía) y 5.6.1 (qué repositorios puedo usar) |
| Siguientes dos semanas | SP-02: ensayo de la sesión de etiquetado; SP-01: primer clasificador real; SP-03: umbral θ | Respuesta a 5.5 y 5.7 |
| En paralelo | Fases F8 (seguridad y ética, incluye la lista para el comité) y F9 (despliegue) | Respuesta a 5.6.2 y 5.6.3 |
| Después | F10: plan de construcción por sprints y construcción | Respuesta a 5.1 y 5.2 |

Todo el material está en el repositorio del proyecto, carpeta `docs/`: el plan exportado (`docs/plan/plan.md`), el protocolo (`docs/protocolo-prompts.md`) y los documentos de arquitectura numerados (`docs/arquitectura/`). Puedo enviarle cualquiera de ellos por separado o preparar una presentación corta para la reunión.
