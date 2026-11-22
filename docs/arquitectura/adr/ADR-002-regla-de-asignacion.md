# ADR-002: Regla de selección de conceptos a reforzar: sorteo entre los débiles con semilla registrada

- Estado: aceptada (2026-11-09, por el autor). Aprobada por el asesor el 2026-11-21 (D3). **Ampliada por ADR-004** (D2): el conjunto sobre el que se sortea sigue una regla escalonada, el campo `comparable` desaparece y el modo exploratorio se trata allí.
- Fecha: 2026-11-09
- Fase y prompt de origen: F5–F6 / decisión anticipada en la revisión de F2 (RV-04 en `03-riesgos-spikes.md`)

## Contexto

El plan (9.2) exige que por estudiante se refuercen como máximo dos conceptos y al menos uno quede sin reforzar, y que los conceptos débiles se identifiquen con el IDC por concepto y no con el pretest, para evitar la regresión a la media. No dice **cómo elegir** entre los conceptos débiles cuáles se refuerzan y cuál queda de control (RF-15). La elección afecta al control intrasujeto (ganancia reforzado vs. ganancia control), que es la comparación que permite atribuir la mejora al refuerzo (plan 9.5).

## Decisión

Entre los conceptos débiles de un participante se eligen los reforzados **por sorteo**, con una semilla generada por análisis y registrada en la asignación y en el archivo de resultados. Con 3 débiles: 2 reforzados y 1 control; con 2: 1 y 1; con 1: se refuerza y el participante queda fuera de la comparación principal (`comparable = false`). Los conceptos no débiles quedan sin asignar. La asignación es inmutable; rehacerla exige borrar la anterior y queda en auditoría.

En modo exploratorio (F1 < 0,70, RF-13), el sorteo se hace entre los conceptos **calculables** (con ≥ m fragmentos) en lugar de entre los débiles [PENDIENTE: confirmar con el asesor; alternativa: entre los tres conceptos].

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Reforzar siempre los de mayor IDC y dejar de control el de menor IDC entre los débiles | El control sería sistemáticamente el "menos débil": la comparación reforzado vs. control queda sesgada por regresión a la media y por diferencias de partida; justo lo que el plan quiere evitar. |
| Reforzar el de mayor IDC y sortear el resto | Mezcla ambas lógicas; más difícil de explicar y de analizar; sigue sesgando el primer reforzado. |
| Dejar que el estudiante elija | Introduce autoselección (motivación, dificultad percibida) en la condición; invalida el control intrasujeto. |

## Consecuencias

- La comparación reforzado vs. control es equitativa en expectativa: ambos grupos de conceptos son débiles y la condición es aleatoria.
- Puede quedar sin refuerzo, hasta después del postest, el concepto de mayor IDC de un estudiante. Se mitiga liberando todo el material tras el postest (RF-19) y se declara como limitación en el plan.
- La semilla y el reparto deben viajar en el archivo de resultados y conservarse en el portal (05 §3.6; 06 §1.2) para reproducir y auditar.
- Cambia el texto del plan en 8.3.1 (nota) y 9.2: hay que escribir la regla [PENDIENTE: redacción para el asesor].

## Verificación

- Prueba unitaria: con la misma semilla y los mismos débiles, `repartir_conceptos` devuelve el mismo reparto (ESC-17).
- Con los datos del diagnóstico (semana 8): la distribución de condiciones por concepto no difiere sistemáticamente del azar (ningún concepto es "siempre control").
- El asesor aprueba la regla por escrito antes de la semana 7.
