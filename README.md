# Prototipo IDC

Primer prototipo de un sistema que analiza repositorios Git con código Python,
estima qué funciones pudieron ser generadas por IA, calcula un Índice de
Dependencia Conductual (IDC) global y por concepto, y entrega material de
refuerzo con ejercicios autocorregidos.

Conceptos analizados: recursión, estructuras de datos y manejo de excepciones.

> **El modelo incluido es de demostración.** Se entrena con un corpus sintético,
> así que sus valores de P(IA) y de IDC solo prueban que el flujo funciona. No
> dicen nada real sobre ningún estudiante.

## Instalación en Windows (PowerShell)

Requiere Python 3.11 o superior y Git. Ejecuta todo desde la carpeta del proyecto.

```powershell
# 1. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar los secretos locales: copia .env.ejemplo como .env y rellena
#    DJANGO_SECRET_KEY e IDC_SAL_CORREOS con los comandos que indica el archivo.
#    .env no se versiona.
copy .env.ejemplo .env

# 4. Crear la base de datos y tu usuario de investigador
python manage.py migrate
python manage.py createsuperuser

# 5. Crear el corpus demo y entrenar el modelo
python scripts\crear_corpus_demo.py
python scripts\entrenar_modelo.py

# 6. Darle historial Git a demo_repo/
python scripts\preparar_demo_repo.py

# 7. Levantar el servidor
python manage.py runserver
```

Abre <http://127.0.0.1:8000/>.

Si PowerShell bloquea la activación del entorno, ejecuta esto y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Probar el flujo con `demo_repo/`

`demo_repo/` es pequeño: antes de empezar, en **Configuración** pon m = 3, λ = 0,4
y el modo **confirmatorio**. Con el valor por defecto (m = 5), recursión y
excepciones quedarían como «datos insuficientes», porque solo tienen 4 fragmentos.
Con λ = 0,5, estructuras de datos no llegaría a débil y el sorteo iría al caso B.

1. En **Participantes**, registra el código `P01` con el repositorio `demo_repo`, el
   correo de commit `demo@example.invalid` y una fecha y versión de consentimiento
   (sin consentimiento no se analiza). Es el autor que usa
   `preparar_demo_repo.py`; con otro correo no se analizaría ninguna función (D19).
2. Pulsa **Analizar**. El diagnóstico calcula el IDC, pero **no sortea**. Puedes
   repetirlo con **Volver a analizar**: reemplaza al anterior.
3. En el detalle de `P01` verás 16 fragmentos (2 triviales omitidos), un IDC
   global de 0,44 y esta evaluación:

   | Concepto | Fragmentos | IDC | IC 95 % | Estado |
   |---|---:|---:|---:|---|
   | Recursión | 4 | 1,00 | 0,51 – 1,00 | Débil |
   | Estructuras de datos | 7 | 0,43 | 0,16 – 0,75 | Débil |
   | Manejo de excepciones | 4 | 0,00 | 0,00 – 0,49 | No débil |

   La columna de asignación dice «Pendiente». Los valores exactos pueden variar un
   poco con otra versión de scikit-learn.
4. Vuelve a **Participantes** y pulsa **Revisar y congelar la asignación**. La página
   muestra lo que va a pasar (1 participante en el caso A, entre los débiles) y pide
   confirmar. Al confirmar se sortea quién se refuerza y quién queda de control, y el
   orden de las formas. Desde ahí ya no se puede reanalizar. Lo mismo hace
   `python manage.py congelar_asignacion`.
5. Prepara la intervención:
   - carga los bloques de ejemplo con `python manage.py cargar_bloques --ejemplo`
     (un bloque por concepto, en la semana 1);
   - en **Gestión**, registra la validación de cada bloque con el número de jueces
     y fija el **inicio de la intervención** en la fecha de hoy.

   Sin validar o sin fecha de inicio, el estudiante no ve ningún bloque.
