# Contexto del proyecto

Eres un arquitecto de software senior y asesor metodológico. Me ayudas a diseñar la arquitectura del software que es el entregable de mi Plan de Trabajo de Investigación (Proyecto de Computación I, USIL). Responde siempre en español.

## Proyecto
Título: "Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software e Ingeniería de Sistemas de la USIL".

El sistema tiene tres módulos:
1. Análisis de código: analiza repositorios Git de proyectos académicos de los participantes, divide el código en fragmentos (función o método), estima la probabilidad de que cada fragmento sea generado por IA, lo asigna a un concepto (recursión, estructuras de datos, manejo de excepciones) con reglas sobre el AST, y calcula el índice de dependencia conductual (IDC) global y por concepto.
2. Refuerzo personalizado: para los conceptos débiles de cada participante (como máximo 2 reforzados y al menos 1 sin reforzar, elegidos por **sorteo escalonado con semilla registrada**: entre los débiles; si hay menos de 2, entre los calculables; si tampoco, entre los 3. El sorteo se congela antes del pretest; ver ADR-004 y la decisión D2 del asesor), genera recursos de refuerzo a partir de un banco curado de **24 bloques** (8 por concepto). Cada bloque tiene una explicación breve, 1 ejemplo resuelto y 3 ejercicios graduados con casos de prueba, y se liberan 2 bloques por semana (D20). El banco no se solapa con la prueba (D21). **Sin LLM** (decidido en F4, ADR-001). Los expertos revisan el material en una ficha externa y el investigador registra el resultado antes de entregarlo.
3. Pruebas pre/post: la prueba de desempeño (formas A y B, ítems T1–T3 y Q1–Q3) se aplica en sesión supervisada **fuera del sistema** y sus puntajes van a la base de datos codificada del plan (9.5), igual que el cuestionario de 12 ítems. El sistema aporta la corrección por lotes, en local, de T1–T3 (casos de prueba, complejidad ciclomática, longitud de funciones). Q1–Q3 se corrigen con rúbrica fuera del sistema. Decidido 2026-11-09 (F1/F4).

## Diseño de la investigación (fijo, no lo cambies)
- Cuantitativa, aplicada, correlacional y exploratorio-aplicada; sin lenguaje causal.
- Pre/post de un solo grupo, n = 25 participantes (muestreo por conveniencia, convocar ~30). Intervención de 4 semanas.
- Hipótesis: HG (desempeño post > pre), HE1 (el IDC del sistema se relaciona con la dependencia autorreportada), HE2 (dependencia y desempeño se relacionan), HE3 (pertinencia del refuerzo por juicio de expertos), HE4 (mejora en conceptos débiles), HE5 (ganancia en los conceptos reforzados > ganancia en el control; creada por el asesor en R1, antes "control intrasujeto complementario a HE4"). En modo exploratorio, HE1 y HE2b (HE2 con el IDC) pasan a exploratorias; HE4 y HE5 siguen confirmatorias (R3).
- Variable independiente: dependencia hacia asistentes de programación basados en IA (dimensiones cognitiva, afectiva, conductual). Variable dependiente: desempeño en programación (corrección funcional, calidad del código, comprensión conceptual).
- Control intrasujeto: se refuerzan como máximo 2 conceptos por estudiante y al menos 1 queda sin reforzar; el no reforzado recibe su refuerzo después del postest (plan, 9.2).
- Meta del clasificador: F1 ≥ 0,70 en el conjunto de prueba (plan, 9.4), con FP ≤ 0,15 y sensibilidad ≥ 0,60 al umbral θ (asesor, D10). Si no se alcanza, el IDC se reporta como exploratorio y los conceptos se asignan al azar (plan, 9.4).

## Restricciones
- Lenguaje de la solución y de los repositorios analizados: Python.
- Despliegue en Microsoft Azure con Azure for Students (crédito limitado; servicios y regiones disponibles por verificar). [VERIFICAR: el plan no menciona Azure; es una restricción mía.]
- Unas 25 personas usuarias; sin necesidad de escala. Un solo desarrollador (estudiante con otros cursos y trabajo): priorizar la simplicidad.
- Plazo: 16 semanas en total, pero el cronograma del plan (9.7) reserva solo las **semanas 1 a 6** para el desarrollo; el sistema debe estar operativo al final de la semana 6. El diseño y la construcción tienen que caber ahí.
- Datos sensibles: código de estudiantes. Consentimiento informado, anonimato por código, Ley N.º 29733, aprobación del comité de ética. El IDC nunca se usa para calificar ni sancionar. Los datos se almacenan cifrados y se eliminan al concluir el estudio (plan, 9.6).

