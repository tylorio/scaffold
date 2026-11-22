# ADR-004: Asignación escalonada: débiles, luego calculables, luego los tres conceptos

- Estado: aceptada (2026-11-21, decisiones D2 y D3 del asesor). Ampliada el mismo día con R2 (orden AB/BA), R3 (modo exploratorio) y R5 (un único análisis)
- Fecha: 2026-11-21
- Amplía: ADR-002 (el sorteo con semilla se mantiene; cambia el conjunto sobre el que se sortea)
- Fuente: `docs/decisiones/decisiones-asesor-2026-11-21.md` (D2, D3, sección 3.2) y `docs/decisiones/decisiones-asesor-2026-11-21b.md` (R2, R3, R5)

## Contexto

Con ADR-002, el sorteo se hacía solo entre los conceptos débiles. Un participante con un único concepto débil quedaba fuera del control intrasujeto (`comparable = false`). Con m = 5 y la escasez de recursión en los proyectos académicos, se preveía que bastantes participantes cayeran en esa situación (RV-03), lo que reducía el n del control intrasujeto por debajo del que supone el cálculo de potencia del plan (9.1.2).

## Decisión

1. **Conjunto elegible**, según el caso del participante:

   | Caso | Condición | Elegibles |
   | --- | --- | --- |
   | A | Hay 2 o más conceptos débiles | Los débiles |
   | B | Hay menos de 2 débiles y 2 o más calculables | Los calculables |
   | C | Hay menos de 2 calculables | Los 3 conceptos |

   Un concepto es calculable si tiene al menos m = 5 fragmentos. Es débil si es calculable y su IDC ≥ λ.

2. Dentro de los elegibles se sortean **hasta 2 reforzados y al menos 1 de control**, con una semilla registrada. El conjunto elegible siempre tiene al menos 2 conceptos, así que **todos los participantes entran en el control intrasujeto**. Este análisis compara puntajes de la prueba, que existen para los 3 conceptos.
3. El **caso** (A, B o C) se guarda junto con la semilla. Viaja en el archivo de resultados y en el CSV de análisis. El campo `comparable` de ADR-002 desaparece.
4. **El sorteo es un paso propio, por lotes, separado del análisis.** El comando `analizar` calcula el IDC y no sortea. Cuando todos los participantes tienen su diagnóstico, el comando `congelar_asignacion` hace dos cosas en una sola transacción:
   - sortea los conceptos de cada participante;
   - sortea el orden de las formas para toda la muestra (punto 7).

   Registra la **fecha de congelación**, anterior al pretest. Antes de congelar, volver a analizar a un participante **reemplaza** su análisis anterior; después de congelar, se rechaza (R5). Un participante tiene un único análisis válido. No hay análisis "post".
5. **Ciego de calificadores:** la asignación no aparece en ninguna salida que vea un calificador. El CSV de corrección de T1–T3 y la exportación para la rúbrica Q no llevan `reforzado`, `caso` ni la semilla.
6. Los conceptos que no salen sorteados como reforzados quedan como control. Su material se desbloquea después del postest (lista de espera, D4).
7. **Orden de las formas AB/BA (R2):**
   - Se aleatoriza **por bloques permutados** de tamaño 2 o 4, en el orden de los códigos, para que |#AB − #BA| ≤ 1.
   - Usa un **flujo aleatorio separado** del de los conceptos, para que el orden no quede correlacionado con la asignación.
   - Ambas semillas se derivan de una **semilla base del estudio** con SHA-256 (`sha256(semilla_base + ":conceptos:" + codigo)` y `sha256(semilla_base + ":orden")`). **No con `hash()` de Python**, porque se aleatoriza en cada proceso y no sería reproducible.
   - El orden se guarda en la asignación, con la misma fecha de congelación.
8. **Modo** (R3): un parámetro de configuración `modo` ∈ {`confirmatorio`, `exploratorio`}. Se fija **una sola vez**, después del go/no-go de la semana 7 y antes de congelar, y queda registrado en cada asignación.

**Modo exploratorio** (F1 < 0,70, plan 9.4), aprobado en R3. No se aplica el caso A, porque "débil" depende de un IDC que no es confiable. El conjunto elegible son los calculables si hay 2 o más, y si no, los 3 conceptos. `caso` registra el caso efectivamente aplicado.

Consecuencias que deben escribirse en el plan **antes de ver los datos**:
- HE1 y HE2b (el análisis de HE2 con el IDC global) pasan a exploratorias.
- HE4 y HE5 siguen siendo confirmatorias, porque la asignación sigue siendo aleatoria.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Mantener ADR-002 y reportar la potencia con los comparables | Pierde participantes del control intrasujeto justo donde n ya es pequeño. |
| Bajar m para que haya más conceptos calculables | Intervalos del IDC más anchos; el asesor fijó m = 5. |
| En el caso C, sortear solo entre los conceptos con al menos 1 fragmento | Complica la regla sin beneficio: la comparación usa los puntajes de la prueba, no el IDC. |

## Consecuencias

- La asignación ya no depende solo del IDC. En los casos B y C, el concepto reforzado puede no ser "débil". Por eso se reporta cuántos participantes hay en cada caso y se explora si la ganancia es mayor en el caso A.
- `repartir_conceptos` recibe el `ResultadoIDC` completo, no solo la lista de débiles. Devuelve `Reparto(reforzados, control, caso, exploratorio, semilla)`. Se añade `sortear_orden(codigos, semilla_base) -> dict[codigo, "AB" | "BA"]`. Esto cambia 05 §3.2.
- **HE4 dice "en los conceptos débiles"**, pero en los casos B y C, y en todo el modo exploratorio, los conceptos reforzados pueden no ser débiles. Para que HE4 se pueda calcular en todos los casos, su variable operativa debe ser el **desempeño en los conceptos reforzados**, que en el caso A y en modo confirmatorio coinciden con los débiles [PENDIENTE: confirmar con el asesor; afecta la redacción de HE4 en el plan].
- Limitación que hay que declarar en el plan: el concepto de mayor IDC puede quedar como control hasta el postest.
- Frase para el plan (8.3.1 nota o 9.2): la de la sección 3.2 del documento del asesor.

## Verificación

- `sortear_orden`: con N participantes, |#AB − #BA| ≤ 1. La misma semilla base reproduce el mismo orden, incluso en otro proceso. Cambiar la semilla de conceptos no cambia el orden.
- `analizar` después de `congelar_asignacion` se rechaza; antes, reemplaza el análisis anterior.
- Pruebas unitarias: para cada caso (A, B, C) y para el modo exploratorio, la misma semilla produce el mismo reparto. Siempre hay al menos 1 control y como máximo 2 reforzados. El caso se calcula bien en los bordes: exactamente 2 débiles, exactamente 2 calculables, 0 calculables.
- La marca de tiempo de la asignación de cada participante es anterior a la fecha de su pretest. Esto se comprueba en la exportación.
- Ninguna salida de `corregir_prueba` contiene `reforzado`, `caso` ni la semilla.