6. Entra como el estudiante:
   - en **Gestión**, pulsa **Generar código** para `P01` y anota el código (se muestra una sola vez);
   - en una **ventana privada** del navegador, abre <http://127.0.0.1:8000/acceso/> y entra con `P01` y ese código;
   - en **Mis conceptos**, abre el concepto reforzado, entra a su bloque y pega su solución.

   Debe mostrar **4 de 4 pruebas pasadas**.

   Recursión, en «Suma de dígitos»:

   ```python
   def suma_digitos(n):
       if n < 10:
           return n
       return n % 10 + suma_digitos(n // 10)
   ```

   Estructuras de datos, en «Elementos únicos»:

   ```python
   def unicos(lista):
       vistos = set()
       resultado = []
       for x in lista:
           if x not in vistos:
               vistos.add(x)
               resultado.append(x)
       return resultado
   ```
7. Prueba el control: con la sesión del estudiante abre `/mi/refuerzo/recursion/` o
   `/mi/refuerzo/estructuras_datos/`, según cuál quedó de control. Debe responder
   «Material no disponible», y el intento queda en el CSV aperturas con
   `permitida = 0`. La dirección no lleva el código del participante: cada
   estudiante solo ve lo suyo.
8. Descarga los datos con los enlaces **CSV** del menú.
9. Para cerrar la intervención, en **Gestión** pulsa **Liberar el material de todos
   los conceptos** (lista de espera, D4). Hazlo solo después del postest: no se
   deshace. Desde ese momento el estudiante ve **Mi informe**, con su IDC y su
   intervalo (D11).

Para repetir la demostración desde cero (por ejemplo, con λ = 0 para ver 3 débiles),
borra `db.sqlite3` y vuelve a ejecutar `python manage.py migrate`: la congelación no
se puede deshacer desde la interfaz.

## Almacén local cifrado

Con datos reales de participantes, la base, `datos/`, los clones temporales de los
repositorios y la sal **no** pueden quedar en la carpeta del proyecto. Van en un disco
virtual cifrado con BitLocker, que se monta para trabajar. Los pasos para crearlo,
montarlo, respaldarlo y borrarlo al final están en
[docs/almacen-cifrado.md](docs/almacen-cifrado.md). Para revisar que todo esté en su
sitio:

```powershell
python manage.py verificar_almacen
```

Para la demostración con `demo_repo/` no hace falta.

## Perfiles: núcleo local y portal en la nube (ADR-001)

El mismo proyecto corre en dos perfiles, que se eligen con `IDC_PERFIL`:

| | `local` (por defecto) | `nube` |
| --- | --- | --- |
| Dónde | Máquina del investigador | Azure |
| Tiene | Repositorios, código de los fragmentos, modelo, banco de la prueba | Códigos anónimos, IDC agregado, asignación, uso del refuerzo |
| No carga | — | Git, GitPython, scikit-learn ni el modelo |
| Exige | `IDC_SAL_CORREOS` | `IDC_EJECUTOR_URL` e `IDC_EJECUTOR_TOKEN` (el ejecutor aislado) |
| Comandos | Analizar, congelar, corregir la prueba, `exportar_resultados`, `exportar_estudio`, `cerrar_estudio` | `importar_resultados` |

Lo único que viaja de un perfil al otro es el archivo `resultados-v1`, que **no lleva código, rutas, URLs, correos ni hashes**:

```powershell
# En local, después de congelar la asignación:
python manage.py exportar_resultados --salida resultados.json
# En el portal:
python manage.py importar_resultados resultados.json
```

El exportador y el importador rechazan cualquier campo fuera del esquema y cualquier texto que parezca código o un dato personal. La importación es idempotente: volver a importar los mismos datos no duplica nada. Un participante con otro diagnóstico, o una congelación distinta, se rechazan. Reanalizar, congelar, exportar e importar quedan en la **auditoría** (admin → Auditoría).

## Corregir la prueba de desempeño (T1–T3)

El banco real de la prueba (formas A y B) **no se versiona**: va en
`datos/banco_prueba/forma_A.json` y `forma_B.json`, que están en `.gitignore`, y
nunca se sube al portal (D21). Si el banco estuviera en Git, los estudiantes podrían
verlo. Para probar con el banco de ejemplo, cópialo a esa carpeta o pasa
`--banco pruebas/banco_ejemplo`.

