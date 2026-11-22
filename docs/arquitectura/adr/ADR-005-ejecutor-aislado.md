# ADR-005: Ejecutor en un contenedor de larga duración, con un proceso hijo limitado por envío

- Estado: aceptada (2026-11-22). Se valida con SP-04
- Fecha: 2026-11-22
- Fase y prompt de origen: F8 / P8 (`08-seguridad-etica.md` §2)

## Contexto

El portal ejecuta las soluciones que los estudiantes envían a los ejercicios de refuerzo. Hoy el prototipo lo hace en un subproceso con tiempo límite, pero con los permisos del servidor: ese código podría leer o borrar archivos, usar la red o agotar la memoria. En la nube y con 25 participantes eso es inaceptable (RNF-08). Las restricciones del proyecto son:
- una persona y pocas semanas;
- el crédito de Azure for Students;
- sin trabajos en segundo plano (ADR-001).

## Decisión

1. El ejecutor es un **contenedor propio, de larga duración**, con un servidor HTTP mínimo hecho solo con la biblioteca estándar. El portal es su único cliente, por una **red interna sin salida a internet**, y le envía un **token compartido**.
2. El contenedor corre con:
   - raíz de solo lectura y `/tmp` en memoria;
   - el usuario `nobody`;
   - todas las capacidades quitadas y `no-new-privileges`;
   - límites de memoria, CPU y procesos.
3. Cada envío corre en un **proceso hijo nuevo**, con:
   - una carpeta temporal propia y entorno vacío;
   - `python -I` y una sesión propia;
   - límites `setrlimit` de CPU, memoria, procesos, tamaño de archivo y archivos abiertos.

   El servidor mata al grupo de procesos completo si se pasa del tiempo de reloj.
4. El protocolo es el de 05 §3.5. El portal sigue usando el mismo `corredor.py`: lo único que cambia es dónde corre.
5. En el perfil local, sin `IDC_EJECUTOR_URL`, se mantiene el subproceso actual, solo para el desarrollo y las pruebas. **El perfil de nube no arranca sin `IDC_EJECUTOR_URL`.**

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| `docker run` por cada envío | Es el aislamiento más limpio, pero obliga a dar al portal acceso al motor de Docker, lo que equivale a ser administrador del servidor. Además no existe en los servicios PaaS de Azure y suma 1–2 s de arranque por envío |
| Mantener el subproceso actual en la nube | No aísla la red, el disco ni la memoria (RNF-08) |
| Una máquina virtual por envío (Firecracker, gVisor) | Más fuerte, pero no cabe en el tiempo ni está disponible en Azure for Students [VERIFICAR] |
| Un servicio externo de ejecución de código | Envía código de estudiantes a un tercero (06 §5) y depende de un proveedor |
| Restringir Python por dentro (prohibir `import os`, etc.) | Se evade con facilidad; no es una barrera de seguridad |

## Consecuencias

- Hay que mantener una imagen más (`ejecutor/Dockerfile`) y desplegarla junto al portal (F9).
- F9 debe resolver la red interna sin salida a internet en Azure. Si no es posible, este ADR se revisa.
- Las pruebas de SP-04 se marcan aparte (`-m docker`) porque necesitan el motor de Docker. Las pruebas normales siguen corriendo sin él.
- La corrección de T1–T3 (pieza 6) puede usar el mismo ejecutor en local con `IDC_EJECUTOR_URL`. Es lo recomendable, porque también es código de estudiantes.

## Verificación

- Las 12 pruebas de SP-04 (08 §2.4) pasan contra el contenedor real.
- El perfil de nube falla al arrancar sin `IDC_EJECUTOR_URL` ni `IDC_EJECUTOR_TOKEN`.
