# Fundamentos — Batalla Naval · Lista de compras (2 tableros 20×20)

> **Estado (2026-11-08): HISTÓRICO.** Sustituida por [LISTA_MERCADOLIBRE](LISTA_MERCADOLIBRE.md); conservada por sus referencias de piezas.
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Lista de compras.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](../00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27 (v3). Reemplaza las versiones anteriores. Base: **dos módulos idénticos** (tablero 20×20 cm con celdas de 1 cm + torreta + ESP32 + potencia propia) en un solo maletín, como describió Sebas; arquitectura y números en el *Diseño de potencia*. Las cantidades son **totales para los dos módulos** e incluyen ~10 % de repuesto en piezas baratas y 1 repuesto de lo que se quema.

> [!warning] Sin precios
> No pude verificar precios en COP (las búsquedas solo trajeron tiendas del exterior). La columna **COP** queda en blanco: cotiza y pásame las cifras; yo sumo. **Disponibilidad antes que precio**: las piezas de volumen (≈ 900 LED y 900 Hall) pueden no existir en Colombia, y la importación (semanas) tiene que salir junto con las PCB.

## Olas de compra

| Ola | Cuándo | Qué |
|---|---|---|
| **0** | hoy y mañana | **Cotizar disponibilidad** de la sección 5 (LED, Hall SMD, mux). Decidir D4 (ensamble por servicio) y presupuesto |
| **1** | pedido el 28-oct | Secciones 1, 2, 3 y 4: control, actuación, kit de pruebas y **potencia** (hay que medirla antes de cerrar la PCB). Llega en días |
| **2** | **antes del lun 2-nov (control A)** | Secciones 5 y 6: PCB y componentes de las 8 losas |
| **3** | tras UT-HW-06 | Mecánica definitiva (sección 7) e imanes de producción |

## 1. Control

| # | Ítem | Especificación | Cant. | Ola | COP |
|---|---|---|---|---|---|
| 1 | ESP32 DevKit | ESP32-WROOM-32 (alimentación recomendada ≥ 0,5 A); 1 por módulo + 1 de repuesto. Confirmar pinout | 3 | 1 | |
| 2 | Cable USB de datos | el conector de la placa, con datos | 2 | 1 | |

## 2. Actuación y apuntado (una torreta por módulo)

| # | Ítem | Especificación | Cant. | Ola | COP |
|---|---|---|---|---|---|
| 3 | Servo MG996R | metálico, 10 kg·cm, eje **pan** (4,8–7,2 V; stall 2,5 A) | 3 | 1 | |
| 4 | Servo MG90S | micro, engranes metálicos, eje **tilt** | 4 | 1 | |
| 5 | Módulo láser KY-008 | 650 nm, ≤ 5 mW (clase 3R: **no mirar el haz**); si se consigue, ≤ 1 mW. Punto ≤ 3 mm | 4 | 1 | |
| 6 | Transistor NPN 2N2222A (o BC337) | maneja el láser (~30 mA) sin cargar el GPIO | 6 | 1 | |
| 7 | Mástil + soporte pan-tilt | impreso en 3D; mástil de **150–180 mm** sobre el margen trasero de cada tablero. Se diseña en CAD | 2 | 3 | |

## 3. Kit de pruebas en protoboard (UT-HW)

| # | Ítem | Especificación | Cant. | Ola | COP |
|---|---|---|---|---|---|
| 8 | Sensor Hall A3144 TO-92 | colector abierto, unipolar | 10 | 1 | |
| 9 | Hall A3144 **SOT-23** (muestra) | el que irá en la PCB; verificar polaridad, punto de operación y consumo | 5 | 1 | |
| 10 | Imán N35 cilíndrico | **dos tamaños** para elegir: Ø5×2 mm × 25 y Ø6×3 mm × 25 | 50 | 1 | |
| 11 | Fototransistor PT334-6B | **5 mm**, pico 940 nm; para ver la respuesta a 650 nm | 10 | 1 | |
| 12 | Fototransistor SMD (muestra) | familia Everlight PT19-21 u otro SMD (verificar) | 5 | 1 | |
| 13 | Multiplexor CD74HC4067 | **módulo breakout** de 16 canales con pines | 2 | 1 | |
| 14 | Registro 74HC595 | DIP-16 | 3 | 1 | |
| 15 | Interruptor de carga | CI de ≥ 2 A con habilitación a 3,3 V y subida controlada (p. ej. familia TPS22918; verificar) + placa adaptadora SOT-23→DIP | 3 | 1 | |
| 16 | Buffer 74AHCT125 | DIP-14, sube el dato LED de 3,3 V a 5 V | 2 | 1 | |
| 17 | LED WS2812B | tira 5 V de 60 LED/m, 1 m | 1 | 1 | |
| 18 | Protoboard | 830 puntos | 2 | 1 | |
| 19 | Cables Dupont | M-M, M-H, H-H, 20 cm | 3 × 40 | 1 | |
| 20 | Resistencias 1/4 W y condensadores | kit: 330 Ω, 1 kΩ, 2,2 kΩ, 10 kΩ, 100 kΩ, 10 Ω; 100 nF × 20, 10 µF × 10 | 1 kit | 1 | |
| 21 | Tiras de pines 2,54 mm | macho y hembra | 1 + 1 | 1 | |

## 4. Potencia y protección (comprar y medir **antes** de cerrar la PCB)

| # | Ítem | Especificación | Cant. | Ola | COP |
|---|---|---|---|---|---|
| 22 | **Adaptador 12 V / 8 A** | externo, **con certificación**, sin red eléctrica dentro del maletín. Si se prefiere comprar con margen: 12 V / 10 A (plan B de la sección 4 del *Diseño de potencia*) | 1 | 1 | |
| 23 | Conector de potencia ≥ 8 A | XT60, GX16 de 2 polos o similar; **verificar la corriente nominal** del jack del adaptador | 3 pares | 1 | |
| 24 | **Convertidor DC-DC 12→5 V ≥ 8 A** | con protección de sobrecorriente; 1 por módulo + 1 de repuesto | 3 | 1 | |
| 25 | **Convertidor DC-DC 12→6 V ≥ 6 A** | ajustable; 1 por módulo + 1 de repuesto | 3 | 1 | |
| 26 | Fusible lento 8 A + portafusible | general en 12 V | 1 + 1 | 1 | |
| 27 | Fusible lento 5 A + portafusible | uno por módulo (+ repuestos) | 2 + 2 | 1 | |
| 28 | TVS 15 V (p. ej. SMBJ15A) y protección de polaridad | diodo/MOSFET de entrada | 2 | 1 | |
| 29 | Interruptor general + LED piloto | | 1 | 1 | |
| 30 | Electrolíticos 1000 µF / 16 V | servos y entrada de convertidores | 6 | 1 | |
| 31 | Electrolíticos 470 µF / 10 V | junto al ESP32 | 4 | 1 | |
| 32 | Cable de silicona 16–18 AWG | rojo/negro, troncales de 12 V, 5 V y 6 V | 8 m | 1 | |
| 33 | Carga de prueba | resistencias de potencia (p. ej. 5 Ω–10 Ω, 25 W) o carga electrónica, para UT-HW-17 | 1 lote | 1 | |

## 5. Componentes de las 8 losas (ola 2) — piezas de volumen

Cada módulo = 4 losas de 100×100 mm (10×10 celdas). Cotiza **stock y plazo**; si no hay en el país, se importa en el mismo pedido de las PCB.

| # | Ítem | Especificación | Por losa | Total (+ repuesto) | COP |
|---|---|---|---|---|---|
| 34 | Hall A3144 **SOT-23** | cara superior junto al LED (distancia al imán ≈ 3 mm). Huella con opción de **no poblar** | 100 | **970** | |
| 35 | LED WS2812B 5050 | 1 por celda | 100 | **880** | |
| 36 | Condensador cerámico 100 nF, 0805 | **1 por LED** (como en la hoja del WS2812B) + 1 por mux + 1 cada 8 Hall | ~135 | **1.100** | |
| 37 | Multiplexor CD74HC4067 **SOIC-24** | 7 por losa para los Hall (7 × 4 × 2 = 56) + 1 por módulo para los fototransistores de referencia | 7 | **62** (58 + 4) | |
| 38 | Registro 74HC595 SOIC-16 | 56 `EN` de mux + 8 interruptores de carga = 64 salidas | — | **10** (8 + 2) | |
| 39 | Interruptor de carga (SOT-23-5 o similar) | 1 por losa: alimenta el riel de Hall. Subida controlada | 1 | **10** | |
| 40 | Buffer 74AHCT125 SOIC-14 | dato de la tira | — | **3** | |
| 41 | PTC de 2 A (retención) | 1 por losa en la entrada de 5 V | 1 | **10** | |
| 42 | Electrolítico 1000 µF / 10 V | riel de LED de cada losa | 1 | **10** | |
| 43 | Condensador 10 µF, 0805 | riel de Hall de cada losa | 2 | **20** | |
| 44 | Resistencias 0805 surtido | 2,2 kΩ (pull-up SIG) × 10, 10 kΩ × 80, 330 Ω × 10, 1 kΩ × 30, divisor de 5 V (100 kΩ / 33 kΩ) × 6 | — | **1 kit** | |
| 45 | **Fototransistor SMD de referencia** | **8 por tablero** (4 esquinas + 4 medios de borde, **en el margen, no en las celdas**) + repuestos | — | **24** | |
| 46 | Borneras 5 mm, 2 polos | alimentación por losa | 2 | **16** | |
| 47 | Conectores de datos entre losas | JST-XH o header 2,54 mm (dato LED, S0–S3, `EN`, SIG) | 2 | **20** | |

## 6. Servicios

| # | Servicio | Detalle | COP |
|---|---|---|---|
| 48 | **Fabricación de PCB** | losa de 100×100 mm; **10 unidades** (8 + 2); 2 capas si el ruteo cierra, 4 si no. Plazo de fabricación + envío: **verificar al cotizar** | |
| 49 | **Ensamble SMD (PCBA)** | **muy recomendado**: ≈ 880 LED, 970 Hall, 1.100 pasivos y 90 CI ≈ **9.000 soldaduras** si se hace a mano. Verificar que las referencias estén en la biblioteca del servicio | |
| 50 | Courier internacional | para las PCB y lo importado; incluye aduana | |
| 51 | FabLab UAO / servicio de corte y 3D | corte láser (chasis, difusoras) e impresión 3D (mástiles, rejillas, barcos) — confirmar disponibilidad y costo | |

## 7. Mecánica (ola 3)

| # | Ítem | Especificación | Cant. | COP |
|---|---|---|---|---|
| 52 | **Maletín rígido** | tipo estuche con bisagra; dimensiones del CAD (≈ 2 tableros de 30×30 cm + torretas de 15–18 cm de alto). Espuma o separadores | 1 | |
| 53 | Chasis 30×30 cm por módulo | MDF o acrílico de 3 mm cortado a láser; el margen trasero aloja el mástil | 2 | |
| 54 | Placa superior difusora | acrílico opal/blanco de 2–3 mm, 200×200 por tablero; **solo 8 ventanas** (los fototransistores de referencia) | 2 | |
| 55 | Rejilla separadora de celdas | 20×20 celdas, pared ~1 mm, 5–8 mm de alto; evita que la luz se cuele a la celda vecina (4 piezas de 100×100 por tablero) | 8 | |
| 56 | Barcos | **2 flotas × (5-4-3-3-2)** = 20 piezas impresas, con alojamiento de imán (misma polaridad, marcada) | 20 | |
| 57 | Imanes N35 de producción | el tamaño que gane en UT-HW-06; 34 por flota + repuesto | 80 | |
| 58 | Tornillería M3 + separadores, pegante | kit | 1 | |

## 8. Audio, cableado y consumibles

| # | Ítem | Especificación | Cant. | Ola | COP |
|---|---|---|---|---|---|
| 59 | DFPlayer Mini + microSD + altavoz | solo en el módulo maestro; altavoz 3 W / 8 Ω; microSD FAT32 con `0001.mp3`…. Cantidades: DFPlayer × 2 (1 de repuesto), microSD × 1, altavoz × 1 | 4 | 1 | |
| 60 | Cable de silicona 22–24 AWG | colores; cableado dentro de cada módulo y servos | 30 m | 1 | |
| 61 | Cable de 4 hilos o conector para el enlace A↔B | 12 V + datos entre los dos módulos, con conectores de potencia | 2 m | 1 | |
| 62 | Estaño 60/40 con flux, pasta de flux, malla desoldante | 0,8 mm | 1 | 1 | |
| 63 | Pasta de soldar SMD + flux | solo si algo del SMD se ensambla a mano | 1 | 2 | |
| 64 | Termoencogible | surtido | 1 | 1 | |
| 65 | Placa de referencias | perfboard o PCB pequeña por tablero, para los 8 fototransistores SMD del marco y su cableado al mux óptico | 2 | 2 | |

## 9. Herramientas — verifica qué ya tienen

Multímetro (idealmente con medida de corriente hasta 10 A), cautín de 40–60 W con punta fina, pelacables, alicate de corte, pinzas finas, regla y transportador. **Si el SMD va a mano:** aire caliente o placa de reflujo (¿FabLab o laboratorios UAO?), lupa o microscopio y pinzas ESD.

## 10. Opcionales (recomendados)

Gafas para láser de 650 nm (OD 2+) · **INA219** para medir corriente en IT-1 · reed switch en la tapa (enclavamiento, IT-8) · pulsador de paro · osciloscopio o analizador lógico del laboratorio para UT-HW-16 (tiempo de arranque del Hall; sin ellos se mide con el propio ESP32).

## Seguro y recortes

- **Si la PCB no llega (nivel 4 del Plan):** un solo módulo en perfboard de 10×10 con THT: +100 Hall TO-92, +1 m de tira LED de 60 LED/m y +8 módulos de mux. Solo se compra si el control A falla.
- **Primer recorte del hardware:** no poblar los Hall (la huella queda): −970 Hall, −56 mux, −10 interruptores, −8 registros. El juego sigue con la flota declarada en la web.

## Preguntas antes de comprar

1. ¿Presupuesto máximo y quién paga? ¿Se divide con tu compañero?
2. ¿Una torreta por tablero (la diapositiva muestra dos cañones) o una compartida? Esta lista asume **una por tablero**; una compartida quita 1 MG996R, 1 MG90S, 1 láser y 1 mástil, pero según la disposición de los tableros puede pedir más de 180° de giro (D7).
3. ¿Qué ya tienen ambos? (ESP32, servos, láser, fuentes, protoboards, soldadura, tu trabajo de grado del colegio).
4. ¿Quién diseña la PCB y en qué herramienta (Eagle, KiCad)?
