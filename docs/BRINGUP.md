# Puesta en marcha en banco (BRINGUP)

Lista de verificación para poner en marcha **un módulo** (A o B) antes de jugar. Haz los pasos **en orden**. Marca cada ☐ solo cuando el criterio se cumple. Si uno falla, para, anota qué pasó y busca la causa antes de seguir.

Antes de encender el láser por primera vez, **lee el paso 8 (seguridad)**.

Referencias, para no repetir datos aquí:

- Comandos y respuestas: `docs/PROTOCOLO.md`.
- Conexiones y alimentación: `docs/PINOUT.md`.
- Constantes (tiempos, límites, signos): `include/config.h`.
- Geometría (fórmulas de apuntado): `lib/core/geometry.h`.
- App Android: `docs/APP_INVENTOR.md`.

Convención: en comandos y código el decimal es **punto** (`100.5`); en tablas y en el texto, **coma** (`100,5`).

---

## Material

- 2 ESP32 DevKit (WROOM-32), uno por módulo. Con PlatformIO instalado en el PC.
- Fuente de 6 V / 4 A para servos. Convertidor de 6 V a 5 V (≥ 1,5 A) para el ESP32, el láser y el zumbador.
- Condensadores de 1000 µF (junto a servos) y 470 µF (junto al ESP32).
- Servo pan MG996R, servo tilt MG90S, láser KY-008 con 2N2222A, resistencias de 1 kΩ, 10 kΩ y 330 Ω.
- Multímetro.
- Celular Android con cámara (vista previa) y una app de **inclinómetro** o de nivel (para medir el ángulo de la carcasa del láser).
- Regla metálica de 30 cm, escuadra y plomada.
- Transportador (opcional, para leer el ángulo del horn).
- **Tester de servos** (módulo PWM con potenciómetro). El firmware no tiene un comando para mover un servo suelto, así que el paso 3 lo necesita.
- Tablero con la cuadrícula de 10 mm, o celdas marcadas; cartulina blanca mate.
- Cronómetro, o un video en cámara lenta del celular.
- Gafas de protección láser adecuadas a la longitud de onda del láser (ver paso 8.1).

## Valores de referencia (por defecto)

Estos son los valores de `include/config.h` y `lib/core/geometry.h`. Tu montaje real puede diferir: el objetivo es medirlo y ajustarlo.

| Constante | Valor | Qué significa |
|---|---|---|
| `STATION_X_MM` | 100 | posición X del eje de pan, respecto a la esquina posterior-izquierda de la matriz |
| `STATION_Y_MM` | -65 | posición Y del eje de pan, respecto al borde posterior; negativo = detrás |
| `TILT_H_MM` | 180 | altura del eje de tilt sobre la matriz |
| `PAN_SIGN`, `TILT_SIGN` | +1 | sentido de los servos (ver 3.3) |
| `PAN_CENTER_SERVO_DEG` | 90 | ángulo de servo con el rayo hacia el frente |
| `TILT_HORIZ_SERVO_DEG` | 90 | ángulo de servo con el rayo horizontal (ver 3.4) |
| `SERVO_MIN_US`, `SERVO_MAX_US` | 500, 2500 | pulso del servo para 0° y 180° (1500 µs = 90°) |
| `PAN_LIMIT_DEG` | 57 | pan máximo, a cada lado |
| `TILT_MIN_DEG`, `TILT_MAX_DEG` | 30, 72 | rayo entre 30° y 72° bajo la horizontal |
| `SETTLE_MS` | 300 | espera antes de encender el láser |
| `LASER_ON_MS` | 1500 | tiempo que el láser queda encendido |
| `MAX_STEP_DEG`, `STEP_MS` | 2, 20 | rampa del servo: 2° cada 20 ms |
| `OVERSHOOT_DEG` | 2 | sobrepaso para acercarse siempre desde el mismo lado |

Ángulos esperados de servo con esos valores (sin trims), calculados con las fórmulas de `geometry.h`:

