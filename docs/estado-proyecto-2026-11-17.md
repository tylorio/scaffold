# Estado del proyecto: 17 de noviembre de 2026

Revisado el 21 de noviembre de 2026: se corrigieron errores de la primera versión (número de fases, relación de spikes con riesgos, fecha del go/no-go y cifras que no tenían fuente).

## Resumen

- **Arquitectura:** 7 de las 12 fases del protocolo están completas (F1 a F7). Hay 3 ADR.
- **Prototipo:** sin cambios desde el 2026-11-09 (262 pruebas pasan). El clasificador sigue siendo de demostración. Según CLAUDE.md, no se añade funcionalidad hasta F10.
- **Spikes:** hay 7 planificados (SP-01 a SP-07) y ninguno se ha ejecutado.
- **Asesor:** se le prepara un informe con 9 decisiones. Aún no se ha enviado.

## Fases

| Fase | Documento | Estado |
| --- | --- | --- |
| F1 Requisitos | `docs/arquitectura/01-requisitos.md` | Completa |
| F2 Escenarios de calidad | `02-escenarios.md` | Completa |
| F3 Riesgos y spikes | `03-riesgos-spikes.md` | Completa |
| F4 Contexto y contenedores | `04-contexto-contenedores.md`, ADR-001 | Completa |
| F5 Componentes e interfaces | `05-componentes-interfaces.md` | Completa |
| F6 Datos y privacidad | `06-datos-privacidad.md`, ADR-002 | Completa |
| F7 Clasificador y evaluación | `07-ml-evaluacion.md`, ADR-003 | Completa como protocolo; los umbrales se rellenan con los spikes |
| F8 Seguridad, ética y sandbox | — | Pendiente; solo depende de SP-04 |
| F9 Despliegue y costos | — | Pendiente; antes hay que verificar el crédito y los servicios de Azure for Students |
| F10 Plan de construcción | — | Pendiente; a partir de aquí se escribe código |
| F11 Revisión crítica | — | Pendiente |
| F12 Redacción para el plan | — | Pendiente |

## ADR

| ADR | Decisión | Estado |
| --- | --- | --- |
| ADR-001 | El análisis corre por lotes en local y en la nube solo hay un portal mínimo; un proyecto Django con dos perfiles | Aceptada |
| ADR-002 | Los conceptos a reforzar se sortean entre los débiles con una semilla registrada | Aceptada por el autor; falta la aprobación del asesor |
| ADR-003 | Clasificador tabular calibrado que se evalúa solo con el corpus propio, dividido por autor | Propuesta; se acepta cuando SP-01 y SP-03 fijen los umbrales |

## Lo que dejaron F6 y F7

**F6: datos y privacidad.** Los datos viven en tres lugares, cada uno con su propia clave, y lo sensible nunca sale del lugar donde se genera:

| Lugar | Contiene | Nunca contiene |
| --- | --- | --- |
| Almacén local, cifrado | Clones, fragmentos, rasgos, P(IA), modelos, soluciones de T1–T3 | Nombres, correos, URLs de repositorios |
| Portal en la nube | Códigos anónimos, IDC agregados con intervalo, asignaciones, uso del refuerzo | Código fuente, rutas, URLs, hashes de commit |
| Fuera del sistema | Tabla nombre ↔ código, cuestionario, puntajes, fichas de expertos | Código fuente |

F6 cambia tres cosas respecto del prototipo, y esos cambios se aplican en F10:
1. No se guarda la URL ni la ruta del repositorio.
2. Los intentos de ejercicios guardan solo el hash y la longitud, no el código.
3. Los tracebacks se recortan en el ejecutor.

**F7: clasificador.**
- El único conjunto de prueba es el corpus de la sesión de etiquetado controlado. Los conjuntos públicos solo se usan para entrenar.
- Los datos se dividen por autor.
- θ se fija por la tasa de falsos positivos y no por el F1.
- El go/no-go es en la **semana 7 del cronograma del plan** (9.4). Si el clasificador no pasa, entra el plan B: el IDC se reporta como exploratorio y el sorteo se hace entre los conceptos calculables.

