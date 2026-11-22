# Revisión del código del prototipo frente a las decisiones del 21 de noviembre

**Proyecto:** Desarrollo de un sistema de detección de dependencia en código generado por IA para optimizar el aprendizaje de programación en estudiantes de Ingeniería de Software e Ingeniería de Sistemas de la USIL, 2026
**Autor:** Juan Pablo Zavala Valle
**Fecha:** 21 de noviembre de 2026
**Para:** el asesor de tesis
**Responde a:** `docs/decisiones/decisiones-asesor-2026-11-21.md` (decisiones D1 a D18)

---

## Cómo leer este documento

Recorro el código del prototipo **en el orden en que viaja un dato**: desde que se lee el repositorio de un estudiante hasta que se exporta el CSV para la estadística. En cada parte explico, sin entrar en el código:

- **Qué hace hoy**;
- **Qué está bien** y conviene conservar;
- **Qué no cumple** el plan o alguna de sus decisiones (D1–D18), con la decisión citada;
- **Qué cambia** en la fase de construcción (F10).

La sección 4 reúne todo en una tabla: cada decisión suya, su estado en el código y el trabajo pendiente. La sección 8 tiene cinco preguntas que surgieron al cruzar sus decisiones con el plan.

Si solo tiene diez minutos, lea la sección 1 y la tabla de la sección 4.

---

## 1. Resumen

| Aspecto | Estado |
| --- | --- |
| Tamaño | Unas 4.600 líneas no vacías de Python, de las cuales ~1.500 son pruebas automatizadas |
| Pruebas | **262 pruebas pasan** (ejecutadas hoy, 68 s) |
| Tecnología | Django 5.2, scikit-learn, `ast` (biblioteca estándar), radon, GitPython y PyDriller, como dice el plan (1.3) |
| Qué funciona de punta a punta | Leer un repositorio → extraer funciones → asignar conceptos → estimar P(IA) → IDC global y por concepto con intervalo de Wilson → sortear reforzados y control → material de refuerzo con ejercicios autocorregidos → exportar CSV por código anónimo |
| Qué **no** vale como resultado | El clasificador: está entrenado con un **corpus sintético** que yo mismo generé con una regla inventada. Sus números solo prueban que el flujo funciona. La interfaz lo advierte en cada página |

**Conclusión general.** La estructura es sólida y gran parte se conserva. Los cálculos (IDC, intervalo, sorteo con semilla) están separados de Django, probados y son reproducibles. Hay buenas prácticas de privacidad desde el inicio. Pero el prototipo es **anterior a sus decisiones**, y hay seis puntos donde el código hace hoy algo distinto de lo decidido:

1. **La regla de estructuras de datos es mucho más amplia** que la lista cerrada de D5. Hoy cuenta cualquier indexación (incluidas las cadenas), cualquier lista literal, las comprensiones de lista y el `append`. Es incluso más amplia que la "definición amplia" del análisis de sensibilidad.
2. **El clasificador usa el tamaño de inserción por commit** como característica. D9 lo saca.
3. **El sorteo sigue la regla anterior** (solo entre débiles, con participantes "no comparables"), no la escalonada de D2.
4. **El estudiante ve su IDC** en la introducción del material de refuerzo. D11 lo prohíbe durante la intervención.
5. **El prototipo hace un segundo análisis del repositorio ("post")**, que el plan no contempla. El postest es la prueba de desempeño.
6. **No hay control de acceso**: cualquiera que conozca la dirección puede abrir cualquier página, incluidas las del investigador, que muestran el código de los estudiantes.

Además faltan partes completas: el módulo de corrección de las pruebas T1–T3, el ejecutor aislado, la verificación de inclusión, el desbloqueo del control tras el postest, el informe personal, el borrado y la separación local/nube.

---

## 2. Mapa del código

| Carpeta o archivo | Qué contiene | Líneas* |
| --- | --- | --- |
| `analisis/servicios/` | **Biblioteca de análisis, independiente de Django**: lectura del repositorio, extracción, conceptos, características, clasificador, IDC, flujo, exportación | ~1.200 |
| `analisis/models.py`, `persistencia.py`, `views.py`, `forms.py` | Capa Django del análisis: tablas, guardado, páginas del investigador | ~480 |
| `refuerzo/servicios/contenido.py` | Banco de material de refuerzo: 3 conceptos × (explicación + 2 ejemplos + 3 ejercicios con casos de prueba) | ~450 |
| `refuerzo/servicios/ejecutor.py`, `corredor.py` | Ejecución de las soluciones de los ejercicios | ~160 |
| `refuerzo/models.py`, `views.py`, `persistencia.py` | Registro de aperturas e intentos; página del material | ~150 |
| `config/` | Configuración de Django | ~120 |
| `templates/`, `static/` | Páginas HTML y estilos | — |
| `scripts/` | Generar el corpus sintético, entrenar el modelo, preparar el repositorio de ejemplo | ~320 |
| `demo_repo/` | Repositorio de ejemplo con funciones de los tres conceptos | ~130 |
| `tests/` | 8 archivos de pruebas | ~1.500 |

