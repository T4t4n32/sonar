# Conexiones (ESP32 clásico, DevKit WROOM-32)

| Señal | GPIO | Conexión |
|---|---|---|
| Servo **pan** (Tower Pro SG5010) | 18 | señal; alimentación a 6 V (4 pilas AA o fuente); GND común con el ESP32 |
| Servo **tilt** (Tower Pro SG5010) | 19 | señal; alimentación a 6 V; **1000 µF entre + y GND junto a los servos** |
| **Láser** (KY-008, 3 pines: `S`, medio sin usar, `-`) | 23 | **Con transistor (recomendado):** GPIO → 1 kΩ → base del 2N2222; emisor a GND; láser entre +5 V (pin `S`) y el colector (pin `-`); **10 kΩ de la base a GND** (queda apagado al arrancar). **Directo (plan B, probado como válido):** pin `S` → GPIO 23, pin `-` → GND (≈ 20–30 mA por el pin y algo menos de brillo). Patillas del 2N2222: según el encapsulado (TO-18 metálico o TO-92 de plástico) E-B-C o C-B-E; verifícalas con el multímetro en modo diodo |
| **Interruptor general** | — (no es GPIO) | mecánico, en serie con la entrada de 6 V, antes de cualquier regulador; corta/da paso a toda la alimentación (servos + ESP32) de una vez |

## Hardware final (decisión de Sebas, 2026-11-20)

**ESP32 + 2 servos + láser + fase de potencia. Nada de luces** (ni matriz WS2812B ni LED de acierto). El sonido y la vibración los hace la app en el celular.

Lo siguiente **ya no se arma**. El firmware conserva los pines y no falla si faltan, porque no hay nada conectado que leer:

| Señal | GPIO | Estado |
|---|---|---|
| Zumbador activo | 21 | **recomendado** (+ a GPIO 21, − a GND): la rúbrica pide «un sonido con cada disparo» y el rival nos maneja con SU app, que no sabemos si suena |
| LED de acierto | 22 | **descartado** |
| Pulsador TEST | 25 | opcional (el TEST se lanza desde la app) |
| Interruptor MAINT | 26 | opcional (modo mantenimiento Wi-Fi) |
| Medida de 5 V | 34 | opcional |
| Matriz LED decorativa (WS2812B) | 4 | **descartada** |

## Alimentación (por módulo)

- Adaptador de **6 V / 4 A** para los servos (stall del MG996R: 2,5 A a 6 V) y convertidor de 6 V a 5 V (≥ 1,5 A) para el ESP32, el láser y el zumbador. **Un condensador de 1000 µF** junto a los servos y 470 µF junto al ESP32.
- **GND común** entre todos. Cables de servo cortos (≤ 30 cm).
- No alimentes los servos desde el pin 5 V del ESP32.
- **Nunca una pila de 9 V como fuente de los servos** (2026-11-15): supera el máximo del MG996R (7,2 V) y una 9V alcalina común no sostiene la corriente de marcha/stall (hasta 2,5 A) — se hunde peor que una pila ya débil y puede resetear el ESP32 por caída de tensión compartida. Ver `registro/2026-11-15-banco-hardware.md`.

## Pines que NO se usan

0, 2, 12, 15 (strapping), 6–11 (flash), 34–39 como salida (solo entrada).
