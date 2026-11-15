# Batalla Naval — Empieza aquí (versión mínima)

> **Estado (2026-11-08): HISTÓRICO.** Versión mínima del 3-nov. Varias decisiones cambiaron después (enlace entre módulos, sensores, web): ver la tabla de conflictos en [ESTADO](../ESTADO.md).
> Origen: vault `borradores/fundamentos/batalla-naval/LEEME - empieza aqui.md` (movido al repositorio el 2026-11-08).

Lucky, 2026-11-03. Una página. Todo lo demás de esta carpeta es **referencia**; si algo choca con esto, manda esto.

## Qué entregar (rúbrica, entrega y demostración **mar 24-nov**)

Test de 5 posiciones **2,0** · prueba con contrincante **1,0** · sustentación individual **1,0** · estética **0,5** · video con los dos **0,5**. Piden: tablero 30×30 con matriz 20×20 elevada 5 cm, láser que aparece en la coordenada `(x,y)`, sonido en cada disparo, y envío desde el celular **por Bluetooth con una app propia**.

## La versión mínima: 2 módulos idénticos e independientes

Cada módulo = **tablero + estación + ESP32**. Es el **mismo programa cargado en los dos ESP32**; no hay cable de datos entre módulos. Es lo que dibuja el profe: cada cañón con su propio controlador y su Bluetooth.

**Por módulo:**

| Pieza | Para qué |
|---|---|
| ESP32 DevKit | cerebro y Bluetooth |
| Servo MG996R (pan) + MG90S (tilt) | mover el láser |
| Láser KY-008 ≤ 5 mW + transistor 2N2222A | marcar la celda |
| Zumbador activo | el sonido de cada disparo |
| Adaptador de 6 V/4 A + convertidor a 5 V (o cargador USB para el ESP32) | alimentación |
| Tablero 30×30 con matriz 20×20 + mástil | estructura (ver *Planos y medidas*) |

## ¿Se queda corto un ESP32 para procesar todo?

**No.** El trabajo es mínimo: dos señales PWM por hardware, leer una línea de texto, un cálculo de ángulos (microsegundos) y un tono. Un ESP32 sobra, incluso para dos punteros (necesita ~7 pines).

**El límite no es de procesamiento sino de Bluetooth clásico:** la librería de Arduino (`BluetoothSerial`) **acepta un solo teléfono a la vez** (verificado; varios clientes exigen programar a bajo nivel con ESP-IDF). Con dos jugadores, un solo ESP32 necesitaría BLE o Wi-Fi, que complican la app. **Dos ESP32 es lo más simple**: la misma placa y el mismo programa dos veces.

## ¿Qué se necesita para controlarlo?

**Solo una app Android con Bluetooth.** Nada de página web.

- **Pantalla:** elegir el módulo (lista de dispositivos emparejados), elegir `x` e `y` (1–20), botón **DISPARAR** y botón **TEST**.
- **Mensajes (texto):** el celular envía `(12,7)` y el ESP32 responde `OK`; `TEST` corre las 5 posiciones.
- **Flujo del ESP32:** valida 1–20 → calcula pan y tilt → se mueve → láser 1–2 s con zumbido → apaga → responde.
- **Quién se conecta a quién:** el **rival** se conecta al módulo que va a recibir el disparo; **tú** te conectas al tuyo para el test.
- **Cómo hacerla:** MIT App Inventor es lo más rápido (≈ 15 bloques); para "software original" diseña tu propia pantalla y tu propio protocolo.
- **Si el celular es iPhone:** el Bluetooth clásico no funciona; hay que decidir entre BLE con app nativa o pedirle a Almario la web por Wi-Fi. **Dime qué celular tienes.**

## Tu panorama (3-nov): qué es viable

