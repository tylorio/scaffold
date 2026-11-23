# Consentimiento informado para participar en el estudio

**Versión:** v1 · 23 de noviembre de 2026
**Estudio:** Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software de la USIL
**Investigador:** Pablo [PENDIENTE: apellidos], estudiante de Ingeniería de Software, Universidad San Ignacio de Loyola
**Asesor:** [PENDIENTE: nombre del asesor]
**Aprobación del Comité de Ética:** [PENDIENTE: código y fecha de aprobación del CEI-USIL]

> Notas para el investigador (borrar antes de entregar el formulario): los campos [PENDIENTE] se completan cuando el CEI responda (plazo de conservación, D13), cuando se elija la región de Azure (F9, D14) y el proveedor de formularios. Si cambia cualquier cosa del texto, la versión pasa a v2 y el sistema registra qué versión firmó cada participante (`consentimiento_version`).

## 1. De qué trata el estudio

Queremos saber si un sistema puede estimar, a partir del código de tus proyectos de curso, en qué conceptos de programación (recursión, estructuras de datos y manejo de excepciones) dependes más de asistentes de IA como ChatGPT o Copilot, y si un material de refuerzo enfocado en esos conceptos mejora tu desempeño cuando programas sin IA.

Usar asistentes de IA no está mal ni está prohibido en este estudio. No buscamos detectar plagio ni faltas.

## 2. Qué te pediremos

| Etapa | Qué haces | Tiempo aproximado |
|---|---|---|
| Registro | Firmas este consentimiento, nos das acceso a un repositorio de un proyecto de curso en Python **con su historial de Git** y nos indicas los correos con los que haces commit | 15 min |
| Cuestionario | Respondes un cuestionario sobre cómo usas los asistentes de IA | 10 min |
| Prueba inicial | Resuelves una prueba de programación en sesión supervisada, **sin asistentes de IA** | [PENDIENTE: duración] |
| Refuerzo | Durante 4 semanas trabajas en un portal web con bloques de refuerzo: explicaciones y ejercicios que se corrigen automáticamente | [PENDIENTE: minutos por semana] |
| Prueba final | Una prueba equivalente a la inicial, en las mismas condiciones | [PENDIENTE: duración] |
| Informe | Recibes un informe personal con tus resultados | — |

**Sobre los conceptos que se refuerzan.** Al final del análisis el sistema elige hasta dos conceptos para reforzar y deja al menos uno sin refuerzo durante las 4 semanas, para poder comparar. La elección tiene una parte de sorteo. El material del concepto que quedó sin refuerzo se te habilita cuando terminas la prueba final, así que al terminar el estudio tendrás acceso a todo.

**Sobre tu estimación.** Durante las 4 semanas de refuerzo no verás tu estimación de dependencia, para que no influya en cómo trabajas. La verás en tu informe personal después de la prueba final.

## 3. Qué datos se recogen y cómo se tratan

**Tu repositorio.** El investigador lo descarga en su computadora, con el acceso que tú le des: como colaborador de solo lectura en GitHub o GitLab, o entregando la carpeta del proyecto con su carpeta `.git`. Un archivo `.zip` sin historial no sirve. El análisis se hace **solo en esa computadora**, en un disco cifrado. Tu código no se envía a ningún servicio de IA ni a ningún otro servidor.

**Tus correos de commit.** Los usamos para analizar solo las funciones que escribiste tú. Si el repositorio es de un trabajo grupal, las funciones de tus compañeros no se analizan. El sistema no guarda tus correos: guarda una huella cifrada (un código HMAC) que sirve para reconocerlos y que no permite recuperarlos. Los correos de tus compañeros solo se comparan en memoria y no se guardan de ninguna forma.

**El análisis automático.** Un programa divide tu código en funciones, identifica qué concepto usa cada una y estima la probabilidad de que haya sido generada por un asistente de IA. Esa estimación **es probabilística y puede equivocarse**: es posible que marque como generado por IA código que escribiste tú, sobre todo si es muy ordenado. Por eso siempre se presenta con su margen de incertidumbre, y ninguna decisión sobre ti se toma solo con ella.

**Tu identidad.** En todo el sistema apareces con un código anónimo (por ejemplo, P07). La única tabla que une tu nombre con tu código la guarda el investigador fuera del sistema, cifrada. Nadie más tiene acceso a ella.