| Celda | Centro del punto (mm) | Pan (servo) | Tilt (servo) | Rayo bajo la horizontal |
|---|---|---|---|---|
| (1,1) | (5, 5) | 36,4° | 146,8° | 56,8° |
| (20,1) | (195, 5) | 143,6° | 146,8° | 56,8° |
| (20,20) | (195, 195) | 110,1° | 123,0° | 33,0° |
| (1,20) | (5, 195) | 69,9° | 123,0° | 33,0° |
| (11,11) | (105, 105) | 91,7° | 136,6° | 46,6° |

Pan servo = 90° + pan. Tilt servo = 90° + rayo bajo la horizontal.

---

## Paso 1. Firmware y PING

- ☐ **1.1** Conecta el módulo A por USB. `pio device list` muestra el puerto. Si no aparece, instala el driver del chip USB de tu placa (CP210x o CH340, según la placa).
- ☐ **1.2** `pio run -e modulo_a -t upload` termina sin errores.
- ☐ **1.3** `pio device monitor` a 115200. Escribe `PING` y pulsa Enter. Respuesta: `PONG DUELO-A 0.1.0` en menos de 1 s. Si el monitor no envía lo que escribes, revisa el fin de línea (verificar con `pio device monitor --help`, opción `--eol`).
- ☐ **1.4** `CAL SHOW` responde `CAL 100.00 -65.00 180.00 0.00 0.00`. Si responde otros valores, hay una calibración guardada en la memoria NVS. Anótala antes de cambiar nada.
- ☐ **1.5** Errores de sintaxis: `HOLA` da `ERR UNKNOWN`; `(3,4` da `ERR FORMAT`; `(21,5)` da `ERR RANGE`.
- ☐ **1.6** Carga el módulo B con `pio run -e modulo_b -t upload`. Responde `PONG DUELO-B 0.1.0`.

**Criterio:** los dos PONG llegan en menos de 1 s y los errores son exactamente los de la lista.

Con los servos desconectados, PING y CAL funcionan igual. Es normal.

---

## Paso 2. Láser

> **Láser clase 3R. No mires el haz**, ni de reojo, ni con lupa, binoculares o cámara. Observa el punto solo en una pared o en una cartulina mate, o en la vista previa de la cámara del celular. Nadie debe estar en la línea del haz.

Preparación: una pared o cartulina mate a 1–2 m. Apunta el láser hacia ahí, con los servos sin brazo o con el brazo en reposo.

- ☐ **2.1** Alimenta el módulo (el USB basta para esta prueba) y espera 30 s sin enviar nada. **Criterio:** no aparece ningún punto en ningún momento.
- ☐ **2.2** Pulsa EN (RST) 10 veces. **Criterio:** 0 de 10 reinicios encienden el láser. Grábalo en cámara lenta si puedes.
- ☐ **2.3** Mantén EN pulsado 5 s. El chip queda en reset y el pin queda flotante, así que el resistor de 10 kΩ lleva la base a masa. Mide con el multímetro entre la base del 2N2222A y GND. **Criterio:** menos de 0,3 V y láser apagado.
- ☐ **2.4** Envía `(11,11)` por el monitor. **Criterio:** el punto aparece y se apaga unos 1,5 s después. La respuesta `OK (11,11)` llega cuando el punto ya se apagó. Mide la duración con el cronómetro o el video: 1,5 s ± 0,2 s.
- ☐ **2.5** Al encender el láser se oye un pitido corto (150 ms).
- ☐ **2.6** STOP durante un disparo. Envía `(20,20)` y, en cuanto veas el punto, envía `STOP`. **Criterio:** el punto se apaga en menos de 0,2 s. El disparo responde `ERR STOP` y luego `OK STOP`.
- ☐ **2.7** Orden durante un disparo. Envía `(20,20)` y, mientras el punto está encendido, envía `PING`. **Criterio:** el PING responde `ERR BUSY` y el disparo termina con `OK (20,20)`.

---

## Paso 3. Servos y calibración

### 3.1 Alimentación

