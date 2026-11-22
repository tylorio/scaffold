# 08. Seguridad, ética y sandbox

- Fase: F8 / Prompt P8
- Fecha: 2026-11-22
- Entrada:
  - `04-contexto-contenedores.md` (ADR-001: núcleo local por lotes y portal mínimo en la nube);
  - `05-componentes-interfaces.md` (E1/E2 ejecutor, rutas del portal);
  - `06-datos-privacidad.md` (tres lugares de datos);
  - decisiones del asesor D3, D4, D11, D13, D14, D19, D21, S1 y P5–P9.
- Decisiones del autor del 2026-11-22:
  - el almacén local va en un **disco virtual cifrado con BitLocker**;
  - el acceso del estudiante se **bloquea tras 10 intentos fallidos en 15 minutos**.
- ADR nuevo: `adr/ADR-005-ejecutor-aislado.md`.
- Regla aplicada (P8): si una mitigación no cabe en el tiempo, se usa la opción mínima segura y se declara el riesgo residual.

## 1. Modelo de amenazas (STRIDE ligero)

### 1.1 Contenedores y flujos

| ID | Elemento | Dónde corre | Qué protege |
| --- | --- | --- | --- |
| C1 | Núcleo de análisis | Máquina del investigador | Clones, fragmentos de código, P(IA), modelo, banco de la prueba, soluciones de T1–T3 |
| C2 | Almacén local | Disco virtual cifrado (`.vhdx` con BitLocker) en esa máquina | `db.sqlite3`, `datos/`, `repos/`, la sal del HMAC (en `.env`) |
| C3 | Portal de refuerzo | Nube (Azure) | Códigos anónimos, hash del código de acceso, asignación, IDC agregado, uso del refuerzo |
| C4 | Ejecutor | Contenedor aislado, solo en red interna | Nada propio; debe contener el código que ejecuta |
| C5 | Tabla de identidades | Archivo cifrado en la máquina del investigador, fuera del sistema | Nombre ↔ código anónimo |

| ID | Flujo | Datos |
| --- | --- | --- |
| F1 | GitHub o carpeta → núcleo | Repositorio del participante, con su historial |
| F2 | Núcleo → portal, subido a mano | Archivo `resultados-v1` (JSON) sin código, rutas, URLs ni hashes |
| F3 | Estudiante ↔ portal | Código de acceso, material, soluciones de los ejercicios (HTTPS) |
| F4 | Portal ↔ ejecutor | Solución y casos de prueba; resultado (red interna) |
| F5 | Núcleo → base codificada externa | CSV por código anónimo |
| F6 | Almacén → respaldo | Copia del `.vhdx` ya cifrado |

### 1.2 Amenazas

Prioridad: **A** = alta, **M** = media, **B** = baja. Estado: **hecho** = implementado y probado; **8a–8d** = parte de la pieza 8 que lo implementa; **9** = pieza 9.