Cada ítem tiene su concepto (T1 recursión, T2 estructuras de datos, T3 excepciones),
el enunciado, el nombre de la función, la **solución de referencia** y los casos de
prueba. Al corregir se comprueba que cada referencia supere todos sus casos.

Las soluciones de una sesión van en una carpeta por participante:

```text
soluciones_pre/
  P01/T1.py  P01/T2.py  P01/T3.py
  P02/T1.py  ...
```

```powershell
python manage.py corregir_prueba --momento pre --soluciones soluciones_pre --salida puntajes_pre.csv
```

- Solo funciona con la **asignación congelada**. La forma de cada participante sale
  de su orden: AB es A en el pretest y B en el postest.
- Por ítem calcula `T_pct` (% de casos superados) y las métricas de D1:
  - `cc_sol` y `cc_ref`: complejidad ciclomática media por función, de la solución
    y de la referencia;
  - `lin_sol` y `lin_ref`: líneas de código fuente, sin blancos ni comentarios.
- Un ítem sin archivo queda `sin_respuesta` (0 %). Un archivo que no es Python
  válido queda `ilegible` (0 %, sin métricas) y el comando termina con código 9.
  Un participante sin carpeta queda `ausente`: sus ítems se registran **vacíos**, como
  dato faltante y nunca como 0 % (P5), para el diagrama de flujo de participantes.
- El CSV **no lleva datos de la asignación** (reforzado, caso, orden, semilla), para
  que quien califique Q1–Q3 no la conozca (D3). La fórmula del puntaje (D1) se
  aplica después, en el análisis estadístico.

Antes de entregar el material de refuerzo, revisa que no se parezca a la prueba:

```powershell
python manage.py controlar_solapamiento
```

Compara la prueba con los bloques de `refuerzo/bloques/` (o los de `--bloques`). Si
todavía no hay bloques reales, usa los de ejemplo y lo avisa.

## Bloques de refuerzo (D20)

El material son 24 bloques: 8 por concepto, 2 por semana durante 4 semanas. Cada
bloque es un archivo JSON en `refuerzo/bloques/` (sí va en Git, para que cada
versión quede trazable):

```json
{
  "id": "recursion-s1-1", "concepto": "recursion", "semana": 1, "orden": 1,
  "version": 1, "titulo": "El caso base",
  "explicacion": ["Párrafo 1", "Párrafo 2"],
  "ejemplos": [{"titulo": "...", "enunciado": "...", "codigo": "...",
                "salida": "...", "explicacion": "..."}],
  "ejercicios": [{"id": "rec-s1-1-a", "nivel": "Fácil", "titulo": "...",
                  "enunciado": "...", "plantilla": "def f(n):\n    pass\n",
                  "funcion": "f",
                  "casos": [{"args": [3], "esperado": 6},
                            {"args": [-1], "lanza": "ValueError"}]}]
}
```

`concepto` es `recursion`, `estructuras_datos` o `excepciones`.

```powershell
python manage.py cargar_bloques            # carga refuerzo/bloques/
python manage.py cargar_bloques --ejemplo  # un bloque de ejemplo por concepto
```

- Se cargan todos o ninguno. Si un bloque cambió, exige una `version` mayor.
- Un bloque nuevo, o una versión nueva, queda **sin validar** y el estudiante no lo
  ve. Cuando los jueces lo aprueben (HE3), regístralo en **Gestión** con el número
  de jueces. Se valida la versión que muestra la tabla, no una más nueva.
- Los bloques de la semana *n* se abren el día 7 × (*n* − 1) contado desde el inicio
  de la intervención, y siguen abiertos después.
- Gestión avisa cuántos bloques faltan por concepto.

Las cargas, validaciones, el inicio de la intervención y la liberación quedan en la
auditoría.

## Muestra: consentimiento, exclusión y retiro

- **Consentimiento:** el registro pide la fecha y la versión del consentimiento
  firmado. Sin él, el repositorio no se analiza.
- **Exclusión (D15):** en el detalle del participante, elige el motivo (sesión de
  etiquetado, piloto o no cumple los criterios). Un excluido no se analiza ni entra
  al sorteo. Tras congelar, quien quedó fuera del sorteo ya no puede volver.
