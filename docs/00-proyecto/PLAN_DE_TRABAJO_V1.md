# Fundamentos — Batalla Naval · Plan de trabajo (2 tableros 20×20)

> **Estado (2026-11-08): HISTÓRICO.** Describe la versión grande (2 tableros 20×20, 12 V, PCB). Hoy manda [ESTADO](../ESTADO.md).
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Plan de trabajo.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27 (v3). Documentos hermanos: *Evaluación* · *Diseño de potencia* · *Lista de compras* · *Pruebas unitarias* · *Pruebas de integración*.

## Lo que fijó el profesor (según Sebas)

- Tablero de **20×20 cm con casillas de 1×1 cm** (400 celdas por tablero).
- **Dos jugadores**: un maletín de mano con **ambos tableros**.
- **Se puede innovar** más allá de Arduino; el propio Almario mencionó el **ESP32**.
- **Pendiente:** la rúbrica, que el profe aún debe enviar. Cuando llegue, cada prueba de integración se mapea a un criterio.

## Estrategia

1. **Dos módulos idénticos** (tablero + torreta + ESP32 + potencia propia) unidos por 12 V y un enlace de datos; uno es maestro (servidor web, lógica, audio). Cada módulo es una mitad del maletín.
2. **Tres capas**, de la más segura a la más ambiciosa. Cada una se puede soltar sin rehacer la PCB:
   - **Núcleo:** LED por celda, torreta + láser, interfaz web y lógica del juego (con la flota **declarada por la web**).
   - **Autodetección (Hall):** el tablero reconoce solo dónde pusiste los barcos. Es la innovación del V1. La huella del Hall va en todas las celdas pero **se puede no poblar**.
   - **Óptica de referencia:** 8 fototransistores por tablero, en el margen, para autocalibrar y verificar el apuntado.
3. **Construir por losas** (10×10 celdas de 100×100 mm; 8 en total). Se valida la **losa 1** completa antes de poblar las demás.
4. **Firmware parametrizado**: `N`, `d`, flota y **máscara de losas activas**; sirve igual con 1, 2, 4 u 8 losas.
5. **Camino crítico: PCB + potencia medida.** Todo lo demás se hace en paralelo mientras la placa se fabrica.

## Calendario con puntos de control

| Fecha | Qué | Control |
|---|---|---|
| **mar 27 – mié 28 oct** | Mensaje a Almario (rúbrica, fecha, torreta compartida o una por tablero). Cotizar **disponibilidad** de LED y Hall. Decidir D4 (ensamble) y presupuesto. **Pedido de la ola 1**, incluida la potencia | |
| mié 28 – sáb 31 oct | **Diseño de la PCB de la losa** (esquemático, layout, DRC). Lucky: mapa celda → (losa, mux, canal), mapa de pines, lista de verificación. Intro: maqueta jue 29 compite | |
| vie 30 oct – dom 1 nov | **Llega la ola 1 → medir:** UT-HW-15 (consumo del Hall), UT-HW-16 (arranque del Hall), UT-HW-06 (imán), UT-HW-07 (fototransistor SMD), UT-HW-17 (convertidores). Con eso se cierra el diseño de la losa | |
| **lun 2 nov** | Revisión de la PCB y **envío a fabricar** + pedido de la ola 2 | 🚦 **A — lun 2 nov, 18:00:** ¿Gerbers enviados y potencia medida? **Si no → nivel 5** |
| mar 3 nov | Pregunta a Almario en clase (si no contestó) | |
| 3 – 9 nov | UT-HW en protoboard; CAD y 3D de mástiles, chasis y maletín; Lucky escribe la lógica y las UT-SW | |
| ~10 – 14 nov | **Llegada de las PCB** (estimado; verificar plazo). Pobla y prueba la losa 1 | 🚦 **B — vie 13 nov:** ¿PCB en mano y losa 1 funcionando (UT-HW-14)? **Si no → nivel 4 o 5** |
| 10 – 16 nov | Un módulo completo (torreta calibrada, IT-2, IT-3a); pobla las losas del otro | |
| 17 – 21 nov | Los dos módulos y el enlace entre ellos; IT-4 a IT-8. **17-nov informes de laboratorio** y Desafío 3 (17–21) compiten | 🚦 **C — vie 20 nov:** ¿módulo A completo y ≥ 2 losas del B? **Si no → nivel 3** |
| sáb 22 nov | **Congelar firmware** | |
| dom 23 nov | SIEA de Mate: sin trabajo en el proyecto | |
| 24 nov – 1 dic | Ensayo (IT-10) y presentación | |

> La holgura es de ~1 semana y solo existe si la PCB llega a más tardar el 14-nov. Con ~9.000 soldaduras en el plan, el **ensamble por servicio (D4)** es lo que más protege el calendario.

## Niveles de retirada

Cada nivel es una versión **presentable**; se baja solo si un control lo exige y se avisa a Almario con tiempo.

