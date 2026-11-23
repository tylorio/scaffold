# Contenido desarrollado y orientación del asesor (22 de noviembre de 2026)

**Responde a:** *Lo que falta para terminar el sistema* (versión 0.10.0)

## 1. Qué contiene esta entrega

| Archivo | Para qué | Dónde va |
|---|---|---|
| `banco_prueba/forma_A.json`, `forma_B.json` | Ítems T1 a T3, con solución de referencia y 10 casos cada uno | Almacén cifrado: `datos/banco_prueba/`. **Nunca en Git** |
| `banco_prueba/prueba-desempeno-formas-A-B.md` | Versión legible para los jueces, ítems Q1 a Q3 con su clave, rúbrica y lista de verificación | Almacén cifrado |
| `refuerzo/bloques/estructuras_datos-s*-*.json` | Los 8 bloques de estructuras de datos (24 ejercicios) | `refuerzo/bloques/` (sí va en Git) |
| `soluciones_privadas/soluciones_estructuras_datos.py` | Una solución por ejercicio, para las pruebas automáticas | Repositorio de pruebas, sin publicarlas en el portal |
| `correo-CEI-autorizacion-azure.md` | Solicitud de la autorización escrita (D14) | Enviar tú |

**Verificación hecha:** las referencias de la prueba pasan sus 60 casos y las soluciones de los bloques pasan sus 120 casos. Los casos se pasaron por JSON antes de comprobarlos, igual que hará el corrector, y no hay diccionarios con claves numéricas (JSON las convierte en texto y haría fallar soluciones correctas).

**Antes de cargar los bloques:** confirma que los nombres de campo coinciden con la sección "Bloques de refuerzo" del README. Usé `concepto`, `semana`, `orden`, `version`, `titulo`, `explicacion`, `ejemplo` (`enunciado`, `codigo`, `comentario`) y `ejercicios` (`id`, `nivel`, `enunciado`, `funcion`, `plantilla`, `casos`). Si el README usa otros nombres, el programador puede adaptarlos con un script sin tocar el contenido.

## 2. Decisiones de diseño del contenido

> **[Omitido en esta copia.]** Esta sección describe los ítems de la prueba y los temas que los bloques de refuerzo no pueden tocar porque serían isomorfos de ellos. Por D21 no va a Git: el original completo está en `datos/banco_prueba/orientacion-asesor-2026-11-22-completa.md`, en el almacén cifrado. Lo único que cambia en esta copia es la omisión. Nota del investigador, 2026-11-23.

## 3. Orientación para lo que falta

### SP-06 (lo primero)

- Puedes usar tus propios repositorios de cursos anteriores en Python y repositorios **públicos** de cursos universitarios de programación en Python (por ejemplo, tareas de cursos introductorios o de estructuras de datos publicadas en GitHub con historial). No uses repositorios de compañeros hasta que el CEI apruebe (D12).
- Elige repositorios parecidos a los que entregarán los participantes: proyectos de curso, no bibliotecas profesionales ni ejercicios sueltos de una función.
- Para los públicos, toma los correos de commit del propio historial (`git log --format="%ae" | sort -u`) y quédate con el del autor principal. Ese dato se usa solo en el análisis local.
- **Cómo leer el resultado:** si menos del 40 % de los repositorios tiene dos conceptos calculables con m = 5, tráeme los números antes de cambiar nada. Las opciones serán bajar m a 4 o 3, ampliar los criterios de inclusión (más de un repositorio por participante) o aceptar más casos C. La regla escalonada ya protege a HE4 y HE5, así que el cambio afecta sobre todo a la precisión del IDC por concepto.

### Sesión de etiquetado

- Los enunciados de la sesión deben ser **distintos** de los de la prueba y de los bloques; si no, el clasificador aprendería con las mismas tareas que luego evalúa el desempeño. Puedo escribirte 6 enunciados (2 por concepto), con 2 o 3 funciones cada uno, como pide el diseño.
- Asigna a cada persona la mitad de las tareas con IA y la otra mitad sin IA, alternando qué tareas van con IA entre personas, para que la etiqueta no quede confundida con la tarea.
- Para C2, fija de antemano tres estilos de instrucción (instrucción breve, instrucción con el enunciado completo y una pidiendo "código como lo escribiría un estudiante") y aplícalos a cada asistente.

### Valores para las decisiones abiertas (provisionales hasta tener datos)

| Decisión | Valor que propongo | Por qué |
|---|---|---|
| Intervalo "ancho" en el informe personal (RF-34) | Ancho de Wilson mayor que 0.5: mostrar "estimación muy incierta"; entre 0.3 y 0.5: "estimación incierta" | Con m = 5, casi todos los intervalos por concepto superan 0.5; el informe debe decirlo así en vez de ocultarlo |
| Umbral de calibración (ECE) | ECE ≤ 0.10 en el conjunto de prueba | Valor habitual para clasificadores binarios calibrados con pocos datos |
| Caída aceptable al dejar fuera un asistente (LOAO) | F1 no baja más de 0.10 respecto al promedio | Si baja más, se declara que el clasificador no generaliza a asistentes no vistos (ya está como limitación) |
| Tiempo límite por envío | 5 s se mantiene | Los ejercicios de los bloques corren en milisegundos; revisar si SP-04 muestra otra cosa |

Cuando tengas los datos de SP-03 y de la pieza 7, confirmamos o corregimos estos valores en un documento de decisiones nuevo.

## 4. Siguiente lote de contenido

En orden de prioridad:

1. Los 8 bloques de **excepciones**.
2. Los 8 bloques de **recursión**.
3. Los 6 enunciados de la **sesión de etiquetado**, con sus instrucciones para C2.
4. **Consentimientos** (estudio y sesión de etiquetado) y **convocatoria**, con su versión `v1`.