\* Líneas no vacías, aproximadas.

Que la biblioteca de análisis no dependa de Django es una decisión de diseño que se comprueba con una prueba automática (`tests/test_sin_django.py`). Gracias a eso, el análisis puede correr como comando local sin la parte web, que es justo lo que pide ADR-001: análisis por lotes en la máquina del investigador y portal mínimo en la nube.

---

## 3. Recorrido punto por punto

### 3.1 Lectura del repositorio (`analisis/servicios/repositorio.py`)

**Qué hace.** Recibe la ruta de una carpeta o la URL de un repositorio. Si es una URL, la clona en una carpeta temporal **que se borra al terminar**. Recorre los archivos `.py` de la versión actual (HEAD) y omite:
- entornos virtuales, migraciones y carpetas de compilación;
- **archivos de pruebas** (`test_*.py`, carpetas `tests/`), porque no miden el concepto.

Con el historial Git calcula dos cosas por fragmento:
- el **commit que escribió la mayoría de sus líneas**, con `git blame`, ignorando cambios de espacios y siguiendo el código movido;
- el **número de líneas que añadió ese commit** ("tamaño de inserción").

También cuenta cuántos autores distintos aparecen, para avisar si el repositorio no es individual.

**Qué está bien.**
- Rechaza las URL que traen usuario, contraseña o token. Quedarían guardados en la base de datos.
- Los correos de los autores se usan **solo en memoria**: se guarda la cantidad, nunca los correos (prueba `test_no_se_guardan_datos_del_autor`).
- El tamaño de inserción se mide por commit, no por archivo. Así, un pegado grande repartido en varios archivos se ve como lo que es.
- Un repositorio sin historial no rompe el análisis: el tamaño queda vacío.

**Qué no cumple.**
- **No verifica los criterios de inclusión** (mínimo de commits y de funciones propias del plan 9.1.2). Hoy se analiza cualquier repositorio.
- **Clona en cada análisis** y no conserva una copia local fija. El diseño (06) exige guardar el clon en `repos/<código>/` dentro del almacén cifrado para poder reproducir el análisis sobre el mismo commit.

**Qué cambia en F10.** Añadir la verificación de inclusión (comando `verificar_inclusion`) y la copia local del clon. El tamaño de inserción **se sigue calculando**: ya no entra al clasificador (D9), sino al índice de delegación por historial.

### 3.2 Extracción de fragmentos (`analisis/servicios/extraccion.py`)

**Qué hace.** Con el analizador sintáctico de Python (`ast`) obtiene **cada función o método** como un fragmento. Para cada uno guarda su código, sus líneas, su complejidad ciclomática (radon) y sus conceptos. **Las funciones anidadas se funden con la que las contiene** y sus conceptos se suman a ella, como aprobó en D6. Las funciones **triviales** (una sola sentencia sin ningún concepto, como un *getter*) se marcan y no cuentan para el IDC. Los archivos que no se pueden interpretar se listan y se omiten.

**Qué está bien.** Cumple D6 en lo relativo a funciones anidadas. Las triviales con `raise` no se descartan, porque tienen un concepto, y eso es coherente con D6 ("cuenta el `raise` en una función corta de validación").

**Qué no cumple.** Nada relevante.

**Qué cambia en F10.** Nada sustancial.

### 3.3 Asignación de conceptos (`analisis/servicios/conceptos.py`)

Es la parte más afectada por sus decisiones D5 y D6. Comparo regla por regla:

| Regla | Qué hace hoy el código | Qué dice su decisión | Estado |
| --- | --- | --- | --- |
| Recursión directa | `f()` dentro de `f`; en métodos, `self.f()`, `cls.f()` o `Clase.f()` | Cuenta | **Cumple** |
| Recursión mutua (`a`→`b`→`a`) | No la detecta | Cuenta (D6) | **No cumple** |
| Recursión sobre atributo (`self.izquierda.insertar(x)`) | No la detecta | Cuenta (D6) | **No cumple** |
| `try/except`, `raise`, `except:` vacío | Cuenta todos | Cuentan (D6) | **Cumple** |
| Diccionario o conjunto construido y consultado | Cuenta, pero también cuenta cualquier literal suelto | Solo si se construye **y** se consulta (D5.1) | Más amplio de lo decidido |
| Comprensión de diccionario o conjunto | Cuenta | Cuenta (D5.2) | **Cumple** |
| **Comprensión de lista** | **Cuenta** | **No cuenta** | **No cumple** |
| `sort`, `sorted` | Cuenta | Cuenta (D5.3) | **Cumple** |
| `bisect`, `heapq` | No los detecta | Cuentan (D5.3) | **No cumple** |
| `deque`, `Counter`, `defaultdict` | Cuenta | Cuenta (D5.4) | **Cumple** |
| Colecciones anidadas | Cuenta de forma indirecta | Cuenta (D5.5) | Parcial |
| Índices sobre listas (`a[i]`) | Cuenta **cualquier** indexación | Solo sobre listas (D5.6) | Más amplio |
| **Indexar o rebanar cadenas** (`s[0]`) | **Cuenta** | **No cuenta** | **No cumple** |
| `pop`, `appendleft` | Cuenta | Cuenta (D5.7) | **Cumple** |
| **`append` acumulativo** | **Cuenta** | **No cuenta** | **No cumple** |
| Clase contenedora propia | Cuenta si define `__len__`, `__iter__`, `__getitem__`, etc. | También `push`/`pop` y nodos enlazados (`self.siguiente`, `self.izquierda`) (D5.8) | Parcial |
| Leer el resultado de una biblioteca (`r["datos"]`) | Cuenta (es una indexación) | No cuenta | **No cumple** |
| `return a, b`, desempaquetado | No cuenta | No cuenta | **Cumple** |
| Anotaciones de tipo (`lista: list[int]`) | **Cuentan** como estructura de datos | Su lista no las incluye | **No cumple** |