| Idea | Veredicto | Qué hacer |
|---|---|---|
| **2 ESP32, uno por jugador** | ✅ | es el diseño |
| **PCA9685 para los servos** | ⚠️ posible, **no hace falta** | el ESP32 ya mueve los 2 servos de cada módulo por hardware y con **mejor resolución** (≈ 0,3 µs por paso contra 4,9 µs ≈ 0,44° del PCA9685, que además tiene un oscilador con ±5 % de error). Solo vale la pena si hay más de 4–5 servos por módulo; su pin `OE` sí sirve para dejar los servos sin energía al arrancar |
| **Una fotorresistencia por celda para saber si acertó (sin LED por celda)** | ⚠️ **posible, pero pesado y sin puntos** | funciona *al revés*: el barco **tapa** la celda, así que **luz = AGUA, sin luz = TOCADO**. Exige lectura diferencial (láser apagado y encendido), una **ventana difusora de 10×10 por celda** (el punto es de ≈ 5 mm y el sensor, de 3–4 mm) y paredes entre celdas. Cuesta **800 fotorresistencias + 50 multiplexores + ≈ 1.600 soldaduras y 800 cables** para los dos tableros. La rúbrica **no califica** acierto automático. Alternativas más baratas abajo |
| **App de celular que manda las órdenes** | ✅ | es lo que pide la rúbrica |
| **Subred (Wi-Fi) de cada ESP32 para test o mantenimiento** | ✅ con cuidado | el ESP32 puede tener Wi-Fi y Bluetooth a la vez, pero ocupa memoria y comparte la radio. Hazlo como **modo mantenimiento** (un interruptor al arrancar): Wi-Fi solo para calibrar; **en juego, solo Bluetooth**. El **TEST de la rúbrica** debe poder correrse desde la **app y desde un botón físico**, no depender de la subred |

**Cómo saber si acertó (de menos a más trabajo):**

1. **Software:** el dueño registra su flota en la app antes de jugar y el módulo la guarda; al recibir `(x,y)` compara y responde `TOCADO` o `AGUA`, y **enciende un LED del módulo**. Cero hardware.
2. **Manual:** el dueño pulsa TOCADO o AGUA en su app (como en el juego real) y se enciende el LED.
3. **Un solo sensor en la estación** (experimento de un día): un fototransistor con tubo y filtro rojo, junto al láser, mide la luz que rebota en el punto. Con **fichas blancas y tablero negro mate**, la ficha refleja del orden de 10 veces más (estimación: hay que medirlo). Un sensor por módulo en vez de 400.
4. **Tu matriz de fotorresistencias** (fila de arriba): la versión grande; solo con tiempo de sobra.

**Regla:** los extras se hacen **solo después** del control del 15-nov (test 5/5 tres veces seguidas).

## Qué se descarta

Sensores Hall, LED por celda, fototransistores, PCB, alimentación de 12 V, enlace entre módulos, página web (queda como extra para calibrar). El maletín y el biombo son opcionales (la estética vale 0,5).

## Lo difícil de verdad (ahí están los puntos)

1. **Precisión:** que el rayo caiga en la celda de 1 cm, 5 de 5, delante del profe. Mástil alto, calibración medida, acercarse siempre desde el mismo lado, punto de 3 mm.
2. **Rutina de TEST** con las 5 posiciones: (1,1), (20,1), (20,20), (1,20), (11,11).
3. **App y código propios** (cada copia descuenta 0,5), y **entenderlo todo** para la sustentación individual.

## Tres semanas

| Fechas | Qué |
|---|---|
| 3 – 8 nov | Comprar (local). ESP32 + servos + láser sobre una cuadrícula impresa. App con el enlace Bluetooth y `(x,y)`. Cortar según los planos |
| 9 – 15 nov | Tablero y mástil armados, calibración, TEST 5/5 tres veces seguidas |
| 16 – 21 nov | Segundo módulo idéntico, prueba con contrincante, sonido, estética, **video con los dos** |
| 22 nov | Congelar firmware y app |
| **24 nov** | **Entrega** |

## Pendiente de Sebas

1. **Android o iPhone** (decide la app).
2. **Mensaje a Almario:** desde dónde se miden los 5 cm, que cada estación apunta a su propio tablero, y si vale la web además del Bluetooth.
3. **Dibujo:** ¿el panel alto es el biombo?
4. **Medir las piezas reales** antes de cortar.

## Mapa de esta carpeta

- **Planos y medidas** — la hoja de cotas para dibujar y modelar.
- **Cumplimiento de la rúbrica y huecos** — la rúbrica requisito por requisito.
- Evaluación del plan V1, Plan de trabajo, Lista de compras v3 y Diseño de potencia — **referencia**: parte de ellos describe la versión grande (Hall, PCB, 12 V) que ya no se hace.
- `modelo-potencia.py`, `geometria-planos.py`, `simulacion-apuntado.py`, `simulacion-partida.py` — cálculos.
