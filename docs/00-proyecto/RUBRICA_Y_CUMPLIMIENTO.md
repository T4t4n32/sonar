# Fundamentos — Batalla Naval · Cumplimiento de la rúbrica y huecos

> **Estado (2026-11-08): PARCIAL.** La lectura de la rúbrica sigue vigente; las decisiones técnicas posteriores están en [ESTADO](../ESTADO.md).
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Cumplimiento de la rubrica y huecos.md` (movido al repositorio el 2026-11-08).

Lucky, 2026-11-03. Fuente: `TRABAJO CORTE FINAL.pdf` (2 págs., en la carpeta del proyecto; su gráfico es la misma diapositiva que ya habíamos visto). **Esta página manda sobre las anteriores** en todo lo que las contradiga.

> [!info] Actualización (3-nov, noche) — lo que aclaró Sebas
> - **Lectura rigurosa de lo dicho por Almario:** se trabaja con **Arduino + módulo Bluetooth**; se permite el **ESP32 porque trae Bluetooth y Wi-Fi integrados**. La **línea base es Bluetooth + app propia**, como dice la rúbrica escrita. La página web por Wi-Fi queda como **extra opcional** (calibración o depuración), no como reemplazo, salvo que Almario lo confirme por escrito.
> - **Cada tablero tiene su propio puntero**: dos estaciones, **un ESP32 por módulo**. Con Bluetooth clásico (equivalente a un HC-05) cada ESP32 acepta **un teléfono a la vez**: el **rival se conecta al módulo que recibe el disparo**; el jugador se conecta a su propio módulo para el test de 5 posiciones. Dos jugadores como máximo.
> - **Lectura de la figura (P1):** cada estación apunta a **su propio tablero** con la coordenada que manda el rival (coincide con "recibe y apunta" de la diapositiva y con el dibujo de Sebas). La distancia estación–celda queda en 19–33 cm y la precisión es alcanzable.
> - **Tablero acostado** con **mástil alto**; **numeración 1 a 20**; los "5 cm" no se saben: el diseño cumple 50 mm desde la base y 53 desde la mesa. Medidas en [Planos y medidas](../01-diseno/PLANOS_Y_MEDIDAS.md).
> - **Hueco nuevo:** el Bluetooth clásico no funciona con iPhone. **Hace falta saber si los celulares son Android.**

## Lo que pide la rúbrica

- Entregable: **una estación base de ataque y un tablero de posicionamiento de flota**.
- Tablero de **30×30 cm** con la **matriz de ubicación de 20×20 cm** adentro, **elevado 5 cm** sobre la base donde se instala.
- La base de ataque dispara un **rayo láser** a la posición que se indique; el resultado se evidencia con **la aparición del rayo en la coordenada** del tablero del contrincante.
- Coordenadas **siempre en formato (x,y)**.
- **Un sonido con cada disparo.**
- Los datos viajan **del celular por Bluetooth** con una **app desarrollada para ese efecto**.
- **Rutina de prueba** de cada jugador en su propio sistema tablero-estación: **test de 5 posiciones de ataque**.
- **Entrega y demostración: martes 24 de noviembre** (21 días desde hoy).
- **Software original**: por cada copia encontrada, **−0,5** a cada estudiante.

| Criterio | Puntos |
|---|---|
| Estética del dispositivo | 0,5 |
| **Funcionamiento del test** (5 posiciones) | **2,0** |
| **Prueba con contrincante** | **1,0** |
| Video de la demostración (participan **los dos** desarrolladores) | 0,5 |
| Sustentación **individual** | 1,0 |
| **Total** | **5,0** |

## Veredicto

- **La rúbrica no califica detección de barcos, LED por celda, fototransistores ni PCB.** El plan V1/v3 (Hall, 8 losas, 12 V/8 A, dos módulos en un maletín con enlace) cuesta semanas y **no suma ningún punto directo**. El 60 % de la nota (test 2,0 + contrincante 1,0) depende de **apuntar bien, repetible, delante del profe**.
- **Tres cosas del plan contradicen la rúbrica** y hay que corregirlas: usamos **Wi-Fi + web** en vez de **Bluetooth + app**, no existía la **rutina de 5 posiciones**, y no se contempló el **tablero de 30×30 elevado 5 cm**. Además el formato de coordenadas era `B7`, no `(x,y)`.
- **El hueco técnico más grande no está en el plan: es la precisión de apuntado a 1 cm** (sección 4). De ahí salen los 2,0 puntos del test.
- **Recomiendo recentrar en un V2 = núcleo de la rúbrica** (sección 5) y dejar la autodetección Hall como extra solo si sobra tiempo. Se conservan: cinemática inversa, mástil, láser seguro, calibración y casi todas las pruebas de la parte A.
- Con la fecha fija del **24-nov** y ningún pedido hecho, el control de PCB del 2-nov venció. El V2 se compra en tienda local y se arma en tres semanas.

## 1. Requisito por requisito

| # | Requisito (rúbrica) | Plan anterior | Estado | Qué hay que hacer |
|---|---|---|---|---|
| R1 | Estación de ataque con láser | torreta pan-tilt + láser | ✅ | precisión: sección 4 |
| R2 | Tablero **30×30** con matriz **20×20** | solo matriz 20×20 con electrónica | ⚠️ | diseñar el tablero de 30×30, matriz centrada con 5 cm de margen |
| R3 | **Elevado 5 cm** sobre la base | no contemplado | ❌ | patas o soporte de 5 cm; cambia la geometría del láser (sección 4) |
| R4 | Rayo láser aparece en la coordenada | sí (cinemática inversa) | ✅ | tolerancia y distancia: sección 4 |
| R5 | Formato **(x,y)** siempre | `B7` | ❌ | protocolo `(x,y)`; definir origen, orientación y rango |
| R6 | **Sonido** con cada disparo | DFPlayer en un solo módulo | ⚠️ | el sonido sale del sistema que dispara; basta un zumbador activo |
| R7 | **Bluetooth + app** desarrollada | Wi-Fi SoftAP + web | ❌ | ESP32 con Bluetooth (Classic SPP o BLE) + app propia; elegir Android/iOS |
| R8 | **Rutina de test de 5 posiciones**, por jugador, en su propio sistema | no existe | ❌ | modo TEST en firmware y botón en la app |
| R9 | **Prueba con contrincante** | rival por web/IA | ⚠️ | dos sistemas por Bluetooth; definir contra quién (ver P3) |
| R10 | **Video** con los dos desarrolladores | no planeado | ⚠️ | guion y grabación antes del 22-nov |
| R11 | **Sustentación individual** | — | ⚠️ | cada uno debe poder explicar todo: preferir lo simple y documentarlo corto |
| R12 | **Software original** | — | ⚠️ | app y firmware propios, protocolo propio, historial de commits como evidencia |
| R13 | Estética | maletín (no lo pide la rúbrica) | ⚠️ | acabado del tablero y la estación, cableado ordenado; el maletín es opcional |
| R14 | Entrega el **martes 24-nov** | ventana "24-nov–1-dic" | ⚠️ | la fecha es **una sola**; los controles se rehacen (sección 6) |

## 2. Huecos que contradicen la rúbrica (hay que corregir) 🔴

1. **Bluetooth + app en vez de Wi-Fi + web.** El ESP32 trae Bluetooth, así que el hardware sirve; cambia el firmware y aparece **un trabajo nuevo: la app**. Decisión: Android nativo (App Inventor, Kotlin o Flutter) vs. página con Web Bluetooth (solo BLE y solo Chrome en Android). La rúbrica dice "aplicación desarrollada": **preguntar si una web con Web Bluetooth cuenta** antes de apostar a ella.
2. **Tablero de 30×30, matriz de 20×20, elevado 5 cm.** El plan no tenía tablero ni elevación. La altura de 5 cm **determina si el láser puede alcanzar la celda con un punto de 1 cm** (sección 4).
3. **Rutina de test de 5 posiciones.** Falta diseñarla: qué 5 posiciones, quién las elige, cómo se dispara (botón de la app o automático), y que el rayo quede visible el tiempo suficiente.
4. **Formato `(x,y)`.** Hay que definir el origen (esquina y eje), el rango (0–19 o 1–20) y la unidad (celdas o cm).
5. **Fecha única, 24-nov.** Ya no hay "ventana" ni margen hasta el 1-dic.

## 3. Ambigüedades de la rúbrica (hay que preguntarle a Almario) 🟠

| # | Pregunta | Por qué importa |
|---|---|---|
| P1 | **¿Quién dispara sobre qué tablero?** El texto dice que el rayo aparece "en el tablero del contrincante", pero la figura muestra cada cañón junto a su propio tablero y el rayo cruzando al otro. | decide la distancia estación–tablero, la orientación del tablero y cuánto debe alcanzar el láser |
| P2 | **¿Cuántos sistemas entrega el grupo, 1 o 2?** ("una estación y un tablero" vs. "cada jugador en su propio sistema") | duplica o no el hardware |
| P3 | **¿Contra quién es la prueba con contrincante?** ¿otro grupo o el otro integrante? ¿cuántos disparos? | define si hace falta interoperar con otros |
| P4 | **¿Qué error cuenta como acierto?** ¿la celda de 1 cm o algo más permisivo? | es la especificación del test de 2,0 puntos |
| P5 | **Matriz:** ¿casillas de 1 cm? ¿origen y orientación de (x,y)? ¿cuántas casillas? | la rúbrica no lo dice; lo trajo Sebas de la clase |
| P6 | **¿Tablero vertical (como la imagen) u horizontal elevado 5 cm?** ¿Qué es "la base"? | cambia la geometría: ver sección 4 |
| P7 | **El test de 5 posiciones:** ¿las elige el profe en el momento o son fijas? ¿se disparan desde la app? | define el modo TEST |
| P8 | **¿Se detecta acierto/fallo o solo se muestra el rayo?** | la rúbrica dice que el resultado se evidencia con el rayo; si es así, el Hall no hace falta |
| P9 | **¿Hay informe escrito?** Solo se mencionan video y sustentación | si no, la documentación puede ser mínima |
| P10 | ¿iPhone o Android? ¿cuál tiene el profe? | decide la tecnología de Bluetooth |

**Borrador para Almario** (lo envías tú):
> Profesor, sobre el trabajo de la estación de ataque: (1) ¿cada estación dispara sobre el tablero del contrincante a distancia, o sobre el tablero propio? (2) ¿el grupo entrega un sistema o uno por integrante? (3) ¿la prueba con contrincante es contra otro grupo o entre nosotros? (4) ¿qué error de puntería se acepta en el test de 5 posiciones? (5) ¿el tablero va vertical o horizontal elevado 5 cm? (6) ¿vale una página con Web Bluetooth o debe ser una app nativa? Gracias.

## 4. El hueco técnico más grande: precisión de apuntado

El test (2,0 pts) pide que el rayo aparezca **en la coordenada**, 5 de 5 veces. Con celdas de 1 cm:

| Distancia estación → celda | Ángulo de 1 cm | Tolerancia de ±5 mm |
|---|---|---|
| 15 cm | 3,81° | ±1,91° |
| 20 cm | 2,86° | ±1,43° |
| 25 cm | 2,29° | ±1,15° |
| 30 cm | 1,91° | ±0,95° |
| 40 cm | 1,43° | ±0,72° |
| 50 cm | 1,15° | ±0,57° |
| 60 cm | 0,95° | ±0,48° |

- La **banda muerta del MG996R es 5 µs [hoja]**: **≈ 0,45°** si el servo usa 500–2500 µs para 180°, **≈ 0,9°** si usa 1000–2000 µs (las fuentes se contradicen). Más holgura de engranes. **Realista: ±0,5–1°.**
- **Conclusión:** con servos de hobby, **la estación debe estar a ≤ 30 cm de la celda más lejana (ideal 20–25 cm)**. A 50 cm o más, ±0,57° exige mejor hardware: servos digitales con menor banda muerta, un servo con lectura de su potenciómetro en lazo cerrado, o un motor paso a paso con reducción. **P1 y P6 deciden la distancia real.**
- **Mitigaciones baratas:** calibrar con tabla medida (no solo con ecuación), **acercarse siempre al objetivo desde el mismo lado** (elimina la holgura), reducir a 0,25° los pasos de la rampa, y un punto láser de ≤ 3 mm.
- **Tablero horizontal elevado 5 cm:** el rayo llega casi rasante y el punto se alarga. Para que un punto de 3 mm no pase de 10 mm hace falta incidencia ≥ 17,5°, es decir, que el láser esté a **≥ 6 cm sobre el plano del tablero si la celda está a 20 cm, ≥ 9,5 cm a 30 cm, ≥ 12,6 cm a 40 cm**. Con la estación al nivel de la base y el tablero a 5 cm, el rayo prácticamente rasa. **O el tablero va vertical, o el láser va en un mástil alto.**
- **Tablero vertical de frente:** el punto casi no se alarga (×1,12 con ±15 cm de giro a 30 cm). Es la geometría de la imagen y la más fácil de cumplir.

## 5. V2: núcleo de la rúbrica (propuesta)

**Por sistema** (tablero 30×30 + estación):

- **Tablero:** 30×30 cm, matriz 20×20 centrada (5 cm de margen), **elevado 5 cm**; cuadrícula de 1 cm impresa/grabada; fichas de la flota (barcos) sin electrónica.
- **Estación:** pan-tilt (MG996R + MG90S) + láser KY-008 ≤ 5 mW con transistor y enclavamiento + zumbador activo + ESP32 (Bluetooth) con tope de software.
- **App propia** (Bluetooth): ingresar `(x,y)`, botón DISPARAR, botón TEST (5 posiciones), estado de conexión.
- **Firmware:** cinemática inversa + calibración (3 parámetros + tabla medida), protocolo `(x,y)`, modo TEST, soft limits, láser con enclavamiento.
- **Potencia (V2, un ESP32 por módulo):** por módulo, 5 V ≤ 0,7 A (ESP32 0,5 A pico [hoja Espressif: fuente ≥ 0,5 A] + láser 0,04 A + zumbador) y servos a 6 V con **3,2 A de pico (stall)**, 1,15 A en marcha. **Un adaptador de 6 V/4 A por módulo** (o uno de 6 V/8 A con cable en Y) + convertidor de 6 V a 5 V de ≥ 1,5 A para el ESP32. Sin 12 V, sin 8 A por módulo, sin compuerta de Hall.
- **Lista corta por sistema:** 1 ESP32 (+1 de repuesto en el grupo), 1 MG996R, 1 MG90S (+1), 1 KY-008 (+1), 2N2222A, zumbador activo, adaptador 6 V/4 A, convertidor 5 V, condensadores, cables, material del tablero y la estación, soportes de 5 cm. Es una fracción de la lista v3: sin 970 Hall, 880 LED, 62 mux, PCB ni servicios.

**Qué se conserva del trabajo anterior:** H2/H3/H4 (precisión y geometría), H8 (láser seguro), cinemática inversa, simulación de apuntado, `modelo-potencia.py` (con las cargas reducidas), UT-SW-01..06, 10, 16 y UT-HW-01..05, y la estructura de los controles.

**Qué se suelta (queda como extra solo si sobra tiempo):** matriz Hall, LED por celda, fototransistores, PCB en losas, 12 V, enlace maestro/esclavo entre módulos, maletín con enlace. **Extras baratos que sí suman creatividad:** autocalibración con 4 fototransistores en las esquinas, sonidos distintos por resultado, pantalla OLED con el puntaje, registro de disparos en la app.

## 6. Calendario (21 días)

| Fecha | Qué | Control |
|---|---|---|
| **mar 3 nov** | Mensaje a Almario (P1–P10). Confirmar el V2. Subir los **diseños a mano** a la carpeta del proyecto | |
| 3 – 8 nov | Compras locales de la lista corta. Bluetooth ESP32 ↔ celular con un `(x,y)`. Pan-tilt con láser sobre una cuadrícula impresa. CAD en SolidWorks del tablero y la estación | 🚦 **dom 8 nov:** el celular manda `(x,y)` y el láser cae dentro de la celda en 5 de 5 posiciones de una cuadrícula impresa |
| 9 – 15 nov | Tablero 30×30 elevado y estación armados; calibración; modo TEST; app v1 | 🚦 **dom 15 nov:** un sistema completo pasa el test 5/5, 3 veces seguidas |
| 16 – 21 nov | Segundo sistema, prueba con contrincante, sonido, estética; **grabar el video con los dos desarrolladores**. 17-nov informes de laboratorio y Desafío 3 compiten | 🚦 **vie 20 nov:** prueba con contrincante hecha y video grabado |
| sáb 22 nov | **Congelar firmware y app** | |
| dom 23 nov | SIEA de Mate: sin trabajo | |
| **mar 24 nov** | **Entrega y demostración** | |

## 7. Los diseños a mano

**No los encontré**: busqué en la carpeta del proyecto, `inbox/`, `borradores/`, Descargas, Escritorio e Imágenes (archivos de la última semana) y solo está `TRABAJO CORTE FINAL.pdf`. Súbelos a `Proyecto - Batalla Naval\Diseños\` (fotos o PDF) o a `inbox/` y los reviso contra esta lista. Para que sirvan, deberían mostrar:

- [ ] Medidas del tablero (**30×30**), de la matriz (**20×20**, centrada) y de la elevación (**5 cm**), con vistas de planta y de perfil.
- [ ] **Origen y ejes de (x,y)** marcados sobre la matriz.
- [ ] **Dónde va la estación** respecto del tablero: distancia a la celda más cercana y a la más lejana, y altura del láser sobre el plano.
- [ ] **El tablero rival**: ¿frente a la estación y a qué distancia?
- [ ] El **eje del láser** pasando por el cruce de los ejes pan y tilt (si no, la ecuación de apuntado se complica).
- [ ] Cómo se sujetan los servos, cableado y **dónde van el ESP32, el zumbador y la fuente**.
- [ ] Cómo se guardan los barcos y cómo se transporta todo (si hay maletín, o no).
- [ ] Tolerancias de impresión o corte (ajustes de 0,2–0,5 mm) y cómo se regula la posición del tablero para calibrar.

Para SolidWorks: modela con **parámetros** (ancho del tablero, elevación, distancia, altura del láser) y exporta a STEP, para que la calibración (x, y, h de la estación) salga del modelo y no de una medición a ojo.

## 8. Lo que no sé

- **Cómo quedó el plan después del 27-oct:** no sé si ya compraste algo o si diseñaron la PCB. Dime qué hay y lo descuento.
- **Contenido de los diseños a mano** (arriba).
- **Qué tienen tú y tu compañero ya a la mano**, y el presupuesto.
- **Quién hace la app** y con qué tecnología.