**Lectura.** Hoy la regla de estructuras de datos es **más amplia incluso que la "definición amplia"** que usted pidió para el análisis de sensibilidad (v1 más `append` y comprensiones de lista). En la práctica, casi cualquier función con una lista cae en este concepto: es el problema de discriminación que motivó D5.

**Qué cambia en F10.**
- Reescribir la regla en **dos versiones con nombre**: `conceptos-v1`, su lista cerrada, y `conceptos-v1-amplia`, v1 más `append` y comprensiones de lista. El IDC se calculará con las dos.
- Añadir la detección de la recursión mutua (ciclos en el grafo de llamadas del archivo) y de la recursión sobre atributo.

**Una limitación técnica que debe conocer: el elemento 6 (`a[i]` solo sobre listas).** Python no declara tipos, y el analizador sintáctico no sabe si `a` es una lista o una cadena. Propongo una heurística conservadora: `a` cuenta como lista si en la misma función se asignó desde una lista literal, `list()`, `sorted()` o `.split()`, o si se le aplica un método propio de las listas. **Si no se puede saber el tipo, no cuenta.** El costo es que algunas listas legítimas quedarán fuera. La validación con anotadores (D7) medirá cuántas.

### 3.4 Características para el clasificador (`analisis/servicios/caracteristicas.py`)

**Qué hace.** Calcula 8 números por fragmento:

| # | Característica | Familia |
| --- | --- | --- |
| 1 | Densidad de comentarios | Estilo |
| 2 | Tiene docstring | Estilo |
| 3 | Proporción de anotaciones de tipo | Estilo |
| 4 | Longitud media de los identificadores | Estilo |
| 5 | Uniformidad de estilo (convención de nombres y tipo de comillas) | Estilo |
| 6 | Complejidad ciclomática | Estructura |
| 7 | Líneas de código | Estructura |
| 8 | **log(tamaño de inserción del commit)** | **Historial** |

**Qué no cumple.** **La característica 8 contradice D9**, que deja el clasificador solo con estilo y estructura.

**Qué cambia en F10.** Se elimina la característica 8 y la versión de las características pasa a `rasgos-v2`. Se añaden las de estructura del protocolo (anidamiento, idioms de Python, retornos tempranos, etc.; documento 07 §2.2), solo si mejoran la validación. El tamaño de inserción pasa a un cálculo aparte, el **índice de delegación por historial**, que será la medida exploratoria para HE1.

**Consecuencia que conviene tener presente.** Con D9 el clasificador queda midiendo **solo el producto** (cómo se ve el código), y no el proceso. El riesgo de que el estudiante ordenado, que documenta y anota tipos, se clasifique como IA aumenta. Por eso el reporte de falsos positivos por nivel de calidad (D10) es imprescindible.

### 3.5 Entrenamiento y clasificador (`entrenamiento.py`, `clasificador.py`, `scripts/`)

**Qué hace.** Entrena una **regresión logística**: imputa los valores faltantes, estandariza y luego ajusta el modelo. Reporta exactitud, F1 y AUROC con validación cruzada estratificada de hasta 5 pliegues, después entrena con todas las muestras y lo guarda en un archivo con su versión y una marca "es demostración".

El corpus actual lo genera `scripts/crear_corpus_demo.py`: 150 funciones "humanas" y 150 "de IA", producidas a partir de plantillas con probabilidades inventadas de docstring, anotaciones, comentarios y nombres largos. **El modelo aprende esa regla inventada, no a detectar IA.**

**Qué está bien.** La regresión logística es la línea base del protocolo (07 §3). El aviso de "modelo de demostración" aparece en todas las páginas mientras el modelo esté marcado así. El módulo de entrenamiento es el único que cambia al pasar al corpus real.

**Qué no cumple el protocolo de evaluación (07) ni D10.**

| Exigencia | Hoy |
| --- | --- |
| División **por autor** (ningún autor en entrenamiento y prueba a la vez) | La división es por fragmento: hay fuga entre autores |
| Conjunto de prueba reservado y evaluado **una sola vez** | No hay conjunto de prueba; solo validación cruzada |
| Calibrar las probabilidades | No se calibran |
| θ elegido por FP ≤ 0,15 con sensibilidad ≥ 0,60 (D10) | θ se fija a mano en la configuración (0,5 por defecto) |
| Falsos positivos por nivel de calidad (D10) | No se calculan |
| `ia_editado` evaluado aparte (D8) | No existe la etiqueta |
| Registro del hash del corpus, la semilla y la versión de las características | Solo se guardan la versión y la fecha |