## Decisiones de esta etapa (registradas en CLAUDE.md)

CLAUDE.md tiene 11 decisiones numeradas. Estas dos son del 2026-11-10:

- **10.** El código de IA editado a mano (`ia_editado`) no se usa para entrenar. Se evalúa aparte, con dos lecturas.
- **11.** Se añade un "índice de delegación por historial" como variable exploratoria para HE1.

## Spikes pendientes

| Spike | Pregunta que responde | Prioridad |
| --- | --- | --- |
| SP-06 | ¿Cuántos fragmentos por concepto hay en repositorios académicos reales? ¿Cuántos participantes tendrán dos conceptos débiles? | Primero |
| SP-05 | ¿Las reglas AST asignan bien los conceptos, comparadas con dos anotadores humanos? | Primero; necesita la guía de casos límite |
| SP-02 | ¿Cuántos fragmentos produce la sesión de etiquetado y cuánto dura? | Segundo |
| SP-01 | ¿El clasificador generaliza? Corpus propio frente a corpus públicos, dejando un asistente fuera | Segundo |
| SP-03 | ¿Con qué θ se mantienen bajos los falsos positivos? ¿Hay sesgo según la calidad del código? | Segundo |
| SP-04 | ¿El ejecutor aislado contiene el código malicioso? | Antes de F8 o junto con ella |
| SP-07 | ¿La perplejidad aporta lo suficiente para justificar su costo? | Solo si SP-01 queda en zona gris |

Los 7 umbrales marcados [PENDIENTE] en 07 se rellenan con SP-01, SP-02 y SP-03.

## Decisiones que esperan al asesor

Detalle en `docs/informe-asesor-2026-11-10.md`, sección 5.

| N.º | Decisión | Urgencia |
| --- | --- | --- |
| 5.1 | Fórmula del puntaje por concepto y del compuesto 0–20 | Alta: bloquea HE4 |
| 5.2 | Qué hacer con participantes que no tengan dos conceptos débiles | Alta: afecta la potencia |
| 5.3 | Aprobar la regla de sorteo (ADR-002) | Media |
| 5.4 | Definición operativa de "estructuras de datos" y casos límite | Alta: bloquea SP-05 |
| 5.5 | Qué lectura le corresponde a `ia_editado` | Media |
| 5.6 | Ética: spikes antes del comité, qué se conserva al final, Azure y Ley 29733, consentimiento de la sesión de etiquetado | Media: bloquea el consentimiento |
| 5.7 | Rangos de umbrales para el piloto | Baja |
| 5.8 | El estudiante no ve su IDC durante la intervención | Baja |
| 5.9 | Ajustes de redacción del plan | Baja |

## Riesgos principales

| Riesgo | Mitigación |
| --- | --- |
| Pocos participantes comparables para HE4 | Medir con SP-06; la regla la decide el asesor (5.2) |
| Corpus de etiquetado pequeño: el F1 tendría un intervalo muy ancho | Ensayo previo (SP-02); 6 enunciados de 2–3 funciones cada uno |
| Validez del constructo: un clasificador exacto no prueba dependencia | Interpretación escrita antes de ver los datos; HE1 y HE2 deciden |
| Falsos positivos contra el estudiante ordenado | Rasgos de historial; falsos positivos medidos por tercil de calidad (SP-03) |
| Tiempo: una persona y las semanas 1–6 del plan para el desarrollo | Corpus y clasificador antes que la interfaz; contingencia del plan 9.7 |

## Próximos pasos

1. Enviar el informe al asesor.
2. Ejecutar SP-06 y SP-05. Para SP-05 hace falta que el asesor y el docente de programación respondan 5.4.
3. Avanzar F8, que no depende del asesor salvo el punto 5.6.
4. Con las respuestas del asesor y los spikes: rellenar los umbrales de 07, aceptar ADR-003, y pasar a F9 y luego a F10.
