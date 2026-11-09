# 00. Estado actual del repositorio y brechas frente al protocolo

- Fecha: 2026-11-09
- Fase: previa a F1 (paso 0 del protocolo, `docs/protocolo-prompts.md`)
- Fuentes: `docs/plan/plan.md` (plan de investigación), código del prototipo en `analisis/` y `refuerzo/`, `README.md`, historial de Git.

Este archivo no forma parte de las fases F1 a F12. Registra qué existía antes de adoptar el protocolo, qué contradice y qué falta, para que las fases siguientes partan de hechos y no del recuerdo. Las fases deben derivar sus artefactos del plan; este archivo solo dice dónde el prototipo ya aporta evidencia.

## 1. Cumplimiento del paso 0 (preparación)

| Paso | Estado | Nota |
| --- | --- | --- |
| Crear `docs/plan`, `docs/arquitectura/adr` | Hecho | |
| Convertir el plan a `docs/plan/plan.md` | Hecho | Sin pandoc (no está instalado). Se exportó el documento de Google Drive "01 Plan Trab Investigación" a Markdown con el conector de Drive. 669 líneas. Conserva la tabla de contenido con enlaces y marcas de formato de la exportación (`\*\*`, `\#`); el contenido es íntegro. |
| Crear `CLAUDE.md` con P0 | Hecho con cambios | Se corrigió lo que contradecía al plan (ver sección 6) y se añadió el estado del repositorio. |
| Guardar el protocolo en el repositorio | Hecho | `docs/protocolo-prompts.md`. |
| Una fase por sesión, con `/clear` | Pendiente | Empieza con P1. |

## 2. Inventario del prototipo

Prototipo en Django 5.2 con dos apps. Cuatro commits (2026-11-05) y **cambios sin confirmar** en 20 archivos más 3 archivos nuevos (asignación pre/post, aperturas de refuerzo, exportaciones). Las 262 pruebas pasan.

| Componente | Archivo | Módulo del plan | Qué hace |
| --- | --- | --- | --- |
| Lectura de repositorios | `analisis/servicios/repositorio.py` | 1 Análisis | Abre ruta local o URL con GitPython/PyDriller; HEAD, historial, `git blame`, número de autores (sin guardar correos). Rechaza URLs con credenciales. |
| Extracción de fragmentos | `analisis/servicios/extraccion.py` | 1 | Funciones y métodos con `ast`; omite archivos de pruebas y funciones triviales; complejidad con radon. |
| Asignación de concepto | `analisis/servicios/conceptos.py` | 1 | Reglas sobre el AST para `recursion`, `estructuras_datos`, `excepciones` (plan, 9.4). Solo recursión directa; sin inferencia de tipos. |
| Rasgos del clasificador | `analisis/servicios/caracteristicas.py` | 1 | 8 rasgos de estilo y estructura (comentarios, docstring, type hints, identificadores, uniformidad, complejidad, líneas, log del tamaño de inserción por commit). Sin perplejidad. |
| Entrenamiento | `analisis/servicios/entrenamiento.py`, `scripts/entrenar_modelo.py` | 1 | Pipeline scikit-learn, validación cruzada, paquete joblib con versión y bandera `es_demo`. **Corpus sintético.** |
| Predicción | `analisis/servicios/clasificador.py` | 1 | Carga el modelo y devuelve P(IA) por fragmento. θ = 0,5 sin calibración. |
| IDC | `analisis/servicios/idc.py` | 1 | IDC global y por concepto, intervalo de Wilson al 95 %, estados débil / no débil / datos insuficientes (m), sorteo reforzado vs. control con máximo 2 reforzados y al menos 1 control. |
| Orquestación y persistencia | `analisis/servicios/flujo.py`, `analisis/persistencia.py` | 1 | Fase pre (sortea y congela la asignación con semilla) y post (solo funciones escritas después del commit del pre). Guarda θ, λ, m y versión del modelo por análisis. |
| Exportación | `analisis/servicios/exportacion.py` | 1 / estadística | CSV de participantes, de análisis por concepto (pre/post, condición), de intentos y de aperturas. Sin código ni rutas. |
| Contenido de refuerzo | `refuerzo/servicios/contenido.py` | 2 Refuerzo | Plantillas fijas por concepto: explicación, ejemplos, ejercicios con casos de prueba. Sin LLM, sin revisión de expertos. |
| Ejecución de soluciones | `refuerzo/servicios/ejecutor.py`, `corredor.py` | 2 | Subproceso con tiempo límite y entorno mínimo. **No es un sandbox** (lo dice el propio módulo). |
| Interfaz | `templates/`, `analisis/views.py`, `refuerzo/views.py` | Plataforma | Lista y detalle de participantes, configuración de θ, λ, m, página de refuerzo por concepto (403 para el concepto de control). **Sin autenticación ni roles.** |
| Modelo de datos | `analisis/models.py`, `refuerzo/models.py` | Plataforma | Configuracion, Participante (código anónimo validado), Analisis, Asignacion, ResultadoConcepto, Fragmento (código completo), AperturaRefuerzo, IntentoEjercicio. SQLite sin cifrar. |

