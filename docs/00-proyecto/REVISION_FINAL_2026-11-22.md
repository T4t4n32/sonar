# Revisión final contra la rúbrica y los avisos de Almario (2026-11-22)

Fuentes: `TRABAJO CORTE FINAL.pdf` (2 págs., releído hoy), las 7 aclaraciones del profesor y el aviso de las franjas del lunes. Estado: **VIGENTE**. Complementa [ESTADO](../ESTADO.md) y [RUBRICA_Y_CUMPLIMIENTO](RUBRICA_Y_CUMPLIMIENTO.md).

## 0. Lo urgente
1. **Correo de intención para sustentar el lunes 23-nov: se recibe hasta el domingo 22-nov a las 8 pm** (hoy). Máximo 8 grupos, franjas 10:00–11:30 y 14:00–15:00, orden de llegada. Da **+0,5** solo si el trabajo cumple las especificaciones. Borrador al final de este documento.
2. Si se presenta el lunes, el firmware 0.2.0 tiene que estar cargado y calibrado **el lunes antes de la franja**.

## 1. Requisitos del PDF
| # | Requisito | Estado | Evidencia / qué falta |
|---|---|---|---|
| 1 | Estación base de ataque + tablero de posicionamiento | ✅ montado | cajón de servos + pared de matriz (maqueta) |
| 2 | Tablero **30 × 30 cm** con matriz **20 × 20 cm** | ⚠️ físico | imprimir `docs/impresos/cuadricula-matriz-20x20.pdf`; el marco de 30×30 lo hace Sebas |
| 3 | Tablero **elevado 5 cm** sobre la base | ⚠️ físico | medir 5 cm desde la base de instalación hasta el tablero; hay que poder mostrarlo |
| 4 | Láser aparece en la coordenada `(x,y)` | ⚠️ por calibrar | firmware 0.2.0 (movimiento suave, mapa de 9 puntos); validar con la hoja impresa |
| 5 | Formato `(x,y)`, **x primero** | ✅ | parser y pruebas; ahora acepta `(x,y)` sin salto de línea |
| 6 | **Sonido con cada disparo** | ⚠️ | el firmware pita (GPIO 21) pero **el zumbador no está cableado**. El rival nos maneja con SU app (no sabemos si suena). **Conectar un zumbador activo: + a GPIO 21, − a GND** |
| 7 | Datos por **Bluetooth desde el celular con una app propia** | ✅ | APK propia + SPP; nombre `SONAR-A`/`SONAR-B` |
| 8 | **Rutina de test de 5 posiciones** en el propio sistema | ✅ | `TEST` (esquinas + centro) desde la app y por USB; también se pueden pedir 5 celdas a mano |
| 9 | Software **original** | ✅ | firmware, app y protocolo propios; historial de commits |
| 10 | Entrega y demostración **martes 24-nov** (o lunes 23 con +0,5) | ⏳ | ver §0 |
| 11 | Video con los **dos** desarrolladores | ⏳ | grabar con los dos participando |
| 12 | Sustentación **individual** | ⏳ | los dos deben poder explicar el sistema (guion abajo) |
| 13 | Estética | ⏳ | amarrar el cableado, tapar el cartón, rotular |

## 2. Las 7 aclaraciones del profesor
| # | Aclaración | Estado |
|---|---|---|
| 1 | Cuadrícula 20×20 de 1 cm | ✅ firmware, app y hoja impresa |
| 2 | Cada grupo coloca su flota en **su** tablero; el rival maneja **tu** tablero por Bluetooth | ✅ el módulo acepta `(x,y)` de cualquier cliente SPP; **probar con otra app/terminal Bluetooth además de la nuestra** |
| 3 | Flota: 3 barcos de 2 cm + 2 submarinos de 4 cm, horizontal o vertical | ✅ «Mi flota» (14 casillas) |
| 4 | Afectado si se alcanza cualquier casilla del barco | ✅ lógica de la app |
| 5 | Un testigo da fe | ✅ la app pregunta «¿le di?» y el testigo confirma |
| 6 | Primero x, luego y; el programa recibe y mueve el láser | ✅ |
| 7 | Ponerle nombre al Bluetooth | ✅ `SONAR-A` / `SONAR-B` (en `platformio.ini`; cambiar `DEVICE_NAME` si se quiere otro) |

