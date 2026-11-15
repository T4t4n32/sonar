# Preflight de publicación — 2026-11-07 (corregido por Claude Code)

Herramienta: `tools/preflight_publicar.py` (la creó Hermes; corregida hoy). Repositorio: `T4t4n32/sonar`, **privado** desde 2026-11-07 (estuvo público 2026-11-04 → 2026-11-07).

> Este informe **reemplaza** el que escribió Hermes, que concluía «LISTO para publicar» con base en un selftest que pasaba por accidente
> (el escáner se marcaba a sí mismo) y sin detectar nombres propios ni la clave Wi-Fi escrita con `#define`. Correcciones: patrón `#define …PASS "valor"`,
> autoexclusión, opción `--root` y selftest sobre un repositorio temporal de verdad, y lista local de nombres (`tools/.preflight-nombres.txt`, ignorada por git).
> **Segunda corrección (misma tarde):** el escaneo del historial usaba `git log -G` con expresiones que Git no entiende (`(?i)`, `\s`, `\b`) y saltaba casi todo en silencio, y el selftest «detectaba en el historial» porque el secreto seguía en el árbol. Ahora se lee todo el historial una vez y se aplican las mismas reglas de Python a cada línea añadida; el selftest borra el secreto del árbol y exige encontrarlo en un commit.

## Resultado: 0 ALTA · 18 MEDIA (10 en el árbol, 8 en el historial) · 1 BAJA
| Sev | Qué | Dónde | Decisión |
|---|---|---|---|
| MEDIA | Clave Wi-Fi por defecto `duelo1234` | `include/config.h:11` (y en el historial) | Es solo la clave del Wi-Fi de mantenimiento de cada módulo. Antes de publicar: pasarla a `include/secrets.h` (ignorado) + `secrets.example.h`, y poner otra en el módulo real. **Pendiente (firmware).** |
| MEDIA | Nombres completos de los dos autores | `docs/00-proyecto/GUIA_DE_PROCESO.md`, `docs/02-electronica/PROPUESTA_TABLERO_LDR.md`, bloque de título de `docs/01-diseno/planos/PLANO_CARCASA_SONAR.pdf` y `tools/gen_plano_carcasa.py`; también en commits `0cf72ee` y `6d796ea` | **Decisión de Sebas y Jader** (autoría pública o iniciales). Ya estuvieron 3 días en un repositorio público con 15 clonaciones únicas: no se pueden retirar las copias. |
| MEDIA | `W@ie****` en el PDF del plano | `docs/01-diseno/planos/PLANO_CARCASA_SONAR.pdf:123` | Probable falso positivo (texto binario del PDF); revisar a ojo. |
| BAJA | Ruta de Windows con usuario | `app/LEEME.md:16` | Cambiar por `<usuario>`. |

No hay claves privadas, tokens, `.jks`, `.env` ni archivos de más de 5 MB.

## Para publicar el 24-nov
1. Decidir lo de los nombres. 2. Mover la clave Wi-Fi a `secrets.h`. 3. `python tools/preflight_publicar.py` sin ALTA. 4. El script programado `tools/publicar.py` repite la verificación y solo publica si sigue sin ALTA.
