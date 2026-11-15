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

## Alimentación (por módulo)

- Adaptador de **6 V / 4 A** para los servos (stall del MG996R: 2,5 A a 6 V) y convertidor de 6 V a 5 V (≥ 1,5 A) para el ESP32, el láser y el zumbador. **Un condensador de 1000 µF** junto a los servos y 470 µF junto al ESP32.
- **GND común** entre todos. Cables de servo cortos (≤ 30 cm).
- No alimentes los servos desde el pin 5 V del ESP32.

## Pines que NO se usan

0, 2, 12, 15 (strapping), 6–11 (flash), 34–39 como salida (solo entrada).