| Amenaza | STRIDE | Activo | P | Mitigación | Cómo se verifica | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| El código de un estudiante sale del sandbox: red, disco, procesos | E | C4 y lo que lo rodea | A | Contenedor sin red de salida, con disco de solo lectura y un usuario sin privilegios. Sin capacidades y con límites de CPU, memoria y procesos. Cada envío corre en un proceso hijo con límites propios (§2) | Las pruebas de SP-04 (§2.4) | 8a |
| Código que agota recursos: bucle infinito, bomba de procesos o de memoria | D | C4 | A | Tiempo límite, límite de memoria y de procesos por envío y por contenedor, y concurrencia acotada | SP-04 | 8a |
| Alguien llama al ejecutor directamente | S/E | C4 | A | Solo escucha en la red interna y exige un token compartido con el portal | Prueba: sin token responde 401 | 8a |
| Se adivina el código de acceso de un estudiante | S | C3 | A | Código aleatorio de 10 caracteres (unas 10¹⁵ combinaciones), guardado solo como hash y entregado en persona. Bloqueo tras **10 intentos fallidos en 15 minutos** | Prueba de bloqueo; prueba de que la base no guarda el código en claro | 8c |
| Un estudiante ve el material o los datos de otro | I | C3 | A | La sesión queda ligada a un código; ninguna vista recibe el código por la URL | Prueba: un estudiante no puede abrir `/mi/` de otro | 8c |
| Alguien sin cuenta abre las vistas del investigador | S/I | C1 y C3 | A | Todas exigen iniciar sesión como investigador. Hoy no hay control de acceso | Prueba por cada ruta de gestión: sin sesión, redirige al login | 8c |
| El código de los estudiantes llega a la nube | I | C3 | A | El portal solo recibe `resultados-v1`. El exportador y el importador rechazan código, rutas, URLs, correos y hashes (ESC-06) | Pruebas del exportador y del importador con campos prohibidos | 8b |
| Roban el equipo del investigador o una copia de sus datos | I | C2 | A | Disco virtual con BitLocker y contraseña propia, desmontado cuando no se usa. El respaldo es el mismo archivo cifrado | Procedimiento escrito (§3.4) y lista de cierre | 8d |
| Se filtra el banco de la prueba | I | C1 | A | Fuera de Git, solo en el almacén local y nunca en el portal (D21) | Prueba de que `datos/` está en `.gitignore` y de que el portal no tiene ruta al banco | Hecho / 8b |
| Se altera la asignación después de congelarla | T | C1 y C3 | M | Congelación única, admin de solo lectura, el portal importa la asignación inmutable (D3) | Pruebas de congelación (pieza 5) | Hecho |
| Se altera el archivo de resultados entre el núcleo y el portal | T | F2 | M | El importador valida el esquema y registra el hash del archivo; reimportar exige el mismo `analisis_id` | Prueba: un archivo modificado queda registrado con otro hash | 8b |
| Una acción del investigador sin registro (importar, liberar, borrar) | R | C3 | M | Tabla de auditoría inmutable | Prueba: cada acción deja su fila | 8b |
| XSS por la salida del código del estudiante | T/E | C3 | M | Plantillas con escapado automático; la salida se trunca a 200 caracteres | Prueba: `<script>` en la salida llega escapado | 8a |
| CSRF en los formularios | T | C3 | M | Protección CSRF de Django en todos los POST | Prueba con un cliente que exige el token CSRF | 8c |
| Secretos en el repositorio | I | Todos | A | Clave, sal y token del ejecutor solo en el entorno o en `.env`, fuera de Git (S1) | `.env` en `.gitignore`; arranque falla si falta un secreto | Hecho / 8a |
| Se identifica a terceros por los commits | I | C1 | A | Filtro por autor: los correos de otros autores solo se hashean en memoria (D19) | Pruebas de la pieza 3 | Hecho |
| El estudiante ve su IDC durante la intervención | I (ética) | C3 | M | El portal no muestra el IDC hasta el postest (D11) | Prueba de la vista del estudiante | 9 |
| Los registros guardan datos personales | I | C3 | M | Se registran códigos anónimos, nunca nombres ni correos. La IP se guarda solo como hash, para el bloqueo de intentos, y se borra a las 24 h | Prueba: la tabla de intentos no contiene la IP en claro | 8c |
| Una dependencia tiene una vulnerabilidad conocida | E | Todos | B | Versiones acotadas en `requirements.txt`; revisión antes de desplegar [VERIFICAR: herramienta de auditoría de dependencias en F9] | Revisión en F9 | F9 |

## 2. Sandbox del ejecutor

### 2.1 Diseño (ADR-005)

Un **contenedor de larga duración** con un servidor HTTP mínimo (`ejecutor/servidor.py`, solo biblioteca estándar). Por cada envío lanza un **proceso hijo nuevo** (`corredor.py`) en una carpeta temporal propia, con límites del sistema operativo. El portal es su único cliente.

Las capas de aislamiento son tres:

