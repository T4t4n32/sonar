# ESTADO de SONAR · Batalla Naval — fuente de verdad (2026-11-15)

Si dos documentos se contradicen, **manda este**. Lo demás es detalle o historia: ver el [índice](README.md). Mantener al día después de cada decisión.

## 1. Qué se entrega (rúbrica verificada en `TRABAJO CORTE FINAL.pdf`, 2 págs.)
Entrega y demostración **martes 24-nov-2026**. Nota: test de 5 posiciones **2,0** · prueba con contrincante **1,0** · sustentación individual **1,0** · estética **0,5** · video con los dos desarrolladores **0,5**.
Piden: estación base de ataque + tablero de posicionamiento de **30 × 30 cm** con **matriz de ubicación de 20 cm × 20 cm**, elevado **5 cm**; el láser **aparece en la coordenada `(x,y)`** del tablero del contrincante; **sonido** con cada disparo; datos **por Bluetooth desde el celular con una app propia**; rutina de **test de 5 posiciones** por jugador en su propio sistema; software **original** (−0,5 por copia). *La rúbrica escrita no dice «casillas de 1 cm»: eso se mencionó en clase.*

### Reglas aclaradas por el profesor (2026-11-15) — mandan sobre lo anterior
1. Cuadrícula **20×20 de 1 cm** (se acabó la duda de 2 cm). 2. Cada grupo coloca su flota en **su** tablero; el rival maneja **tu** tablero por Bluetooth. 3. Flota: **3 embarcaciones de 2 cm + 2 submarinos de 4 cm**, horizontal o vertical (14 casillas). 4. Afectado si se alcanza cualquier casilla del barco. 5. **Un testigo da fe** de la afectación. 6. Coordenada **primero x, luego y**. 7. Ponerle nombre al Bluetooth.
Consecuencias: **no hacen falta sensores por casilla** (ni matriz LDR ni fotodetectores; Plan B y puerta del 10-nov quedan sin objeto); la petición a Almario de casillas de 2 cm **queda sin efecto**; la app es de verdad (APK propia), no App Inventor: ver [APP_SONAR](03-firmware-y-app/APP_SONAR.md).

## 2. Decisiones vigentes
| Tema | Decisión | Desde | Detalle |
|---|---|---|---|
| Alcance mínimo | **2 módulos idénticos** (tablero + estación + ESP32 clásico), mismo programa | 3-nov | [EMPIEZA_AQUI](00-proyecto/EMPIEZA_AQUI_2026-11-03.md) |
| Casillas | **20×20 de 1 cm, definitivo** (profesor, 15-nov). La petición de 2 cm a Almario queda sin efecto | 15-nov | [PREGUNTAS_ALMARIO](00-proyecto/PREGUNTAS_ALMARIO.md) |
| Comunicación | Línea base de la rúbrica: **Bluetooth clásico (SPP) + APK Android** (Capacitor). Wi-Fi con página en el ESP32 = **extra** (mantenimiento y «para todos»). BLE / Web Bluetooth solo si Almario acepta «web = app» | 7-nov | [ARQUITECTURA_UNIVERSAL](01-diseno/ARQUITECTURA_UNIVERSAL.md) |
| Protocolo | v2 en el núcleo: `HELLO`, `MODE`, `ARM`, `ERR DISARMED`. En el firmware solo `HELLO`; **`MODE` y `ARM` aún sin manejador** | 7-nov | [PROTOCOLO](03-firmware-y-app/PROTOCOLO.md) |
| Juego completo | Vincular, bando rojo/azul, sorteo, **barcos físicos**, árbitro **replicado en los dos ESP32**, LED rojo al fallar, estadísticas. **Es extra (no se califica): después del test 5/5** | 7-nov | [FLUJO_JUEGO](01-diseno/FLUJO_JUEGO.md) |
| Detección | **Ya no hay sensores**: barcos físicos + **testigo** confirma (profesor, 15-nov). La app pre-marca y el testigo da fe. Adjudicación automática por el módulo = extra opcional (protocolo v3 `FLEET`) | 15-nov | [APP_SONAR](03-firmware-y-app/APP_SONAR.md) |
| App | **APK nativa propia** (Vite + Preact + TS + Capacitor): Batalla, Mi flota, Enlace/TEST, Partida; rival simulado; asistente de tiro | 15-nov | [APP_SONAR](03-firmware-y-app/APP_SONAR.md) |
| Torreta | Abatible en el maletín: **B (con la tapa) o C (a mano)**; A (servo de levante) solo si sobra tiempo | 8-nov | [TORRETA_ABATIBLE](01-diseno/TORRETA_ABATIBLE.md) |
| Potencia | **Adaptador 12 V 5 A** + buck 6 V (servos) y 5 V (ESP32/láser); batería 3S opcional | 8-nov | [POTENCIA](02-electronica/POTENCIA.md) |
| Servos | **MG996R ×2 por módulo** (pan y tilt) + repuestos | 7-nov | [LISTA_MERCADOLIBRE](04-compras/LISTA_MERCADOLIBRE.md) |
| Compras | Mercado Libre / tiendas colombianas, **nada de China** (llega tarde) | 7-nov | idem |
| Publicación | Repositorio **privado** hasta el 24-nov; publicación programada ese día a las 20:00 (`tools/publicar.py`) | 7-nov | [LICENCIAS](05-publicacion/LICENCIAS.md) |
| Hardware final | **ESP32 + 2 servos + láser + fase de potencia. Nada de luces** (sin matriz LED ni LED de acierto). Sonido y vibración en la app | 20-nov | [PINOUT](02-electronica/PINOUT.md) |
| App: orientación del radar | La estación y el disparo salen **desde abajo** y (1,1) queda abajo-izquierda, como en el tablero físico (el usuario ve lo mismo que la estación) | 20-nov | [APP_SONAR](03-firmware-y-app/APP_SONAR.md) |