**Qué cambia en F10.** Comandos `entrenar` y `evaluar` que implementen el protocolo 07: división por autor, prueba reservada, calibración, curva FP–sensibilidad para elegir θ, reporte por tercil de calidad, por concepto y por longitud, y registro de experimentos. Esto **depende del corpus real**, que sale de la sesión de etiquetado.

### 3.6 IDC, intervalo y sorteo (`analisis/servicios/idc.py`)

**Qué hace.**
- **IDC** = fragmentos con P(IA) ≥ θ ÷ fragmentos analizados, global y por concepto.
- Un concepto con menos de **m = 5** fragmentos queda como "datos insuficientes" (no calculable). Si es calculable y su IDC ≥ λ, es **débil**.
- **Intervalo de Wilson al 95 %** para cada IDC. El código documenta que el intervalo no incluye el error del clasificador.
- **Sorteo**: con una semilla aleatoria segura, reparte los débiles entre reforzados (máximo 2) y control (al menos 1). Con un solo débil, lo refuerza y marca al participante como "no comparable".

**Qué está bien.**
- m = 5 por defecto (D2).
- Wilson está bien implementado, con pruebas en los bordes (0 y 1).
- La semilla se guarda y **reproduce la misma asignación** (prueba `test_la_semilla_guardada_reproduce_la_asignacion`).
- La asignación es **inmutable**: no se puede editar, solo borrar desde el panel de administración, y borrarla queda visible.
- Se sortea en el **primer análisis**, que es el diagnóstico, y por tanto antes del pretest, como exige D3.

**Qué no cumple.**
- **Asignación escalonada (D2):** faltan los casos B (sortear entre calculables) y C (entre los tres). Hoy, quien tiene menos de dos débiles queda "no comparable", justo lo que D2 elimina.
- **Modo exploratorio:** no existe. Si el F1 queda por debajo de 0,70, no hay cómo cambiar la regla.
- **Marca de tiempo "congelada antes del pretest" (D3):** hay una fecha de creación, pero el sistema no registra la fecha del pretest, así que no puede comprobar el orden.
- **Orden de las formas AB/BA (D16):** no existe.

**Qué cambia en F10.** Reescribir el sorteo con los casos A, B y C y el modo exploratorio (ADR-004). Guardar el caso y el orden AB/BA, y registrar la fecha de congelación para compararla con la del pretest.

### 3.7 El flujo completo y el "análisis post" (`analisis/servicios/flujo.py`, `persistencia.py`)

**Qué hace.** Une las piezas: abre el repositorio → extrae → omite triviales → calcula inserciones → predice P(IA) → calcula el IDC. Si el resultado no tiene fragmentos, no lo guarda, para no tapar un análisis anterior válido.

Además existe un **segundo análisis, "post"**: cuando el participante ya tiene asignación, el siguiente análisis mide **solo el código escrito después** del commit del diagnóstico, manteniendo la asignación original.

**Qué no cumple.** El plan (9.7) analiza los repositorios **una sola vez**, en la semana 8, y mide el resultado de la intervención con la **prueba de desempeño**, no con un nuevo IDC. Este análisis "post" lo añadí antes de fijar el diseño. Ninguna hipótesis lo usa, complica el modelo de datos (el campo "fase") y puede confundir en la exportación.

**Qué cambia en F10.** **Lo elimino**, con sus pruebas. Lo menciono para que sepa que existió y por qué se quita. Si usted quisiera un IDC post como análisis exploratorio, habría que decidirlo antes, porque exige que los estudiantes sigan trabajando en el mismo repositorio durante la intervención.

### 3.8 La base de datos (`analisis/models.py`, `refuerzo/models.py`, migraciones)

| Tabla | Qué guarda hoy | Problema frente al diseño (06) |
| --- | --- | --- |
| Configuración | θ, λ, m vigentes | — |
| Participante | Código anónimo (valida el patrón `P01`) y **ruta o URL del repositorio** | La URL identifica al estudiante (por ejemplo, su usuario de GitHub): no debe guardarse. Faltan la fecha de consentimiento, la de retiro y la marca de exclusión (D15) |
| Análisis | Parámetros usados, versión del modelo, commit analizado, conteos, IDC global, n.º de autores | Sobra la "fase" pre/post (3.7). Faltan las versiones de reglas y características, el resultado de inclusión y el índice por historial |
| Asignación | Semilla, débiles, reforzados, control, "comparable", fecha | Cambiar "comparable" por "caso" (D2) y añadir el orden AB/BA (D16) |
| Resultado por concepto | n, n_ia, IDC, estado, reforzado | — |
| Fragmento | Código de la función, archivo, líneas, conceptos, inserción, P(IA) | Correcto **en el almacén local**; nunca debe llegar a la nube |
| Apertura de refuerzo | Participante, concepto, fecha | Correcto: mide la exposición real |
| Intento de ejercicio | **Código de la solución**, casos, aciertos, error | 06 decidió **no guardar** el código de las soluciones en la nube, solo su longitud y su hash |

