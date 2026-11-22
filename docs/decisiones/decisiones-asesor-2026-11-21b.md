# Decisiones del asesor sobre la revisión del código (complemento)

**Proyecto:** Sistema de detección de dependencia hacia código generado por IA con refuerzo personalizado (tesis de Juan Pablo Zavala Valle, USIL)
**Responde a:** *Revisión del código del prototipo frente a las decisiones del 21 de noviembre* (secciones 3, 4 y 8)
**Complementa a:** `docs/decisiones/decisiones-asesor-2026-11-21.md` (D1–D18), que no se modifica
**Fecha:** 21 de noviembre de 2026
**Ubicación sugerida:** `docs/decisiones/decisiones-asesor-2026-11-21b.md`

---

## 0. Resumen para el programador

- Hay **5 respuestas** a las preguntas de la sección 8 (R1–R5) y **3 decisiones nuevas** (D19–D21).
- Hay **una acción de seguridad inmediata** (S1).
- La sección 4 fija el **orden de trabajo de F10** según el camino crítico. Las piezas que bloquean el pretest son el **banco A/B y el corrector de T1–T3**.
- Todo lo que sigue está aprobado; no queda nada pendiente del asesor.

---

## 1. Respuestas a la sección 8

### R1. HE5 se crea formalmente

- La comparación reforzado frente a control (control intrasujeto) pasa a ser **HE5**, una hipótesis propia y no un análisis "complementario a HE4".
- Se **agrega al final**: HG y HE1–HE4 mantienen la numeración de `plan.md` (D18 sigue vigente).
- **En el código y la documentación:**
  - Agregar HE5 a la matriz hipótesis ↔ requisitos (F1).
  - Los requisitos que hoy apuntan a "control intrasujeto" se reetiquetan como HE5.
  - Prueba principal: t pareada (o Wilcoxon) sobre Δ_reforzados − Δ_control por participante. Respaldo: modelo mixto `Δ ~ reforzado + concepto + (1 | participante)` (D17).

### R2. Orden AB/BA: aleatorización por bloques, en un flujo separado

- **Aprobado**, con dos condiciones:
  1. **Aleatorización por bloques**: permutaciones en bloques de tamaño 2 o 4, para garantizar que la mitad de la muestra reciba cada orden. Nada de una moneda independiente por participante.
  2. **Flujo aleatorio separado** del reparto de conceptos: derivar una semilla propia (por ejemplo, `hash(semilla_base + "orden")`) para que el orden no quede correlacionado con la asignación de conceptos.
- El orden se guarda **junto con la asignación**, con la misma fecha de congelación, **antes del pretest**.
- **En el código:**
  - Campo `orden` ∈ {`AB`, `BA`} en la tabla de asignación.
  - Función `sortear_orden(participantes, semilla)` con bloques permutados.
  - Prueba: con N participantes, |#AB − #BA| ≤ 1; la misma semilla reproduce el mismo resultado.

### R3. Modo exploratorio (F1 < 0.70)

- **Aprobado como propone ADR-004**: en modo exploratorio **se omite el caso A**, porque "débil" depende de un IDC que no sería confiable.
  - Se sortea entre los **calculables** (caso B).
  - Si hay menos de dos calculables, entre los **tres conceptos** (caso C).
- **Consecuencia que debe quedar escrita en el plan antes de ver los datos:**
  - **HE1 y HE2b pasan a exploratorias**, porque dependen del IDC.
  - **HE4 y HE5 siguen siendo confirmatorias**, porque la asignación sigue siendo aleatoria.
- **En el código:**
  - Parámetro `modo` ∈ {`confirmatorio`, `exploratorio`} en la configuración. Se fija una sola vez después de la evaluación del clasificador (go/no-go de la semana 7) y queda registrado en cada análisis.
  - El sorteo consulta `modo` antes de aplicar el caso A.
  - El valor de `caso` en la exportación refleja el caso efectivamente aplicado.

### R4. Heurística de tipos para el elemento 6 (`a[i]` sobre listas)

- **Aceptada**: "si no se puede saber el tipo, no cuenta".
- **Agregar una tercera salida**: además de *cuenta* y *no cuenta*, el elemento 6 devuelve **`indeterminado`** cuando hay indexación pero no se pudo inferir el tipo.
- `indeterminado` **no** asigna el concepto (se mantiene el criterio conservador), pero **se cuenta**.
- **En el código:**
  - Contador `n_indexacion_indeterminada` por fragmento y por participante, incluido en el análisis.
  - Incluir esos fragmentos en la muestra estratificada de D7, para que los anotadores midan cuántas listas reales esconde ese grupo.
  - Si resultan muchas, la regla v2 podrá sumar las anotaciones de tipo de los parámetros (`a: list[...]`). **No implementar eso ahora.**

### R5. Análisis "post" del repositorio: se elimina

- **Confirmado.** No hay IDC post, ni siquiera exploratorio.
- **En el código:**
  - Eliminar el segundo análisis, el campo `fase` y sus pruebas.
  - Un participante tiene **un único análisis válido**: el diagnóstico.
  - Si se vuelve a analizar el mismo participante (por ejemplo, por un error), el nuevo análisis **reemplaza** al anterior solo si la asignación todavía no se congeló. Si ya se congeló, se rechaza.

