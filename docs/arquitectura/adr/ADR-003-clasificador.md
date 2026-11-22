# ADR-003: Clasificador tabular calibrado, evaluado solo en corpus propio por autor

- Estado: aceptada el 2026-11-21 (decisiones D8, D9 y D10 del asesor). Siguen pendientes los umbrales secundarios: ECE, caída en LOAO, F1 por concepto y casi duplicados. Los fijan SP-01 y SP-03.
- Fecha: 2026-11-10; modificada el 2026-11-21
- Fase y prompt de origen: F7 / P7. Fuente de los cambios: `docs/decisiones/decisiones-asesor-2026-11-21.md`

## Contexto

El plan (9.4) exige un clasificador scikit-learn entrenado con un corpus etiquetado por procedencia, evaluado con validación cruzada estratificada, con F1 ≥ 0,70 en un conjunto de prueba, y un umbral θ fijado en el piloto. Los riesgos dominantes son que el clasificador no generalice del código de competencia al código académico de la USIL (RT-01), que el corpus propio sea pequeño (RT-02), que los falsos positivos perjudiquen a estudiantes (RT-03) y que los rasgos de estilo marquen como IA al estudiante ordenado (RV-02). Hay una sola persona, CPU y seis semanas; el prototipo ya tiene 8 rasgos de estilo y un pipeline de scikit-learn.

## Decisión

1. **Rasgos tabulares** por fragmento, **solo de estilo y de estructura AST** (D9). La perplejidad es una familia **condicional** a SP-07. El tamaño de inserción por commit **sale del clasificador**: los rasgos de historial alimentan solo el índice de delegación por historial, que se calcula aparte como medida exploratoria para HE1.
2. **Modelo de scikit-learn** elegido entre regresión logística (línea base), bosque aleatorio y gradient boosting por AUROC en validación cruzada **por autor**, prefiriendo el más simple a ±0,02 AUROC; **calibrado** (Platt) antes de usarse.
3. **El corpus de la sesión de etiquetado controlado (C1) es el único conjunto de prueba.** Los conjuntos públicos y la generación directa por asistentes solo alimentan el entrenamiento, y se mide si ayudan.
4. **θ se fija por la tasa de falsos positivos (≤ 0,15) con una sensibilidad ≥ 0,60** (D10), no por el F1. Se calibra con probabilidades calibradas fuera de pliegue y no se cambia después del diagnóstico. Los falsos positivos se reportan por nivel de calidad del código.
5. **Go/no-go en la semana 7**, con F1 ≥ 0,70 en prueba como condición necesaria y una única evaluación sobre el conjunto de prueba. Si falla, se aplica el plan B: el IDC pasa a exploratorio y el sorteo sigue el modo exploratorio de ADR-004.
6. **El código de IA editado a mano** se excluye del entrenamiento y se evalúa aparte (D8). La lectura principal es que sigue siendo delegación; se reportan las dos lecturas.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Ajuste fino de un modelo de lenguaje de código (clasificador neuronal) | Cientos de muestras, CPU, una persona y seis semanas: no cabe, y no sería reproducible con la misma facilidad. |
| Usar un detector de código IA de terceros (servicio o modelo preentrenado) | Caja negra sin calibración para código académico peruano; dependencia externa; posible envío de código a terceros (06 §5); no permite evaluar por concepto ni fijar θ por FP. |
| Entrenar y evaluar con conjuntos públicos (AIGCodeSet, MultiAIGCD) como referencia | Problemas tipo concurso, una función, asistentes antiguos: un F1 alto ahí no dice nada sobre el código de la USIL (RT-01). Se usan solo como aumento. |
| Solo rasgos de estilo (prototipo actual) | Mide "orden", no procedencia (RV-02). Se añaden rasgos de estructura y se exige revisar los falsos positivos por tercil de calidad. |
| Incluir los rasgos de historial en el clasificador (propuesta original de F7) | El asesor decidió sacarlos (D9). Así el clasificador mide solo el producto y el historial queda como una medida independiente, lo que permite triangular con HE1. Se pierde el contrapeso al sesgo por calidad; por eso el reporte de falsos positivos por calidad pasa a ser obligatorio. |
| Fijar θ = 0,5 | Solo tiene sentido con probabilidades calibradas y no prioriza al estudiante frente a los falsos positivos. |
| Validación cruzada por fragmento (aleatoria) | Fuga por autor y por tarea: infla el F1 (RV-08). |

## Consecuencias

- La calidad del estudio depende de la sesión de etiquetado: su diseño (07 §1.3) y su consentimiento (06 §6) son parte del clasificador, no un trámite.
- Hay que generar y guardar salidas de varios asistentes con fecha y versión; no son reproducibles después.
- El modelo es interpretable por familias de rasgos, lo que permite explicar en la tesis qué separa las clases y revisar el sesgo por calidad.
- F1 ≥ 0,70, FP ≤ 0,15 y sensibilidad ≥ 0,60 están fijados para el piloto (D10). ECE, caída en LOAO, F1 por concepto y el umbral de casi duplicados quedan como propuestas hasta SP-01 y SP-03.
- En el prototipo se elimina la característica 8 (log de inserción por commit) del vector del clasificador. Esto se hace en F10.
- Artefactos que cambian: `05` (A5 quita el historial y añade rasgos de estructura; `RASGOS_VERSION` sube a `rasgos-v2`; aparece un componente nuevo para el índice por historial) y `10` (en los sprints, el corpus y la sesión van antes que la interfaz).

## Verificación

- ESC-01: F1 ≥ 0,70 en el 20 % de autores de C1 reservado, evaluado una vez.
- ESC-02: en ese conjunto, FP a θ ≤ 0,15 y sensibilidad ≥ 0,60. La diferencia de FP entre terciles de calidad se reporta siempre; su tope sigue [PENDIENTE].
- ESC-03: caída de F1 en LOAO ≤ [PENDIENTE] (si hay ≥ 3 asistentes).
- ESC-13: dos ejecuciones de `entrenar` con la misma semilla producen las mismas métricas y predicciones.
- SP-01 confirma o refuta que los conjuntos públicos aportan; el resultado se anota aquí.
