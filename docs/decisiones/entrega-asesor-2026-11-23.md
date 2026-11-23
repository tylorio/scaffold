# Entrega del asesor (23 de noviembre de 2026)

**Responde a:** `docs/necesidades-2026-11-23.md` (versión 0.11.0)

## Qué contiene

| Archivo | Para qué | Dónde va |
|---|---|---|
| `refuerzo/bloques/excepciones-s*-*.json` | 8 bloques de excepciones (24 ejercicios, 120 casos) | `refuerzo/bloques/` (sí va en Git) |
| `refuerzo/bloques/recursion-s*-*.json` | 8 bloques de recursión (24 ejercicios, 120 casos) | `refuerzo/bloques/` (sí va en Git) |
| `soluciones_privadas/soluciones_excepciones.py` | Una solución por ejercicio, con el mismo nombre de función | Repositorio de pruebas, sin publicarlas en el portal |
| `soluciones_privadas/soluciones_recursion.py` | Igual, para recursión | Igual |
| `soluciones_privadas/soluciones_sesion_etiquetado.py` | Referencias de los 6 enunciados de la sesión, solo para el supervisor y SP-05 | Almacén cifrado. **No** va al corpus ni se muestra en la sesión |
| `sesion-etiquetado/enunciados-sesion-etiquetado-v1.md` | Los 6 enunciados, la tabla de asignación, el protocolo de la sesión y las 3 instrucciones fijas de C2 | `docs/` |
| `consentimientos/consentimiento-estudio-v1.md` | Consentimiento del estudio | `docs/` y solicitud al CEI |
| `consentimientos/consentimiento-sesion-etiquetado-v1.md` | Consentimiento de la sesión (D15) | `docs/` y solicitud al CEI |
| `consentimientos/convocatoria-v1.md` | Convocatoria del estudio (A) y de la sesión (B) | `docs/`; se publica cuando el CEI apruebe |
| `decisiones-asesor-2026-11-23.md` | Confirmaciones (D22, D23) y decisiones nuevas (D24 a D28) | `docs/decisiones/` |

## Verificación hecha

- Las 48 soluciones nuevas pasan sus 240 casos, uno por uno y también con cada archivo de soluciones importado completo. Los casos pasaron por JSON antes de comprobarse, como hará el corrector.
- Cada ejemplo resuelto devuelve el resultado que muestra en su comentario.
- Los `id` tienen hasta 20 caracteres y no se repiten entre los 24 bloques.
- Los ejemplos de los 6 enunciados de la sesión salen de ejecutar sus soluciones de referencia.
- Comparé enunciados y soluciones contra T1 a T3. Cambié un ejercicio que se parecía a T3 en la forma de la solución (D22). Quedan cuatro pares para los jueces (D23).

## Lo que cambia en otros documentos

- `docs/arquitectura/07-ml-evaluacion.md` §1.3 y §1.4: tres estilos en C2 en vez de cuatro (D24), bloque sin IA primero (D25), un solo texto por enunciado (D26) e identidad de sesión en los commits (D27).