---

## 2. Decisiones nuevas

### D19. Filtro por autor en repositorios grupales

**Problema.** Hoy el sistema calcula con `git blame` el commit que escribió la mayoría de las líneas de cada función, y cuenta los autores, pero **no filtra**. En un repositorio grupal, el IDC incluye funciones de los compañeros: contamina la medida y analiza código de personas que no firmaron el consentimiento.

**Decisión.** Solo se analizan los fragmentos cuyo **commit mayoritario** (el que ya calcula `git blame`) pertenece al participante.

**Implementación:**
1. En el registro, el participante declara el o los correos que usa en sus commits (también figuran en el consentimiento).
2. Al registrarlo, el sistema guarda **solo un hash con sal** de cada correo (por ejemplo, HMAC-SHA256 con una sal local que no se versiona). El correo en claro no se guarda.
3. Durante el análisis, el correo del autor del commit mayoritario se hashea **en memoria** con la misma sal y se compara. No se guarda ni el correo ni el hash de terceros.
4. Los fragmentos de otros autores se **descartan** antes de clasificarlos. Se registra solo `n_fragmentos_otros_autores`.
5. El aviso de "varios autores" se mantiene como control de calidad.
6. El criterio de inclusión (verificar_inclusion) se evalúa **después** del filtro, con los fragmentos propios.

**Pruebas:**
- Un repositorio de ejemplo con dos autores: solo se analizan las funciones del participante.
- Ningún correo, en claro ni hasheado de terceros, aparece en la base de datos ni en los CSV (extender `test_no_se_guardan_datos_del_autor`).

**Limitación para declarar en la tesis:** la autoría del commit no siempre refleja quién escribió el código (programación en pareja, un compañero que sube el trabajo de otro).

### D20. Dosis y tamaño del banco de refuerzo

**Problema.** El banco actual (2 ejemplos y 3 ejercicios por concepto) se termina en una tarde. Con eso, la intervención de 4 semanas no tiene material y la "dosis" de refuerzo sería mínima, lo que debilita HE4 y HE5.

**Decisión:**
- **Dosis:** 2 bloques por semana, durante 4 semanas: **8 bloques por concepto reforzado**.
- **Bloque:** 1 explicación breve, 1 ejemplo resuelto y 3 ejercicios de dificultad creciente con casos de prueba.
- **Tamaño del banco:** 8 bloques × 3 conceptos = **24 bloques**, unos **72 ejercicios** y 24 ejemplos.
- Los bloques se liberan **por semana**, dos a la vez, para que el estudiante no consuma todo el material el primer día.

**Implementación:**
- Modelo `Bloque(concepto, semana, orden, version, validado)`. Los ejercicios y ejemplos cuelgan del bloque.
- Liberación por semana relativa a la fecha de inicio de la intervención (parámetro de configuración).
- Solo se entregan bloques con `validado = True` (HE3).
- Cada apertura e intento registra `bloque_id` y `version`.
- La adherencia = ejercicios intentados (o resueltos; definir uno y registrarlo) ÷ ejercicios liberados.

**Nota:** el contenido de los 24 bloques es trabajo de autoría, no de programación. Debe avanzar **en paralelo** con F10, porque los jueces tienen que validarlo antes de la semana 9.

### D21. Sin solapamiento entre el banco de refuerzo y la prueba de desempeño

**Problema.** Si un ejercicio del banco se parece demasiado a un ítem de la prueba (T1–T3, Q1–Q3), la mejora en el postest puede ser memoria del ejercicio y no aprendizaje ("enseñar para la prueba").

**Decisión:**
- Ningún ítem de las formas A y B, **ni sus isomorfos**, puede aparecer en el banco de refuerzo.
- Los jueces lo verifican con una pregunta específica en la ficha de validación.

**Implementación:**
- Guardar el banco de la prueba (formas A y B) **separado** del banco de refuerzo, en el perfil local, nunca en el portal.
- Script de control que compare los enunciados y las soluciones de referencia de ambos bancos (por ejemplo, similitud de AST de las soluciones) y liste los pares sospechosos para revisión manual. No hace falta que sea perfecto: es una alarma.

---

## 3. Acción de seguridad inmediata

### S1. Clave secreta de Django expuesta

- La clave secreta está escrita en el código y **publicada en el repositorio**. Aunque sea un prototipo local, **se considera comprometida**: queda en el historial de Git.
- **Hacer ya, antes de cualquier otra tarea:**
  1. Generar una clave nueva (`django.core.management.utils.get_random_secret_key()`).
  2. Leerla desde una variable de entorno (`DJANGO_SECRET_KEY`), con un `.env` local en `.gitignore`.
  3. `DEBUG` desde una variable de entorno, `False` por defecto.
  4. No hace falta reescribir el historial de Git, porque la clave vieja simplemente deja de usarse.

---

## 4. Orden de trabajo de F10 (camino crítico)

El orden lo fija **la fecha en que cada pieza bloquea el estudio**, no su tamaño.

