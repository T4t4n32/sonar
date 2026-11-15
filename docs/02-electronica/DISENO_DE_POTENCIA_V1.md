# Fundamentos — Batalla Naval · Diseño de potencia

> **Estado (2026-11-08): HISTÓRICO.** Sustituido por [POTENCIA](POTENCIA.md) (adaptador 12 V 5 A, buck 6 V y 5 V).
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Diseno de potencia.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](../00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27. Alcance: **dos tableros de 20×20 cm (celdas de 1 cm) en un solo maletín**, cada uno con su torreta (Almario fijó las medidas). Cada cifra lleva su origen: **[HD]** hoja de datos del fabricante que leí, **[2a]** fuente secundaria (tienda/wiki), **[SUP]** supuesto mío que se mide en las pruebas. El cálculo está en `modelo-potencia.py` (misma carpeta); si cambias un dato, se recalcula.

## 1. Veredicto

- **El presupuesto de potencia del V1 estaba mal**, y el error crece con dos tableros. El V1 decía 3,87 A para un tablero con "≈ 100 mA" de sensado. Pero el Hall A3144 consume **4,4 mA típico y 9,0 mA máximo cada uno [HD]**: 400 sensores son **1,76 A (máx. 3,6 A)**. El mismo tablero queda en **5,6 A típico** (7,5 A con el máximo de la hoja): no cabe en la fuente de 5 A del V1.
- **La solución de diseño es alimentar los Hall por losa, de a una a la vez** (interruptor de carga + escaneo en rotación): el pico de Hall baja de 3,6 A a 0,9 A por módulo y el promedio a ~11 mA.
- **Arquitectura recomendada:** un solo **adaptador externo de 12 V** (sin red eléctrica dentro del maletín) y, **por módulo**, dos convertidores DC-DC: **5 V** (ESP32, LED, Hall, lógica) y **6 V** (servos). Los servos nunca comparten riel con la lógica.
- **Números de diseño** (ambos módulos, peor caso): **5,3 A a 12 V (63 W)** → adaptador de **12 V / 8 A**; convertidor de 5 V de **≥ 8 A** nominal y de 6 V de **≥ 6 A** nominal, uno de cada uno por módulo (se pide margen: los módulos genéricos suelen exagerar su corriente).
- Falta medir 4 datos que cierran el diseño (sección 8). Uno puede cambiarlo: **si el A3144 tarda mucho en encender, la compuerta no sirve** y el adaptador sube a 12 V / 10 A.

## 2. Datos de entrada y su origen

| Componente                           | Dato                                                                                                                                                                                                                                                         | Origen                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| **Hall A3144** (Allegro A3141–A3144) | Vcc 4,5–24 V; **ICC 4,4 mA típ / 9,0 mA máx** (salida OFF, medido a Vcc = 8 V); salida colector abierto hasta 25 mA; V sat. 175 / 400 mV a 20 mA; **BOP 70–350 G** a 25 °C y hasta 450 G en temperatura; BRP 50–330 G. **La hoja no da tiempo de encendido** | **[HD]**                                                        |
| **CD74HC4067** (TI)                  | Vcc 2–6 V; VIH = 3,15 V con Vcc = 4,5 V; Ron 70 Ω típ (160 máx) a 4,5 V; **fuga de canal apagado ±0,8 µA a 25 °C y ±8 µA a 85 °C**; ICC 8 µA                                                                                                                 | **[HD]**                                                        |
| **ESP32** (Espressif v5.3)           | 2,3–3,6 V; **fuente recomendada ≥ 0,5 A**; Tx 802.11b 240 mA, 802.11g 190 mA, 802.11n 180 mA, Rx 95–100 mA; salida ≤ 40 mA por pin (baja a ~29 mA con varios), sumidero 28 mA, suma de salidas ≤ 1200 mA; entradas ≤ 3,6 V (no toleran 5 V); VIH = 0,75·VDD  | **[HD]**                                                        |
| **WS2812B** (Worldsemi)              | VDD 3,5–5,3 V; **VIH = 0,7·VDD** (3,5 V a 5 V); reset > 50 µs; circuito típico con **100 nF por píxel**. La corriente por LED **no figura** en la hoja                                                                                                       | **[HD]**                                                        |
| WS2812B: corriente                   | **60 mA a blanco pleno** (3 × 20 mA); **~1 mA apagado** por píxel                                                                                                                                                                                            | **[2a]** Adafruit                                               |
| **Servo MG996R**                     | 4,8–7,2 V; **stall 2,5 A (6 V)**; marcha 500 mA (4,8 V) / **900 mA (6 V)**; banda muerta 5 µs                                                                                                                                                                | **[2a]** tabla "de la hoja de datos" reproducida por un tercero |
| **Servo MG90S**                      | las fuentes se contradicen: stall 0,4–0,7 A, marcha 70–250 mA, banda muerta 1–15 µs. Diseño con **0,7 A stall / 0,25 A marcha**                                                                                                                              | **[2a]** + **[SUP]**                                            |
| **Láser KY-008**                     | 30 mA típico, < 40 mA; 650 nm, ≈ 5 mW                                                                                                                                                                                                                        | **[2a]**                                                        |
| **DFPlayer Mini**                    | 3,2–5 V; ~20 mA en espera, ~100 mA reproduciendo; altavoz de hasta 3 W; UART a 3,3 V con 1 kΩ en serie                                                                                                                                                       | **[2a]** DFRobot                                                |
| Fototransistor PT334-6B              | 5 mm, VCEO 30 V, IC 20 mA                                                                                                                                                                                                                                    | **[HD]** Everlight                                              |
| Eficiencia de los convertidores      | 90 %                                                                                                                                                                                                                                                         | **[SUP]**                                                       |

## 3. Arquitectura propuesta

Dos **módulos idénticos** (tablero 20×20 + torreta + ESP32 + potencia propia) unidos por 12 V y un enlace de datos. Uno es **maestro** (servidor web, lógica del juego, audio); el otro, **esclavo**. Cada módulo es una de las dos mitades del maletín.

```
Adaptador externo 12 V / 8 A  ──►  conector ≥ 8 A  ──►  fusible 8 A lento · TVS 15 V · protección de polaridad
         │
         ├──► MÓDULO A (maestro) ──── fusible 5 A lento
         │         ├─ Convertidor 12→5 V ──┬─ ESP32 · 74HC595 · mux · buffer LED · DFPlayer
         │         │                        └─ por losa (×4): PTC 2 A ─┬─ riel LED (1000 µF) ──► 100 WS2812B
         │         │                                                    └─ interruptor de carga ─► riel Hall (10 µF) ──► 100 A3144
         │         └─ Convertidor 12→6 V ──── servos MG996R + MG90S (1000 µF) ── retorno propio a la estrella
         │                                              ▲
         │                         enlace de datos A↔B (UART o ESP-NOW)
         └──► MÓDULO B (esclavo): igual, sin DFPlayer
```

- **Una sola torreta se mueve a la vez** (juego por turnos); el firmware desactiva el PWM de la otra (`detach`), así que su consumo es ~0.
- **Tierra en estrella** dentro de cada módulo, en el negativo del convertidor de 5 V; el retorno de los servos llega a ese punto por su propio cable.
- Alternativa descartada: un solo ESP32 para los dos tableros. Pide ~24 GPIO y cables largos entre mitades; la modularidad simplifica cableado, aísla fallas y reparte el consumo.

## 4. Presupuesto de corriente

Por módulo, a 5 V y 6 V. Peor caso = todos los topes a la vez, que el firmware evita.

| Escenario | 5 V maestro | 5 V esclavo | 6 V torreta activa | 6 V torreta inactiva |
|---|---|---|---|---|
| Reposo (LED con estático, sin juego) | 0,72 A | 0,70 A | 0,05 A | 0,05 A |
| **Juego típico** | **1,50 A** | **1,38 A** | **1,15 A** | 0,05 A |
| **Pico de diseño** | **3,99 A** | **3,49 A** | **3,20 A** (stall) | 0,05 A |

Componentes del pico de 5 V del maestro: ESP32 0,50 + **Hall 0,90** (una losa, valor máximo de la hoja) + **LED 2,00** (tope del limitador) + láser 0,04 + lógica 0,05 + DFPlayer 0,50.
Juego típico del LED: ≈ 1,0 A (166 casillas azules al 10 %, 34 rojas al 20 %, estático de 0,4 A).

| Entrada de 12 V (ambos módulos, η = 90 %) | Potencia | Corriente |
|---|---|---|
| Reposo | 8,6 W | 0,7 A |
| **Juego típico** | **24 W** | **2,0 A** |
| **Pico de diseño** | **63 W** | **5,3 A** |

**Sin compuerta de Hall** (los 400 siempre encendidos), pico de 5 V: **6,7 A** por módulo (maestro) y 12 V: **≈ 7,8 A** → habría que subir a un adaptador de **12 V / 10 A**. Es el plan B si la compuerta no funciona.

## 5. Dimensionado

| Elemento | Valor | Cómo sale |
|---|---|---|
| Adaptador 12 V | **12 V / 8 A (96 W)**, externo y certificado | pico 5,3 A ÷ 0,8 = 6,6 A mínimo |
| Convertidor 12→5 V (×2) | **≥ 8 A nominal**, con protección de sobrecorriente | pico 4,0 A ÷ 0,75 = 5,3 A, más margen por rating exagerado |
| Convertidor 12→6 V (×2), ajustable | **≥ 6 A nominal** | stall 3,2 A ÷ 0,75 = 4,3 A |
| Fusible 12 V por módulo | **5 A lento** | pico 3,6 A × 1,25 |
| Fusible general | **8 A lento** | pico total + margen |
| PTC por losa | **2 A de retención** | losa: LED 0,5 A + Hall 0,9 A = 1,4 A |
| Cable de 12 V y 5 V | **16–18 AWG** | 3,6 A en 1 m de ida y vuelta = **23 mV** |
| Cables de servo | **cortos (≤ 30 cm) o reemplazar por 22 AWG** | el cable original (~28 AWG) cae **0,3 V** con 2,5 A y 0,1 V con 0,9 A |
| Pistas de 5 V de la losa | **≥ 2 mm** en la entrada; ≥ 1 mm en el bus | 2 A → 0,78 mm; 3 A → 1,37 mm (IPC-2221, cobre de 1 oz, +10 °C) |
| Caída en el bus de LED | despreciable | 98 mΩ por 200 mm; 0,5 A repartidos → **24 mV** al final |
| Conector de potencia | **≥ 8 A** (XT60, GX16 de 2 polos…) | los jacks de barril típicos de 5,5×2,1 mm no suelen aguantar 8 A: verificar la clasificación |
| Pérdidas | 6 W en el peor caso | 10 % de 63 W; ventilación del maletín |

**Condensadores:** 1000 µF/10 V por losa en el riel de LED · 10 µF + 100 nF en el riel de Hall · **100 nF por píxel** (así lo dibuja la hoja del WS2812B) · 1000 µF + 100 nF en cada riel de servos · 470 µF + 100 nF junto al ESP32 · 100 nF por mux y por cada 8 Hall.

## 6. Reglas de integración

1. **Hall por losa, de a una.** El firmware enciende una losa, espera el tiempo de estabilización (se mide, UT-HW-16), lee sus 100 celdas y la apaga; rota por las 4. Escaneo completo ≤ 400 ms, así que levantar un barco se detecta en < 1 s.
2. **Tope de LED en firmware: 2 A por módulo.** El limitador escala el cuadro (UT-SW-13). Mientras una torreta se mueve, baja a **1,5 A**.
3. **Una torreta a la vez**; la otra, sin PWM.
4. **Arranque seguro:** todo habilitador (74HC595 `OE`, interruptores de carga, transistor del láser) lleva una resistencia que lo deja **inactivo** si el GPIO está flotante. Orden: convertidores → ESP32 → `OE` de los 595 → riel de LED → escaneo de Hall → **servos al final**, láser siempre apagado hasta calibrar.
5. **Niveles lógicos:** mux a **3,3 V** (con 5 V el VIH sería 3,15 V, sin margen para el ESP32); Hall a 5 V con **pull-up a 3,3 V**; LED por **74AHCT125** (VIH del WS2812B = 3,5 V) + 330 Ω; el ESP32 no tolera 5 V en ningún pin.
6. **Línea SIG de los mux: pull-up de 2,2 kΩ, no 10 kΩ.** Cada mux apagado fuga hasta ±0,8 µA a 25 °C (±8 µA a 85 °C); con 28 mux por tablero en la misma línea son hasta 22 µA → 0,05 V con 2,2 kΩ, pero 0,22 V con 10 kΩ, y mucho peor con calor. Una línea SIG **por tablero**.
7. **Vigilancia del riel:** divisor resistivo a un ADC1 para leer el 5 V; si cae bajo 4,6 V el firmware reduce el LED y avisa.
8. **Servos:** retorno propio hasta la estrella; 1000 µF junto al servo; PWM sin sacudidas (rampa de aceleración) para no pedir el pico de arranque de golpe.
9. **ESP32 aislado del ruido:** ferrita o 10 Ω + 470 µF desde el riel de 5 V; el DFPlayer y su altavoz con su retorno directo a la estrella.
10. **Protección de entrada:** TVS de 15 V, fusible, protección de polaridad; el WS2812B lleva protección propia contra polaridad inversa, el A3144 también (−35 V).
11. **Medir antes de cerrar** (sección 8), y registrar cada resultado en la tabla de pruebas.

## 7. Qué se agrega a las pruebas

| Prueba | Para qué |
|---|---|
| UT-HW-02 (ampliada) | los dos convertidores y el adaptador bajo carga, con rizado y temperatura |
| UT-HW-15 | consumo real del Hall (decide fusibles y compuerta) |
| **UT-HW-16** (nueva) | tiempo de arranque del Hall: viabilidad de la compuerta |
| **UT-HW-17** (nueva) | convertidores: corriente real que entregan, caída y calor a 75 % de carga |
| IT-1 (ampliada) | los dos módulos juntos, peor caso, con todos los rieles medidos |

## 8. Lo que falta medir

| Dato | Por qué importa | Cómo se mide | Si sale mal |
|---|---|---|---|
| **ICC real del A3144 a 5 V** (la hoja lo da a 8 V; los clones difieren) | decide fusibles y la compuerta | UT-HW-15, con 10 sensores | si es < 3 mA, la compuerta sobra |
| **Tiempo de arranque del A3144** (la hoja no lo da) | si es muy largo, la compuerta no funciona | UT-HW-16: ESP32 enciende el sensor y lee tras 5, 10, 20, 50, 100, 200 µs, 1000 veces con imán | **plan B sin compuerta: 12 V / 10 A** |
| Corriente real del MG90S y del DFPlayer reproduciendo | las fuentes se contradicen | UT-HW-03/04/12 con el multímetro en serie | ajustar el convertidor de 6 V o el limitador de audio |
| Capacidad real de los convertidores genéricos | muchos exageran la corriente nominal | UT-HW-17 | comprar de otra referencia |

## Fuentes

- Allegro, *A3141–A3144 sensitive Hall-effect switches* (copia: [cdn.shopify.com](https://cdn.shopify.com/s/files/1/1560/1473/files/a3144eul.pdf)).
- TI, [CD74HC4067](https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf) (SCHS209D, 2024).
- Espressif, [ESP32 Series Datasheet v5.3](https://documentation.espressif.com/esp32_datasheet_en.pdf).
- Worldsemi, [WS2812B](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf) (copia de Adafruit); regla de 60 mA / 1 mA en la [guía de Adafruit](https://learn.adafruit.com/introducing-feather-rp2040-scorpio/powering-scorpio-neopixel-projects).
- [MG996R](https://www.espboards.dev/sensors/mg996r) (tabla de la hoja, vía espboards.dev) y [MG90S](https://components101.com/motors/mg90s-metal-gear-servo-motor) (fuentes discrepantes).
- [KY-008](https://hackaday.io/project/166042), [DFPlayer Mini (DFRobot)](https://wiki.dfrobot.com/dfplayer_mini_sku_dfr0299), Everlight [PT334-6B](https://www.mouser.com/datasheet/2/143/PT334-6B-1663203.pdf).