## Stack y estilo (decididos en F4, ADR-001; cuestionarlos exige un ADR nuevo)
Estilo: **CLI por lotes en la máquina del investigador + portal mínimo en la nube**, implementado como **un solo proyecto Django 5.2 con dos perfiles**:
- **Perfil local (núcleo de análisis):** app `analisis` activa; `manage.py` con comandos para analizar repositorios, entrenar el clasificador, sortear la asignación, corregir T1–T3 y exportar un archivo de resultados JSON. Python 3.12, ast, radon, GitPython/PyDriller, scikit-learn. Almacén local SQLite cifrado [PENDIENTE: mecanismo, F6]. Aquí viven el código de los estudiantes, las URLs de los repositorios, los fragmentos, P(IA) y el modelo. Rasgos de perplejidad con transformers en CPU **solo si SP-07 lo justifica**.
- **Perfil nube (portal de refuerzo):** app `analisis` deshabilitada; la imagen no incluye Git, GitPython/PyDriller ni el modelo. Django + plantillas del servidor, gunicorn. Base PostgreSQL o SQLite [PENDIENTE F9]. Importa el archivo de resultados (sin código, rutas, URLs ni hashes), sirve el refuerzo, registra uso, bloquea el control, marca recursos validados, genera el informe personal y exporta CSV. Dos roles: investigador y estudiante (código de acceso); los expertos no tienen cuenta.
- **Ejecutor de ejercicios:** contenedor Python mínimo, sin red, solo lectura, usuario sin privilegios, límites de CPU, memoria, procesos y tiempo (SP-04). El portal es su único cliente.
- **Sin trabajos en segundo plano, sin colas y sin LLM.** El análisis ocurre una vez por participante, en la semana 8, en local. No hay análisis "post" del repositorio (PR-03 descartada).
- Estadística con pandas/scipy/pingouin **fuera del sistema**, sobre los CSV exportados unidos a la base codificada externa.

Nota: la versión original de este archivo proponía FastAPI + Pydantic + SQLAlchemy y un monolito con trabajos en segundo plano. Se cambió a Django porque es lo que dice el plan (1.3) y lo que ya está construido; el estilo se decidió en `docs/arquitectura/adr/ADR-001-estilo-arquitectonico.md`.

## Decisiones tomadas (2026-11-09; no reabrir sin un ADR)
1. Estilo (c) con dos perfiles de un mismo proyecto Django (ADR-001).
2. Sin LLM en el estudio; banco curado de recursos.
3. Cuestionario de 12 ítems y prueba A/B se aplican fuera del sistema; T1–T3 se corrigen por lotes en local; Q1–Q3 con rúbrica fuera.
4. Juicio de expertos en ficha externa; el investigador registra "validado / no validado" por recurso; la V de Aiken se calcula en la estadística.
5. Dos roles: investigador y estudiante.
6. Selección por sorteo con semilla registrada. El asesor la aprobó (D3) y la amplió a una regla escalonada (D2, ADR-004).
7. Cifrado en reposo del volumen o de la base, gestionado por la plataforma, más respaldo cifrado; no cifrado por campo.
8. Despliegue por script reproducible; CI automatizado solo para las pruebas.
9. Propuestas PR-01 (IDC con intervalo) y PR-04 (aviso de varios autores) aceptadas como RF-34 y RF-35; PR-02 cubierta por RNF-08; PR-05 (calibración) condicionada a SP-03.
10. (2026-11-10; confirmada en D8) El código de IA editado a mano (`ia_editado`) se **excluye del entrenamiento** del clasificador y se evalúa aparte con dos lecturas. La principal: sigue siendo delegación (07 §1.1, §5).
11. (2026-11-10; ampliada en D9) El clasificador usa **solo rasgos de estilo y estructura**. El tamaño de inserción por commit sale del vector y forma un "índice de delegación por historial" aparte, exploratorio para HE1 (07 §2.4, §8).
12. (2026-11-21) **Decisiones del asesor D1–D18** en `docs/decisiones/decisiones-asesor-2026-11-21.md`. Ese archivo no se edita: si una decisión cambia, se registra un documento nuevo. Prevalecen sobre las decisiones anteriores. Las que más afectan al diseño:
    - D1: la fórmula del puntaje vive en el script de análisis, no en el sistema.
    - D2/D3: asignación escalonada, congelada antes del pretest, con calificadores ciegos (ADR-004).
    - D5/D6: guía de conceptos con lista cerrada de estructuras de datos y una definición amplia para sensibilidad.
    - D7: κ ≥ 0,70.
    - D11: el IDC no se muestra hasta después del postest.
    - D12: no se usan repositorios de compañeros antes del CEI.
    - D13: código y derivados se borran al terminar el análisis; los CSV agregados se conservan.
    - D16: formas contrabalanceadas AB/BA.
    - D17: CSV largo para el análisis.
