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

# 3. Crear la base de datos
python manage.py migrate

# 4. Crear el corpus demo y entrenar el modelo
python scripts\crear_corpus_demo.py
python scripts\entrenar_modelo.py

# 5. Darle historial Git a demo_repo/
python scripts\preparar_demo_repo.py

# 6. Levantar el servidor
python manage.py runserver
```

Abre <http://127.0.0.1:8000/>.

Si PowerShell bloquea la activación del entorno, ejecuta esto y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Probar el flujo con `demo_repo/`

`demo_repo/` es pequeño: antes de empezar, pon m = 3 en **Configuración**. Con el
valor por defecto (m = 5), recursión y excepciones quedarían como «datos
insuficientes», porque solo tienen 4 fragmentos.

1. En **Participantes**, registra el código `P01` con el repositorio `demo_repo`.
2. Pulsa **Analizar repositorio (pre)**. Este primer análisis sortea la asignación.
3. En el detalle de `P01` verás 16 fragmentos (2 triviales omitidos), un IDC
   global de 0,44 y esta evaluación:

   | Concepto | Fragmentos | IDC | IC 95 % | Estado | Asignación |
   |---|---:|---:|---:|---|---|
   | Recursión | 4 | 1,00 | 0,51 – 1,00 | Débil | Sorteo |
   | Estructuras de datos | 8 | 0,50 | 0,22 – 0,78 | Débil | Sorteo |
   | Manejo de excepciones | 4 | 0,00 | 0,00 – 0,49 | No débil | Sin asignar |

   Hay 2 conceptos débiles: uno sale reforzado y el otro queda de control, por
   sorteo. Los valores exactos pueden variar un poco con otra versión de
   scikit-learn.
4. Pulsa **Abrir refuerzo** y pega la solución del concepto que te tocó. Debe
   mostrar **4 de 4 pruebas pasadas**.

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
       vistos = []
       for x in lista:
           if x not in vistos:
               vistos.append(x)
       return vistos
   ```
5. Prueba el control: abre `/refuerzo/P01/recursion/` o
   `/refuerzo/P01/estructuras_datos/`, según cuál quedó de control. Debe responder
   «Refuerzo no disponible».
6. Pulsa **Analizar repositorio (post)**. Debe avisar de que no hay funciones
   nuevas: el post solo mide lo escrito después del pre.
7. Para ver el caso de 3 conceptos débiles, pon λ = 0 en **Configuración** y
   registra otro participante: se refuerzan 2 y el tercero queda de control. La
   asignación de `P01` no cambia, porque está congelada.
8. Descarga los datos con los enlaces **CSV** del menú.

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

`etiqueta` es 1 si es IA y 0 si es humano. `insercion_commit` puede ser `null`.
Luego entrena:

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
  persistencia.py    Une los servicios con la base de datos, y hace el sorteo
refuerzo/
  persistencia.py    Exporta intentos y aperturas
  servicios/
    contenido.py       Plantillas: explicaciones, ejemplos y ejercicios
    ejecutor.py        Lanza el subproceso con tiempo límite
    corredor.py        Proceso hijo que corre la solución
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
- **Repositorios individuales:** el estudio los supone y el sistema no filtra por
  autor. Si hay más de un correo de autor avisa en el detalle y lo exporta en
  `n_autores`; los correos no se guardan.
- **Concepto débil:** IDC ≥ λ y al menos m fragmentos. Con menos de m se marca
  «datos insuficientes» y no se calcula.
- **Asignación:** se sortea entre los conceptos débiles en el análisis pre y queda
  congelada, con su semilla. Con 3 débiles se refuerzan 2 y 1 queda de control; con
  2 débiles, 1 y 1. Con 1 débil se refuerza, pero el participante queda fuera de la
  comparación principal (`comparable = 0`). Los conceptos no débiles quedan sin
  asignar.
- **Fases:** el primer análisis es `pre` y los siguientes son `post`. Un `post` solo
  mide las funciones cuya mayoría de líneas se escribió después del commit del pre,
  y necesita historial Git.
- **Repetir un participante:** borra su asignación desde el admin. El siguiente
  análisis vuelve a ser `pre`. Hazlo con todos si cambias del modelo demo al real.
- **Control:** la página de refuerzo de un concepto no reforzado responde 403.
- **Cada análisis guarda** θ, λ, m y la versión del modelo. Volver a analizar crea
  un análisis nuevo y conserva los anteriores. La interfaz y el CSV de participantes
  usan el último.
- **Datos para el estudio:** el **CSV análisis** trae una fila por análisis y
  concepto, con su fase y condición; es la tabla para comparar pre y post. El **CSV
  intentos** trae cada envío numerado y el **CSV aperturas**, cada vez que se abrió
  el material. No incluyen código, rutas, URLs ni hashes de commit.
- **Sin funciones:** si el repositorio no tiene funciones Python se avisa y no se
  guarda nada, para no ocultar un análisis válido anterior.
- **Tamaño de inserción:** cuenta las líneas `.py` añadidas en el commit, sin las
  carpetas excluidas (`.venv`, `build`, `migrations`...). El commit de cada línea
  sale de `git blame -w -M -C`, que ignora los cambios de espacios y sigue al
  código movido.
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
- Las características son solo de estilo. Un estudiante ordenado puede parecer IA
  y un código de IA retocado puede parecer humano.
- El tamaño de inserción castiga a quien trabaja mucho y sube todo en un commit.
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
- La recursión mutua se detecta dentro del mismo archivo. La recursión sobre un
  atributo (`self.izquierda.insertar(x)`) también marca como recursión una
  delegación con el mismo nombre (`self.repo.guardar()` dentro de `guardar`).
- Las clases contenedoras se reconocen por `push`, `pop`, `__len__` o `__iter__`;
  nombres en español como `apilar` no cuentan.
- El estudio supone tareas que empiezan desde cero: un código inicial del docente
  contaría como del estudiante.
- Un archivo de tarea llamado `test_algo.py` se omite por su nombre.

**Sistema**
- No hay usuarios ni permisos: cualquiera con acceso ve a todos los participantes.
- El análisis es síncrono: un repositorio grande bloquea la petición, y un clon
  colgado no tiene tiempo límite.
- Se analiza solo HEAD y se omiten carpetas como `venv`, `build` y `migrations`.
- Una función con el mismo commit de otras recibe el mismo tamaño de inserción.
- Reescribir el historial (`push --force`) borra el commit del pre y el análisis
  post dará error.
- Las pruebas corren en Windows. Se probó con Python 3.12 y 3.13, no con 3.11.