## 3. Conflictos entre fuentes (resueltos aquí)
| Tema | Antes (3-nov, vault) | Ahora |
|---|---|---|
| Enlace entre módulos | «no hay cable de datos entre módulos»; descartado | **Sí**: ESP-NOW módulo↔módulo para el juego completo (por probar en hardware) |
| Sensor por celda | «posible, pero pesado y **sin puntos**»; 800 LDR + 50 multiplexores | Es el deseo de Sebas como extra; se reduce con 10×10 si Almario acepta, o Plan B |
| Aviso de acierto | por software, manual, o **un solo sensor** junto al láser con fichas blancas y tablero negro mate | sigue siendo la alternativa barata si no hay sensores por celda |
| Servos | MG996R (pan) + **MG90S** (tilt) | **MG996R ×2** (la torreta abatible exige el par) |
| Alimentación | adaptador 6 V/4 A + conversor a 5 V | adaptador **12 V 5 A** + dos buck (6 V y 5 V) |
| Página web | «Nada de página web» | **Extra** ya hecho (`web/index.html`), útil para iPhone y mantenimiento |
| Quién se conecta a quién | el rival se conecta al módulo que recibe el disparo | cada celular a **su** módulo (Bluetooth); los módulos se hablan entre sí (juego completo) |
| Mensaje a Almario | P1–P10 | **una sola petición** (casillas de 2 cm); el resto se asume |

## 4. Calendario
| Fecha | Hito |
|---|---|
| **dom 8-nov** | Control 1: el celular manda `(x,y)` por Bluetooth y el láser cae 5/5 en una cuadrícula impresa ([CONTROL1](03-firmware-y-app/CONTROL1.md)) |
| **mar 10-nov** | Puerta de decisión: visión / sensores / respaldo manual |
| **dom 15-nov** | Control 2: sistema completo, test 5/5 tres veces seguidas |
| **vie 20-nov** | Control 3: prueba con contrincante y video con los dos |
| **sáb 22-nov** | Congelar firmware y app |
| **mar 24-nov** | Entrega y demostración · 20:00 publicación programada del repositorio |

## 5. Estado técnico (verificado)
Núcleo: **52/52** pruebas nativas · simulador: selftest **24/24** · web: e2e **29/29** (capturas en [`registro/`](../registro/)) · firmware `modulo_a` compila (flash 51,4 %) · **app SONAR 0.1.0** (`app/`, Vite+Preact+TS+Capacitor): núcleo 160 pruebas + transportes/STOP urgente + store 27 = **189 Vitest**, e2e de la app 42/42 con módulo simulado, APK debug 4,3 MB compilado; firmware anuncia `SONAR-A`/`SONAR-B` · concepto 3D del maletín en [`cad/`](../cad/LEEME.md) (modelo SolidWorks **a medias**).

**Primera prueba en ESP32 real (15-nov, tarde, con Lucky/heat-lucky):** `PING`→`PONG SONAR-A 0.1.0` por USB · Bluetooth real con la APK conectó estable · servos pan/tilt moviéndose comandados desde la App real · `TEST` (5 posiciones) corrido por USB, `TEST DONE` sin errores. Detalle completo, bug de firmware encontrado/corregido y causa de los resets espontáneos (fuente de 6 V débil, no firmware) en [`registro/2026-11-15-banco-hardware.md`](../registro/2026-11-15-banco-hardware.md). **Falta aún:** precisión 5/5 dentro de 1 cm en cuadrícula impresa real (Control 1 completo), fuente de 6 V dedicada (la actual se hunde y resetea el ESP32), láser armado con su transistor propio.

## 6. Pendientes y responsable
| Qué | Quién |
|---|---|
| Control 1 con el hardware (Bluetooth real, `PING`, 5/5) | Sebas |
| Respuesta de Almario sobre casillas de 2 cm | Sebas (correo) |
| Elegir B o C, medidas del maletín, pedido del Bloque A con el compañero | Sebas |
| Decidir si los nombres completos de los autores quedan públicos; mover `WIFI_PASS_MAINT` a `secrets.h` | Sebas + Jader / Claude |
| Terminar el modelo SolidWorks (3 piezas) y pasar a ensamblaje | Claude |
| `MODE`/`ARM` en el firmware, servidor en vivo, transporte Bluetooth del APK | Claude (después del control 1) |
| Commit y push al repositorio privado antes del 24-nov | Claude (con visto bueno de Sebas) |
Lista detallada: [PENDIENTES](00-proyecto/PENDIENTES.md).