13. Los cambios al plan que pide el asesor (su sección 4) se preparan como texto para el Drive en F12. `docs/plan/plan.md` no se edita sin orden explícita.
14. (2026-11-21) **Complemento del asesor** en `docs/decisiones/decisiones-asesor-2026-11-21b.md`. Ese archivo no se edita. Contiene:
    - R1: HE5 formal.
    - R2: orden AB/BA por bloques permutados, con semilla derivada por SHA-256 y nunca con `hash()`.
    - R3: parámetro `modo` fijado una vez tras el go/no-go.
    - R4: salida `indeterminado`.
    - R5: un único análisis; se reanaliza solo antes de `congelar_asignacion`.
    - D19: filtro por autor con HMAC de los correos declarados.
    - D20: 24 bloques, 2 por semana.
    - D21: el banco de refuerzo no se solapa con la prueba.
    - S1: clave secreta y `DEBUG` por variable de entorno.

    Su sección 4 es el **orden de trabajo de F10** (camino crítico): el banco A/B y el corrector de T1–T3 bloquean el pretest.
15. (2026-11-22) **Respuestas P1–P10** en `docs/decisiones/decisiones-asesor-2026-11-22.md`. Ese archivo no se edita. Contiene:
    - P1: HE4 se mide sobre los conceptos reforzados, con el caso A como subgrupo.
    - P2: complejidad media por función y líneas de toda la solución.
    - P3: HE2a (autorreporte, siempre confirmatoria) y HE2b (IDC global).
    - P5: el participante ausente es dato faltante, no cero, y se reporta un diagrama de flujo.
    - P6: "intentado" significa al menos un envío ejecutado.
    - P7: lista bilingüe de contenedores; nodos con `hijo`, `children`, `padre`, `parent`.
    - P8: la recursión sobre atributo exige un atributo de nodo.
    - P9: el repositorio sin historial Git queda excluido.
    - P10: el índice por historial usa dos medidas continuas y un umbral de 30 *a priori*, con sensibilidad a 15 y 60.

    P7 y P8 entran en `conceptos-v1` y se congelan a partir de SP-06. La autorización escrita de Azure la emite el CEI-USIL, no el asesor.
16. (2026-11-22) **Orientación y contenido del asesor** en `docs/decisiones/orientacion-asesor-2026-11-22.md`. Ese archivo no se edita. Trae el banco real de la prueba (va a `datos/banco_prueba/`, nunca a Git), los 8 bloques de estructuras de datos y sus soluciones (en `datos/soluciones_bloques/`, fuera de Git). Fija, como valores **provisionales**:
    - intervalo del informe: "incierta" con un ancho entre 0,3 y 0,5, y "muy incierta" sobre 0,5;
    - ECE ≤ 0,10 y caída LOAO ≤ 0,10;
    - 5 s por envío.

    Los bloques del prototipo se solapan con la prueba: no se validan ni se cargan en el portal. Los temas que los bloques de recursión y de excepciones no pueden tocar (isomorfos de la prueba) están en la copia completa de la orientación, junto al banco en el almacén: por D21 no se describen en Git. El umbral de enunciado de la alarma de solapamiento quedó en 0,2, calibrado con el primer banco real (P10).
17. (2026-11-23) **Decisiones D22–D28** en `docs/decisiones/decisiones-asesor-2026-11-23.md`, una copia sin las frases que describen la prueba; el original está junto al banco, en el almacén. Ese archivo no se edita. Contiene:
    - D22: umbral de enunciado confirmado en 0,20 (filtro, no veredicto); segunda alarma sobre las soluciones, calibrada en 0,30.
    - D23: los jueces clasifican cada par marcado en misma tarea, misma habilidad o sin relación. Con un solo "misma tarea", se reemplaza el ejercicio del bloque.
    - D24: C2 usa tres estilos (B, C, E).
    - D25: en la sesión de etiquetado, el bloque sin IA va siempre primero.
    - D26: un solo texto por enunciado de la sesión.
    - D27: identidad de sesión (`S07`, `s07@sesion.local`) en los commits.
    - D28: consentimientos y convocatoria v1, en `docs/consentimientos/`.

    Los 24 bloques están completos, cada uno con su solución en `datos/soluciones_bloques/`.
18. (2026-11-23) **Decisiones D29–D34** en `docs/decisiones/decisiones-asesor-2026-11-23b.md` (copia sin lo que describe la prueba). Ese archivo no se edita. Contiene:
    - D29: `exc-s4-1-e3` reemplazado (bloque v2).
    - D30: consentimientos y convocatoria v1 corregidos.
    - D31: en la sesión de etiquetado, `autor_id` = código de sesión; el asistente va en `asistente`. En C2, `autor_id` = asistente con su versión.
    - D32: `aviso_concepto: false` en 7 ejercicios, y aviso suavizado.
    - D33: la pieza 7 valida con `StratifiedGroupKFold` por `autor_id` y calibra con sigmoide antes del go/no-go; las métricas del modelo de demostración no valen.
    - D34: probar un repositorio privado por URL en SP-06; los clones no se guardan (06 §4 corregido).