| Capa | Qué hace |
| --- | --- |
| Contenedor (Docker) | Sin red de salida: una red interna sin acceso a internet, que solo usa el portal. Raíz de solo lectura (`--read-only`), `/tmp` en memoria (`tmpfs`) y usuario sin privilegios (`65534`, *nobody*). `--cap-drop ALL`, `no-new-privileges` y límites de memoria, CPU y procesos (`--memory`, `--cpus`, `--pids-limit`) |
| Proceso hijo | `setrlimit`: tiempo de CPU, memoria, procesos, tamaño de archivo y archivos abiertos. Sesión propia, para matar todo el grupo de procesos al terminar. Entorno vacío y `python -I` |
| Servidor | Corre como **proceso 1** del contenedor: Linux no le entrega las señales que le envían otros procesos del contenedor, así que el código del estudiante no puede matarlo. Atiende **un envío a la vez** y, al terminar cada uno, mata y recoge todo proceso que haya quedado. Además exige un token compartido con el portal, limita el código a 20 KB y la salida a 64 KB, y aplica un tiempo límite de reloj. Se niega a arrancar si no es el proceso 1, porque su limpieza mataría procesos ajenos |

### 2.2 Límites

| Límite | Valor | Dónde |
| --- | --- | --- |
| Tiempo de reloj por envío | 5 s (máximo 10) | Servidor: mata el grupo de procesos |
| Tiempo de CPU por envío | 5 s | `RLIMIT_CPU` |
| Memoria por envío | 256 MB | `RLIMIT_AS` |
| Procesos | 128 en el contenedor; 64 para el usuario del hijo | `--pids-limit` y `RLIMIT_NPROC` |
| Archivo más grande que puede escribir | 1 MB | `RLIMIT_FSIZE` |
| Archivos abiertos | 32 | `RLIMIT_NOFILE` |
| `/tmp` | 16 MB, en memoria | `tmpfs` |
| Memoria del contenedor | 512 MB | `--memory` |
| CPU del contenedor | 1 | `--cpus` |
| Envíos simultáneos | 1 (los demás esperan su turno hasta 15 s; después, 503) | Cerrojo del servidor. Es la opción mínima segura: permite limpiar todos los procesos tras cada envío. Si hiciera falta más capacidad, se agregan réplicas del contenedor |
| Tamaño del código | 20 KB | Servidor y portal |
| Tamaño de la respuesta del hijo | 64 KB | Servidor |

[PENDIENTE: ajustar con SP-04 y con la carga real de 25 participantes; son valores de partida.]

### 2.3 Limpieza

- La carpeta temporal de cada envío se borra al terminar.
- Al terminar cada envío, haya superado o no el tiempo, el servidor **mata y recoge todo proceso que no sea él mismo**. Así no quedan procesos huérfanos, ni siquiera los que crearon una sesión propia para escapar de su grupo. La respuesta informa `procesos_restantes`, que SP-04 exige que sea 0.
- El contenedor no guarda nada entre envíos: tiene disco de solo lectura y `/tmp` en memoria.

### 2.4 Pruebas de aislamiento (SP-04)

Cada prueba envía código malicioso al ejecutor real, en su contenedor, y comprueba que **no lo logra** y que **el servidor sigue respondiendo** después.

| N.º | El código intenta | Resultado esperado |
| --- | --- | --- |
| 1 | Abrir una conexión de red (`socket.create_connection(("1.1.1.1", 53))`) | Error de red |
| 2 | Resolver un nombre de dominio | Error |
| 3 | Escribir fuera de `/tmp` (en `/app` o `/etc`) | Error de permisos o de disco de solo lectura |
| 4 | Leer las variables de entorno | El entorno está vacío y no aparece el token |
| 5 | Bomba de procesos (`os.fork()` en bucle) | Se corta por el límite de procesos; el servidor sigue vivo |
| 6 | Reservar 2 GB de memoria | `MemoryError` o el proceso muere; el servidor sigue vivo |
| 7 | Bucle infinito | Se corta por tiempo y se informa |
| 8 | Dejar un proceso huérfano que siga corriendo | No queda ningún proceso después de la respuesta |
| 9 | Escribir un archivo de 100 MB | Se corta por el límite de tamaño |
| 10 | Matar al servidor (`os.kill(os.getppid(), 9)`) | El servidor sigue respondiendo |
| 11 | Imprimir 10 MB por la salida | La respuesta se trunca o se descarta; el servidor sigue vivo |
| 12 | Llamar al ejecutor sin token | 401 |

