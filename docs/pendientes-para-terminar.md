# Lo que falta para terminar el sistema

- Fecha: 2026-11-22. Estado del código: versión 0.10.0, 643 pruebas en verde.
- Para quién: el investigador. Dice qué tienes que hacer o entregarme tú, y en qué formato, para que el sistema quede completo.

## Resumen

El orden de F10 que fijó el asesor está construido, salvo la **pieza 7**: piezas 1 a 6, 8, 9 y 10. Lo que queda en código depende de cosas que solo tú puedes conseguir:

| Falta | Qué hago yo | Qué necesito de ti | Para cuándo |
|---|---|---|---|
| **SP-06**: distribución real de fragmentos | Correr el análisis sobre los repositorios y entregarte el informe para el asesor | Entre 5 y 10 repositorios (§1) | **Antes de la semana 4** (03-riesgos) |
| **SP-05**: validar las reglas de concepto | Muestrear los 150 fragmentos y calcular kappa y concordancia | Una segunda persona que anote, y tu propia anotación (§2) | Después de SP-06 |
| **Pieza 7**: modelo real y go/no-go | Evaluación por autor, calibración, elección de θ y decisión go/no-go | El corpus etiquetado (§3) | **Semana 7** |
| **F9**: despliegue en Azure | Configurar el portal y el ejecutor, y verificar la red y los límites | Acceso a Azure y la autorización escrita (§7) | Antes de la semana 9 |

Además, el sistema ya funciona, pero **no tiene contenido real**. El banco de la prueba, los 24 bloques de refuerzo y la rúbrica Q los escribes tú (§4 a §6).

## Actualización del 2026-11-23: entrega del asesor

Ya está en el sistema (`docs/decisiones/orientacion-asesor-2026-11-22.md`):

| Pieza | Estado |
|---|---|
| Banco de la prueba, formas A y B (§4) | **Listo.** En `datos/banco_prueba/`, fuera de Git; las 6 referencias pasan sus 60 casos con el corrector. Cuando crees el almacén cifrado, muévelo ahí (§8) |
| Bloques de estructuras de datos (§5) | **8 de 8.** Las 24 soluciones pasan sus 120 casos con el ejecutor, y los ejemplos devuelven lo que muestran (`tests/test_contenido.py`) |
| Bloques de excepciones y recursión | **Pendientes**: el asesor los manda en el próximo lote |
| Bloques del prototipo | No se pueden validar ni cargar en el portal: se solapan con la prueba |
| Alarma de solapamiento | Umbral calibrado a 0,2 con el banco real. Marca 3 pares con los bloques nuevos, que parecen falsas alarmas: los jueces los confirman con la pregunta 4 de su lista |
| Decisiones abiertas (§9) | Valores provisionales del asesor: informe «incierta» (0,3–0,5) y «muy incierta» (> 0,5); ECE ≤ 0,10; LOAO ≤ 0,10; 5 s por envío |
| Correo al CEI (§7) | Borrador en el zip del asesor: completa los campos `[COMPLETAR]` y envíalo tú |

**Guarda bien el zip** `contenido-asesor-2026-11-22.zip`: trae el banco real de la prueba. Está excluido de Git; muévelo al almacén cuando lo crees.

## Actualización del 2026-11-23 (tarde): segunda entrega del asesor

| Pieza | Estado |
|---|---|
| 24 bloques de refuerzo | **Completos.** Las 72 soluciones pasan todos sus casos con el límite real de 5 s |
| Alarma de soluciones (D22) | Hecha y calibrada en 0,30. Con la de enunciados marca 20 pares; `controlar_solapamiento --ficha` escribe la ficha para los jueces (D23) |
| Enunciados de la sesión de etiquetado | v1.1 en `datos/sesion_etiquetado/` (D31), fuera de Git. Las soluciones de referencia llegaron en la entrega 23b y pasan los 23 ejemplos; van al almacén, no a Git |
| Consentimientos, convocatoria y correo al CEI | Corregidos (D30) y en `docs/consentimientos/`. El correo v2 está en la entrega 23b: completa los `[COMPLETAR]` y envíalo |
| D29, D32 y D34 | `exc-s4-1-e3` reemplazado (la ficha baja a 18 pares), `aviso_concepto` en 7 ejercicios y 06 §4 corregido |
| 07 §1.3 y §1.4 | Actualizados con D24 a D27 |