## 3. Qué se mejoró hoy en el ESP32 (firmware 0.2.0)
- **Movimiento:** los dos ejes a la vez con perfil suave (antes: uno tras otro, arranque y frenado bruscos); remate lento siempre subiendo (compensa la holgura); no repite movimientos de menos de 0,01°.
- **Calibración:** hasta 9 puntos (esquinas + 4 medios de borde) por mínimos cuadrados, con el error reportado; el mapa viejo guardado se sigue leyendo.
- **Diagnóstico:** `INFO` informa la causa del último reinicio (`BROWNOUT` delata una fuente que se hunde: es la causa más probable de «servos trabados» con pilas), memoria y posición.
- **Compatibilidad con la app del rival:** `(x,y)` se acepta sin salto de línea; una orden válida suelta se entrega a los 300 ms.
- 71/71 pruebas nativas; `modulo_a` y `modulo_b` compilan. **No probado todavía en el ESP32 real.**

## 4. Pendiente en la app (se deja para después de la sustentación o para mañana temprano)
- «Mi flota» **no se usa al disparar**: hoy hay que marcar a mano el barco golpeado. Propuesta: al decir «sí le di», la app compara con la plantilla y avisa «tocaste un barco cerca de …».
- Plantillas de flota: 5–10 plantillas rotativas que se vayan gastando; elegir una o sortear.
- Pensar la pantalla para el profesor: pocas pantallas, textos grandes, un solo botón de disparo y de test.
- Registrar desde la app los medios de borde (6–9) de la calibración.

## 5. Checklist del lunes
1. Cargar `modulo_a` 0.2.0 (`PING` → `PONG SONAR-A 0.2.0`; `HELLO` con `pts9`).
2. Fijar cajón y pared; poner la hoja impresa; conectar zumbador.
3. Calibrar: 4 esquinas + control, idealmente también los 4 medios de borde. Aceptar con error ≤ 0,5°. `CAL SAVE`.
4. Probar `TEST` 3 veces seguidas con testigo; anotar fallos.
5. Probar desde **otro celular** con la APK y desde una terminal Bluetooth cualquiera.
6. `INFO`: confirmar que el último reinicio no fue `BROWNOUT`; pilas nuevas.
7. Llevar: cables de respaldo, pilas de repuesto, cinta, la hoja impresa de repuesto, el portátil con el repositorio.

## 6. Guion corto de sustentación (cada uno debe poder decirlo)
- **Qué hace:** el celular manda `(x,y)` por Bluetooth, el ESP32 convierte la celda en ángulos de dos servos y enciende el láser 1,5 s con un pitido.
- **Cómo apunta:** se calibra apuntando a las esquinas de la matriz; el módulo ajusta una homografía y calcula las 400 celdas. No depende de medir distancias.
- **Cómo es seguro:** el láser nunca está encendido mientras se mueve un servo; `STOP` lo apaga al instante; se apaga solo a los 120 s.
- **Qué es original:** firmware (C++ con pruebas), app (Preact + Capacitor), protocolo de líneas.

## 7. Borrador del correo (completar nombres y enviar **hoy antes de las 8 pm**)
> **Asunto:** Intención de sustentar el lunes 23-nov — Fundamentos de Ingeniería Mecatrónica — Batalla Naval
>
> Profesor Almario: somos el grupo de **[nombres completos]**, de la sección **[grupo/curso]**. Confirmamos nuestra intención de sustentar el trabajo «Batalla Naval» el **lunes 23 de noviembre**, en la franja que nos pueda asignar (10:00–11:30 o 14:00–15:00). Entendemos que el +0,5 aplica solo si el trabajo cumple las especificaciones de la consigna. Quedamos atentos a la programación. Gracias.
>
> **[Nombres] · [códigos]**
