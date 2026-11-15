# Fundamentos — Batalla Naval · Evaluación del plan V1

> **Estado (2026-11-08): HISTÓRICO.** Evaluación del plan V1 de 12 páginas; conservada como referencia.
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Evaluacion del plan V1.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](../00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27 (v3, actualizada con lo que aclaró Sebas). Insumos: `Batalla Naval - V1.pdf` (12 págs), la foto del enunciado, lo dicho por Almario según Sebas y las hojas de datos de los componentes.
Documentos hermanos: **Plan de trabajo** · **Diseño de potencia** · **Lista de compras** · **Pruebas unitarias** · **Pruebas de integración**.

> [!info] Lo que fijó el profesor (según Sebas, 27-oct)
> Tableros de **20×20 cm con casillas de 1×1 cm**; **dos jugadores** con ambos tableros en **un maletín de mano**; se puede **innovar** más allá de Arduino y el propio Almario mencionó el **ESP32**. Falta la **rúbrica**. Por tanto el 20×20 y el ESP32 no son una desviación: son el enunciado. Todo lo de esta evaluación se aplica **a dos tableros**.

## Veredicto

- **El concepto es bueno y cumple el enunciado**: torreta pan-tilt + láser + detección de barcos + interfaz + sonido. Se conserva.
- **El tamaño es el que pidió el profe, pero son dos tableros**: ≈ 2.700 elementos sobre PCB y ≈ 9.000 soldaduras si se hace a mano. Riesgo alto en 28 días; se maneja con módulos idénticos, **capas que se pueden soltar** (el Hall es opcional por losa) y **puntos de control** (*Plan de trabajo*).
- **Cinco errores del V1 se corrigen sí o sí**: faltan canales de sensado (H1), el barco tapa el sensor óptico (H2), la calibración de 4 esquinas no acierta a la celda (H3), **la potencia estaba mal calculada** (H14, verificada con las hojas de datos) y el fototransistor citado es de 5 mm (H15).
- Lo que está en juego: el corte 3 vale **35 %** y para cerrar Fundamentos en ≥ 4,5 necesitas **≥ 4,43** ahí (`[[fundamentos-ingenieria-mecatronica]]`).

> [!warning] Dos cosas que no pude confirmar
> 1. `Batalla Naval - Rubrica - Imagen.jpeg` **no es una rúbrica**: es la foto de la diapositiva del enunciado. No tengo los criterios de evaluación.
> 2. Asumo que Batalla Naval es el "proyecto" del **corte 3** (presentación **24 nov – 1 dic**, tabla del curso). Confírmalo con Almario.

## Plazo real

Hoy 2026-10-27 (martes de Fundamentos; la próxima clase es el **3-nov**). Quedan **28 días** hasta el 24-nov y compite con: maqueta de Intro (29-oct), sustentación PFI (9–21 nov), informes de laboratorio de Fundamentos (17-nov), Desafío 3 de Paz y Cultura (17–21 nov) y el SIEA de Mate (23-nov). El camino crítico es la **PCB**: hay que enviarla a fabricar a más tardar el **2-nov**.

## Contra el enunciado

| Enunciado | Plan V1 | Estado |
|---|---|---|
| Diapositiva: Arduino Uno + HC-05 | ESP32 + Wi-Fi + WebSocket | ✅ Almario mencionó el ESP32 y animó a innovar |
| Tablero: 20×20 cm, casillas de 1 cm (lo dijo Almario; la diapositiva muestra 10×10 de ejemplo) | 20×20 | ✅ |
| Dos jugadores; ambos tableros en un maletín | V1 describe **un** tablero y un rival remoto/IA | ⚠️ el plan hay que extenderlo a **dos módulos** (hecho en el *Plan de trabajo*) |
| 2 servos pan/tilt + láser de baja potencia | MG996R + MG90S + KY-008 | ✅ |
| App en el celular | Interfaz web en el celular | ✅ mejor: no hay que desarrollar app |
| Aviso: láser de baja potencia, nunca a los ojos, con supervisión | Soft limits | ✅ falta enclavamiento (H8) |
| Indicar acierto / fallo | LED por celda + audio | ✅ supera lo pedido |

## Hallazgos técnicos

🔴 bloqueante · 🟠 serio · 🟡 menor

| # | | Hallazgo | Corrección |
|---|---|---|---|
| H1 | 🔴 | **Faltan canales.** 400 fototransistores + 400 Hall por tablero = **800 señales**; el BOM trae 25 CD74HC4067 = 400 canales. No hay forma de habilitar los `EN`, y el ADC2 del ESP32 **no funciona con Wi-Fi activo** (solo ADC1). | **Hall:** 28 mux por tablero (7 por losa); **fototransistores:** solo 8 de referencia por tablero → 1 mux por módulo. En total **58 mux (+4)** y **8 registros 74HC595** que habilitan de a un mux. La señal óptica va a un pin ADC1; los Hall, a un pin digital por tablero. |
| H2 | 🔴 | **El barco tapa el fototransistor.** Con un barco sobre la celda, el láser pega en el barco, no en el sensor: "impacto óptico" y "hay barco" son excluyentes. | **Acierto/fallo = sensor Hall.** El fototransistor solo verifica *apuntado* y autocalibra, en el **margen** del tablero (8 por tablero), no en las celdas. |
| H3 | 🔴 | **La interpolación bilineal de 4 esquinas no acierta a la celda.** Simulación (`simulacion-apuntado.py`, tablero 200 mm, torreta a 25–100 mm del borde, h = 150 mm): error máximo de **3,7 a 6,9 celdas de 10 mm**; con 3×3 puntos baja a 1,1–2,6; con 5×5, a 0,3–0,9. | **Cinemática inversa analítica** (`pan = atan2(dy,dx)`, `tilt = atan2(h, r)`) calibrando 3 parámetros (x, y, h) con las 4 esquinas; la bilineal solo para residuos. |
| H4 | 🟠 | **El punto láser puede desbordar la celda de 10 mm.** Con h = 60 mm el punto se alarga ×4 (3 mm → 12 mm); con h = 150 mm, ×1,8; con h = 180 mm, ×1,6. | **Mástil de 150–180 mm** sobre el margen trasero: incidencia ≥ 33°, punto ≈ 5 mm. Exigir punto ≤ 3 mm (colimar/enfocar el KY-008). |
| H5 | 🟠 | **Mano de obra e infraestructura.** Por tablero: 400 celdas × (LED 4 + Hall 3) + 100 pasivos de desacople ≈ **4.500 soldaduras**; dos tableros ≈ **9.000**. A 10 mm de paso no se cablea a mano: exige **PCB a medida**. | PCB en **8 losas de 100×100 mm** idénticas (tarifas económicas de fábrica suelen ser ≤ 100×100 mm; verificar). **Ensamble SMD por servicio muy recomendado.** |
| H6 | 🟠 | **Potencia de servos y LED.** Pico de arranque/bloqueo del MG996R: **2,5 A a 6 V [hoja]** (el V1 usa 1,5 A). LED de un tablero a blanco pleno al 20 %: ≈ 5,2 A. | Rieles separados y **tope de LED en firmware**: ver *Diseño de potencia*. |
| H7 | 🟠 | **Niveles lógicos.** A3144: 4,5–24 V (salida colector abierto). CD74HC4067 a 5 V exige VIH = **3,15 V [hoja TI]**: sin margen para los 3,3 V del ESP32. WS2812B exige VIH = **0,7·VDD = 3,5 V [hoja]**. | Mux a 3,3 V; Hall a 5 V con pull-up a 3,3 V; **74AHCT125** + 330 Ω en el dato LED. |
| H8 | 🟠 | **Seguridad láser.** KY-008 ≤ 5 mW ≈ clase 3R. Un GPIO flotante en el arranque del ESP32 puede encender el láser. | Transistor + pull-down 10 kΩ (el KY-008 consume ~30 mA, más de lo cómodo por GPIO; hoja ESP32: 40 mA por pin y baja con varios); enclavamiento en firmware (UT-SW-10); no usar pines de *strapping*. |
| H9 | 🟡 | **"Precisión > 0,05° por paso" no es real.** Banda muerta del MG996R = **5 µs [hoja]** ≈ 0,5°, más holgura de engranes. | Lo necesario es ≈ ±0,5°; con celdas de 10 mm a ~25 cm una celda subtiende ~2,3°. Margen estrecho pero alcanzable. Quitar la cifra del informe. |
| H10 | 🟡 | **Reglas sin definir.** No hay flota; con solo Hall, dos barcos pegados son indistinguibles de uno largo; 100 imanes sin flota. | **2 × (5-4-3-3-2)** por jugador (34 celdas), **sin tocarse ni en diagonal**; imanes de la misma polaridad; 80 de producción. |
| H11 | 🟡 | **El documento tiene residuos.** LaTeX sin renderizar, fórmula bilineal con paréntesis perdidos (`1-xy Q01` debe ser `(1−x)·y·Q01`), esquinas ilegibles (`$A10,0$`), placeholders ("Person", "Date"), "Aprobada" sin aprobador, referencia `PT3346B` inexistente (H15). | Limpiar antes de entregarlo al profe. |
| H12 | 🟡 | **BOM incompleto**: buffer de nivel, registros de habilitación, interruptores de carga, protecciones, convertidores, transistor del láser, resistencias, condensadores, microSD, cableado, barcos, maletín, PCB. | Cubierto en la *Lista de compras* (v3). |
| H13 | 🟡 | **Sensibilidad del Hall al imán.** Hoja Allegro: el A3144 opera entre **70 y 350 G a 25 °C, hasta 450 G en temperatura**, y suelta entre 50 y 330 G. Estimación (cilindro axial, N35): un imán **Ø5×2 da ≈ 450 G a 4 mm y ≈ 760 G a 3 mm**; Ø6×3, ≈ 470 G a 5 mm. Un vecino en la misma altura a 10 mm ve ≈ −18 G (polo contrario: el A3144 solo responde a un polo). | Diseñar para **≥ 450 G a la distancia real (≈ 3 mm)**. Validar en **UT-HW-06**, incluido que **suelte** al retirar el imán y que **no** active al vecino. |
| H14 | 🔴 | **Potencia mal calculada** (verificada con hojas de datos). El V1 supone ≈ 100 mA para "25 mux + 400 sensores"; el A3144 consume **4,4 mA típ / 9,0 mA máx cada uno [hoja Allegro]** → 400 = **1,76 A (3,6 A máx)**. Un tablero queda en **5,6 A típico (7,5 A)**, no en 3,87 A: no cabe en la fuente de 5 A del V1. Con dos tableros, el error se duplica. | **Hall alimentados por losa, de a una** (interruptor de carga): pico 0,9 A y promedio ~11 mA por módulo. Adaptador externo de **12 V/8 A** y dos convertidores por módulo. Ver *Diseño de potencia* (con el plan B si la compuerta no funciona). |
| H15 | 🟠 | **Fototransistor y densidad de celda.** El PT334-6B es de **5 mm** (T-1¾), pico a 940 nm [hoja Everlight]; no cabe cómodo en una celda de 10×10 mm junto al Hall y el LED, y a 650 nm responde menos. | Solo **8 de referencia por tablero**, en el margen, **SMD**; en las celdas van únicamente **LED + Hall SOT-23** (huella del Hall con opción de no poblar). Medir la respuesta a 650 nm en UT-HW-07. |
| H16 | 🟡 | **Duración de la partida.** Simulación (`simulacion-partida.py`): en 20×20 con 34 celdas la IA necesita **≈ 198 disparos** (p95 228); a 3–4 s por disparo (supuesto) ≈ 10–13 min por lado. | **Modo demo** (flota reducida o tope de turnos) para la presentación (D6). |
| H17 | 🟠 | **El V1 describe un tablero**, no dos. Un solo ESP32 para dos tableros pide ≈ 24 GPIO, cables largos entre mitades y un único punto de falla. | **Dos módulos idénticos** (tablero + torreta + ESP32 + potencia) y un enlace de datos (UART o ESP-NOW); uno maestro (servidor web, lógica, audio). Ver *Plan de trabajo*. |
| H18 | 🟡 | **Fuga de los mux.** CD74HC4067: canal apagado fuga **±0,8 µA a 25 °C y ±8 µA a 85 °C [hoja TI]**. Con 28 mux en una línea SIG y pull-up de 10 kΩ, la tensión se corre 0,22 V (más con calor). | Pull-up de **2,2 kΩ** y una línea SIG **por tablero**. |

## Correcciones al V1

| Aspecto | V1 original | V1 corregido |
|---|---|---|
| Alcance | 1 tablero | **2 módulos** idénticos en un maletín (H17) |
| Acierto / fallo | fototransistor | **Hall** (H2) |
| Fototransistores | 400 en las celdas | **8 SMD de referencia por tablero**, en el margen (H2, H15) |
| Mux | 25 | **58 + 4** y **8 × 74HC595** (H1) |
| Apuntado | bilineal de 4 esquinas | **cinemática inversa** + 3 parámetros (H3) |
| Torreta | margen de 5 cm | **mástil 150–180 mm** (H4) |
| Hall | A3144, siempre alimentado | A3144 **SOT-23 alimentado por losa, de a una** (H14) |
| Potencia | 5 V/5 A | **12 V/8 A** externo + convertidores 5 V y 6 V por módulo (H6, H14) |
| Niveles lógicos | directos | mux a 3,3 V; **74AHCT125** para el LED (H7) |
| Láser | GPIO | **transistor + pull-down + enclavamiento** (H8) |
| Flota / imanes | sin definir / 100 | **2×(5-4-3-3-2) por jugador / 80** (H10) |
| Infraestructura | no mencionada | **8 losas de PCB 100×100 mm** + ensamble por servicio (H5) |
| Cerebro / software | ESP32, SoftAP, WebSocket, FSM, PvE | **igual** + enlace entre módulos y máscara de losas |

## Decisiones

| # | Decisión | Estado / recomendación |
|---|---|---|
| D1 | Alcance 20×20 con celda de 1 cm | ✅ **lo fijó el profesor** |
| D2 | ESP32 en lugar de Arduino | ✅ **lo mencionó Almario** |
| D3 | Dos jugadores | ✅ **un maletín con ambos tableros** |
| D4 | Ensamble SMD: a mano o por servicio (PCBA) | **Servicio** (≈ 9.000 soldaduras a mano); a mano solo la losa 1 si no hay presupuesto |
| D5 | Presupuesto máximo y quién compra | sin dato |
| D6 | **Modo demo**: flota reducida / tope de turnos | Tope de turnos y flota de 3 barcos para la presentación; a decidir con el profe |
| D7 | **Una torreta por tablero** (como la diapositiva) **o una compartida** | **Una por tablero**: módulos idénticos y sin pedir más de 180° de giro; una compartida ahorra 1 MG996R + 1 MG90S + 1 láser pero complica la mecánica |
| D8 | **Ocultar la flota** de cada jugador en un maletín abierto | Biombo central o la tapa; a decidir con el diseño del maletín |

**Borrador para Almario** (lo envías tú, es hacia afuera):
> Profesor, sobre el proyecto de Batalla Naval: (1) ¿nos puede compartir la rúbrica y la fecha exacta de presentación? (2) ¿cada tablero lleva su propia torreta/cañón, como en la diapositiva, o puede haber una compartida? (3) ¿cómo espera que se mantenga en secreto la flota de cada jugador si ambos tableros van en el mismo maletín? (4) Para la detección de barcos pensamos usar sensores de efecto Hall e imanes en la base de cada barco: ¿le parece bien? Gracias.

## Lo que está bien en el V1

Arquitectura por capas clara (procesamiento, actuación, sensado, retroalimentación); FSM de 4 fases con validación de flota antes de habilitar "Iniciar Partida"; Core 0 para red y Core 1 para tiempo real; calibración guardada en NVS; muestreo diferencial láser/ambiente; límites de software para el láser; potencia con cálculo explícito (el método es bueno; los datos no). La base es sólida: el trabajo es acotarla y construirla por partes.
