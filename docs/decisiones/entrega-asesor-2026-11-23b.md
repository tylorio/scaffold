# Entrega del asesor (23 de noviembre de 2026, segunda parte)

**Responde a:** `docs/lo-que-necesito-2026-11-23.md` §1. Las decisiones están en `decisiones-asesor-2026-11-23b.md` (D29 a D34).

| Archivo | Qué es | Dónde va |
|---|---|---|
| `decisiones-asesor-2026-11-23b.md` | Respuestas a §1 y decisiones D29 a D34 | `docs/decisiones/` |
| `refuerzo/bloques/excepciones-s4-1.json` (v2) | Ejercicio `exc-s4-1-e3` reemplazado (D29) | `refuerzo/bloques/` |
| `refuerzo/bloques/estructuras_datos-s1-1`, `s2-1`, `s2-2`, `s4-1` y `excepciones-s4-2` (v2) | Campo `aviso_concepto: false` en 7 ejercicios (D32) | `refuerzo/bloques/` |
| `soluciones_privadas/soluciones_excepciones.py` | Soluciones de excepciones con el ejercicio nuevo | Reemplaza `tests/soluciones_bloques/excepciones.py` |
| `soluciones_privadas/soluciones_sesion_etiquetado.py` | Referencias de los 6 enunciados de la sesión | Almacén cifrado. No va a Git ni al corpus |
| `consentimientos/*.md` | Consentimientos y convocatoria v1, corregidos (D30) | Reemplazan `docs/consentimientos/*.md` |
| `sesion-etiquetado/enunciados-sesion-etiquetado-v1.1.md` | §3 y §4 con el `autor_id` de D31 | Reemplaza la copia de `docs/sesion-etiquetado/`, quitando lo que describa la prueba, como hiciste con v1 |
| `correo-CEI-v2.md` | Correo al CEI con las tres consultas de D28 | Lo envía Pablo después de completar los `[COMPLETAR]` |

**Verificación hecha:**
- Los bloques nuevos pasan sus casos.
- El módulo de soluciones de excepciones, importado completo, pasa sus 120 casos.
- Las funciones auxiliares repetidas son idénticas.
- El ejercicio nuevo da 0,186 contra T3 con tu métrica de soluciones.
- Los 5 bloques de D32 son idénticos a los tuyos salvo el campo y la versión.

**Lo que tienes que programar:** el campo `aviso_concepto` y el texto nuevo del aviso, y la prueba de `test_contenido.py` (D32). La pieza 7 (D33) se hace antes del go/no-go.
