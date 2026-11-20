# APP SONAR — plan de la aplicación (APK nativa propia)

Desde 2026-11-15. Sustituye a `APP_INVENTOR.md` como línea principal: la rúbrica pide «una app propia por Bluetooth», y esta es una app de verdad (instalable, sin App Inventor). El diseño 3D lo lleva Sebas; **todo el software es de Claude**.

## 1. Reglas del profesor (2026-11-15) y qué cambian
| # | Regla | Consecuencia para la app |
|---|---|---|
| 1 | Cuadrícula **20×20, casillas de 1 cm** | Se acabó la duda de 2 cm: el tablero de la app es 20×20 |
| 2 | Cada grupo coloca su flota en **su** tablero; el rival maneja **tu** tablero por Bluetooth y apunta a las coordenadas que tú ubicaste | Mi celular se conecta **al módulo del rival** y dispara; el láser aparece en el tablero del rival |
| 3 | Flota: **3 embarcaciones de 2 cm + 2 submarinos de 4 cm**, horizontales o verticales | 5 barcos = **14 casillas**; el editor de flota valida esto |
| 4 | Afectado si el enemigo alcanza **cualquier** casilla del barco | Impacto por casilla; hundido cuando caen todas las suyas |
| 5 | **Un testigo da fe** de la afectación | Tras cada disparo, hoja de confirmación grande para el testigo: ACIERTO / AGUA |
| 6 | Coordenada siempre **primero x, luego y** | Ya es el protocolo `(x,y)` |
| 7 | Ponerle **nombre al Bluetooth** | El firmware se anuncia como `SONAR-A` / `SONAR-B`; la app los lista por prefijo |

**Efecto grande:** como los barcos son **físicos** y hay testigo, **no hacen falta sensores por casilla** (adiós a 800 LDR, multiplexores y matriz vertical de fotodetectores). Queda la electrónica mínima: ESP32 + 2 servos + láser + buzzer.

## 1b. Dinámica de la evaluación (aclarada por Sebas, 2026-11-15)
1. **El profesor se conecta al Bluetooth de nuestro módulo** (`SONAR-A`) con la app.
2. Primero se cumplen los protocolos de la rúbrica: **TEST de 5 posiciones**.
3. El profesor escribe una **coordenada completa** (p. ej. `1, 6`) → el láser aparece en **nuestro** tablero físico.
4. **Nosotros somos el testigo/defensor**: miramos nuestro tablero y le decimos «le dio al barco» o «no le dio, profe».
Consecuencia: el flujo principal es **atacante → módulo del defensor**; la app debe ser **instantánea de operar** (teclear o tocar `x, y` → disparar) y la hoja de veredicto la usa **el defensor** (nosotros), no el atacante.
Por eso la app tiene **dos vistas en una sola APK** (se cambia con un interruptor, y recuerda la última):
- **Modo Atacante** (lo que ve el profesor): conectar, TEST, entrada de coordenada, DISPARAR/STOP, radar de lo disparado. **Sin flota a la vista.**
- **Modo Defensor** (nosotros): «Mi flota» cargada; tras cada disparo que llega al módulo, la app **dice de inmediato «TOCADO — Submarino 1» o «AGUA»** (con `resolveShot`) para que respondamos sin equivocarnos, y lleva el marcador de nuestros barcos. La flota se muestra solo con **mantener pulsado** (para que el profesor no la vea si usa nuestro celular).
Pendiente de confirmar con Sebas: si el profesor usa **su** celular (hay que instalarle la APK) o **el nuestro** (basta una vista simple).

