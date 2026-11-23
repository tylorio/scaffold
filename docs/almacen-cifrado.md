# Almacén local cifrado

Procedimiento del almacén donde viven los datos de los participantes en la máquina del investigador (08 §3.4, decisión del 2026-11-22).

## Qué es y qué guarda

El almacén es un **disco virtual** (un archivo `.vhdx`) cifrado con **BitLocker** y con una contraseña propia. Se monta para trabajar y se desmonta al terminar. Mientras está desmontado, el archivo no se puede leer sin la contraseña.

| Va en el almacén | No va en el almacén |
| --- | --- |
| `db.sqlite3`: diagnósticos, fragmentos de código, asignación, puntajes | La **tabla de identidades** (nombre ↔ código), que tiene su propio archivo cifrado y su propia contraseña (06 §3) |
| `datos/`: modelos, corpus, banco real de la prueba (formas A y B) | El código del sistema (el repositorio Git) |
| `tmp/`: los clones temporales de los repositorios durante el análisis | |
| `.env`: la sal de los correos de commit (`IDC_SAL_CORREOS`) | |

Si `IDC_ALMACEN` está definido y el disco no está montado, **el sistema no arranca**. Así nunca crea una base sin cifrar en otro lugar.

## 1. Crearlo (una sola vez)

Hace falta una **PowerShell como administrador**. Elige una carpeta que **no** esté dentro del repositorio ni en una carpeta sincronizada (OneDrive, Google Drive). En el ejemplo se usa `D:\idc\` y la letra `Z:`.

```powershell
New-Item -ItemType Directory -Force D:\idc
diskpart
```

Dentro de `diskpart` (20 GB como máximo; el archivo crece según se usa):

```text
create vdisk file="D:\idc\almacen-idc.vhdx" maximum=20480 type=expandable
select vdisk file="D:\idc\almacen-idc.vhdx"
attach vdisk
create partition primary
format fs=ntfs label="ALMACEN-IDC" quick
assign letter=Z
exit
```

Cifra la unidad con BitLocker y una contraseña. Usa una **distinta** de la de Windows y de la de la tabla de identidades:

```powershell
manage-bde -on Z: -UsedSpaceOnly -Password
manage-bde -protectors -add Z: -RecoveryPassword
manage-bde -status Z:
```

El segundo comando muestra una **clave de recuperación** de 48 dígitos. Anótala en papel y guárdala lejos del equipo, nunca dentro del almacén. Sin la contraseña ni la clave de recuperación, los datos no se recuperan.

También se puede activar desde el Explorador: clic derecho en `Z:` → *Activar BitLocker*.

## 2. Mover los datos al almacén

Con el almacén montado y el servidor detenido:

1. Mueve `db.sqlite3` y la carpeta `datos/` del proyecto a `Z:\`.
2. Crea `Z:\.env` y **mueve** a él la línea `IDC_SAL_CORREOS=...` del `.env` del proyecto. No la regeneres: con otra sal, los correos ya registrados dejan de reconocerse.
3. En el `.env` del proyecto agrega:

   ```text
   IDC_ALMACEN=Z:\
   ```

4. Comprueba:

   ```powershell
   python manage.py verificar_almacen
   ```

   Debe mostrar todo en `[OK]`. La línea de BitLocker necesita administrador; sin él aparece como `[AVISO]`, y entonces se comprueba con `manage-bde -status Z:`. Si queda algún `[FALTA]`, el comando termina con código 18.

## 3. Cada sesión de trabajo

- **Montar:** doble clic en `D:\idc\almacen-idc.vhdx` en el Explorador. Windows pide la contraseña de BitLocker. Si no la pide, ejecuta `manage-bde -unlock Z: -Password`. Comprueba que la letra siga siendo `Z:`; si cambia, actualiza `IDC_ALMACEN`. [VERIFICAR la primera vez: Windows suele conservar la letra si está libre.]
- **Trabajar** con el sistema como siempre.
- **Desmontar** al terminar: detén el servidor y, en el Explorador, clic derecho en `Z:` → *Expulsar*.

Mientras el almacén está montado, cualquier programa de tu sesión puede leerlo. Desmóntalo cuando no lo uses, y siempre antes de prestar o dejar el equipo.

## 4. Respaldo

Con el almacén **desmontado**, copia `almacen-idc.vhdx` a un disco externo. La copia ya está cifrada. Guarda la clave de recuperación aparte, no junto al disco externo.

## 5. Borrado al terminar el análisis (D13)

1. Exporta los **CSV agregados** (por código anónimo y sin código fuente). Son lo único que se conserva, por el plazo que fije el CEI-USIL.
2. Desmonta el almacén y **borra el `.vhdx` y todas sus copias de respaldo**. Vacía la papelera.
3. Destruye la clave de recuperación.

Borrar el archivo cifrado elimina, de una vez, el código, los fragmentos, la sal y los diagnósticos.

## Riesgo residual

- Mientras está montado, el almacén es legible para cualquier programa de la sesión del investigador (08 §3.4).
- Si se olvidan la contraseña y la clave de recuperación, los datos se pierden. Es el costo de que nadie más pueda leerlos.