## 3. Lo que el prototipo ya cubre del plan

| Exigencia del plan | Sección | Evidencia en el prototipo |
| --- | --- | --- |
| Fragmento = función o método; concepto por reglas AST; un fragmento puede tener varios conceptos | 9.4 | `extraccion.py`, `conceptos.py` |
| IDC global = fragmentos con P(IA) ≥ θ ÷ analizados; IDC por concepto | 8.3.1 | `idc.py` |
| IDC por concepto solo con al menos m fragmentos | 9.4 | `evaluar_concepto`, estado `datos_insuficientes` |
| Máximo 2 conceptos reforzados y al menos 1 sin reforzar; selección independiente del pretest | 9.2 | `repartir_conceptos`, `Asignacion` congelada con semilla |
| Rasgos de estilo, nomenclatura, comentarios, complejidad y tamaño de inserción por commit | 9.4 | `caracteristicas.py` |
| Clasificador scikit-learn con validación cruzada | 9.4 | `entrenamiento.py` |
| θ y λ calibrables en el piloto | 9.3, 9.4 | `Configuracion`, y cada `Analisis` guarda los valores usados |
| Recurso de refuerzo con explicación, ejemplos y ejercicios con casos de prueba automáticos | 9.3 | `contenido.py`, `ejecutor.py` |
| Registro de uso del refuerzo (semanas 9–12) | 9.7 | `AperturaRefuerzo`, `IntentoEjercicio` |
| Participantes solo con código anónimo | 9.6 | validador `CODIGO_ANONIMO` |
| Exportación para el análisis estadístico | 9.5 | CSV de análisis con fase y condición |

## 4. Brechas frente al plan (insumo para F1 a F9)

| Brecha | Sección del plan | Fase donde resolverla |
| --- | --- | --- |
| No existe el cuestionario diagnóstico de 12 ítems ni su registro; HE1 y HE2 no se pueden contrastar con los datos que produce el sistema | 8.3.1, 9.3 | F1 (RF), F6 (datos) |
| No existe la prueba de desempeño, formas A y B (T1–T3, Q1–Q3), ni sus métricas de calidad; decidir qué parte administra el sistema | 8.3.2, 9.3 | F1, F5 |
| No hay flujo de juicio de expertos para los recursos de refuerzo (HE3, V de Aiken) | 8.1.2, 9.3 | F1, F5 |
| No hay informe personal de diagnóstico para el participante | 9.1.2 | F1 |
| No se verifican los criterios de inclusión (≥ 10 commits, ≥ 5 funciones propias) | 9.1.2 | F1 |
| El refuerzo de los conceptos de control después del postest no está contemplado | 9.2 | F1, F5 |
| Datos sin cifrar; sin procedimiento de borrado al concluir; se guarda el código completo de cada fragmento y la ruta o URL del repositorio | 9.6 | F6, F8 |
| Sin autenticación ni roles (estudiante, investigador, experto) | 9.6 | F8 |
| La ejecución de código ajeno no está aislada (sin contenedor, sin límites de memoria ni red) | — (seguridad) | F8 |
| Clasificador entrenado con corpus sintético; sin corpus real, sin calibración de probabilidades, sin evaluación por concepto ni por longitud, sin "dejar un LLM fuera" | 9.4 | F3 (spike), F7 |
| Sin rasgos de perplejidad; decidir si se incorporan | — | F7 |
| El análisis es síncrono y bloquea la petición; un clon colgado no tiene tiempo límite | — | F4, F5 |
| Sin despliegue, sin CI, sin respaldo; `SECRET_KEY` y `DEBUG=True` fijos en `settings.py` | — | F9 |
| No hay documentación de arquitectura ni ADR | — | F1 a F12 |

## 5. Riesgos ya detectados en sesiones anteriores

- Con m = 5, cada concepto necesita 5 funciones en el pre y 5 funciones nuevas en el post para compararse; falta validar con el asesor que los repositorios de 4 semanas produzcan eso. Llevar a F3.
- El concepto de control solo existe cuando hay al menos 2 débiles; con 1 débil el participante queda fuera de la comparación principal (`comparable = 0`). Impacta el n efectivo de HE4. Llevar a F3.
- El análisis post mide solo código nuevo desde el commit del pre; un `push --force` lo invalida. Llevar a F3 y F8.
- El tamaño de inserción por commit penaliza a quien sube todo en un commit. Llevar a F7.