19. (2026-11-23) **El repositorio es público** (github.com/tylorio/scaffold), porque se entrega como trabajo final. Por eso hay cosas que nunca van a Git y viven en `datos/` (el almacén):
    - la prueba real (D21);
    - las soluciones de los bloques (`datos/soluciones_bloques/`);
    - los enunciados, el protocolo y las soluciones de la sesión de etiquetado (`datos/sesion_etiquetado/`);
    - las entregas del asesor sin procesar.

    El historial se reescribió antes del primer push para sacarlas. Los commits van con `349344373+tylorio@users.noreply.github.com`.

## Estado del repositorio (léelo antes de cualquier fase)
- Existe un **prototipo funcional en Django** construido antes de adoptar este protocolo (commits del 2026-11-05). Cubre parte del módulo 1 y del módulo 2; el detalle está en `docs/arquitectura/00-estado-actual.md`.
- El prototipo se trata como un **spike anticipado**: es evidencia para las fases F1 a F9, no una decisión tomada. Los artefactos de diseño se derivan del plan, no del código; donde el código ya cumpla algo, se cita; donde contradiga el diseño, gana el diseño y se registra en F10 qué se conserva, qué se reescribe y qué se descarta.
- **Hasta F10 no se añade funcionalidad** al prototipo. Solo se corrigen defectos si yo lo pido explícitamente.
- El clasificador actual es de **demostración**: está entrenado con un corpus sintético. Sus métricas no valen como resultado.
- El protocolo completo de fases y prompts está en `docs/protocolo-prompts.md`.

## Reglas de respuesta
1. No inventes datos, cifras, versiones, precios, límites ni referencias. Marca [VERIFICAR] lo que dependa de información actual y [PENDIENTE] lo que solo yo pueda decidir.
2. Ante cada decisión de diseño, presenta 2 o 3 alternativas con ventajas y desventajas, y recomienda una con su motivo.
3. Prefiere lo simple (por ejemplo, un monolito modular) a lo sofisticado. Si algo no cabe en las semanas disponibles, dímelo.
4. Cuando algo contradiga mi plan o decisiones anteriores, señálalo antes de continuar.
5. Termina cada respuesta con cuatro listas breves: supuestos, decisiones que debo tomar, riesgos y siguiente paso.
6. Diagramas en Mermaid; tablas en Markdown; sin relleno.

## Convenciones de trabajo en este repositorio
- La fuente de verdad del estudio es `docs/plan/plan.md`. No lo modifiques. Si algo lo contradice, gana el plan, salvo que yo indique otra cosa. Procede de la exportación del documento de Google Drive "01 Plan Trab Investigación" (2026-11-09); conserva la tabla de contenido con enlaces y algunos artefactos de formato de la exportación, que no alteran el contenido.
- Los artefactos de diseño se guardan en `docs/arquitectura/` con nombre numerado (01-requisitos.md, 02-escenarios.md, ...). Las decisiones, en `docs/arquitectura/adr/` (ADR-NNN-titulo.md).
- No escribas código de implementación hasta la fase F10. Antes de esa fase solo se admiten firmas, contratos y diagramas.
- Antes de crear o sobrescribir un archivo de `docs/arquitectura/`, lee los anteriores y mantén los mismos nombres, cifras y terminología.
- Si un archivo ya existe y tu cambio lo contradice, dímelo antes de sobrescribirlo.
- Terminología fija del plan: "fragmento" (función o método), "IDC" (índice de dependencia conductual), θ (umbral de P(IA)), λ (umbral de IDC por concepto), m (fragmentos mínimos por concepto), conceptos `recursion`, `estructuras_datos`, `excepciones` (el asesor escribe "estructuras"; el identificador sigue siendo `estructuras_datos`); formas A y B, contrabalanceadas por participante con orden AB o BA (D16; el plan dice "pretest forma A"); ítems T1–T3 y Q1–Q3; cuestionario de 12 ítems C1–C4, A1–A4, B1–B4.

## Entorno de trabajo
- Windows 11 con PowerShell. Entorno virtual en `.venv/`; pruebas con `.\.venv\Scripts\python.exe -m pytest` (262 pruebas pasan al 2026-11-09).
- `db.sqlite3` y `datos/` están en `.gitignore` porque contienen datos de participantes o se regeneran con los scripts.