- **Retiro (D13):** en **Gestión**, escribe el código del participante y pulsa
  **Borrar datos**, o usa `python manage.py retirar_participante P01 --confirmo P01`.
  Se borran su análisis, su código, su asignación, sus puntajes y su uso del
  refuerzo; queda solo el código, para el diagrama de flujo. **Hazlo en local y en
  el portal**, que tienen bases distintas, y borra su fila de la tabla de
  correspondencia. El portal no vuelve a cargarlo aunque reimportes el archivo.

## Base para el análisis (D17)

Después del postest, y una vez calificada la rúbrica Q:

```powershell
python manage.py exportar_estudio --calificaciones datos\calificaciones_q.csv --convocados 40
```

Escribe en `datos/estudio/<fecha>/` (o en `--salida`):

| Archivo | Contenido |
| --- | --- |
| `largo.csv` | Una fila por participante × concepto × momento: forma, orden, T_pct, Q (promedio), Q_cal1 y Q_cal2 (para el ICC), métricas de calidad, reforzado, caso, IDC del concepto con su intervalo y la trazabilidad del análisis |
| `participantes.csv` | Una fila por participante incluido: IDC global con intervalo (HE2b), índice por historial (HE1), estado del pretest y del postest, y `en_HG`, `en_HE1`, `en_HE2a`, `en_HE2b`, `en_HE4`, `en_HE4_casoA` y `en_HE5` |
| `flujo.csv` | Etapas del diagrama de flujo: convocados → registrados → incluidos → con pretest → con postest, con los motivos de pérdida |
| `LEEME.txt` | Qué es cada columna y las reglas de inclusión |

El CSV de calificaciones tiene las columnas `participante,concepto,momento,calificador,Q`,
con calificador 1 o 2 y Q de 0 a 20.

Reglas de inclusión (P5), sin imputar:
- quien falta al pretest solo queda en HE1;
- quien falta al postest conserva HE1 y HE2;
- `ausente` y `sin_corregir` son datos faltantes, nunca cero.

La dependencia autorreportada (HE2a) y el cuestionario de HE1 vienen de fuera del
sistema: se unen por el código del participante. La adherencia sale del portal
(**CSV adherencia**).

## Cierre del estudio (D13)

Al terminar el análisis de datos:

```powershell
python manage.py exportar_estudio
python manage.py cerrar_estudio --confirmo borrar-codigo
```

Borra los fragmentos (el código), las rutas de los repositorios, los hashes de
correo, los códigos de acceso y los clones que hayan quedado. Se conservan los
agregados, que son los mismos de la base exportada. Exige haber exportado antes y no
se deshace. Después:
- borra también las carpetas de entregas de la prueba y la tabla de correspondencia;
- en el portal, descarga los CSV y elimina el recurso de Azure.

Los CSV agregados se conservan por el plazo que fije el CEI-USIL. [PENDIENTE: plazo]

## Pruebas

```powershell
python -m pytest
```

Las pruebas no necesitan el modelo ni `demo_repo/`: crean sus propios datos.

## Reemplazar el modelo de demostración

Prepara un corpus JSONL con una línea por función:

```json
{"codigo": "def f(): ...", "etiqueta": 1, "insercion_commit": 42}
```

`etiqueta` es 1 si es IA y 0 si es humano. `insercion_commit` puede ser `null`. El
clasificador no lo usa (D9), pero conviene guardarlo para calibrar el índice por
historial. Luego entrena. Un modelo entrenado con otra versión de las
características (`rasgos-v1`, de antes de D9) se rechaza al cargarlo, así que
vuelve a entrenar el de demostración después de actualizar el código:

```powershell
python scripts\entrenar_modelo.py --corpus datos\corpus_real.jsonl `
    --salida datos\modelos\modelo_demo.joblib --version real-v1 --real
