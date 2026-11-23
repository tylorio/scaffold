# Convocatoria

**Versión:** v1 · 23 de noviembre de 2026

> Notas para el investigador (borrar antes de publicar): la convocatoria se publica solo cuando el CEI-USIL haya aprobado el estudio. Completa los [PENDIENTE] con las fechas reales del cronograma. La parte B (sesión de etiquetado) se difunde por separado y antes, porque la sesión tiene que hacerse antes de la semana 7.

---

## A. Participa en un estudio sobre programación y asistentes de IA

¿Usas ChatGPT, Copilot u otro asistente de IA para programar? Buscamos estudiantes de **Ingeniería de Software e Ingeniería de Sistemas de la USIL** para un estudio de tesis que prueba un sistema de refuerzo personalizado en **recursión, estructuras de datos y manejo de excepciones**.

**Qué recibes**
- Material de refuerzo con ejercicios que se corrigen solos, enfocado en los conceptos donde más te sirve.
- Un informe personal con tus resultados al final.
- Usar IA no está mal: no se evalúa si la usas, y nada de esto afecta tus notas ni llega a tus docentes.

**Qué te pedimos**

| Cuándo | Qué |
|---|---|
| [PENDIENTE: fecha] | Registro: consentimiento, repositorio y cuestionario (25 min) |
| [PENDIENTE: fecha] | Prueba inicial de programación, presencial y sin IA ([PENDIENTE: duración]) |
| [PENDIENTE: fechas] | 4 semanas de refuerzo en un portal web ([PENDIENTE: minutos por semana]) |
| [PENDIENTE: fecha] | Prueba final, igual que la inicial |

**Requisitos**
1. Ser estudiante de Ingeniería de Software o de Ingeniería de Sistemas de la USIL y mayor de 18 años.
2. Tener **un repositorio de un proyecto de curso en Python con su historial de Git**, en el que hayas escrito código tú. Puede ser individual o grupal. Necesitamos el historial, así que tiene que ser:
   - un repositorio en GitHub o GitLab al que puedas invitar al investigador como colaborador de solo lectura, **o**
   - la carpeta del proyecto **con su carpeta `.git`** dentro.

   Un archivo `.zip` descargado de GitHub **no sirve**, porque no trae el historial.
3. Saber con qué correo o correos haces commit en ese repositorio (abajo te explicamos cómo verlo). Los usamos para analizar solo tu código, no el de tus compañeros de grupo.
4. No haber participado en la sesión de etiquetado de este estudio (parte B).

**Antes de inscribirte, comprueba tu repositorio**

Abre una terminal (PowerShell, cmd o la de tu editor) en la carpeta del proyecto y ejecuta:

```text
git log --oneline -5
```

Si ves una lista de commits, el historial está. Si sale `fatal: not a git repository`, esa carpeta no tiene historial: busca la versión clonada de GitHub o GitLab.

Para ver los correos con los que hiciste commit:

```text
git shortlog -sne --all
```

Cada línea muestra un nombre, un correo y cuántos commits hizo. Anota los correos que sean tuyos. Si en GitHub tu correo aparece como `...@users.noreply.github.com`, anótalo también.

**Tus datos.** Tu código se analiza solo en la computadora del investigador, en un disco cifrado, y no se envía a ningún servicio de IA. En todo el sistema apareces con un código anónimo. Puedes retirarte cuando quieras y tus datos se borran. Todo está en el consentimiento, que puedes leer antes de decidir.

**Inscripción:** [PENDIENTE: enlace o correo de inscripción] · Cupos: 25 · Cierre: [PENDIENTE: fecha]
**Contacto:** Juan Pablo Zavala Valle, juan.zavalav@usil.pe
**Aprobado por el Comité de Ética en Investigación de la USIL:** [PENDIENTE: código]

---

## B. Sesión de etiquetado de código (una sola sesión de 2 horas)

Buscamos de 10 a 16 personas que programen en Python y usen algún asistente de IA, para **una sesión de 2 horas** en la que resolverán seis ejercicios cortos: tres sin IA y tres con su asistente habitual. Ese código sirve para entrenar el sistema del estudio.

- **Fecha y lugar:** [PENDIENTE]
- **Requisitos:** mayor de 18 años, Python al nivel de un segundo curso de programación, usar algún asistente de IA para programar.
- **Importante:** quien participa en esta sesión **no puede** inscribirse después en el estudio principal (parte A).
- No se evalúa tu nivel ni afecta tus notas. Trabajas con un código de sesión, no con tu nombre.
- **Inscripción:** [PENDIENTE] · **Contacto:** juan.zavalav@usil.pe