## 1c. Ciclo de disparo y tutorial animado (Sebas, 2026-11-15) — sustituye el reparto de modos de 1b
La app es **muy animada**; el profesor opera el celular de Sebas y **ellos (estudiantes) dan el veredicto**. Un solo flujo, sin modos Atacante/Defensor:
1. **Apuntar** (radar o teclado `x, y`) → **DISPARAR**: se envía `(x,y)` al módulo (el láser real cae en la coordenada: eso cumple la rúbrica) y la app anima el proyectil.
2. **Pausa antes del impacto**: el tiempo se congela justo antes de tocar la coordenada y aparecen dos botones grandes: **SÍ LE DIO / NO LE DIO** (los pulsan los estudiantes tras mirar su tablero físico).
3. **NO LE DIO** → animación de gota de agua (anillos) en la celda, marca de agua, vuelve a apuntar.
4. **SÍ LE DIO** → explosión (partículas, onda, vibración) y pantalla **«Ubica el barco»**: el tablero completo a pantalla grande; el estudiante **arrastra el dedo** sobre las casillas del barco (recta H o V, largo 2 o 4, debe incluir la casilla del impacto, sin solapar otros barcos ubicados); valida en vivo, **LISTO** lo registra y vuelve a apuntar; «No sé / después» lo deja pendiente.
5. Con el barco ubicado, los disparos siguientes sobre sus casillas son impacto directo; al caer todas: **¡HUNDIDO!**; con los 5 hundidos: **victoria**.
**Tutorial inicial** (primera vez y en Ajustes → «Ver tutorial»): animación de arranque del logotipo (ping de sonar) y luego, **sin interacción**, primero la **dinámica del juego** (flota, conexión Bluetooth, TEST, coordenada x→y, láser, veredicto, explosión/gota, ubicar el barco) y después el **recorrido de la interfaz** con pantallas simuladas animadas. Siempre con «Saltar».
Nota de diseño: ubicar el barco completo revela su posición al jugador que dispara (lo que se quiere aquí); el asistente de tiro sigue disponible, apagado por defecto.

**Orientación (2026-11-20):** el radar se ve como lo ve quien está detrás de la estación: la **estación abajo**, el disparo **sube** hacia la casilla y **(1,1) queda abajo-izquierda** (y crece hacia arriba). Lo mismo en «Mi flota» y «Ubica el barco».

## 2. Cómo se ve la app (norte: «puente de mando de un submarino»)
Android nativo (APK), vertical, una mano, modo oscuro por defecto (claro opcional). Sin menús escondidos: **barra inferior de 4 pestañas**.

1. **Batalla** (principal): radar 20×20 del tablero rival con barrido animado. Se toca/arrastra para apuntar (retícula con cota X/Y), botón grande **DISPARAR**, **STOP** siempre visible. Al disparar: haz del láser animado hasta la celda, eco sonoro, y **hoja del testigo** (ACIERTO / AGUA / HUNDIDO). El radar pinta aciertos (rojo), agua (cian), hundidos (barco completo). Contador de flota rival (qué barcos quedan), marcador de disparos/aciertos, cronómetro de turno.
2. **Mi flota**: mini-tablero 20×20 donde Sebas coloca 3×2 y 2×4 (tocar, rotar, arrastrar), botón **Aleatoria**, y una **lista de coordenadas para colocar las piezas físicas** («Submarino 1: (5,7)→(5,10)»). Es la referencia para el testigo y para que nadie se equivoque al armar el tablero real.
3. **Enlace**: Bluetooth. Lista de módulos emparejados `SONAR-*`, conectar/desconectar, estado vivo (latido `PING`), reconexión automática, guía de emparejado, **TEST de 5 posiciones** con progreso por casilla (esto es lo que vale 2,0), y calibración de la torreta (modo mantenimiento).
4. **Partida**: historial (bitácora de disparos con hora y resultado), estadísticas (precisión, racha, tiempo medio), exportar JSON/CSV, y **Ajustes** (tema, sonido, vibración, pantalla encendida, modo simulado).