### 2.5 Riesgo residual

- El contenedor **comparte el núcleo** del sistema operativo anfitrión. Un fallo del núcleo podría permitir escapar. En Windows, Docker Desktop corre dentro de una máquina virtual (WSL2), que agrega una capa. La opción más fuerte sería una máquina virtual por envío, pero no cabe en el tiempo ni en el presupuesto.
- Los límites dependen de que la plataforma de la nube los respete. [VERIFICAR en F9: si el servicio de contenedores de Azure elegido permite una red interna sin salida a internet y los límites de procesos.]
- El código del estudiante puede **falsificar su resultado**, por ejemplo redefiniendo la comparación. Para el refuerzo no importa, porque no se califica. La corrección de T1–T3 ocurre en local, sobre las soluciones de la sesión supervisada.

## 3. Autenticación, autorización, secretos y registros

### 3.1 Roles

| Rol | Cómo entra | Qué puede hacer |
| --- | --- | --- |
| Investigador | Cuenta de Django con contraseña, creada con `createsuperuser` en cada perfil | Todo lo de `/gestion/` y, en local, las vistas de análisis |
| Estudiante | Código de acceso de 10 caracteres, entregado en persona | Solo `/mi/`: sus conceptos, sus bloques liberados, sus intentos y, después del postest, su informe |
| Expertos y docentes | No tienen cuenta | Nada (RF-28, plan 9.6) |

### 3.2 Código de acceso del estudiante

- Se genera al azar con un alfabeto sin caracteres ambiguos (sin `0`, `O`, `1`, `l`, `I`). Se muestra **una sola vez**, al registrarlo, para entregarlo impreso.
- Se guarda solo su hash, con el mismo mecanismo que las contraseñas de Django (PBKDF2).
- **Bloqueo:** 10 intentos fallidos en 15 minutos desde la misma conexión. La IP se guarda solo como hash y los intentos se borran a las 24 h.
- Si un estudiante pierde su código, el investigador genera uno nuevo y el anterior deja de servir.

### 3.3 Secretos

| Secreto | Dónde vive | Perfil |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Entorno o `.env` (fuera de Git) | Los dos, con un valor distinto en cada uno |
| `IDC_SAL_CORREOS` | `.env` del almacén local | Solo local (D19) |
| `IDC_EJECUTOR_TOKEN` | Entorno del portal y del ejecutor | Nube (y local si se usa el contenedor) |
| Credenciales de la base de la nube | Configuración del servicio en Azure | Solo nube [F9] |

Si falta un secreto, el sistema no arranca (`ImproperlyConfigured`). Así nunca corre con un valor por defecto inseguro.

### 3.4 Almacén local cifrado (decisión del autor, 2026-11-22)

- Un **disco virtual** (`.vhdx`) cifrado con **BitLocker** y una contraseña propia, distinta de la de Windows y de la tabla de identidades.
- Ahí van `db.sqlite3`, `datos/` (banco de la prueba, modelos, corpus), `repos/` (clones) y el `.env` con la sal.
- El sistema solo necesita saber dónde está, con una variable de entorno (`IDC_ALMACEN`).
- Se monta para trabajar y se desmonta al terminar.
- **Respaldo:** copiar el `.vhdx` desmontado, que ya está cifrado, a un medio externo.
- **Borrado final (D13):** destruir el `.vhdx` y sus copias, y conservar solo los CSV agregados.

Los pasos para crearlo van en el README (pieza 8d). Riesgo residual: mientras está montado, cualquier programa que corra en la sesión del investigador puede leerlo.

### 3.5 Registro de accesos y acciones

- **Auditoría** (portal y núcleo): importar resultados, congelar, liberar el control, validar bloques, borrar participantes, crear y revocar códigos de acceso. Cada fila guarda fecha, usuario, acción y objeto (un código anónimo).
- **Entradas de estudiantes:** fecha y código, para la adherencia y para detectar abusos. Los intentos fallidos guardan solo el hash de la IP.
- No se registra el código de las soluciones (06).