| Nivel | Qué se entrega | Se activa si |
|---|---|---|
| **0** | 2 tableros 20×20, **Hall + LED + torreta** en ambos | todo en tiempo |
| **1** | Hall solo en un tablero; el otro registra su flota por la web | retraso en el ensamble del segundo tablero |
| **2** | 2 tableros 20×20 con LED + torretas, **sin Hall** (flota declarada por la web) | el Hall falla (consumo, imán, arranque) o no hay piezas |
| **3** | **1 tablero físico 20×20** (4 losas) con su torreta + el otro tablero solo en la interfaz web | control C sin el módulo B |
| **4** | **1 losa de 10×10** (el enunciado de la diapositiva) | control B sin suficiente hardware |
| **5** | 10×10 en perfboard (el *seguro* de la lista), sin PCB | control A o B sin PCB |

## Reglas de juego (propuestas)

- **Flota por jugador:** 2 × (5-4-3-3-2) = 10 barcos, 34 celdas; rectos, horizontal o vertical, **sin tocarse ni en diagonal**; imanes con la misma polaridad.
- **Turno** (como en la diapositiva): el jugador A elige celda en su celular → la **torreta del módulo B** apunta y dispara sobre el tablero de B → el **Hall de B** decide agua / tocado / hundido → LED y sonido → cambio de turno.
- **Secreto de la flota:** el maletín abierto deja ver los dos tableros. Hace falta un **biombo central o la tapa** que oculte cada flota al rival (decisión D8).
- **Partida completa:** ≈ 198 disparos por jugador (simulación, p95 ≈ 228) ≈ 10–13 min de torreta por lado. **Modo demo** para la presentación: flota de 3 barcos y/o tope de turnos (D6).
- **Pausa:** levantar un barco o perder al cliente pausa la partida y apaga el láser.

## Requisitos de diseño de la losa (PCB)

- 100×100 mm, 100 celdas a **10 mm**, índice de celda serigrafiado. Un solo tipo de losa; 10 unidades.
- **Cara superior:** LED WS2812B + Hall SOT-23 (huella con opción de no poblar). Distancia del imán al Hall ≈ **3 mm** (difusora 2 mm + base del barco 1 mm). **No hay fototransistores en las celdas.**
- **Riel de LED** (5 V): PTC de 2 A, 1000 µF, **100 nF por LED**; pistas de entrada ≥ 2 mm, bus ≥ 1 mm. **Riel de Hall** separado, detrás de un **interruptor de carga** con **puente de 0 Ω** que lo anula (así la losa sirve con o sin compuerta, según lo que midan UT-HW-15/16).
- 7 mux de Hall con S0–S3 comunes; un `EN` por mux; una línea SIG de **pull-up 2,2 kΩ**; mux alimentados a **3,3 V**.
- Mapa celda → (losa, mux, canal) **escrito junto al netlist** y comparado con él (UT-SW-18).
- Dato LED entra por un conector y sale por otro; los mux se encadenan por conectores.
- Puntos de prueba: 5 V, 3,3 V, GND, SIG, dato LED. Agujeros de montaje coherentes con la rejilla, la difusora y el chasis.
- 2 capas si el ruteo cierra con holgura; si no, 4. Se decide **antes** de enviar.
- **Placa de referencias** de cada tablero (perfboard o PCB pequeña): 8 fototransistores SMD en el marco.

## Reparto sugerido (a conversar con tu compañero)

| Quién | Qué |
|---|---|
| Hardware (uno de ustedes) | PCB, ensamble, torretas, chasis, maletín, potencia |
| Firmware y web (el otro) | FSM, protocolo WebSocket, interfaz, IA, calibración, enlace entre módulos |
| Lucky | mapa celda → mux, mapa de pines, lógica y pruebas unitarias, lista de verificación de la PCB, registro de mediciones |

## Riesgos principales

| Riesgo | Mitigación |
|---|---|
| PCB tarda o se atasca en aduana | control A estricto; nivel 5 con el *seguro*; courier con rastreo |
| ≈ 9.000 soldaduras | ensamble por servicio (D4); losas en secuencia; nivel 2 (sin Hall) |
| Potencia: el Hall consume más o arranca lento | UT-HW-15/16 **antes** de enviar; puente de 0 Ω; adaptador de 10 A como plan B |
| Punto láser mayor que la celda de 10 mm | mástil de 150–180 mm, colimar el láser, IT-2 con criterio estricto |
| Dos módulos y un enlace entre ellos | probar el enlace temprano (IT-12); nivel 3 como respaldo |
| Carga académica de noviembre | congelar firmware el 22-nov; sin trabajo el 23-nov |

## Pendiente de Sebas

1. Enviar el mensaje a Almario (rúbrica, fecha, torreta compartida o una por tablero, ocultar la flota).
2. Cotizar disponibilidad de LED y Hall SMD en Colombia; si no hay, decidir importación ya.
3. Cerrar D4 (ensamble) y presupuesto; hacer el pedido de la ola 1 (incluye la potencia).
4. Acordar con tu compañero quién diseña la PCB y en qué herramienta.