---

## 1. Repositorios para SP-06

**Para qué:** saber cuántos participantes tendrán al menos 2 conceptos calculables con m = 5. De eso dependen m, los criterios de inclusión y la potencia de HE4 y HE5 (riesgos RT-09 y RV-03). Es lo primero, porque puede obligar a cambiar el plan.

**Qué necesito:**

| Dato | Detalle |
|---|---|
| Repositorios | Entre 5 y 10, académicos y en **Python**, con **historial Git**: una carpeta local con `.git` o una URL pública |
| Origen | **Tuyos o públicos.** De compañeros o voluntarios, solo si el asesor y el CEI lo autorizan (03, SP-06: [VERIFICAR ética]) |
| Correos de commit | Los correos con que se hicieron los commits de cada repositorio. Sin ellos, el filtro por autor (D19) descarta todo |
| Contexto | Una línea por repositorio: de qué curso o tarea es |

**Cómo pasármelos:** una lista como esta, en un archivo que **no se sube a Git**:

```text
C:\Users\...\mi_tarea_estructuras    correo1@ejemplo.com
https://github.com/usuario/proyecto  correo2@ejemplo.com, otro@ejemplo.com
```

**Qué te entrego:** por repositorio, los fragmentos totales y por concepto, los triviales, los commits, los autores y el tiempo de análisis. También el porcentaje de repositorios con 2 conceptos calculables (éxito ≥ 70 %; fracaso < 40 %), listo para el asesor.

## 2. Anotación para SP-05

- Una **segunda persona con formación en programación**, que anote a ciegas respecto a las reglas.
- Primero, una ronda de calibración de 20 fragmentos. Después, 150 fragmentos estratificados. Yo armo la muestra con los repositorios de SP-06 y te doy la planilla y la guía de una página (07 §7).
- Se exige kappa ≥ 0,70 por concepto (D7). Si no llega, se discuten los desacuerdos y se anota la decisión en la guía.
- Cuando termine SP-05, `conceptos-v1` queda congelada.

## 3. Corpus para la pieza 7

**Para qué:** reemplazar el modelo de demostración y decidir el go/no-go en la semana 7. GO exige F1 ≥ 0,70, falsos positivos ≤ 0,15 y sensibilidad ≥ 0,60 (07 §8, D10). Sin GO, el estudio pasa a **modo exploratorio**.

**Qué tienes que organizar:**

1. **Sesión de etiquetado (C1).** Entre 10 y 15 personas **fuera de la muestra**, con su consentimiento propio aprobado por el CEI (D15). Resuelven tareas de los tres conceptos, la mitad sin IA y la mitad con IA, en sesión supervisada. Cada una trabaja en un repositorio Git con un commit por tarea. Guarda dos cosas:
   - la salida cruda del asistente;
   - la versión final que entregó la persona (C3, `ia_editado`, que se evalúa aparte).
2. **Generación directa (C2).** Los mismos enunciados de C1, resueltos con los asistentes que usan los estudiantes y con varios estilos de prompt. Guarda cada salida con la fecha y la versión del asistente, porque no se puede regenerar igual.
3. **Tamaños orientativos (07 §1):**
   - C1: entre 60 y 120 fragmentos por clase;
   - C2: entre 300 y 450;
   - prueba final: **≥ 40 por clase**, solo de C1 y separada por autor.

**Formato:** JSONL, una línea por función, con los campos de 07 §1.2:

```json
{"id": "c1-007-t2", "fuente": "C1", "etiqueta": "humano", "autor_id": "E07",
 "tarea_id": "t2", "concepto_previsto": "estructuras_datos", "asistente": null,
 "estilo_prompt": null, "fecha": "2026-12-01", "insercion_commit": 42,
 "codigo": "def f(...): ..."}
```

- `etiqueta` es `humano`, `ia` o `ia_editado`.
- `autor_id` es obligatorio: la evaluación separa por autor para evitar fugas.
- **Nunca** entra al corpus código de participantes del estudio.

