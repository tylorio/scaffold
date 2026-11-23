# Decisiones del asesor (23 de noviembre de 2026, segunda parte)

**Responde a:** `docs/lo-que-necesito-2026-11-23.md` §1 (versión 0.12.0) y a la revisión del código que hice el mismo día.
**Numeración:** sigue la de `decisiones-asesor-2026-11-23.md` (D22 a D28).
**Nota del investigador (2026-11-23):** en esta copia se omitió, por D21, una frase que describe un ítem de la prueba. Lo demás está igual que el original.

## 1. Respuestas a §1

| # | Pediste | Respuesta |
|---|---|---|
| 1 | El archivo `soluciones_sesion_etiquetado.py` que faltó | No faltó: se lo envié a Pablo aparte para que no pasara por la carpeta del proyecto. Ahora va en esta entrega, en `soluciones_privadas/`, dentro de `docs/entregas-asesor/`, que está fuera de Git. Cuando exista el almacén, pasa al almacén junto con el resto de la entrega |
| 2 | Confirmar el `autor_id` de la sesión | **Aprobada tu propuesta (D31)** |
| 3 | Dos correcciones del consentimiento del estudio | **Aprobadas, con un agregado (D30)** |
| 4 | Dos comandos de la convocatoria que fallan en Windows | **Aprobados (D30)** |
| 5 | Revisar la pregunta 2 de D28 | **Aprobada tu redacción** para el correo al CEI (D30). Ya está en `correo-CEI-v2.md` |

## 2. Decisiones

### D29. Se reemplaza `exc-s4-1-e3` sin esperar a los jueces

La alarma de soluciones puso `procesar_inscripciones` contra T3 en 0,393, el par más alto de la ficha. Ese valor está dentro del rango de los solapamientos reales del prototipo con los que calibraste la alarma (0,32 a 0,57). D23 dice que basta un "misma tarea" para reemplazar, y aquí la evidencia ya apunta a eso. Además, yo mismo lo había dejado en duda en D22.

**El ejercicio nuevo** practica lo que el bloque s4-1 enseña: una jerarquía de excepciones propias, un atributo en la excepción y capturar solo la clase base. Se definen `ErrorReserva`, `SinStock(ErrorReserva)` con el atributo `faltan` y `ProductoDesconocido(ErrorReserva)`. `reservar_unidades(stock, producto, cantidad)` las lanza. `explicar_reserva(stock, producto, cantidad)`:

- devuelve `"reservado"`, `"faltan N"` o `"producto desconocido"`;
- deja pasar el `ValueError` de una cantidad no positiva.

[omitido en esta copia: describe un ítem de la prueba (D21); el original está junto al banco, en el almacén]

**Verificación con tu propia métrica.** Reproduje tu Jaccard de trigramas y obtuve el mismo 0,393 para el ejercicio viejo. Con el nuevo:

| Ítem | Parecido de soluciones | Parecido de enunciados |
|---|---|---|
| A/T3 y B/T3 | 0,186 | 0,056 |
| A/T1, B/T1 | 0,118 y 0,111 | menos de 0,05 |
| A/T2, B/T2 | 0,086 | menos de 0,08 |

Las 24 soluciones del concepto siguen pasando sus 120 casos, también con el archivo importado completo.

**Archivos:**
- `excepciones-s4-1.json` pasa a la **versión 2**: solo cambia el tercer ejercicio.
- Reemplaza `tests/soluciones_bloques/excepciones.py` por `soluciones_privadas/soluciones_excepciones.py` de esta entrega. Ese archivo ya no tiene `procesar_inscripciones`.
- Vuelve a generar la ficha de los jueces: los dos pares de `exc-s4-1-e3` deben desaparecer.

### D30. Correcciones a los documentos antes de enviarlos al CEI

Las cuatro correcciones de tu §3 estaban bien, y las apliqué. Los documentos siguen en **v1**, porque nadie los ha firmado ni el CEI los ha visto.