Extras que marcan la diferencia (todos deterministas, sin IA):
- **Asistente de tiro** (activable): mapa de calor de probabilidad = en cuántas ubicaciones legales cabrían los barcos restantes dados los aciertos/aguas. Sugiere la mejor celda; con un acierto pasa a modo «rematar».
- **Modo simulado**: un rival virtual con flota aleatoria responde como el módulo real. Sirve para practicar, para grabar el video y para probar sin hardware.
- **Inferencia de hundido**: si los aciertos contiguos igualan el largo de un barco restante y están acotados por agua/borde, la app propone «HUNDIDO».
- **Voz/sonido y vibración** por evento (disparo, acierto, agua, hundido, victoria).

## 3. Arquitectura técnica
Capas, de abajo a arriba (todo TypeScript, en `app/`):

| Capa | Carpeta | Qué hace | Pruebas |
|---|---|---|---|
| Núcleo de reglas | `src/core/` | tablero, flota (validación 3×2+2×4), disparos, hundidos, partida, estadísticas, mapa de probabilidad, protocolo (formatear/parsear líneas) | Vitest (sin UI) |
| Transportes | `src/transport/` | interfaz `LineTransport` y 3 implementaciones: **Bluetooth SPP** (Capacitor), **Wi-Fi HTTP** (mantenimiento, `/cmd?l=`), **Simulado** (módulo falso en memoria) | Vitest sobre el simulado |
| Estado | `src/state/` | store reactivo (persistencia local), orquesta partida + transporte | Vitest |
| Interfaz | `src/ui/` | Preact (3 KB) + CSS propio con los tokens de `web/index.html` | Playwright con transporte simulado |
| Envoltorio nativo | `android/` (Capacitor 8) | permisos Bluetooth (Android 12+: `BLUETOOTH_CONNECT/SCAN`), icono, ícono adaptativo, orientación | APK en el celular |

Piezas: Vite + Preact + TypeScript + Vitest + Capacitor 8 + `@e-is/capacitor-bluetooth-serial`.
La interfaz web de `web/index.html` **se queda** como página del ESP32 en modo mantenimiento y para iPhone; la app es la línea principal.

## 4. Protocolo
La app habla el **protocolo vigente v1+v2** (`PROTOCOLO.md`): `(x,y)`, `TEST`, `STOP`, `PING`, `HELLO`, `MARK HIT|MISS`, `CAL …`. No hace falta tocar el firmware para el mínimo.

**Propuesta v3 (opcional, después del control):** que el módulo conozca la flota de su tablero para adjudicar solo.
`FLEET CLEAR` · `FLEET ADD x y len H|V` (una línea por barco; el límite de 64 caracteres lo exige) · `FLEET LOCK` → luego cada disparo responde `OK (x,y)` y `RES HIT|MISS|SUNK <len>`. La app lo detecta por el campo `caps` de `HELLO` (`fleet`). El testigo sigue confirmando (la app solo pre-marca).

## 5. Fases
| Fase | Entregable | Criterio |
|---|---|---|
| **F1 — mínimo de rúbrica** | Enlace Bluetooth, apuntar, DISPARAR, STOP, TEST de 5 posiciones, hoja del testigo, radar con marcas | probado contra el simulado y contra el ESP32 real |
| **F2 — juego** | Mi flota, estadísticas, historial, asistente de tiro, hundidos, victoria, modo simulado | Vitest + e2e verdes |
| **F3 — pulido** | animaciones, sonido, vibración, icono, exportar, v3 `FLEET` | APK firmado debug en el 13C |

## 6. Instalación y entrega
`npm run build && npx cap sync android && (cd android && gradlew.bat assembleDebug)` → `app/dist-apk/SONAR-<versión>-debug.apk`; instalación por `adb install -r` en el celular conectado. Versión visible en Ajustes. Código **original** (rúbrica: −0,5 por copia): nada de plantillas de App Inventor.

## 7. Riesgos
- **Bluetooth real sin probar** (SPP + plugin): primer hito en cuanto haya un ESP32 clásico (`BRINGUP.md`).
- Permisos de Bluetooth en Android 12+ (pedir en tiempo de ejecución) y emparejado previo del módulo.
- El Bluetooth clásico acepta **un** teléfono a la vez: el módulo A solo habla con el celular del rival.