- ☐ Con los servos conectados y sin moverse, la línea de servos da **6,0 V ± 0,3 V** (multímetro).
- ☐ Con láser y zumbador conectados, la salida del convertidor da **5,0 V ± 0,1 V**.
- ☐ Hay **GND común** entre la fuente de 6 V, el convertidor, el ESP32 y los servos. Compruébalo con el multímetro en continuidad.
- ☐ Los condensadores de 1000 µF (junto a los servos) y 470 µF (junto al ESP32) están instalados.
- ☐ Los cables de servo miden 30 cm o menos. Los servos **no** se alimentan desde el pin 5 V del ESP32 (ver `docs/PINOUT.md`).

### 3.2 Recorrido real de cada servo (sin brazo)

El firmware no tiene un comando para mover un servo suelto. Por eso esta prueba se hace con el **tester de servos**. Desconecta el cable de señal del ESP32 mientras usas el tester.

Según `include/config.h`, 500 µs son 0°, 1500 µs son 90° y 2500 µs son 180°. Verifícalo con el servo real: si no llega a 0° o a 180° con esos pulsos, anótalo.

- ☐ **Pan (MG996R):** recorre el servo de un extremo a otro. Debe llegar al menos de **30° a 150°** sin topar la mecánica ni zumbar. Mide con el transportador en el horn. Anota el mínimo y el máximo: `____° a ____°`.
- ☐ **Tilt (MG90S):** debe cubrir al menos de **115° a 165°** sin tope ni zumbido. Anota: `____° a ____°`.

Por qué esos rangos: el pan necesita ±57° más el sobrepaso de 2°, así que 31° a 149°. El tilt necesita de 30° a 72° bajo la horizontal, que son 120° a 162° de servo, más 2° de sobrepaso.

- ☐ **Brazo centrado.** Al arrancar, los servos están sueltos (el firmware los `detach`). Al primer disparo, el firmware supone que están en 90° y 90°. Si el brazo no está ahí, el primer movimiento es un salto. Centra el brazo a mano antes de encender el módulo con los servos conectados.

### 3.3 Signos de los servos

Con `PAN_SIGN = +1`, subir el ángulo de servo gira el rayo a la derecha, vista desde la estación mirando al tablero. Con `TILT_SIGN = +1`, subir el ángulo baja el rayo.

- ☐ **Pan:** `(1,11)` cae a la izquierda del centro y `(20,11)` cae a la derecha. Si están al revés, cambia `PAN_SIGN` a `-1.0f` en `include/config.h`, recompila y vuelve a cargar.
- ☐ **Tilt:** `(11,1)` (la fila más cercana a la estación) cae sobre el tablero, cerca del borde posterior. `(11,20)` (la fila lejana) cae cerca del borde delantero. Si el rayo sube o sale del tablero, **apaga el módulo antes** de corregir. Luego cambia `TILT_SIGN` a `-1.0f` y recompila.

Los signos son constantes de compilación. `CAL SET` no los cambia.

### 3.4 Ángulo del servo con el rayo horizontal (`TILT_HORIZ_SERVO_DEG`)

Según `geometry.h`, el ángulo de tilt es `TILT_HORIZ + TILT_SIGN × tilt + tiltTrim`. El valor 90 supone que, con el servo en 90°, la carcasa del láser queda horizontal. Ese supuesto depende de cómo montes el horn.

- ☐ Con el tester, lleva el servo tilt a 1500 µs (90°) y monta el láser en el brazo.
- ☐ Apoya el celular con la app de inclinómetro sobre la carcasa del láser. Ajusta el brazo hasta leer 0° (±1°).
- ☐ Lee el ángulo real del servo en el horn. **Criterio:** 90° ± 3°.
- ☐ Si la diferencia es mayor que 3°, cambia `TILT_HORIZ_SERVO_DEG` en `include/config.h` por el valor medido y recompila. Así `tiltTrim` queda casi en 0 para la calibración fina.
- ☐ **Verificación con el firmware:** envía `(11,11)`. El rayo debe quedar a 46,6° bajo la horizontal (servo 136,6°). Después del `OK`, los servos siguen reteniendo; apoya el celular sobre la carcasa **con el láser apagado** y mide. **Criterio:** 46,6° ± 2°.

### 3.5 Posición real de la estación (xs, ys, h)

Mide desde la esquina posterior-izquierda de la matriz, que es el origen (1,1).

