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

1. En **Participantes**, registra el código `P01` con el repositorio `demo_repo`.
2. Pulsa **Analizar repositorio**.
3. En el detalle de `P01` verás 18 fragmentos, un IDC global de 0,39 y esta
   asignación:

   | Concepto | Fragmentos | IDC | Estado | Refuerzo |
   |---|---:|---:|---|---|
   | Recursión | 4 | 1,00 | Débil | Reforzado |
   | Estructuras de datos | 8 | 0,50 | Débil | Reforzado |
   | Manejo de excepciones | 4 | 0,00 | No débil | No reforzado (control) |

   Los valores exactos pueden variar un poco con otra versión de scikit-learn.
4. Abre **Abrir refuerzo** en Recursión y pega esta solución en «Suma de dígitos»:

   ```python
   def suma_digitos(n):
       if n < 10:
           return n
       return n % 10 + suma_digitos(n // 10)
   ```

   Debe mostrar **4 de 4 pruebas pasadas**.
5. Prueba el control: abre `/refuerzo/P01/excepciones/`. Debe responder
   «Refuerzo no disponible».
6. Para ver el caso de 3 conceptos débiles, pon λ = 0 en **Configuración** y
   vuelve a analizar: se refuerzan 2 y excepciones queda sin reforzar.
7. Descarga los datos con **Exportar CSV**.

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
  persistencia.py    Une los servicios con la base de datos
refuerzo/
  servicios/
    contenido.py       Plantillas: explicaciones, ejemplos y ejercicios
    ejecutor.py        Lanza el subproceso con tiempo límite
    corredor.py        Proceso hijo que corre la solución
scripts/             Corpus, entrenamiento e historial de demo_repo
demo_repo/           Repositorio de ejemplo
tests/               Pruebas con pytest
```

## Reglas implementadas

- **IDC** = fragmentos con P(IA) ≥ θ ÷ fragmentos analizados.
- **Concepto débil:** IDC ≥ λ y al menos m fragmentos. Con menos de m se marca
  «datos insuficientes» y no se calcula.
- **Refuerzo:** como máximo los 2 conceptos débiles de mayor IDC; siempre queda
  al menos 1 sin reforzar.
- **Empates:** gana el concepto con más fragmentos y, si persiste, el orden fijo
  recursión, estructuras, excepciones.
- **Control:** la página de refuerzo de un concepto no asignado responde 403.
- **Cada análisis guarda** θ, λ, m y la versión del modelo. Volver a analizar crea
  un análisis nuevo y conserva los anteriores. La interfaz y el CSV usan el último.
- **Sin funciones:** si el repositorio no tiene funciones Python se avisa y no se
  guarda nada, para no ocultar un análisis válido anterior.
- **Tamaño de inserción:** cuenta las líneas `.py` añadidas en el commit, sin las
  carpetas excluidas (`.venv`, `build`, `migrations`...).
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
- Falta calibrar las probabilidades, y θ = 0,5 solo tiene sentido si lo están.

**Detección de conceptos**
- No hay inferencia de tipos: `s[0]` sobre una cadena cuenta como estructura de
  datos, y `requests.get(url)` también.
- Solo se detecta recursión directa. No se detecta la mutua (`a` llama a `b` y
  `b` a `a`), ni `self.izquierda.insertar(x)` en un árbol.
- `return a, b` y el desempaquetado no cuentan como uso de tuplas.

**Sistema**
- No hay usuarios ni permisos: cualquiera con acceso ve a todos los participantes.
- El análisis es síncrono: un repositorio grande bloquea la petición, y un clon
  colgado no tiene tiempo límite.
- Se analiza solo HEAD y se omiten carpetas como `venv`, `build` y `migrations`.
- Una función con el mismo commit de otras recibe el mismo tamaño de inserción.
- Los intentos quedan ligados a su análisis: tras volver a analizar, la página de
  refuerzo aparece sin intentos previos, aunque siguen en la base de datos.
- Las pruebas corren en Windows. Se probó con Python 3.12 y 3.13, no con 3.11.