## 6. Contradicciones entre el P0 original, el plan y el prototipo

La regla del protocolo es que gana el plan. Así se resolvieron en `CLAUDE.md`:

| Punto | P0 original | Plan | Prototipo | Resolución |
| --- | --- | --- | --- | --- |
| Framework web | FastAPI + Pydantic + SQLAlchemy | "Python, Django y scikit-learn" (1.3) | Django | `CLAUDE.md` fija Django como partida; FastAPI se compara en el ADR-001 (F4). |
| Módulo 3: pruebas pre/post dentro del sistema | Sí, con autocorrección | Prueba "en sesión supervisada y sin asistentes de IA", corregida "con rúbrica" (8.2, 9.3); no dice que la administre el sistema | No existe | [PENDIENTE] Decidir el alcance del módulo 3 en F1. T1–T3 son automatizables (casos de prueba, radon); Q1–Q3 necesitan rúbrica humana. |
| Explicaciones por LLM | Sí | No lo menciona (9.3) | Plantillas fijas | [PENDIENTE] Decidir en F1/F4; afecta costo, privacidad (envío de código a terceros) y la revisión de expertos. |
| Alcance del estudio | "correlacional y exploratorio-aplicada; sin lenguaje causal" | "correlacional y explicativo", preexperimental; en 9.5 habla de "atribuir" la mejora al refuerzo | — | Se mantiene lo de P0 para la redacción del software; señalar al asesor la diferencia de redacción en el plan [PENDIENTE]. |
| Plazo de desarrollo | 16 semanas | Desarrollo en semanas 1–6; operativo al final de la 6 (9.7) | — | `CLAUDE.md` hace explícito que diseño y construcción caben en 6 semanas. Afecta a F10. |
| Despliegue en Azure | Sí | No lo menciona | Solo local | Se conserva como restricción del autor, marcada [VERIFICAR]. |
| Base de datos | PostgreSQL | No lo menciona | SQLite | SQLite en desarrollo; PostgreSQL en despliegue [PENDIENTE] (F9). |

## 7. Desvío del proceso: hay código antes de F10

El protocolo prohíbe implementar antes de F10. El código ya existe y borrarlo no aporta nada. Tratamiento acordado en `CLAUDE.md`:

1. El prototipo es un **spike anticipado**. Sirve como evidencia en F1 a F9 (por ejemplo, demuestra que la extracción con `ast` y el cálculo del IDC son viables) y como medida de esfuerzo.
2. Las fases F1 a F9 **no deben describir el código**; describen lo que exige el plan. Donde coincidan, se cita el archivo. Donde no, gana el diseño.
3. En F10 se decide, componente por componente, qué se conserva, qué se reescribe y qué se descarta.
4. Hasta F10 no se añade funcionalidad. Los cambios sin confirmar de hoy deben confirmarse o descartarse antes de empezar P1, para que el punto de partida sea un commit identificable [PENDIENTE: decisión del autor].

## 8. Siguiente paso

Ejecutar **P1 (requisitos y trazabilidad)** en una sesión nueva (`/clear`). Entrada: `docs/plan/plan.md`, en especial objetivos (6), hipótesis (8.1), operacionalización (8.3) y metodología (9.1 a 9.7; en el plan la numeración interna va de 9.1 a 9.7, no de 9.1 a 9.4 como dice el prompt). Salida: `docs/arquitectura/01-requisitos.md`. Antes de aprobarla, aplicar la "Revisión de fase" del protocolo.

---

**Supuestos**
- El documento de Drive exportado es la versión vigente del plan.
- Azure for Students sigue siendo la plataforma de despliegue prevista.
- El prototipo se conserva como punto de partida y no se descarta.

**Decisiones que debes tomar**
- Alcance del módulo 3 (qué parte de la prueba A/B administra el sistema).
- Si el refuerzo usa un LLM o solo un banco curado.
- Confirmar o descartar los cambios sin confirmar en Git antes de P1.
- Si el plan debe decir "explicativo" o limitarse a "correlacional" (consultar al asesor).

**Riesgos**
- Seis semanas de desarrollo para 12 fases de diseño más construcción: el protocolo puede consumir el tiempo de implementar.
- El clasificador real no existe; todo el estudio depende de conseguir el corpus etiquetado (semanas 1–6).
- Con m = 5 y repositorios de 4 semanas, el análisis post puede quedar sin datos suficientes.

**Siguiente paso**
- `/clear` y pegar P1.