**Ojo:** quienes participen en la sesión de etiquetado no pueden estar en la muestra. Si alguno se registró, márcalo como **excluido → «Participó en la sesión de etiquetado»** en su detalle, antes de congelar.

## 4. Banco de la prueba (formas A y B)

**Bloquea el pretest:** sin el banco no hay validación de jueces, ni piloto, ni corrección.

- **Dónde:** `datos/banco_prueba/forma_A.json` y `forma_B.json`, dentro del almacén cifrado. **Nunca en Git ni en el portal** (D21).
- **Qué:** tres ítems por forma:
  - T1, recursión;
  - T2, estructuras de datos;
  - T3, excepciones.

  Las formas A y B van en **pares isomorfos**: misma estructura y mismos casos límite, con distinto contexto y valores (D16).
- **Formato:** igual al de [pruebas/banco_ejemplo/forma_A.json](../pruebas/banco_ejemplo/forma_A.json):

```json
{
  "forma": "A", "version": "real-v1",
  "items": [
    {"item": "T1", "concepto": "recursion", "enunciado": "...", "funcion": "contar",
     "referencia": "def contar(lista, x):\n    ...\n",
     "casos": [{"args": [[1, 2, 1], 1], "esperado": 2},
               {"args": [[], 5], "esperado": 0}]}
  ]
}
```

  - `referencia` es la solución modelo: el corrector comprueba que pase todos sus casos.
  - Un caso puede esperar una excepción con `"lanza": "ValueError"`.
- **Después:**
  - pásalo por los jueces;
  - corre `python manage.py controlar_solapamiento` contra los bloques de refuerzo;
  - ajustamos juntos los umbrales de la alarma de solapamiento, que siguen provisionales (P10).

## 5. Los 24 bloques de refuerzo

**Bloquean la semana 9:** el estudiante solo ve bloques validados.

- **Cuántos:** 8 por concepto (2 por semana × 4 semanas). Orden sugerido por el asesor: estructuras de datos, excepciones y recursión.
- **Cada bloque:** una explicación breve, **1 ejemplo resuelto** y **3 ejercicios** (fácil, medio y difícil), cada ejercicio con casos de prueba.
- **Dónde:** un archivo por bloque en `refuerzo/bloques/`, que sí va en Git. Nombre sugerido: `recursion-s1-1.json` (concepto, semana, orden).
- **Formato:** está en el README, sección «Bloques de refuerzo». Reglas:
  - `concepto` es `recursion`, `estructuras_datos` o `excepciones`;
  - `semana` va de 1 a 4 y `orden` es 1 o 2;
  - cada ejercicio lleva su `id`, la `plantilla` inicial, el nombre de la `funcion` y sus `casos`;
  - si cambias un bloque ya cargado, **sube su `version`**.
- **Cuidado con los casos de prueba:** el sistema no comprueba que estén bien. Un caso mal escrito hace fallar soluciones correctas. Si me pasas tu solución de cada ejercicio (aparte, sin publicarla), la agrego a las pruebas automáticas, como ya hice con los bloques de ejemplo.
- **Después:**
  - `python manage.py cargar_bloques`;
  - los jueces validan;
  - registras la validación en **Gestión**, con el número de jueces;
  - `controlar_solapamiento`.

  Cierra la validación **antes de la semana 9**: si validas tarde, cambia el denominador de la adherencia.

## 6. Rúbrica Q

Si quieres que `exportar_estudio` una las notas Q de los dos calificadores con los puntajes T, prepara un CSV con estas columnas:

```text
participante,concepto,momento,calificador,Q
P01,recursion,pre,1,14
P01,recursion,pre,2,15.5
```

- `momento` es `pre` o `post`, `calificador` es 1 o 2, y Q va de 0 a 20.
- Quien califica trabaja con el CSV de `corregir_prueba`, que no muestra la asignación (D3).

## 7. Trámites