## 4. Controles éticos incorporados al diseño

| Control | Cómo se cumple | Estado |
| --- | --- | --- |
| El IDC siempre se muestra con su incertidumbre | Intervalo de Wilson en la interfaz, el CSV y el informe (RF-34) | Hecho |
| El estudiante no ve su IDC durante la intervención | Oculto en las semanas 9–12; aparece en el informe tras el postest (D11) | 9 |
| No hay vistas con nombres reales | El sistema no guarda nombres; la tabla de identidades vive fuera (D14) | Hecho |
| No hay reportes disciplinarios ni de plagio | No existe ninguna vista ni exportación por estudiante con fines de sanción. El IDC se presenta como estimación (RF-32) | Hecho |
| El participante puede ver sus datos | Informe personal al final (RF-31); consulta al investigador | 10 |
| El participante puede retirarse | Borrado en el portal y en el almacén, sin consecuencias (RF-30, D13) | 10 |
| Solo se analiza a quien consintió | Filtro por autor (D19); sin consentimiento registrado no se analiza (RF-29) | D19 hecho; consentimiento en 10 |
| Lista de espera para el control | El material del concepto de control se desbloquea tras el postest (D4) | 9 |
| Los calificadores no conocen la asignación | El CSV de puntajes no lleva asignación (D3) | Hecho |
| El código de los estudiantes no sale de la máquina del investigador | ADR-001; exportador e importador sin código | 8b |

## 5. Lista para el comité de ética (CEI-USIL)

Evidencia del diseño que se puede adjuntar a la solicitud:

- [ ] Diagrama de contexto y contenedores (04), que muestra que el código de los estudiantes no sale de la máquina del investigador.
- [ ] Modelo de datos y diccionario con la sensibilidad de cada campo (06 §1–§2).
- [ ] Lista de lo que **no** se recoge: nombres, correos de terceros, URLs, código de las soluciones de refuerzo y código en la nube (06).
- [ ] Procedimiento de custodia de la tabla de identidades y del almacén cifrado (06 §3; este documento §3.4).
- [ ] Procedimiento y plazos de borrado por retiro y al cierre, y qué se conserva (D13).
- [ ] Modelo de amenazas con sus mitigaciones (§1) y resultado de las pruebas de aislamiento (SP-04).
- [ ] Descripción del ejecutor aislado: el código de los ejercicios se ejecuta sin red y no se guarda.
- [ ] Controles éticos (§4): IDC con incertidumbre, oculto durante la intervención, sin uso disciplinario, lista de espera, calificación ciega.
- [ ] Consentimiento principal y consentimiento de la sesión de etiquetado (D15), con:
  - la entrega del repositorio **con historial Git** (P9);
  - los correos de commit declarados y el filtro por autor (D19);
  - el alojamiento de datos codificados en Azure y su región (D14).
- [ ] Autorización escrita del alojamiento en Azure, que emite el CEI-USIL (D14, Anexo F). [PENDIENTE: pedirla.]

---

**Supuestos**
- La máquina del investigador es de uso personal y tiene Windows 11 Pro, con BitLocker disponible.
- El portal corre en un servicio de contenedores de Azure que permite una red interna entre el portal y el ejecutor. [VERIFICAR en F9.]
- 25 participantes: un envío a la vez basta, porque cada uno dura menos de un segundo salvo los que llegan al tiempo límite. Si hiciera falta, se agregan réplicas.

**Decisiones que debes tomar**
1. Ninguna nueva. Los límites de §2.2 se ajustan con SP-04.

**Riesgos**
- Núcleo compartido del contenedor (§2.5).
- Si Azure no permite cortar la salida a internet del ejecutor, hay que buscar otro servicio o aceptar un riesgo mayor. Se decide en F9.

**Siguiente paso**
- Pieza 8, en este orden:
  - 8a: ejecutor aislado y SP-04;
  - 8b: exportador e importador de `resultados-v1`, perfiles y auditoría;
  - 8c: acceso del investigador y del estudiante;
  - 8d: almacén cifrado.