- **xs:** distancia en X desde el origen hasta el eje de pan (el centro del giro). Referencia: 100 mm.
- **ys:** distancia en Y desde el borde posterior hasta el eje de pan. Negativo si el eje queda detrás del borde. Referencia: -65 mm.
- **h:** altura del eje de tilt sobre la superficie de la matriz. Referencia: 180 mm.

- ☐ Mide con regla y plomada (baja la plomada desde el eje hasta el plano de la matriz). Precisión de 1 mm. Anota los tres valores.
- ☐ Si difieren de la referencia en 3 mm o más, aplícalos con `CAL SET` en el paso 3.6. **No** cambies `config.h` para esto.

Rangos aceptados por `CAL SET`: x entre -200 y 400; y entre -300 y 400; h entre 50 y 400 (mm). Los trims van de -30 a 30.

### 3.6 Calibración con 5 cruces

Marca en el tablero los centros de las 5 celdas del TEST. El centro de la celda (x,y) está en `((x − 0,5) × 10, (y − 0,5) × 10)` mm, desde la esquina posterior-izquierda de la matriz:

| Celda | Centro (mm) |
|---|---|
| (1,1) | (5, 5) |
| (20,1) | (195, 5) |
| (20,20) | (195, 195) |
| (1,20) | (5, 195) |
| (11,11) | (105, 105) |

Procedimiento:

- ☐ **Primer intento:** `CAL SET xs ys h 0 0` con los valores que mediste en 3.5. `CAL SHOW` debe devolverlos.
- ☐ Dispara las 5 celdas, una por una, esperando el `OK` de cada una. Mide con la regla la distancia del centro del punto a la cruz. Anota el error en X (+ a la derecha) y en Y (+ hacia el frente).
- ☐ **Objetivo:** |error| ≤ 2 mm en las 5 posiciones.

Cómo leer el error:

- **Mismo error en las cinco celdas:** es un desplazamiento parejo, y se corrige con trims. `panTrim` mueve el punto en X: cada grado mueve unos 2 mm en las celdas cercanas y unos 5 mm en las lejanas. `tiltTrim` mueve el punto en Y: entre 4,5 y 10,6 mm por grado (más en las celdas lejanas). Usa pasos de 0,5°.
- **Error que crece con la distancia o cambia de signo entre celdas:** la posición medida de la estación está mal. Vuelve a 3.5 y mide otra vez.
- **Antes de corregir, prueba el sentido de cada trim.** Pon `panTrim` en +1,0, dispara `(11,11)` y mira hacia dónde se mueve el punto. No supongas el signo.
- **Trims pequeños.** Tienen margen de ±30 en `CAL SET`, pero el límite de 30° de tilt se comprueba solo con el ángulo nominal (ver paso 8.6). Un trim grande puede mandar el rayo fuera del tablero.

- ☐ Cuando las 5 celdas están dentro de ±2 mm: `CAL SAVE` → `OK SAVE`.
- ☐ Apaga y enciende el módulo. `CAL SHOW` devuelve los mismos valores, y las 5 celdas siguen dentro de ±2 mm.

> `CAL RESET` borra la calibración guardada y vuelve a los valores por defecto. Anota los valores antes de usarlo.

---

## Paso 4. Aproximación desde un solo lado y asentamiento

El firmware se acerca al punto siempre por el mismo lado, con un sobrepaso de 2°, para compensar las holguras de los engranes. Después espera 300 ms antes de encender el láser.

- ☐ **4.1 Aproximación.** Desde cinco celdas de partida distintas, `(1,1)`, `(20,20)`, `(1,11)`, `(20,11)` y `(11,1)`, envía `(11,11)` después de cada una. Mide el centro del punto en cada caso. **Criterio:** la diferencia entre la medida máxima y la mínima es **≤ 1 mm**.
- ☐ **4.2 Asentamiento.** Dispara `(20,20)` y observa el punto durante los 1,5 s. **Criterio:** no se mueve más de **1 mm**. El video en cámara lenta ayuda.
- ☐ **4.3 Repetibilidad.** Haz 10 disparos alternando `(1,1)` y `(20,20)`. **Criterio:** el punto no baila (no hay vaivén visible durante el láser) y no aparece ningún `ERR`.