- **Consentimiento del estudio, «El portal web».** Usé tu texto y le agregué el mensaje de error: «**No se guarda tu código**: solo su longitud, una huella que no permite recuperarlo, el resultado de cada caso de prueba y, si el programa falló, el mensaje de error». El portal sí guarda ese mensaje (`IntentoEjercicio.error`), y puede contener texto que escribió el estudiante, como el de un `raise ValueError("...")`.
- **Consentimiento del estudio, «Tu repositorio».** Agregué tu texto tal cual.
- **Convocatoria.** Cambié los comandos a `git log --oneline -5` y `git shortlog -sne --all`, y les puse una línea que explica qué muestra `shortlog`.
- **Correo al CEI.** Tu redacción del punto 2 está en `correo-CEI-v2.md`, junto con los otros dos puntos de D28.
- **Nombre y correo del investigador.** Completé los tres documentos y el correo con Juan Pablo Zavala Valle y juan.zavalav@usil.pe, que es el correo de los commits del proyecto. Pablo debe confirmar que es el que quiere publicar.

**Para integrar:** reemplaza `docs/consentimientos/*.md` por los de esta entrega.

### D31. `autor_id` en la sesión de etiquetado: siempre el código de sesión

Tienes razón: mi §3 contradecía D27. Si el `autor_id` de las salidas crudas fuera el asistente, el código de una misma persona quedaría repartido entre dos autores. Entonces la separación por autor de la prueba final dejaría a la misma persona en entrenamiento y en prueba.

- **C1** (todo lo que sale de la sesión): `autor_id` es el código de sesión (S07), y el asistente va en el campo `asistente`.
- **C2**: no hay persona, así que `autor_id` es el asistente con su versión, como dice 07 §1.2.
- Dejar fuera un asistente (LOAO) se hace con el campo `asistente`, que cubre C1 y C2.

`enunciados-sesion-etiquetado-v1.1.md` cambia solo §3 y §4. Los enunciados de §1 no cambian, así que siguen sirviendo como instrucción del estilo C.

### D32. El aviso "No detectamos el concepto" se apaga en 7 ejercicios

Pasé las 72 soluciones de referencia por `extraer_funciones`, igual que hace `usa_concepto`. Siete no activan su concepto, aunque son correctas. Un estudiante que las resuelva bien vería que el portal le pide rehacerlas:

| Ejercicio | Por qué no se detecta |
|---|---|
| `ed-s1-1-e1` `stock_de` | `.get` sobre un parámetro: la regla v1 no sabe que es un diccionario (R4) |
| `ed-s2-1-e1` `tiene_duplicados` | `set(lista)` construido y no consultado: D5.1 exige consultarlo |
| `ed-s2-2-e1` `es_creciente` | Índices sobre un parámetro: indeterminado (R4) |
| `ed-s2-2-e2` `rotar_derecha` | Índices sobre un parámetro, dentro de una comprensión de lista |
| `ed-s2-2-e3` `par_con_suma` | Dos punteros sobre un parámetro |
| `ed-s4-1-e3` `fusionar_ordenadas` | Índices sobre parámetros |
| `exc-s4-2-e1` `dividir_lista` | La lección es justamente **no** capturar: la solución correcta no tiene `try` |

**Qué cambia:**

1. **Campo nuevo en el formato de bloques:** `"aviso_concepto": false` en el ejercicio. Si no está, vale `true`. Esta entrega trae los 5 bloques afectados con el campo y la versión subida: `estructuras_datos-s1-1`, `s2-1`, `s2-2` y `s4-1`, y `excepciones-s4-2`, todos en **v2**. Comprobé que, aparte del campo y la versión, son idénticos a los que tienes.
2. **El portal** no muestra el aviso cuando el ejercicio tiene `aviso_concepto: false`. Sigue guardando `usa_concepto` en el intento, que sirve para el análisis.
3. **El texto del aviso** se suaviza en todos los ejercicios: «No detectamos {concepto} en tu solución. Si funciona, está bien, pero este ejercicio busca practicar {concepto}: prueba resolverlo usándolo».
4. **`tests/test_contenido.py`:** agrega una prueba que falle si una solución de referencia no activa su concepto y el ejercicio no tiene `aviso_concepto: false`. Así esto no vuelve a pasar con un bloque nuevo.
5. **Documentación:** el README, sección «Bloques de refuerzo», documenta el campo.