**Qué está bien.** El patrón del código anónimo impide registrar un nombre. Borrar un participante borra en cascada todo lo suyo (prueba `test_borrar_el_participante_borra_todo`), y el análisis que dio origen a la asignación no se puede borrar mientras ella exista.

**Qué no cumple.** La base es **una sola** (SQLite, sin cifrar), con el código de los estudiantes y el material de refuerzo juntos. El diseño separa **dos almacenes**: uno local y cifrado con el código, y otro en la nube sin código.

**Qué cambia en F10.** Separar los dos perfiles (local y nube), cifrar el almacén local y ajustar las tablas según 06.

### 3.9 Exportaciones (`analisis/servicios/exportacion.py`, `refuerzo/persistencia.py`)

**Qué hace.** Genera cuatro CSV, todos **por código anónimo**:
- participantes, con el último análisis en formato ancho;
- análisis por concepto, en formato largo;
- intentos de ejercicios;
- aperturas del material.

**Qué está bien.** Los CSV **no incluyen** el origen del repositorio, los hashes de commit (en un repositorio público llevan al autor) ni el código de las soluciones. Hay pruebas automatizadas que verifican que no salgan datos identificables ni el origen del repositorio.

**Qué no cumple (D17).** El formato no es el de su sección 3.4:

| Columna de D17 | Hoy |
| --- | --- |
| `participante`, `concepto`, `idc_concepto`, `idc_lo`, `idc_hi`, `n_fragmentos`, `semilla`, `theta`, `lambda`, `m`, `version_modelo` | Existen, con otros nombres |
| `reforzado` | Existe como "condición" |
| `caso` | No existe (hoy, "comparable") |
| `momento`, `forma`, `orden`, `T_pct`, `cc_sol`, `cc_ref`, `lin_sol`, `lin_ref` | **No existen**: falta el módulo de pruebas |
| `Q`, `Q_cal1`, `Q_cal2` | Vienen de la rúbrica, fuera del sistema |
| `version_reglas` | No existe |

**Qué cambia en F10.** Para respetar el ciego de los calificadores (D3), el CSV largo se arma **uniendo tres partes después de cerrar la calificación**:
1. los puntajes T, que produce el corrector y no llevan ningún dato de asignación;
2. la rúbrica Q, que hacen los calificadores sin conocer la asignación;
3. la asignación con el IDC, que produce el núcleo.

La unión la hace el script de análisis. Detalle en el documento 06 §2.

Una nota de nombres: el sistema llama al concepto `estructuras_datos`, y en D17 aparece como `estructuras`. Es el mismo concepto; mantengo el identificador interno para no romper el código y los datos.

### 3.10 Interfaz del investigador (`analisis/views.py`, `forms.py`, `templates/analisis/`)

**Qué hace.** Cinco páginas:
- lista de participantes, con alta por código y repositorio;
- detalle de un participante: IDC global y por concepto con intervalos, conceptos débiles, reforzados y de control, aviso de varios autores, y la tabla de fragmentos con su código y su P(IA);
- botón para analizar;
- configuración de θ, λ y m, con validación de rangos;
- descarga de los CSV.

**Qué está bien.** Los formularios usan protección CSRF, y el botón "analizar" solo funciona con POST. Los errores (repositorio inaccesible, sin funciones, modelo ausente) se muestran sin romper la página.

**Qué no cumple.** **No hay inicio de sesión**: estas páginas, incluidas las que muestran el código de los estudiantes y los CSV, son accesibles para quien conozca la dirección. En una máquina local es tolerable; en la nube, no.

**Qué cambia en F10.** Con ADR-001, estas páginas **se quedan solo en el perfil local** (la máquina del investigador). Allí se sustituyen por comandos `manage.py`, o se conservan para revisar, siempre con inicio de sesión. **No se suben a la nube.**

### 3.11 Material de refuerzo (`refuerzo/servicios/contenido.py`, `refuerzo/views.py`)

**Qué hace.** Para cada concepto hay un material fijo, sin modelos de lenguaje:

| Concepto | Ejemplos resueltos | Ejercicios (fácil / medio / difícil) |
| --- | --- | --- |
| Recursión | Factorial; suma de una lista | Suma de dígitos; palíndromo; aplanar una lista anidada |
| Estructuras de datos | Contar votos con un diccionario; alumnos en común con conjuntos | Elementos únicos; palabra más frecuente; agrupar anagramas |
| Excepciones | Convertir con valor por defecto; validar y lanzar con `raise` | División segura; convertir solo lo válido; retiro de una cuenta con excepción propia |

Cada ejercicio tiene casos de prueba (entre ellos, casos que deben lanzar una excepción concreta). Al enviar una solución, el sistema la ejecuta, muestra caso por caso qué pasó y avisa si la solución **no usa el concepto**; por ejemplo, una solución iterativa a un ejercicio de recursión. Cada apertura del material se registra. **El concepto de control queda bloqueado** (error 403), y una prueba verifica que no se pueda forzar por la dirección.