| Prioridad | Pieza | Decisiones | Por qué en este orden | Lista para |
|---|---|---|---|---|
| 1 | Clave secreta y `DEBUG` por variable de entorno | S1 | Riesgo inmediato, trabajo trivial | Ya |
| 2 | Reglas `conceptos-v1` y `conceptos-v1-amplia`; recursión mutua y sobre atributo; salida `indeterminado` | D5, D6, R4 | SP-06 debe medirse con v1 | Antes de SP-06 |
| 3 | Filtro por autor | D19 | Cambia qué fragmentos entran y, con eso, lo que mide SP-06 | Antes de SP-06 |
| 4 | Quitar la característica 8 (`rasgos-v2`) e implementar el índice por historial | D9 | Pieza aislada; desbloquea el protocolo 07 | Antes del corpus real |
| 5 | Sorteo escalonado A/B/C, modo exploratorio, orden AB/BA por bloques, fecha de congelación; eliminar el análisis "post" | D2, D3, D16, R2, R3, R5 | Lo exige el diagnóstico | Semana 7 |
| 6 | **Banco A/B de la prueba y corrector de T1–T3** (`T_pct`, `cc_sol`, `cc_ref`, `lin_sol`, `lin_ref`) | D1, D16, D21 | **Sin esto no hay pretest.** Es la pieza más crítica que no está en marcha | Semana 7 |
| 7 | Protocolo 07: comandos `entrenar` y `evaluar` (división por autor, prueba reservada, calibración, θ por FP/sensibilidad, reporte por calidad, `ia_editado`, registro de experimentos) | D8, D10 | Depende de la sesión de etiquetado; da el go/no-go | Semana 7 |
| 8 | Perfiles local/nube, almacén local cifrado, acceso del investigador y del estudiante, contenedor aislado validado con SP-04 | D13, D14 | Nada sale a la nube sin esto | Antes de la semana 9 |
| 9 | Ajustes del portal: IDC oculto, liberación del control tras el postest, bloques por semana, versión y validación del material, registro de intentos bloqueados, no guardar el código de las soluciones (solo longitud y hash), quitar el enlace a la página del investigador | D4, D11, D20 | Obligatorios para la intervención | Antes de la semana 9 |
| 10 | Exportación D17 (unión de las tres partes después de cerrar la calificación), informe personal, borrado masivo al cierre, marca de exclusión | D13, D15, D17 | Se usan al final | Semana 13 |
| Paralelo | **Contenido de los 24 bloques de refuerzo** | D20, D21 | Lo validan los jueces | Antes de la semana 9 |
| Paralelo | Script de muestreo estratificado y exportación ciega para los anotadores | D7, R4 | Valida las reglas | Antes del diagnóstico |

**Si el tiempo no alcanza** (contingencia del plan 9.7): llegar a la semana 8 con el análisis, el sorteo y el corrector, y dejar el portal lo más simple posible. **No se recorta** el aislamiento del ejecutor si el portal va a la nube.

---

## 5. Cambios al modelo de datos (resumen)

| Tabla | Agregar | Quitar o cambiar |
|---|---|---|
| Configuración | `modo` (confirmatorio / exploratorio), fecha de inicio de la intervención, región de Azure | — |
| Participante | hashes de correos de commit (D19), fecha de consentimiento, fecha de retiro, `excluido` y motivo (D15) | **Quitar** la URL o ruta del repositorio (D14) |
| Análisis | `version_reglas`, `version_rasgos`, `n_fragmentos_otros_autores`, `n_indexacion_indeterminada`, resultado de inclusión, índice por historial | **Quitar** `fase` (R5) |
| Asignación | `caso` (A/B/C), `orden` (AB/BA), `modo` aplicado, fecha de congelación | **Cambiar** `comparable` por `caso` |
| Bloque de refuerzo (nuevo) | concepto, semana, orden, versión, validado | — |
| Intento de ejercicio | `bloque_id`, versión del recurso, longitud y hash de la solución; intentos sobre el concepto bloqueado | **Quitar** el código de la solución |
| Prueba de desempeño (nuevo, solo local) | ítems por forma, soluciones de referencia y métricas; puntajes T por participante y momento, sin datos de asignación | — |

---

## 6. Cambios en la documentación

| Documento | Cambio |
|---|---|
| `01-requisitos.md` | Agregar HE5 a la matriz; requisitos nuevos de D19, D20 y D21 |
| `05-componentes-interfaces.md` | Filtro por autor en el pipeline; modo exploratorio; orden AB/BA; bloques por semana |
| `06-datos-privacidad.md` | Hash con sal de los correos de commit; tablas nuevas; banco de la prueba solo en local |
| `07-ml-evaluacion.md` | Consecuencias del modo exploratorio sobre HE1 y HE2b |
| ADR-004 | Incluir el modo exploratorio y el orden AB/BA |
| `plan.md` (próxima versión, con cuadro de cambios) | HE5 formal; D19 en métodos y ética; dosis de refuerzo (D20); no solapamiento (D21); modo exploratorio y sus consecuencias; salida `indeterminado` |