```

Con `--real` desaparece el aviso de la interfaz. Para cambiar la ruta del modelo,
edita `RUTA_MODELO` en `config/settings.py`. Para cambiar el algoritmo, edita
`construir_pipeline` en `analisis/servicios/entrenamiento.py`; es el único módulo
que conoce el entrenamiento.

## Estructura

```text
analisis/
  servicios/         Lógica sin Django
    conceptos.py       Detección de conceptos con ast
    extraccion.py      Extracción de funciones, radon
    caracteristicas.py Características para el clasificador
    entrenamiento.py   Entrenamiento (punto de reemplazo del corpus)
    clasificador.py    Carga del modelo y P(IA)
    idc.py             IDC y selección de conceptos
    repositorio.py     Lectura con PyDriller y GitPython
    flujo.py           Orquestación del análisis
    exportacion.py     CSV
    estudio.py         Reglas de inclusión (P5), rúbrica Q y diagrama de flujo
  persistencia.py    Une los servicios con la base de datos, y hace el sorteo
  participacion.py   Exclusión (D15) y retiro con borrado (D13)
  estudio.py         Base para el análisis (D17) y cierre del estudio
refuerzo/
  bloques/           Los 24 bloques de refuerzo en JSON (D20)
  liberacion.py      Qué bloques ve cada participante y desde cuándo (D4, D20)
  administracion.py  Cargar y validar bloques, inicio y fin de la intervención
  persistencia.py    Exporta intentos, aperturas y adherencia
  servicios/
    banco.py           Formato, validación y semanas de los bloques
    adherencia.py      Intentados y resueltos ÷ liberados (P6)
    contenido.py       Tipos del material y plantillas de ejemplo
    ejecutor.py        Lanza el subproceso con tiempo límite
    corredor.py        Proceso hijo que corre la solución
pruebas/
  banco_ejemplo/     Formas A y B de ejemplo (el banco real va en datos/banco_prueba/)
  servicios/
    banco.py           Lectura y validación de las formas A y B
    corrector.py       T_pct y métricas por ítem, con el corredor del refuerzo
    calidad.py         Complejidad ciclomática y líneas (D1)
    solapamiento.py    Alarma de parecido con el material de refuerzo (D21)
  persistencia.py    Corrige una sesión con la forma de cada participante