**Qué está bien.** Cumple la parte de "material curado, sin LLM" (ADR-001). El bloqueo del control protege la comparación intrasujeto. Las aperturas miden la exposición real (RF-18). La recarga después de enviar una solución no se cuenta como apertura.

**Qué no cumple.**
- **D11: el estudiante ve su IDC.** La introducción del material dice: *"…se analizaron N funciones de X y K parecen haber sido generadas con ayuda de IA (IDC = 0,60)"*. Hay que quitarlo durante las semanas 9–12.
- **D4: lista de espera.** El control está bloqueado siempre; no existe la acción de desbloquearlo después del postest.
- **Acceso:** el estudiante no inicia sesión. Cualquiera que conozca `/refuerzo/P01/recursion/` ve el material de P01 y sus intentos. Además, la página tiene un enlace "Volver a P01" que lleva a la **página del investigador**, con el código de todos sus fragmentos.
- **Validación por expertos (HE3):** el material no tiene versión ni marca de "validado". El diseño exige que solo se entregue material validado y que cada intento registre la versión del recurso.
- Los intentos sobre el control bloqueado no se registran. El diseño propone registrarlos para documentar posibles contaminaciones.

**Qué cambia en F10.**
- Quitar el IDC de la introducción.
- Añadir el código de acceso del estudiante.
- Quitar el enlace a la página del investigador.
- Versionar el material y marcarlo como validado.
- Añadir la liberación del control tras el postest.
- Registrar los intentos bloqueados.
- Al dejar de guardar el código de las soluciones, el cuadro de texto ya no mostrará la última solución enviada. Es un costo menor de comodidad, y el estudiante puede guardarla él mismo.

### 3.12 Ejecución de las soluciones (`refuerzo/servicios/ejecutor.py`, `corredor.py`)

**Qué hace.** Ejecuta la solución del estudiante en un **proceso aparte**, con:
- un límite de tiempo de 5 s, que corta bucles y recursiones infinitas;
- el modo aislado de Python;
- una carpeta temporal propia;
- un entorno sin las variables del servidor (no hereda claves).

La salida que imprime el estudiante se descarta, para que no se mezcle con el resultado. Los mensajes de error se recortan.

**Qué no cumple.** El propio código lo advierte: **no es un entorno aislado (sandbox)**. La solución corre con los permisos del servidor: podría leer o borrar archivos, o usar la red. Tampoco tiene límite de memoria. En la máquina del investigador, con código de prueba, el riesgo es controlable; **expuesto a 25 estudiantes en la nube, es inaceptable**.

**Qué cambia en F10.** Un **contenedor dedicado** (el "ejecutor" de ADR-001) con:
- sin red;
- sistema de archivos de solo lectura;
- usuario sin privilegios;
- límites de CPU, memoria, procesos y tiempo.

Antes de construirlo se valida con el spike SP-04, en el que se intenta escapar de él con código malicioso.

### 3.13 Configuración y seguridad general (`config/`)

| Punto | Hoy | Para la nube |
| --- | --- | --- |
| Clave secreta de Django | Escrita en el código y publicada en el repositorio | Variable de entorno, nueva y nunca versionada |
| Modo de depuración | Activado | Desactivado |
| Base de datos | SQLite sin cifrar, junto al código | Dos almacenes (local cifrado / nube) y cifrado en reposo (decisión 7 de CLAUDE.md) |
| Roles | Ninguno; solo el panel de administración de Django pide contraseña | Investigador (cuenta de Django) y estudiante (código de acceso) |
| Perfiles local/nube | No existen | Un solo proyecto con dos perfiles (ADR-001) |
| Región de Azure | — | Parámetro de configuración documentado (D14) |

Para un prototipo local es normal. Lo dejo explícito para que no se interprete como el estado final.

### 3.14 Pruebas automatizadas (`tests/`)

| Archivo | Pruebas* | Qué cubre |
| --- | --- | --- |
| `test_repositorio.py` | 33 | Clonado, URL con secretos, archivos excluidos, inserción por commit, autores, repositorios sin historial |
| `test_vistas.py` | 57 | Flujo completo por la interfaz: alta, análisis, sorteo, bloqueo del control, aperturas, intentos, exportaciones sin datos identificables |
| `test_idc.py` | 27 | IDC, Wilson, m, estados, sorteo reproducible |
| `test_refuerzo.py` | 20 | Material, ejecución de soluciones, tiempo límite, detección del concepto |
| `test_conceptos.py` | 18 | Reglas de concepto actuales |
| `test_clasificador.py` | 15 | Características, entrenamiento, carga del modelo |
| `test_extraccion.py` | 13 | Funciones, métodos, anidadas, triviales, errores de sintaxis |
| `test_sin_django.py` | 1 | Que la biblioteca de análisis no dependa de Django |

\* Funciones de prueba. Algunas se repiten con varios datos, por eso el total ejecutado es 262.

