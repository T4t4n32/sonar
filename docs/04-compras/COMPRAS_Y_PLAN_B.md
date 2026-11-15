# Compras y Plan B — sin sensores por celda (2026-11-07)

**Problema:** la versión con 400 LDR + 400 fototransistores por matriz necesita >100 piezas de cada tipo que no hay en tiendas locales; desde China llegan entre el 19-nov y el 1-dic (control 2: 15-nov, entrega: 24-nov). **Todo lo que se compre debe llegar a Cali antes del miércoles 11-nov.**

## Plan B: una cámara en lugar de cientos de sensores
Con una **ESP32-CAM** (OV2640): (1) mirando la matriz vertical, el punto láser es un píxel saturado → posición y validación del test de 5 posiciones; (2) mirando la cama desde arriba, cada celda se compara con «tablero vacío» → mapa de barcos de 400 bits. Resultado por UART al ESP32 principal (`CAMV …` / `CAMB …`).
Cálculos míos (est., no medidos): a ~20 cm del plano de 20 cm una celda de 1 cm ocupa ~30 px y el punto láser ~10-16 px; a ~28 cm sobre un tablero de 30 cm una celda ocupa ~21×21 px. Exposición manual baja para que solo el láser sature.
**Lo que no da:** detección instantánea (a ~20 cuadros/s son ~50 ms; el tiempo de disparo lo mide el firmware).
**Riesgos:** luz del salón y sombras de manos (luz fija, calibración «vacío», lectura estable 1-2 s), 3-5 días de desarrollo, ESP32-CAM aún sin probar aquí. **Respaldo:** barcos marcados en la app para no perder la demostración.
Puerta de decisión **mar 10-nov** (con las piezas en la mano): ¿la visión entra o se queda el respaldo?

## Lista de compra (precios y estado leídos en vistronica.com el 2026-11-07; COP, IVA según la tienda)
Envío según la propia tienda: **Cali, 1 a 2 días hábiles** (vistronica.com/info/7-como-envian-mi-pedido). Pedido mínimo $5.000.
| Pieza | Cant. | Referencia / enlace | Precio unit. |
|---|---|---|---|
| Servomotor **MG996R 180°** (engranajes metálicos) | 6 (4 + 2 repuesto) | vistronica.com/robotica/motores/servomotores/servomotor-mg996r-180-grados-detail.html | $32.368 |
| *(alternativa)* Servomotor MG995 metálico 180° | — | …/servomotor-mg995-pinoneria-metalica-180-detail.html | $28.441 |
| **Módulo láser** 650 nm, **5 mW**, 5 V, Ø6 mm, cabeza de cobre | 4 (2 + 2 repuesto) | vistronica.com/optoelectronico/modulo-laser-detail.html | $3.213 |
| **ESP32-CAM** (OV2640) | 3 para el prototipo | vistronica.com/iot-internet-de-las-cosas/placa-de-desarrollo-wifibluetooth-esp32-s-con-camara-ov2640-esp32-cam… | $53.610 |
| Adaptador USB CH340 para ESP32-CAM | 2 | …/modulo-adaptador-usb-ch340-para-placa-de-desarrollo-esp32-cam… | $5.058 |
| Convertidor Buck **LM2596 3 A** | 4 | vistronica.com/fuente-de-voltaje/conversores-dc-dc/convertidor-dc-dc-buck-lm2596-3a… | $5.534 |
| Módulo **MOSFET** LR7843 (para las tiras LED) | 2 | vistronica.com/modulos/modulo-mosfet-aislado-lr7843-pc817-hw-532-control-pwm-d… | $5.950 |
| Fuente conmutada 12 V 3 A | 2 | vistronica.com/fuente-de-voltaje/fuente-conmutada/fuente-conmutada-12v-3a-detail.html | $37.902 |
Total aproximado de esta tabla: **≈ $480.000** (sin envío). Los enlaces completos están en `tools/compras_buscar.py` (búsqueda); los precios cambian.

**Aviso técnico (conocimiento general, no medido):** un LM2596 «3 A» entrega de forma continua bastante menos sin disipador, y un MG996R puede pedir ~2,5 A si se atasca. Usa **un buck por servo** y confirma con el multímetro. Los servos admiten ~4,8-7,2 V.

## Lo que NO está en esa tienda (buscar en Mercado Libre; Mercado Libre bloquea a los programas, se busca a mano)
| Pieza | Búsqueda sugerida | Qué exigir |
|---|---|---|
| **Soporte pan-tilt metálico** para 2 servos MG995/MG996R (×2) | `soporte pan tilt metalico mg996r` / `pan tilt servo bracket mg995` | metálico (no plástico), compatible con servos grandes, vendedor MercadoLíder, «Full» o «llega mañana/≤ 11-nov» a Cali |
| Cinta LED **roja** 5 V o 12 V (1 m, ×2) | `tira led roja 5v 1 metro` | 12 V si se alimenta con la fuente de 12 V a través del MOSFET |
| *(si prefieres ML)* cualquiera de las piezas de arriba | usa el nombre de la tabla | láser **≤ 5 mW** (descartar mayores), punto rojo 650 nm, cabeza de cobre Ø6 mm; MG996R con engranajes metálicos (hay clones de plástico) |
Lo que sí hay en tiendas físicas de Cali (resistencias, 2N2222, condensadores 1000 µF y 470 µF, protoboard, cables) se compra allá.

## Orden de trabajo
1. **Hoy/domingo:** pedir servos, láseres, soportes pan-tilt, buck, fuentes y **3 ESP32-CAM** (el núcleo del test 5/5 + la prueba de visión).
2. **Lun 9 → mar 10:** montar un módulo, `docs/03-firmware-y-app/BRINGUP.md`, y probar visión con la cámara.
3. **Mar 10-nov (puerta de decisión):** visión sí/no. Si sí, se piden las cámaras restantes (1-2 días de envío).
4. **15-nov:** control 2 (test 5/5 ×3). La visión no es requisito de la rúbrica.

## Pendientes de verificar
Existencias reales al comprar (la web no garantiza), que el soporte pan-tilt de ML llegue a tiempo, la clase del láser por etiqueta (BRINGUP 8.1), y el consumo real de los servos.
