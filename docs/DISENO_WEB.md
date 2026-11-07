# Diseño de la web «SONAR · Batalla Naval»

Aplica `wiki/concepts/guia-diseno-interfaces.md` (vault T4) al oficio de este proyecto. Escrito 2026-11-06.

## 1. Oficio y usuario
Un estudiante (o un compañero) con el celular en una mano, frente a un tablero físico de 30×30 cm y una torreta láser, con prisa y
con el miedo de que **el láser apunte mal o no pare**. Entorno: aula iluminada, Wi-Fi `DUELO-A-MANT` sin internet. La página
debe ser rápida, legible al sol y **honesta** sobre lo que hace el hardware.

## 2. Filosofía (la vara de cada pantalla)
> **«Puente de mando de un submarino: oscuro, preciso, el sonar late.»**

Si una pieza no se explica con eso, sobra.

## 3. Tres motivos (no se mezclan con otros)
| Motivo | Qué es en SONAR | Dónde aparece |
|---|---|---|
| **Barrido** | La torreta barre su rango real de pan (±57°, `PAN_LIMIT_DEG`) desde la estación | logo, radar en reposo, «conectando» |
| **Eco** | Anillos que nacen en la celda donde cae el láser; color y forma distinguen *tocado* (relleno, rojo) y *agua* (anillo, cian) | disparo, marcas, resultado del TEST |
| **Cota** | Líneas finas de plano que miden: las guías de fila y columna hasta la celda elegida, las marcas de 5 en 5 | radar, calibración, el mismo lenguaje del plano de la carcasa |

## 4. Tokens (todo sale de `:root`)
| Token | Abismo (oscuro) | Carta náutica (claro) | Uso |
|---|---|---|---|
| `--bg` | `#040a0f` | `#e9f2f1` | fondo |
| `--panel` | `#0a1822` | `#ffffff` | tarjetas |
| `--sonar` | `#46f0b5` | `#007a5a` | acento único: DISPARAR, estado vivo |
| `--echo` | `#5ad6ff` | `#0b78a8` | eco de *agua*, tráfico enviado |
| `--hit` | `#ff5d4d` | `#c8281b` | solo *tocado*, rayo láser, errores |
| `--warn` | `#ffc24a` | `#946200` | ocupado, calibración |
| `--stop` | `#e5303c` | `#c4222e` | solo STOP |

Un solo botón de acento por pantalla: **DISPARAR**. Movimiento: `--ease-out: cubic-bezier(.23,1,.32,1)`, interacciones ≤ 200 ms,
entradas ≤ 700 ms, solo `transform`/`opacity`, `:active` con `scale(.97)`, `prefers-reduced-motion` respetado.

## 5. Presupuesto de acciones
Disparar: **tocar el radar → DISPARAR** (2 toques). Marcar resultado: 1 toque más (*Tocado* / *Agua*). Nada de «Siguiente».
Arrastrar el dedo sobre el radar afina la celda; las flechas del teclado también; `Esc` = STOP.

## 6. Estados (cada uno con texto y forma propios)
buscando · conectado · ocupado (`ERR BUSY`) · sin enlace (con instrucciones) · simulado (insignia fija) · disparando (rayo) ·
disparo completado · error de protocolo (`ERR RANGE/LIMIT/STOP/FORMAT…` traducido) · TEST en curso / resultado 5/5.

## 7. Honestidad
- **STOP por Wi-Fi no interrumpe un disparo en curso** (`WebServer` atiende una petición a la vez): se dice en la interfaz; por USB y Bluetooth sí.
- El TEST responde **al final** (HTTP no transmite por partes): la barra de progreso no inventa avance; los cinco objetivos
  pulsan «en curso» y se resuelven con la respuesta.
- `OK (x,y)` significa «disparo ejecutado», no «tocado»: el *tocado* lo decide el dueño del tablero (`MARK HIT` / `MARK MISS`).
- **Modo simulado** (sin módulo): insignia permanente y nombre `DUELO-DEMO`; nunca se hace pasar por el hardware.
- Nada probado todavía en un ESP32 real (ver `PENDIENTES.md`).

## 8. Restricciones técnicas
Un solo archivo, sin CDN ni fuentes externas, ES2017, compatible con `board_build.embed_txtfiles` (se sirve desde flash).
El protocolo (`PROTOCOLO.md`) **no cambia**.

## 9. Verificación (ver `registro/`)
Navegador real contra `tools/fake_device.py` (consola sin errores), `tools/sim_phone.py selftest` (20/20), capturas 375×812 y
1280×800 de cada estado, `pio run -e modulo_a`.