Si el punto baila:

1. Sube `SETTLE_MS` de 300 a 500 en `config.h` y recompila.
2. Si sigue bailando, baja `MAX_STEP_DEG` de 2 a 1. Es más lento y más suave.
3. Revisa la alimentación de 6 V: si cae bajo carga, los servos tiemblan.

Repite 4.1 a 4.3 después de cada cambio.

---

## Paso 5. TEST de 5 posiciones, tres veces seguidas

`TEST` dispara `(1,1)`, `(20,1)`, `(20,20)`, `(1,20)` y `(11,11)`, con 1,5 s entre disparos. Dura unos 20 a 30 s.

La celda (x,y) ocupa de (x − 1) × 10 a x × 10 mm, en X y en Y. **Criterio:** en cada una de las 3 vueltas, las 5 posiciones caen dentro de su celda (5 de 5), es decir, 15 de 15 en total.

- ☐ Vuelta 1 — 5 de 5
- ☐ Vuelta 2 — 5 de 5
- ☐ Vuelta 3 — 5 de 5

Anota en la tabla de medidas, por cada posición, "ok" o "fuera: +X mm", donde X es la distancia del punto al borde de su celda.

Si falla:

- Anota cuántas veces falló y por cuántos mm.
- Si aparece `TEST ABORT` seguido de un error, mira el código: `ERR RANGE` o `ERR LIMIT` indican que la calibración sacó el apuntado de sus límites. `ERR STOP` indica que alguien pulsó STOP.
- Si las fallas son de pocos mm, vuelve a 3.6. Si son de más de una celda, vuelve a 3.5.

---

## Paso 6. Bluetooth y la app

- ☐ **6.1** Sin el puente MAINT, el módulo arranca en modo Bluetooth. Empareja `DUELO-A` con el celular Android (ver `docs/APP_INVENTOR.md`, punto 1).
- ☐ **6.2** Desde la app: Conectar → `PONG DUELO-A 0.1.0`.
- ☐ **6.3** Desde la app, dispara `(1,1)` y `(20,20)`. Ambos responden `OK`. Haz 10 disparos seguidos sin desconectarse.
- ☐ **6.4** Desde la app, pulsa TEST. Llegan 5 `OK` y `TEST DONE`.
- ☐ **6.5** Desconecta y vuelve a conectar desde la app. Responde `PONG` otra vez.
- ☐ **6.6** Apaga y enciende el módulo. La app vuelve a conectar al pulsar Conectar.
- ☐ **6.7** Haz el plan de pruebas de `docs/APP_INVENTOR.md` (sección 7). Al menos 8 casos aprobados.

---

## Paso 7. Modo mantenimiento (Wi-Fi)

El modo se decide **al arrancar**. Por eso el puente va antes de encender o reiniciar.

- ☐ **7.1** Con el módulo apagado, pon un puente entre el pin MAINT (GPIO 26) y GND. Enciende el módulo, o pulsa EN con el puente puesto.
- ☐ **7.2** Aparece la red `DUELO-A-MANT` (o `DUELO-B-MANT`). Conéctate desde el celular o el PC. La clave está en `include/config.h`; no la copies en el informe.
- ☐ **7.3** Abre `http://192.168.4.1/` en el navegador. Carga la interfaz web.
- ☐ **7.4** Desde la web, PING responde `PONG ...`, y CAL SHOW devuelve lo mismo que por USB.
- ☐ **7.5** Quita el puente y reinicia. Vuelve el Bluetooth y ya no aparece la red de mantenimiento.
- ☐ **7.6** Por USB, PING responde en los dos modos.

---

## Paso 8. Seguridad (léelo antes del paso 2)

