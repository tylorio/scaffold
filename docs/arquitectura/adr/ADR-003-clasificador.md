# ADR-003: Clasificador tabular calibrado, evaluado solo en corpus propio por autor

- Estado: propuesta (se acepta cuando SP-01 y SP-03 rellenen los umbrales)
- Fecha: 2026-11-10
- Fase y prompt de origen: F7 / P7

## Contexto

El plan (9.4) exige un clasificador scikit-learn entrenado con un corpus etiquetado por procedencia, evaluado con validación cruzada estratificada, con F1 ≥ 0,70 en un conjunto de prueba, y un umbral θ fijado en el piloto. Los riesgos dominantes son que el clasificador no generalice del código de competencia al código académico de la USIL (RT-01), que el corpus propio sea pequeño (RT-02), que los falsos positivos perjudiquen a estudiantes (RT-03) y que los rasgos de estilo marquen como IA al estudiante ordenado (RV-02). Hay una sola persona, CPU y seis semanas; el prototipo ya tiene 8 rasgos de estilo y un pipeline de scikit-learn.

## Decisión

1. **Rasgos tabulares** por fragmento (estilo, estructura AST, historial de commits), con la perplejidad como familia **condicional** a SP-07.
2. **Modelo de scikit-learn** elegido entre regresión logística (línea base), bosque aleatorio y gradient boosting por AUROC en validación cruzada **por autor**, prefiriendo el más simple a ±0,02 AUROC; **calibrado** (Platt) antes de usarse.
3. **El corpus de la sesión de etiquetado controlado (C1) es el único conjunto de prueba.** Los conjuntos públicos y la generación directa por asistentes solo alimentan el entrenamiento, y se mide si ayudan.
4. **θ se fija por tasa de falsos positivos** (≤ FP_max [PENDIENTE]), no por F1, sobre probabilidades calibradas fuera de pliegue, y no se cambia después del diagnóstico.
5. **Go/no-go en la semana 7** con F1 ≥ 0,70 en prueba como condición necesaria; si falla, plan B: IDC exploratorio y sorteo entre conceptos calculables (ADR-002).

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Ajuste fino de un modelo de lenguaje de código (clasificador neuronal) | Cientos de muestras, CPU, una persona y seis semanas: no cabe, y no sería reproducible con la misma facilidad. |
| Usar un detector de código IA de terceros (servicio o modelo preentrenado) | Caja negra sin calibración para código académico peruano; dependencia externa; posible envío de código a terceros (06 §5); no permite evaluar por concepto ni fijar θ por FP. |
| Entrenar y evaluar con conjuntos públicos (AIGCodeSet, MultiAIGCD) como referencia | Problemas tipo concurso, una función, asistentes antiguos: un F1 alto ahí no dice nada sobre el código de la USIL (RT-01). Se usan solo como aumento. |
| Solo rasgos de estilo (prototipo actual) | Mide "orden", no procedencia (RV-02). Se añaden estructura e historial y se exige revisar FP por tercil de calidad. |
| Fijar θ = 0,5 | Solo tiene sentido con probabilidades calibradas y no prioriza al estudiante frente a los falsos positivos. |
| Validación cruzada por fragmento (aleatoria) | Fuga por autor y por tarea: infla el F1 (RV-08). |

## Consecuencias

- La calidad del estudio depende de la sesión de etiquetado: su diseño (07 §1.3) y su consentimiento (06 §6) son parte del clasificador, no un trámite.
- Hay que generar y guardar salidas de varios asistentes con fecha y versión; no son reproducibles después.
- El modelo es interpretable por familias de rasgos, lo que permite explicar en la tesis qué separa las clases y revisar el sesgo por calidad.
- Todos los umbrales salvo F1 ≥ 0,70 son propuestas hasta que SP-01 y SP-03 los fijen; este ADR pasa a "aceptada" cuando se rellenen.
- Artefactos que cambian: `05` (A5 añade rasgos de estructura e historial; `RASGOS_VERSION` sube), `10` (sprints: corpus y sesión antes que interfaz).

## Verificación

- ESC-01: F1 ≥ 0,70 en el 20 % de autores de C1 reservado, evaluado una vez.
- ESC-02: FP a θ ≤ FP_max en ese conjunto, y diferencia de FP entre terciles de calidad ≤ [PENDIENTE].
- ESC-03: caída de F1 en LOAO ≤ [PENDIENTE] (si hay ≥ 3 asistentes).
- ESC-13: dos ejecuciones de `entrenar` con la misma semilla producen las mismas métricas y predicciones.
- SP-01 confirma o refuta que los conjuntos públicos aportan; el resultado se anota aquí.
