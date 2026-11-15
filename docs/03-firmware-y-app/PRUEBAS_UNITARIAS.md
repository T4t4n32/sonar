# Fundamentos — Batalla Naval · Pruebas unitarias

> **Estado (2026-11-08): PARCIAL.** Plan de pruebas original; el estado real (52/52 nativas, selftest 24/24, e2e 29/29) está en [ESTADO](../ESTADO.md).
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Pruebas unitarias.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](../00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27. Una prueba unitaria verifica **una sola cosa aislada**. Aquí hay dos capas:

- **Parte A — lógica de firmware (UT-SW)**: funciones puras probadas en el PC, sin hardware (PlatformIO `native` + Unity). Se pueden escribir **ya**, mientras llegan las piezas.
- **Parte B — componentes en banco (UT-HW)**: cada pieza sola en protoboard, con criterio de aprobación medible. Se hacen al recibir la ola 1.

Parámetros de referencia (decidido el 27-oct): **2 módulos** (A maestro, B esclavo), cada uno con tablero **N = 20**, celda **d = 10 mm**, flota **2 × (5-4-3-3-2)** (34 celdas) y 4 losas de 10×10. **Todo el código recibe N, d, flota y máscara de losas activas como parámetros**: el 10×10 (una losa) es el mismo código con otros valores, y las pruebas que dependen de N se corren también con N = 10.
Estado: ☐ pendiente · ✔ aprobada · ✘ falló (anota qué).

## Parte A — Lógica de firmware (sin hardware)

| ID | Unidad bajo prueba | Casos y resultado esperado | Est. |
|---|---|---|---|
| UT-SW-01 | Parser de celdas (`"B7"` ↔ fila, columna; letra = fila, número = columna) | N=20: `A1`→(0,0) · `T20`→(19,19) · `b7`→(1,6) (acepta minúscula) · inválidos → `ERR_RANGE`: `U1`, `A0`, `A21`, `""`, `1A`, `AA1`. Con N=10: `J10`→(9,9) y `K1` inválido | ☐ |
| UT-SW-02 | Celda → mm (centro de celda) | `X = X0 + (j+0,5)·d`. Con X0=0, d=10: j=0→5 mm, j=19→195 mm. Índice fuera de [0,N−1] → error | ☐ |
| UT-SW-03 | Interpolación bilineal (ajuste fino) | Q00=0, Q10=100, Q01=50, Q11=150: f(0,0)=0 · f(1,1)=150 · f(0,5; 0)=50 · f(0; 0,5)=25 · f(0,5; 0,5)=75. Las esquinas se reproducen exactas | ☐ |
| UT-SW-04 | **Cinemática inversa** pan/tilt (H3) | Torreta del V1 en el margen trasero (100, −25, 150) mm: objetivo (100,100) → pan 90,00° / tilt 50,19° · (0,0) → 165,96° / 55,50° · (200,200) → 66,04° / 31,35° · (100,0) → 90,00° / 80,54°. Torreta (100, −100, 150): (100,100) → 90,00° / 36,87° · (0,0) → 135,00° / 46,69°. Tolerancia ±0,01°. Ida y vuelta (`inversa` → `directa`) < 0,01 mm en las 400 celdas | ☐ |
| UT-SW-05 | Ángulo → PWM → duty LEDC (16 bit, 50 Hz) | 0° → 500 µs → 1638 · 90° → 1500 µs → 4915 · 180° → 2500 µs → 8192. Se ajusta a los extremos reales medidos en UT-HW-03 | ☐ |
| UT-SW-06 | Límites de software (soft limits) | Ángulo fuera de [min,max] → se recorta **y** `laser_allowed=false`. Objetivo fuera del tablero → rechazado | ☐ |
| UT-SW-07 | Detección óptica diferencial | `hit` si `V1−V0 ≥ umbral`: (400, 420, 150) → no · (400, 900, 150) → sí. **Invariante al nivel ambiente**: mismo resultado sumando offsets 0…2000 mientras `V1 < 4000`. `V1 ≥ 4000` → `SATURADO` (no decide). Umbral = `max(150, 4·σ)` con 32 muestras oscuras (σ=10 → 150). Mediana de 5 muestras | ☐ |
| UT-SW-08 | Decodificación de la matriz Hall | Trama de 400 bits (activo en bajo) → cuadrícula 20×20; un patrón dorado de la flota se reproduce exacto. Antirrebote: un cambio cuenta solo tras 3 escaneos iguales | ☐ |
| UT-SW-09 | Validación de flota | **OK**: 2×(5-4-3-3-2) (34 celdas) horizontal/vertical, separados. **Error**: 33 celdas (`ERR_COUNT`) · 35 celdas (`ERR_COUNT`) · barco diagonal (`ERR_SHAPE`) · en L (`ERR_SHAPE`) · hueco `X.X` (`ERR_LENGTHS`) · largos distintos de la flota (`ERR_LENGTHS`) · dos barcos pegados por lado o diagonal (`ERR_TOUCH`) · tablero vacío (`ERR_EMPTY`) · tablero lleno (`ERR_COUNT`). Con la flota estándar de 17 celdas y N=10, igual | ☐ |
| UT-SW-10 | **Enclavamiento del láser** | Tabla exhaustiva de 2⁶ combinaciones de {estado=PLAY, fase=DISPARO, dentro de límites, torreta estabilizada, flota íntegra, tapa cerrada}: **solo la fila con todo en verdadero** da `laser_allowed=true`. El láser arranca en OFF tras reset | ☐ |
| UT-SW-11 | Lógica de disparos | Agua / tocado / hundido (con el barco correcto) · tiro repetido → `ERR_REPEAT` · fuera de rango → `ERR_RANGE` · tras 34 aciertos (17 con la flota estándar) `game_over` y ganador · disparo tras fin → rechazado · **modo demo**: termina por tope de turnos o por N barcos hundidos | ☐ |
| UT-SW-12 | Máquina de estados (FSM) | Estados: INIT, DEPLOY, CONNECT, PLAY, PAUSED, END, FAULT. INIT→DEPLOY solo con POST_OK (POST_FAIL→FAULT) · `start_enabled` solo con flota válida · PLAY→PAUSED si se levanta un barco o el cliente se pierde > T · PAUSED→PLAY al restaurar · PLAY→END con todos hundidos · END→DEPLOY con reinicio. **Propiedad**: toda combinación estado × evento tiene resultado definido; los eventos ilegales no cambian el estado | ☐ |
| UT-SW-13 | Limitador de corriente de LED | `I = Σ((r+g+b)/255·20 mA) + 1 mA·n`. 400 LED blancos al 20 % → 5,2 A **> tope de 3,0 A** → el limitador **escala** el cuadro hasta ≤ 3,0 A · 50 LED azules al 20 % → 0,25 A → pasa sin tocar. Un cuadro nunca supera el tope | ☐ |
| UT-SW-14 | IA PvE (caza y destrucción) | Con semilla fija: nunca repite casillas · tras un tocado dispara a los 4 vecinos · con 2 tocados alineados continúa en la línea · tras hundir vuelve a caza · en 1000 flotas aleatorias sin contacto termina siempre. **Umbrales (de la simulación de Lucky, `simulacion-partida.py`):** N=20 con 34 celdas → media ≈ 198, p95 ≈ 228, máx ≈ 233: se exige **media ≤ 220 y máx ≤ 260**; N=10 con 17 celdas → media ≈ 53, máx 68: se exige **media ≤ 60 y máx ≤ 80** (el azar puro daría ~390 y ~95) | ☐ |
| UT-SW-15 | Protocolo JSON (WebSocket) y **mensajes entre módulos** | `{"t":"fire","cell":"B7"}` válido · JSON roto, tipo desconocido, campo faltante o mensaje > 256 B → `{"t":"err",...}` sin tumbar el servidor. `{"t":"result","cell":"B7","r":"hit"}` se serializa como se espera. **Enlace A↔B:** `fire` / `result` / `pause` / `hello` con número de secuencia; pérdida del enlace > T → ambos módulos pausan y apagan el láser; mensaje duplicado o desordenado se ignora | ☐ |
| UT-SW-16 | Calibración en NVS | Serializa (x, y, h, versión, CRC) y recupera idéntico. CRC corrupto o ausente → valores por defecto + bandera `NEEDS_CAL` (usando NVS simulada) | ☐ |
| UT-SW-17 | **Máscara de losas activas** (retirada por niveles) | Por módulo: 4 losas ≡ 20×20; 2 ≡ 20×10; 1 ≡ 10×10 en la esquina; **0 losas con Hall** ≡ flota declarada por la web (nivel 2). Disparos a celdas inactivas → `ERR_INACTIVE`; validación de flota, IA, límites de la torreta y modo demo usan solo el área activa; el mismo código juega una partida completa en cada configuración | ☐ |
| UT-SW-18 | **Mapa celda → (losa, mux, canal)**, para **los 2 tableros** | Biyectivo: las 800 celdas ↔ 800 tuplas únicas (módulo, losa, mux, canal); ida y vuelta exacta; cada habilitación decodificada por los 74HC595 activa **exactamente un** mux. **Se escribe junto con el netlist de la PCB y se compara con él antes de enviarla a fabricar** | ☐ |
| UT-SW-19 | **Política de potencia** (*Diseño de potencia* §6) | El planificador de escaneo **nunca** deja más de 1 losa con el riel de Hall encendido; ciclo completo de las 4 losas ≤ 400 ms; el limitador de LED aplica **2,0 A** en reposo y **1,5 A** mientras una torreta se mueve; la torreta inactiva queda sin PWM (`detach`); al arranque todos los habilitadores quedan inactivos y los servos se activan los últimos; si el riel de 5 V medido cae bajo 4,6 V, el LED se reduce | ☐ |

Criterio de la Parte A: **19/19 en verde**, `pio test -e native` corre en < 5 s y sin hardware.

## Parte B — Componentes en banco

Equipo mínimo: multímetro, protoboard, regla, transportador, celular. Anota cada medida en la columna final.

| ID | Componente | Procedimiento | Aprueba si | Resultado |
|---|---|---|---|---|
| UT-HW-01 | ESP32 | Carga el parpadeo; abre SoftAP y conéctate desde el celular; lee un divisor de 1,65 V en ADC1; define el **mapa de pines** (15 GPIO, evita *strapping* y ADC2) | LED parpadea · AP visible y conecta · ADC = 1,65 V ±3 % · mapa documentado | ☐ |
| UT-HW-02 | **Adaptador de 12 V** y **fusibles / protección de entrada** | Mide en vacío y con carga resistiva al 50 % y 80 % de su capacidad; prueba la protección de polaridad con el multímetro (sin conectar los convertidores); verifica que el fusible general y el de módulo no se calientan a 5 A | 12 V ±5 % bajo carga · sin recalentar a 10 min · polaridad inversa bloqueada · conector sin calentarse | ☐ |
| UT-HW-03 | Servo MG996R (pan) | Barre 500→2500 µs con fuente propia; mide el ángulo real en 0/45/90/135/180° con transportador; repite 10 veces 90° llegando desde cada lado | Extremos reales anotados (alimenta UT-SW-05) · error ≤ ±2° · dispersión ≤ ±1° · corriente < 1 A al mover sin carga | ☐ |
| UT-HW-04 | Servo MG90S (tilt) | Igual que UT-HW-03 | Igual | ☐ |
| UT-HW-05 | Láser KY-008 + transistor | Conmuta con el 2N2222A; mide corriente; pulso de 1 ms con el celular grabando; diámetro del punto a 15 cm (**no mirar el haz**) | ~30 mA · enciende/apaga limpio · **apagado en reset y en arranque** · punto ≤ 4 mm | ☐ |
| UT-HW-06 | **Hall A3144 + imán** (decide el imán; **antes de enviar la PCB**) | Con el TO-92 **y con la muestra SOT-23**, en **los 15 sensores** (el A3144 opera entre 70 y 350 G, hasta 450 G con temperatura): imán a 0/2/3/4/5/6/8/10 mm, con Ø5×2 y Ø6×3 y ambas polaridades; después con una lámina de 2 mm (difusora) + 1 mm (base) entre imán y sensor; luego imán en la celda vecina a **10 mm** | Detecta a **3 mm** en el **100 %** de los sensores, incluidos los menos sensibles · **no** detecta al vecino a 10 mm · **suelta** al retirar el imán (no enclava) · polo activo identificado y marcado en los barcos | ☐ |
| UT-HW-07 | Fototransistor de **referencia** (THT 5 mm **y** muestra SMD) | Mide V en oscuridad / luz del salón / punto láser a 15 cm, con luces encendidas y apagadas; con el SMD, a través de una ventana de Ø3 mm en la difusora; a 650 nm | `ΔV` láser ≥ 300 mV en ambos casos · sin saturar · **se elige el SMD que cumpla antes de pedir los 24** | ☐ |
| UT-HW-08 | Multiplexor CD74HC4067 | Con 16 cables a GND/3,3 V en patrón conocido, recorre los canales 0–15 | 16/16 correctos · sin fugas entre canales · estable con S0–S3 a 3,3 V | ☐ |
| UT-HW-09 | **74HC595** + `EN` de los mux + interruptor de carga | Encadena 2 registros (16 salidas): comprueba que `OE` alto deja **todas** las salidas inactivas, el desplazamiento de un bit habilita exactamente un mux y el interruptor de carga enciende y apaga su riel con rampa | `OE` seguro en el arranque · 16/16 salidas direccionables · exactamente un mux habilitado · rampa del interruptor sin sobrecorriente | ☐ |
| UT-HW-10 | WS2812B + buffer 74AHCT125 | 1 LED, luego 10 en cadena, luego **100** (una losa); colores R, G, B | Colores correctos · sin parpadeo · dato limpio con buffer y 330 Ω · los 400 se prueban en IT-5 | ☐ |
| UT-HW-11 | Corriente de LED | Mide con multímetro: 10 LED blancos al 20 % y extrapola | ≈ 12–13 mA por LED (UT-SW-13 la usa) | ☐ |
| UT-HW-12 | DFPlayer Mini + altavoz | Reproduce pistas 1–3 por UART; volumen; pin `BUSY` | 3/3 pistas · sin ruido de masa cuando se mueve un servo | ☐ |
| UT-HW-13 | **Losa desnuda** (al llegar la PCB) | Inspección y multímetro: continuidad 5 V / 3,3 V / GND, **sin cortos** entre rieles, huellas completas, agujeros de montaje | 0 cortos · continuidad correcta · coincide con el netlist | ☐ |
| UT-HW-14 | **Losa poblada** (una a una) | Alimenta con límite de corriente: consumo en reposo; lee las 100 celdas con un imán paseado celda por celda; enciende los 100 LED; con el láser, verifica fototransistores poblados | Consumo en reposo dentro de lo previsto · **100/100 celdas** detectan el imán y solo esa · 100/100 LED responden · fototransistores poblados responden | ☐ |
| UT-HW-15 | **Consumo real del Hall** (H14; **antes de fijar fusibles y pedir la PCB**) | 10 A3144 TO-92 y las 5 muestras SOT-23 alimentados a **5 V**: corriente de cada uno con el multímetro, con y sin imán; extrapola a 100 por losa y 400 por tablero | mA por sensor medido (referencia: 4,4 mA típ / 9,0 mA máx de la hoja, medidos a 8 V) · total por losa ≤ 0,9 A · si el promedio supera 6 mA, se confirma la compuerta y el adaptador no baja de 12 V/8 A | ☐ |
| UT-HW-16 | **Tiempo de arranque del Hall** (viabilidad de la compuerta; la hoja no lo da) | ESP32 enciende el interruptor de carga, espera 5 / 10 / 20 / 50 / 100 / 200 µs y lee la salida con un imán presente y sin él; 1000 repeticiones por tiempo. Con osciloscopio o analizador lógico, si hay | Se encuentra el tiempo mínimo con **0 errores en 1000** lecturas; ese tiempo × 100 canales ≤ 10 ms por losa. **Si no hay tiempo razonable → plan B sin compuerta (12 V/10 A)** | ☐ |
| UT-HW-17 | **Convertidores DC-DC** (5 V ≥ 8 A y 6 V ≥ 6 A) | Con la carga de prueba al 25 / 50 / 75 % de su capacidad nominal: tensión, rizado y temperatura a 10 min; corte por sobrecorriente; arranque sin pico | Tensión ±5 % · **entregan al menos 75 % de lo nominal sin recalentar** (si no, se descarta la referencia) · se protegen solos en cortocircuito | ☐ |

## Compuerta

- **Antes de enviar la PCB a fabricar (lun 2-nov):** UT-HW-06 (imán), UT-HW-07 (elección del SMD), **UT-HW-15 y UT-HW-16 (consumo y arranque del Hall)**, UT-HW-17 (convertidores) y UT-SW-18 (mapa de la PCB) en ✔.
- **Antes de armar la torreta:** UT-HW-03/04 (extremos de servo), UT-HW-01 (mapa de pines).
- **Antes de poblar las losas 2–4:** UT-HW-13/14 de la losa 1 en ✔.
- La Parte A completa es requisito de IT-6 en adelante.