scripts/             Corpus, entrenamiento e historial de demo_repo
demo_repo/           Repositorio de ejemplo
tests/               Pruebas con pytest
```

## Reglas implementadas

- **IDC** = fragmentos con P(IA) ≥ θ ÷ fragmentos analizados. Se muestra y se
  exporta con su intervalo de confianza de Wilson al 95 %, que no incluye el
  error del clasificador.
- **Fragmento:** cada función o método. Una función anidada es parte de la que la
  envuelve, y sus conceptos se suman a ella.
- **Se omiten** los archivos de pruebas (`test_*.py`, `*_test.py`, `conftest.py` y
  las carpetas `test`, `tests` y `pruebas`) y las funciones triviales: una sola
  sentencia sin conceptos, como un getter. El análisis guarda cuántas triviales
  omitió.
- **Filtro por autor (D19):** solo se analizan las funciones cuyo commit mayoritario
  es de un correo declarado por el participante. Si hay más de un autor, avisa en
  el detalle y lo exporta en `n_autores`. Los correos de otros autores no se
  guardan, ni en claro ni hasheados.
- **Concepto débil:** IDC ≥ λ y al menos m fragmentos. Con menos de m se marca
  «datos insuficientes» y no se calcula.
- **Un diagnóstico por participante (R5):** el repositorio se analiza una vez. No
  hay análisis post: el resultado de la intervención se mide con la prueba de
  desempeño. Volver a analizar reemplaza al diagnóstico anterior mientras la
  asignación no esté congelada.
- **Congelación (D3, ADR-004):** se hace una vez, para toda la muestra, cuando todos
  tienen diagnóstico y el modo está fijado. Sortea, con una semilla base registrada:
  - los conceptos de cada participante, con la regla escalonada (caso A entre los
    débiles, caso B entre los calculables, caso C entre los tres; en modo
    exploratorio no hay caso A). Siempre quedan hasta 2 reforzados y al menos 1 de
    control;
  - el orden de las formas AB/BA, por bloques permutados de 4 y con un flujo
    aleatorio separado (R2).

  Después no se puede reanalizar, ni cambiar el modo, ni editar o borrar la
  asignación desde el admin.
- **Control:** la página de refuerzo de un concepto no reforzado responde 403 y
  registra el intento como apertura no permitida. Antes de congelar no hay ningún
  concepto reforzado. Tras **liberar el control** (D4), todos ven los tres
  conceptos.
- **IDC oculto (D11):** el portal del estudiante no muestra el IDC ni los datos de
  su análisis. La introducción del material es igual para todos.
- **Soluciones sin código:** de cada envío se guardan la longitud y el SHA-256 del
  código, nunca el código. El estudiante lo ve en la respuesta a su envío para
  seguir corrigiéndolo; al volver a abrir el bloque aparece la plantilla.
- **Cada análisis guarda** θ, λ, m y las versiones del modelo, las reglas y las
  características.
- **Datos para el estudio:** el **CSV análisis** trae una fila por participante y
  concepto, con su condición, caso, orden y modo. El **CSV intentos** trae cada
  envío numerado, con su bloque y versión, si se ejecutó, si repite el envío
  anterior y si fue después del postest. El **CSV aperturas** trae cada apertura,
  también las bloqueadas. No incluyen código, hashes, rutas, URLs ni commits.
- **Adherencia (P6):** el **CSV adherencia** trae una fila por participante y
  concepto reforzado. La principal es ejercicios **intentados** ÷ liberados, y la
  secundaria, **resueltos** ÷ liberados. Intentado = al menos un envío ejecutado;
  varios envíos al mismo ejercicio cuentan como uno y abrir el bloque no cuenta. El
  corte es la liberación del control o, antes de ella, el día de la descarga.
- **Sin funciones:** si el repositorio no tiene funciones Python se avisa y no se
  guarda nada, para no ocultar un análisis válido anterior.
- **Tamaño de inserción:** cuenta las líneas `.py` añadidas en el commit, sin las
  carpetas excluidas (`.venv`, `build`, `migrations`...). El commit de cada línea
  sale de `git blame -w -M -C`, que ignora los cambios de espacios y sigue al
  código movido. No entra al clasificador (D9).
- **Índice por historial** (`historial-v1`, P10): medida exploratoria para HE1,
  independiente del clasificador. Reporta dos medidas:
  - la proporción de las líneas propias que entraron en commits de 30 líneas o más,
    calculada línea por línea con `git blame`, y repetida con 15 y 60 como
    sensibilidad;
  - la media de log(1 + tamaño de inserción) de las funciones, sin umbral.

  El umbral de 30 se fijó *a priori*. No se calibra con la sesión de etiquetado,
  donde se pidió un commit por tarea.
- **URLs:** no se aceptan con usuario, token, parámetros ni fragmento, porque
  quedarían guardados en la base de datos.

## Advertencias

**La ejecución de soluciones no es un sandbox seguro.** El código corre en un
subproceso con tiempo límite y entorno mínimo, pero con los permisos del usuario
que levantó el servidor: puede leer o borrar archivos, usar la red o agotar la
memoria. Tampoco es a prueba de trampas: el código puede falsificar su resultado.
No lo expongas en producción ni a usuarios no confiables.

**Privacidad.** El sistema no guarda autores de commits y los clones de URL se
borran al terminar, pero estos datos sí pueden identificar a alguien:

- La ruta o URL del repositorio se guarda en la base de datos. No se muestra en
  la interfaz ni en el CSV, pero un usuario de GitHub en la URL identifica a la
  persona, y también una ruta como `C:\Users\Nombre\...`.
- El código de los fragmentos se guarda tal cual, incluidos comentarios como
  `# Autor: ...`.

Por eso `db.sqlite3` y `datos/` están en `.gitignore`.

## Limitaciones del prototipo

**Clasificador**
- El corpus es sintético y las métricas de `entrenar_modelo.py` no valen como
  resultado: miden si recupera la regla con la que se generó el corpus.
- Las características son solo de estilo y estructura (`rasgos-v2`). Un estudiante
  ordenado puede parecer IA y un código de IA retocado puede parecer humano. Sin
  el historial no hay contrapeso dentro del clasificador, así que hay que revisar
  los falsos positivos por nivel de calidad (D10).