**Lectura.** La cobertura es buena para un prototipo, y las pruebas de privacidad (que no se guarden autores, que los CSV no identifiquen) son un activo. **Las pruebas de conceptos y de sorteo van a cambiar**, porque hoy verifican las reglas anteriores a D2 y D5. La validación de las reglas con anotadores (D7) dará además un **conjunto dorado** de fragmentos etiquetados a mano, que pasará a ser una prueba permanente: si una regla cambia y empeora la concordancia, la prueba falla.

### 3.15 Datos y scripts de demostración

- `scripts/crear_corpus_demo.py`: genera el corpus sintético (sección 3.5). **Se conserva solo para las pruebas automatizadas**; nunca para resultados.
- `scripts/entrenar_modelo.py`: entrena y guarda el modelo. Lo reemplaza el comando `entrenar`.
- `scripts/preparar_demo_repo.py` y `demo_repo/`: un repositorio de ejemplo con historial, para probar el flujo sin datos reales. Cumple D12, porque no usa repositorios de compañeros.

---

## 4. Tabla consolidada: sus decisiones frente al código

| # | Decisión | Estado en el código | Trabajo en F10 |
| --- | --- | --- | --- |
| D1 | Fórmula del puntaje; valores crudos y solución de referencia | **No existe** el módulo de pruebas | Banco A/B con soluciones de referencia; corrector de T1–T3 con `cc_sol`, `cc_ref`, `lin_sol` y `lin_ref`. La fórmula va en el script de análisis |
| D2 | Asignación escalonada A/B/C | Solo el caso A; el resto, "no comparable" | Reescribir el sorteo (ADR-004) |
| D3 | Sorteo antes del pretest; calificadores ciegos | Se sortea en el diagnóstico ✔. No hay fecha del pretest ni corrector | Registrar la congelación; exportación de puntajes sin datos de asignación |
| D4 | Control desbloqueado tras el postest | Bloqueado siempre | Acción de liberación |
| D5 | Lista cerrada de ED + definición amplia | Regla mucho más amplia | `conceptos-v1` y `conceptos-v1-amplia` |
| D6 | Recursión mutua y sobre atributo; excepciones | Excepciones ✔; las dos recursiones faltan | Detectarlas |
| D7 | Calibración con 20, 150 estratificados, κ ≥ 0,70 | No existe | Script de muestreo estratificado y exportación ciega para los anotadores |
| D8 | `ia_editado` aparte | No existe | Etiqueta en el corpus y métrica separada |
| D9 | Clasificador sin historial; índice aparte | El historial es la característica 8 | Quitarla; calcular el índice por historial |
| D10 | F1 ≥ 0,70, FP ≤ 0,15, sensibilidad ≥ 0,60; FP por calidad | Solo F1 y AUROC en validación cruzada por fragmento | Protocolo 07 completo |
| D11 | IDC oculto en semanas 9–12 | **Se muestra** en el material | Quitarlo; mostrarlo en el informe personal tras el postest |
| D12 | Sin repositorios de compañeros antes del CEI | El repositorio de ejemplo es sintético ✔ | — |
| D13 | Borrar código y derivados; conservar CSV | Borrado por participante ✔ (en una sola base); no hay borrado masivo | Borrado en los dos almacenes y cierre |
| D14 | Tabla de identidades solo en la máquina; región como parámetro | El sistema no guarda nombres ✔. Guarda la URL ✘ | Dejar de guardar la URL; parámetro de región |
| D15 | Marca de exclusión (etiquetado y piloto) | No existe | Añadirla |
| D16 | Forma y orden AB/BA | No existe | Guardarlos |
| D17 | CSV largo | Formato distinto | Unión de tres partes (06 §2) |
| D18 | Numeración del plan | — | Ver la pregunta 1 |

Resumen: hoy solo **D12 se cumple por completo**, y D3, D6, D13 y D14 se cumplen **en parte**. Las demás requieren trabajo, que en su mayoría ya está especificado en los documentos 05, 06 y 07.

---

## 5. Lo que falta por completo

| Parte | Por qué importa | Dónde está diseñada |
| --- | --- | --- |
| Corrección de las pruebas T1–T3 (banco A/B, corrector, métricas de calidad) | Sin esto no hay variable dependiente desde el sistema | 05 §1 (T1–T4) |
| Verificación de inclusión | Criterio de la muestra (plan 9.1.2) | 05 §2, etapa 2 |
| Ejecutor aislado | Seguridad de los estudiantes y del servidor | 05 §3.5, SP-04 |
| Acceso del estudiante y del investigador | Privacidad (plan 9.6) | 05 §3.4 |
| Separación local/nube y archivo de resultados sin código | ADR-001; el código nunca sale de la máquina del investigador | 05 §3.6 |
| Cifrado y respaldo | Plan 9.6 | 06 |
| Informe personal al final | D11, plan 9.1.2 | 05 (P4) |
| Liberación del control | D4 | 05 §3.4 |
| Versión y validación del material | HE3 | 05, 06 |
| Índice por historial | D9, HE1 | 07 §2.4 |
| Protocolo del clasificador | D10, meta del plan | 07 |