**Para SP-05 y SP-06.** Cinco de los siete casos vienen de la misma causa: código de estructuras de datos que trabaja sobre un parámetro, donde la regla v1 no puede saber el tipo. En los repositorios reales eso es lo más común. Revisa en SP-06 qué proporción de fragmentos queda con `n_indexacion_indeterminada > 0`. Si es alta, es la primera limitación que irá al informe sobre la sensibilidad de ED.

### D33. Validación del clasificador en la pieza 7: separada por autor y calibrada

Hoy `entrenamiento.py` valida con `StratifiedKFold`, que reparte las muestras al azar. Con el corpus real, las muestras de una misma persona o de un mismo asistente caerían en entrenamiento y en prueba, y el F1 saldría inflado. Eso contradice 07 §5 y deja sin sentido la comparación con F1 ≥ 0,70. Además, las probabilidades no se calibran, así que θ = 0,5 todavía no significa nada (la propuesta PR-05 que dejamos pendiente).

Para la pieza 7, sin cambiar el algoritmo:

1. `cargar_corpus` lee también `autor_id`, `asistente` y `fuente`. Una muestra sin `autor_id` se rechaza.
2. La validación cruzada usa `StratifiedGroupKFold` agrupado por `autor_id`. Las métricas de validación del modelo de demostración se marcan como no válidas.
3. **Calibración:** `CalibratedClassifierCV` con `method="sigmoid"` y los mismos grupos. Con 300 a 500 muestras, `isotonic` sobreajusta. θ se elige en validación, y la prueba final se corre una sola vez (D10).
4. **Métricas en la prueba final:**
   - F1, FP y sensibilidad a θ;
   - ECE, con 10 intervalos de igual tamaño;
   - FP por tercil de calidad (D10);
   - F1 dejando fuera cada asistente, con su caída frente al promedio (LOAO).
5. El paquete del modelo guarda esas métricas y la lista de autores de la prueba final, para auditar que nadie quedó en los dos lados.

No hace falta implementarlo antes de tener el corpus, pero sí antes del go/no-go de la semana 7.

### D34. Repositorios privados: probarlo en SP-06 y corregir 06

El consentimiento ofrece entrar como colaborador de solo lectura. El sistema clona sin pedir credenciales y rechaza URLs con token, así que un repositorio privado solo se clona si Git, en la máquina de Pablo, ya tiene guardada su sesión de GitHub (Git Credential Manager).

- **En SP-06:** incluye al menos un repositorio **privado** de Pablo y analízalo por URL. Si falla, la salida para los participantes es la carpeta con su `.git`, que ya está en la convocatoria. En ese caso, avísame para ajustar el consentimiento.
- **El documento 06 no coincide con el código.** Dice que los clones se guardan hasta el final del análisis, y el código los borra en el momento. Corrige 06 §5 para que diga lo que hace el código, como ya dice el consentimiento. Lo que permite volver a un fragmento es `Fragmento.codigo` más `commit_head`.

## 3. Sobre las tareas de Pablo (§2)

El orden está bien. Dos precisiones:

- **Jueces (tarea 4):** antes de entregarles la ficha, intégrame D29 y vuelve a generarla. Si no, los jueces gastan tiempo en un ejercicio que ya se reemplazó.
- **Almacén (tarea 1):** que sea lo primero de hoy. En la carpeta del proyecto están sin cifrar el banco real, la ficha de pares y las copias completas de mis decisiones. Esta entrega también trae material privado, en `docs/entregas-asesor/2026-11-23b/`.