| Trámite | Detalle | Bloquea |
|---|---|---|
| **Autorización escrita del alojamiento en Azure** | La emite **quien dio la autorización verbal (CEI-USIL)**, no el asesor. Pídela por correo y explica tres cosas: (1) qué se aloja: solo códigos anónimos, la asignación, el IDC agregado y el uso del refuerzo; (2) en qué región; (3) que la tabla código–nombre no sale de tu máquina. Va al Anexo F (D14) | El despliegue (F9) |
| **Consentimientos** | Dos documentos aprobados por el CEI: el del estudio y el de la sesión de etiquetado (D15). Ponle una **versión** a cada uno (p. ej. `v1`): el sistema pide la fecha y la versión al registrar | Registrar y analizar |
| **Convocatoria** | Exigir que cada participante entregue su repositorio **con el historial Git** y declare los correos de sus commits. Sin historial no hay índice por historial (HE1), y sin correos no hay filtro por autor (D19) | El diagnóstico |
| **Plazo de conservación** | El CEI fija cuánto tiempo se guardan los CSV agregados (D13). Está marcado [PENDIENTE] en el README | El cierre |

**Para F9, además:**
- dime qué suscripción de Azure usarás (¿Azure for Students?) y en qué región;
- tienes que poder crear recursos en ella. El resto de la configuración lo hago yo.

Tengo que verificar dos cosas en F9:
- que el servicio de contenedores permita una red interna sin salida a internet para el ejecutor;
- de qué cabecera sale la IP real detrás del proxy, para el bloqueo de accesos.

## 8. Tu máquina

Pasos que haces una sola vez, en este orden:

1. Crea el **almacén cifrado** (VHDX con BitLocker) siguiendo [docs/almacen-cifrado.md](almacen-cifrado.md), §1 y §2.
2. Pon `IDC_ALMACEN` en tu `.env` y genera la sal en el `.env` del almacén.
3. Prepara la base y comprueba el almacén:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py verificar_almacen
   ```

4. **Respalda** la clave de BitLocker y la sal. Si se pierden, no se puede repetir el filtro por autor.

Si ya tenías participantes de prueba registrados, no tienen consentimiento: regístralo o bórralos antes de analizar.

## 9. Decisiones que siguen abiertas

Llévalas al asesor cuando tengas los datos que las desbloquean:

| Decisión | Se decide con | Valor actual |
|---|---|---|
| m definitivo y criterios de inclusión | SP-06 | m = 5 |
| Modo del estudio (confirmatorio o exploratorio) | El go/no-go de la pieza 7, en la semana 7 | Se fija en Configuración antes de congelar |
| Umbrales de ECE y de caída LOAO | SP-03 y la pieza 7 | [PENDIENTE] en 07 |
| Umbrales de la alarma de solapamiento | Los primeros bancos reales (P10) | 0,5 y 0,8, provisionales |
| Cuándo un intervalo es «ancho» en el informe (RF-34) | Asesor | 0,5, provisional |
| Tiempo límite por envío de ejercicio | SP-04 y la carga real | 5 s |

## 10. Calendario

Necesito las **fechas reales** de cada semana del estudio para armar el cronograma. Por ahora solo sé lo que dicen los documentos:

| Semana | Qué pasa |
|---|---|
| Antes de la 4 | Resultados de SP-06 (y SP-02) al asesor |
| 7 | Go/no-go del clasificador, piloto y modo fijado en Configuración |
| 8 | Diagnóstico de los repositorios, **congelación** de la asignación (siempre antes del pretest) y pretest |
| 9 | Inicio de la intervención: fija esa fecha en **Gestión** |
| 9–12 | Intervención: 2 bloques por semana |
| 13 | Postest; después, **liberar el control** en Gestión |
| 14 | Análisis estadístico: `exportar_estudio` |
| Al terminar el análisis | `cerrar_estudio` y borrado (D13) |

## Lista corta, por prioridad

1. [ ] Pasarme de 5 a 10 repositorios con sus correos de commit (SP-06).
2. [ ] Pedir por escrito la autorización de Azure al CEI-USIL.
3. [ ] Escribir los ítems de las formas A y B.
4. [ ] Escribir los bloques, empezando por estructuras de datos.
5. [ ] Organizar la sesión de etiquetado y la generación del corpus.
6. [ ] Conseguir a la segunda persona que anote para SP-05.
7. [ ] Crear el almacén cifrado y correr `migrate` y `createsuperuser`.
8. [ ] Ajustar la convocatoria y los consentimientos, con su versión.
9. [ ] Pasarme las fechas reales de las semanas del estudio.