**El portal web.** El portal donde haces el refuerzo está alojado en Microsoft Azure, en la región [PENDIENTE: región]. Allí solo hay datos codificados: tu código anónimo, tus resultados agregados por concepto y el registro de qué bloques abriste y cuándo. **No hay nombres ni el código de tu repositorio.** Las soluciones que escribes en los ejercicios se ejecutan automáticamente para corregirlas, durante unos segundos, y **no se guardan**; solo se guarda si el intento pasó o no.

**Formularios.** El cuestionario y algunas fichas se responden en [PENDIENTE: proveedor del formulario] y se identifican solo con tu código anónimo.

**Las pruebas.** Tus respuestas las corrigen un programa y, en las preguntas abiertas, personas que no saben qué conceptos se te reforzaron.

## 4. Para qué se usan y para qué no

- Se usan **solo para esta investigación**.
- **No** afectan tus notas en ningún curso, ni para bien ni para mal.
- **No** se comparten con tus docentes ni con la universidad de forma individual.
- **No** se usan para detectar plagio ni con fines disciplinarios. El sistema no tiene ninguna función para eso.
- Los resultados se publican solo de forma agregada (promedios, porcentajes), sin datos que permitan identificarte.

## 5. Riesgos y beneficios

**Riesgos.** Son bajos. El principal es que la estimación sobre tu uso de IA te incomode o no coincida con lo que crees; por eso se presenta con su incertidumbre y puedes conversarla con el investigador. El otro riesgo es una filtración de datos, que reducimos con el disco cifrado, el código anónimo y el portal sin nombres ni código fuente.

**Beneficios.** Recibes material de refuerzo en tres conceptos que se evalúan en los cursos de programación y un informe personal con tus resultados. No hay pago ni otro incentivo por participar.

## 6. Tus derechos

- **Participar es voluntario.** Puedes negarte sin dar explicaciones y sin ninguna consecuencia.
- **Puedes retirarte cuando quieras**, también sin consecuencias. Basta con escribir al investigador. En un plazo máximo de 7 días se borran tus datos del portal y de la computadora del investigador, incluida la copia de tu repositorio, y te confirmamos el borrado por escrito.
- **Puedes ver tus datos.** Tienes tu informe personal y puedes pedirle al investigador lo que el sistema tiene sobre ti.
- **Puedes pedir que se corrija** cualquier dato equivocado.

Tus datos personales se tratan según la Ley N.° 29733, Ley de Protección de Datos Personales.

## 7. Cuánto tiempo se conservan

- **La copia de tu repositorio, las funciones extraídas y todo lo que se calcula a partir de ellas** se borran al terminar el análisis de datos del estudio, [PENDIENTE: fecha prevista].
- **Los datos del portal** se borran en la misma fecha.
- Se conservan solo **tablas de resultados agregados con tu código anónimo, sin nombre y sin código fuente**, como datos de investigación, durante [PENDIENTE: plazo que fije el CEI-USIL]. Después se eliminan.

## 8. Requisitos para participar

- Ser estudiante de Ingeniería de Software o de Ingeniería de Sistemas de la USIL.
- Ser mayor de 18 años.
- Tener al menos un repositorio de un proyecto de curso en Python, con su historial de Git, en el que hayas escrito código tú.
- No haber participado en la sesión de etiquetado de este mismo estudio.

## 9. Contacto

- Investigador: Pablo [PENDIENTE: apellidos] · [PENDIENTE: correo institucional]
- Asesor: [PENDIENTE: nombre y correo]
- Comité de Ética en Investigación de la USIL: [PENDIENTE: correo o teléfono del CEI-USIL]

## 10. Declaración

He leído este documento (versión v1), he podido hacer preguntas y me las han respondido. Entiendo que participar es voluntario y que puedo retirarme cuando quiera sin consecuencias.

Acepto participar y autorizo:

- [ ] el acceso a mi repositorio indicado abajo y su análisis en la computadora del investigador;
- [ ] el uso de los correos de commit que declaro abajo para filtrar mis funciones;
- [ ] el alojamiento de mis datos codificados, sin nombre ni código fuente, en el portal en Microsoft Azure.

Si no marcas las tres casillas no podemos incluirte en el estudio, porque el análisis no funciona sin ellas.

| | |
|---|---|
| Nombre completo | |
| Código de alumno | |
| Carrera y ciclo | |
| Repositorio (enlace o "entregado en carpeta") | |
| Correos con los que haces commit en ese repositorio | |
| Fecha | |
| Firma | |

**Para llenar por el investigador:** código anónimo asignado: ______ · versión del consentimiento: v1 · fecha de registro en el sistema: ______

*Se entregan dos copias: una para ti y otra para el investigador.*
