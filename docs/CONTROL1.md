# Control 1 — domingo 8-nov-2026 (lista corta)

**Qué pide el control:** el celular manda `(x,y)` por **Bluetooth** y el láser cae dentro de su celda en **5 de 5 posiciones** de una cuadrícula impresa.
Esta lista es un resumen; los criterios y medidas completos están en `docs/BRINGUP.md` (cada punto cita su paso). Seguridad primero: **lee BRINGUP paso 8 antes de encender el láser.**

## Llevar
ESP32 clásico (WROOM-32) cargado con `modulo_a` · 2 servos + brazo + KY-008 + 2N2222A (1 kΩ y 10 kΩ) · fuente externa de 6 V para los servos (GND común; **nunca** servos desde el pin 5 V del ESP32) ·
cuadrícula impresa 20×20 con celdas de 10 mm · cinta métrica · celular Android (A04s o 13C) con **«Serial Bluetooth Terminal»** instalado · cable USB · multímetro · gafas de protección.

## Orden (cada paso tiene su criterio en BRINGUP)
| # | Qué | Criterio | BRINGUP |
|---|---|---|---|
| 1 | Cargar el firmware: `pio run -e modulo_a -t upload` y abrir `pio device monitor` | `PING` por USB → `PONG DUELO-A 0.1.0` en < 1 s | 1.3 |
| 2 | **Láser apagado al arrancar** (EN pulsado 5 s) | < 0,3 V en la base del 2N2222A, láser apagado | 2.3 |
| 3 | Disparo y orden en curso | `(20,20)` + `PING` → `ERR BUSY`, luego `OK (20,20)` | 2.7 |
| 4 | Servos y calibración (recorrido, signos, altura, 5 cruces) | el punto cae en la celda pedida | 3.1–3.6 |
| 5 | `TEST` tres veces | 15 de 15 | 5 |
| 6 | **Bluetooth** (sin el puente MAINT): emparejar `DUELO-A` en los ajustes del celular | aparece en la lista de emparejados | 6.1 |
| 7 | En «Serial Bluetooth Terminal»: conectar a `DUELO-A`, enviar `PING` | `PONG DUELO-A 0.1.0` | 6.2 |
| 8 | Enviar `(1,1)`, `(20,1)`, `(20,20)`, `(1,20)`, `(11,11)` | cada uno responde `OK (x,y)` y el punto cae en su celda | control 1 |

## Si el Bluetooth no responde (en este orden)
1. ¿Arrancó en modo Bluetooth? El pin `MAINT` (GPIO 26) **no** debe estar a GND.
2. ¿Emparejado en los ajustes del celular? El PIN heredado es `1234` (por confirmar con el celular).
3. En el terminal: fin de línea `\n` activado; las órdenes son una línea (`(11,11)` con paréntesis).
4. `PING` por USB sí responde pero por Bluetooth no → es emparejamiento o servicio SPP, no el núcleo (el núcleo pasó 48/48 pruebas y 20/20 contra el simulador).
5. Respaldo para mostrar el apuntado: modo mantenimiento por Wi-Fi (puente MAINT–GND, red `DUELO-A-MANT`, `http://192.168.4.1/`) — **no** cumple «Bluetooth», solo sirve para calibrar y demostrar.

## Qué anotar (alimenta el plan de `ARQUITECTURA_UNIVERSAL.md`)
- Tiempo desde «abrir el terminal» hasta el primer disparo (por Bluetooth) · si pidió PIN · si reconectó solo tras apagar y encender.
- Por cada posición: `ok` o `fuera: +X mm`.
- Si el emparejamiento falló en el A04s o en el 13C (modelo y versión de Android).

## Estado verificado hoy (2026-11-07), sin hardware
`pio test -e native` → **48/48** · `sim_phone.py selftest` → 20/20 · `pio run -e modulo_a` compila · **nada de esto está probado en un ESP32 real todavía.**
