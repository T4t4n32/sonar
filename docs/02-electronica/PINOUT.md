# Conexiones (ESP32 clásico, DevKit WROOM-32)

| Señal | GPIO | Conexión |
|---|---|---|
| Servo **pan** (MG996R) | 18 | señal; alimentación a 6 V; GND común con el ESP32 |
| Servo **tilt** (MG90S) | 19 | señal; alimentación a 6 V |
| **Láser** (KY-008) | 23 | GPIO → 1 kΩ → base de un 2N2222A; emisor a GND; el láser entre 5 V y el colector; **10 kΩ de la base a GND** (queda apagado al arrancar) |
| **Zumbador** activo | 21 | GPIO → zumbador → GND (si consume > 12 mA, con transistor) |
| **LED** de acierto | 22 | GPIO → 330 Ω → LED → GND |
| Pulsador **TEST** | 25 | a GND (pull-up interno) |
| Interruptor **MAINT** | 26 | a GND al arrancar = modo mantenimiento (Wi-Fi) |
| Medida de 5 V (opcional) | 34 | divisor 100 kΩ / 33 kΩ |
| **Interruptor general** | — (no es GPIO) | mecánico, en serie con la entrada de 6 V, antes de cualquier regulador; corta/da paso a toda la alimentación (servos + ESP32) de una vez |

## Reservado (propuesto 2026-11-15, NO implementado)

| Señal | GPIO | Conexión |
|---|---|---|
| Matriz LED decorativa (WS2812B) | 4 | dato; VCC a 5 V; GND común; 100 nF por LED + 470 µF al inicio de la tira |

Solo decorativa (feedback visual de acierto/fallo), sin lógica de juego ni detección — eso ya se descartó por tiempo (ver `docs/00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md`, no suma puntos de rúbrica). Pin reservado para no chocar con nada de la lista de arriba; sin código todavía. El WS2812B a 5 V espera ≥3,5 V en la señal y el GPIO da 3,3 V — en tiras cortas suele andar igual; si hay parpadeo, agregar un buffer 74HCT125 entre GPIO4 y la tira.

## Alimentación (por módulo)

- Adaptador de **6 V / 4 A** para los servos (stall del MG996R: 2,5 A a 6 V) y convertidor de 6 V a 5 V (≥ 1,5 A) para el ESP32, el láser y el zumbador. **Un condensador de 1000 µF** junto a los servos y 470 µF junto al ESP32.
- **GND común** entre todos. Cables de servo cortos (≤ 30 cm).
- No alimentes los servos desde el pin 5 V del ESP32.
- **Nunca una pila de 9 V como fuente de los servos** (2026-11-15): supera el máximo del MG996R (7,2 V) y una 9V alcalina común no sostiene la corriente de marcha/stall (hasta 2,5 A) — se hunde peor que una pila ya débil y puede resetear el ESP32 por caída de tensión compartida. Ver `registro/2026-11-15-banco-hardware.md`.

## Pines que NO se usan

0, 2, 12, 15 (strapping), 6–11 (flash), 34–39 como salida (solo entrada).
