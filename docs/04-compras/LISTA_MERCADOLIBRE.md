# Lista de compra para Mercado Libre (v2, 2026-11-07)

Sustituye la tabla de Vistronica de `COMPRAS_Y_PLAN_B.md` para quien compre en Mercado Libre. Cantidades para **2 módulos**. Marca ✔ lo que ya está en el carrito.
Regla: pedir solo a vendedores con buena reputación y envío rápido a Cali (≤ 11-nov para lo del Bloque A). **Antes de pagar**: pegarle el anuncio a Claude para revisarlo.

## Bloque A — comprar YA (no depende de las respuestas de Almario)
| ✔ | Pieza | Cant. | Búsqueda / qué exigir |
|---|---|---|---|
| ✔ | **Kit soporte pan-tilt de aluminio** para servos MG995/MG996R, con tornillería | 2 | Ya encontrado. Que el anuncio diga aluminio y compatibilidad MG995/MG996R |
| ✔ | **Módulo emisor láser 650 nm** (punto) | 4 (2 + 2 repuesto) | Ya encontrado. **≤ 5 mW**, 5 V, Ø6 mm; si dice «enfocable», mejor. Descartar > 5 mW |
| | **Servo MG996R 180°** engranajes metálicos | **8** si el levante será motorizado, **6** si no | `servo mg996r 180 engranaje metalico`; vendedor con muchas ventas (hay clones de plástico) |
| | **ESP32 con PSRAM** (clásico, con Bluetooth clásico) | 3 (2 + 1 repuesto) | `esp32 wrover devkit` (ver nota abajo) |
| | ESP32-S3 N16R8 DevKit *(opcional, para experimentos con BLE/visión)* | 1 | `esp32-s3 devkitc n16r8` |
| | **Fuente 12 V 5 A** (jack DC) | 2 | `fuente 12v 5a 60w` |
| | **Buck 5 A ajustable** (XL4015 o similar) para los servos a 6 V | 3 | `xl4015 buck 5a` — uno por módulo + repuesto |
| | Buck LM2596 (5 V para ESP32, láser y zumbador) | 3 | `lm2596 buck ajustable` |
| | Tira LED **roja** (1 m) + módulo MOSFET | 2 + 2 | `tira led roja 12v 1m`, `modulo mosfet pwm` |
| | Zumbador activo 5 V · pulsadores · interruptor · portafusible 5 A · borneras · cable de silicona 18 AWG · Dupont · termoencogible | 3 · 6 · 2 · 2 · 6 · 3 m | tienda de electrónica de Cali o ML |
| | Condensadores 1000 µF 16 V y 470 µF 16 V · transistor 2N2222 · resistencias 1 kΩ, 10 kΩ, 330 Ω | 4 · 2 · 10 · surtido | tienda local |
| | Imán + **interruptor reed** (tapa abierta/cerrada), *opcional* | 4 | `interruptor reed iman` |

### Nota sobre el ESP32 «potente»
- **Lo que limita este proyecto no es la CPU**: el firmware usa 18 % de la RAM estática y 51 % de la flash. Lo que da trabajo es que Bluetooth + Wi-Fi + muchos pines convivan, y eso no lo arregla un chip más grande.
- **El ESP32-S3 NO tiene Bluetooth clásico (SPP), solo BLE.** El firmware y el control 1 de mañana usan SPP. Con S3 habría que pasar todo a BLE (posible, ver `ARQUITECTURA_UNIVERSAL.md`).
- **Recomendación:** quédate con el chip clásico y toma la versión **WROVER (con PSRAM)** como principal: mismo Bluetooth clásico y más memoria. Sobre WROVER: los pines **GPIO16 y 17 quedan ocupados por la PSRAM** (no los uses; los pines actuales del proyecto no los usan). El S3 N16R8 queda como pieza de experimento.
- (Conocimiento general, no medido aquí.) Con un WROOM-32 normal ya sirve; WROVER es la mejora barata.

## Bloque B — comprar DESPUÉS de la respuesta de Almario
| Si dice… | Comprar |
|---|---|
| **Sí a 10×10 de 2 cm** | LDR GL5516 ×240 (200 + 20 % de repuesto) o fototransistores ×240; resistencias 10 kΩ ×250; multiplexores CD74HC4067 ×14 (7 por módulo); cable de 30 AWG; placa perforada |
| **No (20×20 de 1 cm)** | ESP32-CAM ×3 + adaptador CH340 ×2 (Plan B de visión) y/o respaldo manual |

## Bloque C — estructura y maletín (DESPUÉS del diseño en SolidWorks)
Maletín rígido (aluminio o ABS) — **se decide con las medidas del diseño** (tablero de 30 × 30 cm elevado 5 cm + tapa con la matriz vertical + torreta plegada); bisagras, resortes, tope y pestillo; tornillería M3/M4 y tuercas de inserción; acrílico/MDF; servicio de impresión 3D (PLA/PETG); fieltro o espuma. **No imprimir el maletín completo:** comprar uno hecho y diseñar por dentro (más rápido y más resistente).
