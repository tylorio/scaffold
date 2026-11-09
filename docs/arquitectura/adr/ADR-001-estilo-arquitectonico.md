# ADR-001: Estilo arquitectónico: análisis por lotes en local y portal mínimo en la nube

- Estado: aceptada (2026-11-09, por el autor)
- Fecha: 2026-11-09
- Fase y prompt de origen: F4 / P4

## Contexto

El sistema tiene dos cargas de trabajo con perfiles opuestos:

1. **Análisis de repositorios y entrenamiento del clasificador.** Ocurre una vez por participante, en la semana 8 (plan 9.7), lo ejecuta el investigador y procesa el activo más sensible del estudio: el código de los estudiantes y la referencia a sus repositorios, a veces privados. El plan exige que estos datos estén cifrados, que se eliminen al concluir y que la vinculación con personas quede "solo en poder del investigador" (plan 9.6; RNF-05, RNF-06; ESC-06, ESC-07). No hay análisis después de la intervención: el postest es la prueba de desempeño (01, PR-03).
2. **Refuerzo.** Lo usan 25 estudiantes durante las semanas 9 a 12, requiere ejecutar sus soluciones contra casos de prueba (RF-17, ESC-08) y registrar el uso (RF-18). Es la única parte que necesita estar en línea.

Restricciones que pesan: una sola persona, 6 semanas de desarrollo (RT-06), prototipo existente en Django con los servicios de análisis ya separados de la persistencia, y el riesgo de filtración de código en un servidor público (RT-10).

El stack de partida de `CLAUDE.md` prefería un monolito modular con trabajos en segundo plano.

## Decisión

Se adopta el estilo **CLI por lotes + portal mínimo**: el análisis, el entrenamiento, la asignación de conceptos y, si se decide, la corrección de T1–T3 corren **en la máquina del investigador** como comandos por lotes sobre un almacén local cifrado; un **portal web mínimo en la nube** importa un archivo de resultados sin código ni rutas y sirve el refuerzo, ejecuta ejercicios en un contenedor aislado, registra uso y exporta datos codificados.

Se implementa como **un solo proyecto Django con dos perfiles de ejecución** (local con la app de análisis; nube sin ella, sin Git y sin modelo), para reutilizar el prototipo y mantener una sola base de código y de pruebas.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| (a) Monolito modular en la nube con trabajos en segundo plano | Obliga a clonar repositorios en el servidor público, gestionar credenciales de repos privados y cifrar el código de todos los participantes en la nube; exige segundo plano, límites de clonado y Git en el servidor. Más superficie de ataque y más trabajo para una tarea que ocurre una vez (RT-10, ESC-06, ESC-07, RT-06). |
| (b) Servicios separados por módulo | Varios despliegues, red y autenticación entre servicios para 25 usuarios y una persona: sobredimensionado (ESC-21 a ESC-25, RNF-13). Hereda además el problema de privacidad de (a). |
| (c') Paquete Python independiente para el análisis + portal Django | Es la versión "limpia" de la decisión tomada, pero costaría una semana de reestructuración y dos sistemas de pruebas. Se deja como evolución posible en F10 si sobra tiempo. |

## Consecuencias

Se gana:
- El código de los estudiantes y las referencias a sus repositorios nunca salen de la máquina del investigador; el portal no puede filtrarlos porque no los tiene.
- El portal no necesita trabajos en segundo plano, colas, Git ni modelo: es una aplicación Django pequeña con una base pequeña.
- La reproducibilidad es natural: cada análisis es un comando con entradas explícitas (commit, versión del modelo, θ, λ, m).
- El módulo 3 [PENDIENTE] puede cerrarse como otro comando por lotes (corrección de T1–T3 en local), sin construir una interfaz de examen.
- Reutiliza el prototipo casi íntegro; el cambio estimado es de 2–3 días [PENDIENTE: validar en F10].

Se pierde o se asume:
- Dos almacenes (local y portal): la trazabilidad de un IDC hasta sus fragmentos exige que un identificador de análisis viaje en el archivo de resultados (ESC-16, ESC-20).
- Un paso manual: el investigador importa los resultados de 25 participantes una vez, en la semana 8. La importación debe validar el esquema y ser idempotente.
- El almacén local depende de la disciplina del investigador: cifrado y respaldo de una máquina personal (F6, F9).
- No habrá análisis "post" del repositorio desde el portal; si en el futuro se quisiera, se haría también en local.

Artefactos que cambian: `CLAUDE.md` (stack de partida: sin trabajos en segundo plano, LLM no en línea), `05-componentes-interfaces.md` (esquema del archivo de resultados, comandos del CLI, interfaz del ejecutor), `06-datos-privacidad.md` (dos almacenes), `09-despliegue.md` (portal + ejecutor; sin Git en la imagen).

## Verificación

- ESC-06/ESC-07: una búsqueda automática sobre la base del portal y sobre el archivo de resultados no encuentra código, rutas, URLs, correos ni hashes de commit (0 coincidencias).
- ESC-12: repetir `analizar` sobre el mismo commit con el mismo modelo y parámetros produce un archivo de resultados idéntico.
- ESC-16: desde cualquier IDC del portal se llega, por el identificador de análisis, a los fragmentos y probabilidades del almacén local.
- ESC-21: el portal se despliega sin Git ni dependencias de análisis instaladas, y la importación de 25 resultados tarda menos de 10 minutos de trabajo del investigador [PENDIENTE].
- RT-06: la adaptación del prototipo a dos perfiles no supera los 3 días en el backlog de F10; si los supera, se revisa esta decisión.