---

## 6. Qué se conserva, qué se reescribe y qué se descarta

| Conservar (con ajustes menores) | Reescribir | Descartar |
| --- | --- | --- |
| Lectura del repositorio, cálculo de inserción por commit, conteo de autores sin guardar correos | Reglas de conceptos (D5, D6) | Análisis "post" del repositorio (3.7) |
| Extracción de fragmentos, funciones anidadas, triviales | Sorteo (D2, ADR-004) | Campo "fase" y "comparable" |
| IDC, Wilson, m, estados | Características: sin historial (D9) | Guardar la URL del repositorio y el código de las soluciones |
| Separación biblioteca / Django y su prueba | Entrenamiento y evaluación (protocolo 07) | Corpus sintético como base de cualquier resultado (se queda solo para las pruebas) |
| Material de refuerzo y casos de prueba (pendiente de validación por expertos) | Exportaciones (D17) | Páginas del investigador en la nube |
| Bloqueo del control, registro de aperturas | Ejecutor (contenedor aislado) | — |
| Pruebas de privacidad de los CSV | Configuración y perfiles | — |

---

## 7. Riesgos para la validez que vienen del código

1. **La definición de estructuras de datos cambia los resultados.** Pasar de la regla actual a v1 reducirá mucho los fragmentos de ese concepto. Habrá participantes en los que deje de ser calculable y pasen del caso A al B o al C. Por eso SP-06, que mide la distribución de fragmentos por concepto, debe hacerse **con la regla v1 ya implementada**, no con la actual.
2. **Sin historial, el clasificador depende solo del estilo** (3.4). Si el reporte de falsos positivos por calidad muestra diferencias grandes, habrá que reconsiderar las características antes del diagnóstico.
3. **La heurística de tipos del elemento 6** (3.3) puede dejar fuera listas legítimas. La validación con anotadores lo medirá.
4. **El ciego de los calificadores depende de un procedimiento, no solo del software.** El sistema puede garantizar que el CSV de puntajes no lleve la asignación, pero la unión de las tres partes debe hacerse después de cerrar la calificación.

---

## 8. Preguntas que surgieron al cruzar sus decisiones con el plan

1. **"HE5".** Las decisiones D2 y D17 hablan de HE5, pero `plan.md` solo tiene HG y HE1 a HE4. La comparación reforzado frente a control figura como "control intrasujeto, complementario a HE4" (tabla de pruebas estadísticas del capítulo 9). Como D18 mantiene la numeración del plan, entiendo que **HE5 se refiere a ese control intrasujeto** y lo nombré así en los documentos. ¿Es correcto, o quiere crear formalmente una HE5?
2. **Orden AB/BA (D16).** El plan dice "pretest (forma A)" (cronograma, semana 8), y D16 introduce el contrabalanceo. ¿Cómo se asigna el orden a cada participante? Propongo **sortearlo con la misma semilla** del reparto de conceptos, para que sea aleatorio y reproducible, y la mitad reciba cada orden.
3. **Modo exploratorio (F1 < 0,70).** D2 no cubre este caso. El plan dice que entonces "los conceptos se asignan al azar". Propongo **no aplicar el caso A** (porque "débil" depende de un IDC que no sería confiable) y sortear entre los calculables, o entre los tres si hay menos de dos (ADR-004). ¿De acuerdo?
4. **Elemento 6 de estructuras de datos.** ¿Acepta la heurística conservadora de la sección 3.3 ("si no se puede saber el tipo, no cuenta")?
5. **Análisis post del repositorio.** Lo elimino por las razones de la sección 3.7. ¿Confirma que no quiere un IDC post, ni siquiera exploratorio?

---

## Glosario

| Término | Significado |
| --- | --- |
| Fragmento | Una función o un método de Python: la unidad de análisis |
| P(IA) | Probabilidad estimada por el clasificador de que el fragmento fue generado por IA |
| θ | Umbral de P(IA) a partir del cual un fragmento cuenta como "probablemente IA" |
| IDC | Proporción de fragmentos con P(IA) ≥ θ, global o por concepto |
| λ | Umbral de IDC a partir del cual un concepto es "débil" |
| m | Fragmentos mínimos para que un concepto sea calculable (5) |
| Calculable / débil | Calculable: ≥ m fragmentos. Débil: calculable e IDC ≥ λ |
| Wilson | Método para el intervalo de confianza de una proporción, robusto con pocos datos |
| Semilla | Número que fija un sorteo para poder repetirlo exactamente |
| Corpus | Conjunto de fragmentos etiquetados (humano / IA) con el que se entrena y evalúa el clasificador |
| Falso positivo (FP) | Código humano que el clasificador marca como IA |
| Sensibilidad | Proporción del código de IA que el clasificador detecta |
| Perfil local / nube | Las dos formas de ejecutar el mismo proyecto: en la máquina del investigador (con el código de los estudiantes) o en la nube (sin código) |
| F10 | La fase del plan de arquitectura en que se construye el sistema definitivo |
