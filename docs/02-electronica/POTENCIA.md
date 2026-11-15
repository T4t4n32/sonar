# Potencia y autonomía — por módulo (2026-11-08)

Cifras marcadas «est.» son estimaciones de hoja de datos/conocimiento general, **no medidas aquí**: se confirman con multímetro al montar.

## Cargas
| Carga                              | Tensión | Consumo típico       | Pico                                             |
| ---------------------------------- | ------- | -------------------- | ------------------------------------------------ |
| 2 servos MG996R (pan + tilt)       | 6 V     | 0,5–1,5 A moviéndose | ~2,5 A **cada uno** si se atascan (~5 A los dos) |
| ESP32 con Bluetooth/Wi-Fi          | 5 V     | 0,15–0,3 A           | ~0,5 A                                           |
| Láser 650 nm 5 mW                  | 5 V     | ~40 mA               | —                                                |
| Zumbador                           | 5 V     | ~30 mA               | —                                                |
| Tira LED roja 1 m (solo al fallar) | 12 V    | ~0,4 A               | —                                                |
| Sensores (LDR/lectura)             | 3,3–5 V | < 50 mA              | —                                                |
**Pico de entrada (est.):** (5 A × 6 V ≈ 30 W) / 0,9 + ~2 W + ~5 W ≈ **40 W ≈ 3,4 A a 12 V**. **Promedio (est.): ~10 W.** Si algún día hay servo de levante (opción A): se mueve **antes** que pan/tilt, nunca a la vez.

## Arquitectura recomendada
```
Entrada 12 V (adaptador 5 A  ó  batería 3S) → fusible 10 A → interruptor general
   ├─ Buck 5 A ajustable (XL4015) → 6,0 V → servos  (+ condensador 1000 µF 16 V pegado a los servos)
   ├─ Buck LM2596 → 5,0 V → ESP32, láser, zumbador  (+ 470 µF)   [láser por transistor 2N2222 desde GPIO]
   └─ 12 V directo → tira LED roja (por módulo MOSFET)
GND común en un solo punto (estrella). Divisor a GPIO34 para leer el voltaje de la batería y avisar en la app.
```
Nunca alimentar los servos desde el 5 V del ESP32. Probar con multímetro: caída de tensión del riel de 6 V al arrancar un servo.

## Fuente: tres opciones
| Opción                                            | Qué es                                                                 | A favor                                                                                | En contra                                                   |
| ------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **1. Adaptador 12 V 5 A** (recomendada como base) | enchufe → jack DC                                                      | simple, barato, llega rápido, sin riesgo de batería                                    | depende de tener un enchufe en el salón                     |
| **2. Batería 3S Li-ion con BMS**                  | 3S2P de 18650 (≈ 6 Ah ≈ 66 Wh) + BMS 3S ≥ 20 A + cargador 12,6 V 2–3 A | autonomía est. **5–6 h** con 10 W promedio (3S1P: ~2,5–3 h); la demo dura menos de 1 h | más piezas; celdas falsas abundan; no cargar sin vigilancia |
| **3. Disparador USB-C PD a 12 V**                 | cualquier cargador USB-C (laptop/teléfono) → 12 V hasta 3 A            | un cargador «de los que ya tienes» sirve                                               | 36 W apenas cubren el pico est. de 40 W                     |

## Sobre el «módulo de carga rápida»
Para Li-ion 3S la carga correcta es **CC/CV a 12,6 V**, ~0,5–1 C (2–3 A con celdas de 3 Ah): unas 3 h (est.). «Más rápida» no ayuda ni conviene. Si se quiere cargar con USB-C, el orden es PD (≥ 15 V) → cargador 3S CC/CV → BMS → batería. **Carga y uso a la vez**: se permite si el cargador y el BMS comparten el puerto «charge/discharge» y la corriente alcanza; no recomendado con los servos moviéndose.

## Un solo pedido (si se hace la opción 2)
Adaptador 12 V 5 A ×2 (sirve también para cargar) · buck XL4015 5 A ×3 · LM2596 ×3 · BMS 3S 20 A con balance ×2 · cargador 12,6 V 3 A ×2 · **ó** batería 12 V Li-ion ya armada con BMS y cargador ×2 (más simple) · fusibles 10 A + portafusible ×2 · conectores XT60 y jack DC ×4 · cable de silicona 14–18 AWG · condensadores 1000 µF y 470 µF. **Celdas 18650 de marca reconocida**, de vendedor con reputación (no «9800 mAh» ni «3000 mAh» de precio imposible).
**Decisión de diseño:** el maletín debe dejar **espacio y conector para la batería** aunque la primera versión use solo el adaptador.

## Batería candidata (2026-11-08, pendiente de compra)
Paquete «Batería 12 V 5200 mAh 18650 3S2P» (Mercado Libre, vendedor BATERIA_CERO, Bogotá): **6 celdas 18650, descarga de 10 A, BMS de 20 A máx. (según la descripción)**; conector a elegir XT30 o XT60 (**elegir XT60**); $119.000 (con cupón, $79.000). Cumple la necesidad (pico est. 3,4 A a 12 V).
**Falta confirmar con el vendedor:** cómo se carga (cargador de 12,6 V por los mismos dos cables) y la marca de las celdas. **Comprar solo 1** para probar; la base sigue siendo el adaptador de 12 V 5 A.
Aparte: cargador 12,6 V 2-3 A, fusible de 10 A con portafusible, conectores XT60. Al recibirla: medir voltaje (11-12,6 V), probar con servos moviéndose vigilando temperatura, primera carga vigilada. Firmware: aviso de batería baja ~10 V (divisor en GPIO34).