- En el índice por historial, el tamaño de inserción castiga a quien trabaja mucho
  y sube todo en un commit.
  Un formateador que cambia más que espacios, como comillas, sigue contando como
  código nuevo: `-w` solo cubre los espacios.
- Falta calibrar las probabilidades, y θ = 0,5 solo tiene sentido si lo están.

**Detección de conceptos** (reglas `conceptos-v1`, decisiones D5, D6 y R4 del asesor)
- Estructuras de datos sigue una lista cerrada. No cuentan el `append` acumulativo,
  las comprensiones de lista, la indexación de cadenas ni el desempaquetado. Esas
  dos primeras sí entran en la definición amplia (`conceptos_amplia`), que solo
  sirve para el análisis de sensibilidad.
- La inferencia de tipos es local y conservadora. Indexar cuenta solo si la
  función deja claro que el objeto es una lista o un diccionario. Si no se puede
  saber (por ejemplo, un parámetro), la indexación se cuenta como indeterminada y
  no asigna el concepto.
- La recursión mutua se detecta dentro del mismo archivo.
- La recursión sobre un atributo exige un atributo de nodo (P8). Ese atributo es uno
  de la lista (`izquierda`, `siguiente`, `hijos`, `left`, `children`…) o uno al que
  la clase asigna una instancia de sí misma. Por eso `self.repositorio.guardar()`
  dentro de `guardar` no cuenta, y `self.parent.guardar()` sí, por el nombre.
- Las clases contenedoras se reconocen por una lista cerrada y bilingüe (P7): `push`,
  `pop`, `peek`, `apilar`, `desapilar`, `cima`, `tope`, `enqueue`, `dequeue`,
  `encolar`, `desencolar`, `frente`, `__len__`, `__iter__`, `__getitem__` y
  `__contains__`.
- Un atributo de nodo cuenta como estructura de datos solo en un **contexto de
  nodos**:
  - en `self.<enlace>`, si la clase lo inicializa como `None`, `[]` o una instancia
    de sí misma;
  - en un recorrido como `actual = actual.siguiente`;
  - en una variable que se compara con `None`.

  Así no cuentan `ruta.parent` (pathlib), `rect.left` (pygame) ni
  `self.parent = ventana` (tkinter).
- El estudio supone tareas que empiezan desde cero: un código inicial del docente
  contaría como del estudiante.
- Un archivo de tarea llamado `test_algo.py` se omite por su nombre.

**Sistema**
- Hay dos roles: el investigador entra con usuario y contraseña, y el estudiante con
  su código de participante más su código de acceso, con bloqueo tras 10 fallos en
  15 minutos. El inicio de sesión del investigador no tiene bloqueo propio, así que
  usa una contraseña larga.
- Detrás de un proxy (Azure), la IP del bloqueo debe salir de la cabecera que ponga
  la plataforma. [VERIFICAR en F9]
- El análisis es síncrono: un repositorio grande bloquea la petición, y un clon
  colgado no tiene tiempo límite.
- Se analiza solo HEAD y se omiten carpetas como `venv`, `build` y `migrations`.
- Una función con el mismo commit de otras recibe el mismo tamaño de inserción.
- La congelación no se puede deshacer desde la interfaz. Corregir un error después
  exige restaurar un respaldo de la base.
- La adherencia cuenta como liberados los bloques validados hoy. Si un bloque se
  valida tarde, o pierde la validación por una versión nueva, el denominador cambia
  retroactivamente: conviene cerrar la validación antes de la semana 9.
- La plataforma no comprueba que los casos de prueba de un bloque sean correctos:
  eso lo revisan los jueces. Las plantillas de ejemplo sí tienen soluciones de
  referencia en las pruebas.
- Al enviar, la página se vuelve a dibujar con la respuesta; recargarla reenvía la
  solución (el navegador pregunta antes).
- El informe personal señala un intervalo como «ancho» cuando mide más de 0,5.
  [PENDIENTE: confirmar el valor con el asesor]
- El informe del portal no trae los puntajes de la prueba, que viven solo en local.
- Las pruebas corren en Windows. Se probó con Python 3.12 y 3.13, no con 3.11.