- ☐ **8.1 Clase del láser.** Lee la etiqueta del módulo KY-008 y anota la longitud de onda y la potencia máxima. Para clase 3R, la potencia debe ser de 5 mW o menos. Si no puedes confirmarlo, trátalo como más peligroso: no lo enciendas sin gafas ni sin control.
- ☐ **8.2 No mirar el haz.** Nadie se pone en la línea del haz. No apuntes a personas, a animales ni a los ojos. Observa el punto solo en la pared, la cartulina o la vista previa de la cámara.
- ☐ **8.3 Sin reflejos.** El rayo no pasa sobre espejos, vidrio, metal pulido, pantallas ni objetos brillantes. El tablero es de superficie mate (cartulina o pintura mate).
- ☐ **8.4 Tilt de 30° o más.** Con el inclinómetro en la carcasa, dispara `(20,20)` y `(1,20)`. El ángulo debe ser de 30° o más. Con los valores por defecto, la celda (20,20) está a 33,0°, así que el margen es de solo 3°.
- ☐ **8.5 El rayo no sale del tablero.** Con el tablero montado, dispara las 5 celdas del TEST y las cuatro esquinas. El punto cae siempre sobre el tablero: no en la mesa, no en el suelo, no en la pared.
- ☐ **8.6 Trims y límite de tilt.** Tras calibrar, comprueba de nuevo 8.4. El firmware limita el ángulo nominal de tilt a 30°, pero suma los trims después. Un `tiltTrim` negativo de más de 3° lleva el rayo de (20,20) por debajo de 30°. Si tu calibración necesita un trim así, reconsidera el montaje antes de forzar el trim.
- ☐ **8.7 Parada.** `STOP` apaga el láser de inmediato (paso 2.6). Si algo sale mal, quita la alimentación del módulo (el USB o el adaptador).
- ☐ **8.8 Gafas.** Usa gafas de protección adecuadas a la longitud de onda anotada en 8.1 si vas a trabajar con el haz a la altura de los ojos.
- ☐ **8.9 Servos.** Mantén los dedos fuera del brazo. Los servos ganan fuerza al encenderse y el brazo se mueve al disparar.
- ☐ **8.10 Láser apagado en reposo.** Confirmado en los pasos 2.1 a 2.3.

---

## Tabla de medidas

Rellena esta tabla al terminar. Es la evidencia de que el módulo está listo.

| Medida | Criterio | Medido | ☐ |
|---|---|---|---|
| Fecha, módulo (A o B), versión de firmware | — | | |
| Tensión en la línea de servos | 6,0 V ± 0,3 V | | |
| Tensión de 5 V con láser y zumbador | 5,0 V ± 0,1 V | | |
| Pan: recorrido libre (mín. a máx.) | ≤ 30° a ≥ 150° | | |
| Tilt: recorrido libre (mín. a máx.) | ≤ 115° a ≥ 165° | | |
| `PAN_SIGN` / `TILT_SIGN` finales | según 3.3 | | |
| Láser apagado tras 10 reinicios | 0 de 10 | | |
| Base del 2N2222A con EN pulsado | < 0,3 V | | |
| Duración del láser en un disparo | 1,5 s ± 0,2 s | | |
| Ángulo de servo con el rayo horizontal | 90° ± 3° | | |
| Ángulo medido del rayo en (11,11) | 46,6° ± 2° | | |
| `xs`, `ys`, `h` medidos (ref. 100, -65, 180) | medidos y aplicados con `CAL SET` si difieren ≥ 3 mm | | |
| `panTrim` / `tiltTrim` finales | valor absoluto pequeño (≤ 5°) | | |
| Error máximo en las 5 cruces tras calibrar | ≤ 2 mm | | |
| Diferencia de aproximación desde distintos lados | ≤ 1 mm | | |
| Movimiento del punto durante el láser | ≤ 1 mm | | |
| TEST: aciertos (de 15) | 15 de 15 | | |
| TEST: fallos y desviación máxima | 0 fallos | | |
| Ángulo mínimo del rayo medido (20,20) | ≥ 30° (esperado 33°) | | |
| Clase y potencia del láser (etiqueta) | 3R, ≤ 5 mW | | |
| `PING` y `CAL SHOW` tras reinicio | igual que antes | | |
| Plan de pruebas de la app (casos aprobados) | ≥ 8 | | |
| Modo mantenimiento Wi-Fi (paso 7) | funciona | | |
