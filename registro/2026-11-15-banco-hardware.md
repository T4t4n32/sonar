# Banco de pruebas con ESP32 real — 2026-11-15 (Lucky, heat-lucky)

Primera sesión con el ESP32 clásico (WROOM-32) físico conectado por USB (`/dev/ttyUSB0`, CP2102). PlatformIO 6.2.0. Repo clonado en `/home/t4t4n32/Documents/sonar` (Heat), HEAD en `ac5ffaa` al empezar.

## 1. Bug encontrado y arreglado: `tools/servo_centrar` no movía los servos

**Síntoma:** con `servo_centrar` cargado, el comando `c` (centrar) respondía "Centrado a 90 deg." y el estado correcto por serie, pero el servo físico no se movía. `u <us>` (pulso directo) sí funcionaba siempre.

**Descartado en el camino** (cada uno confirmado antes de seguir al siguiente):
1. Puerto/hardware: `/dev/ttyUSB0`, CP2102, detectado bien por `pio device list`.
2. GND común entre la fuente de 6 V y el ESP32 — confirmado con continuidad.
3. Continuidad de GPIO18↔pan y GPIO19↔tilt a los cables de señal — las dos, OK.
4. Alimentación a 6 V en los servos — confirmada.
5. Los dos servos probados **sanos** en un CCPM Servo Consistency Master externo (tester de servos): se mueven bien con su propia fuente y señal.
6. Atasco mecánico — descartado (giran libres a mano, no vibran, no se calientan).

**Causa real:** `moveTo()` en `tools/servo_centrar/main.cpp` solo llamaba a `writeUs()` (el que manda el pulso PWM real) cuando el servo aún no estaba activado (`!s.on`), o mientras el bucle de rampa tenía un paso pendiente. El comando `c` siempre apunta a 90°; en cuanto el servo llegaba ahí (o ya arrancaba ahí, como tilt por defecto), repetir `c` no volvía a tocar el pin — el firmware imprimía éxito sin mandar ningún pulso real.

**Fix:** una línea — `moveTo()` ahora siempre reenvía el pulso actual antes de decidir si hay un paso que dar, sin importar `s.on` ni si el ángulo ya es el mismo. Probado físicamente: `c`, `p <ángulo>`, `t <ángulo>` mueven el servo cada vez, no solo la primera.

**Commit:** `c43baaa` — `fix(servo_centrar): mandar siempre el pulso en moveTo(), no solo al primer attach` (subido a `origin/main`).

**No se tocó `lib/core/controller.cpp`** (usado por `modulo_a`/`modulo_b`, el firmware de juego real): su `fire()` ya reescribe el ángulo explícitamente en cada reattach tras un reset o arranque, así que no tiene la misma severidad de bug (el caso "mismo ángulo dos veces seguidas sin reset" es raro, no garantizado como con `c`). Además el set de pruebas nativas (`test/test_core`) tiene conteos exactos de escrituras de servo que asumen el comportamiento actual; tocarlo sin evidencia real de falla habría roto esas pruebas a cambio de nada comprobado.

## 2. Resets espontáneos del ESP32 — causa: fuente/batería débil, no firmware

Durante toda la sesión aparecieron `POWERON_RESET` espontáneos (banner de arranque completo reapareciendo sin ningún comando nuevo), intermitentes. Diagnosticados como **no relacionados** con el bug de arriba ni con el firmware: ocurrían incluso en reposo, y con distinta frecuencia según el estado de la fuente.

**Confirmado 2026-11-15 (tarde):** Sebastián reportó que la pila/fuente de los servos había bajado ~1 V. Justo después, un `c` disparó un reset inmediato y reproducible. Conclusión: la fuente actual no sostiene la corriente de arranque del servo (hasta 1,5 A en marcha) sin hundirse lo suficiente para resetear el ESP32 — caída de tensión compartida, no un problema de GND, de cableado ni de firmware.

**Pendiente de compra:** fuente de 6 V dedicada (adaptador de pared ≥2 A, o 4×AA NiMH recargables). **Descartado expresamente: una pila de 9 V** — supera el máximo del MG996R (7,2 V, riesgo de sobrevoltaje/quemarlo) y tiene aún menos capacidad de corriente sostenida que la fuente actual débil, empeorando justo el síntoma que se quiere arreglar. Detalle en `docs/02-electronica/PINOUT.md`.

## 3. `modulo_a` (firmware de juego) — primera prueba en hardware real

- `pio run -e modulo_a -t upload` → SUCCESS (RAM/flash dentro de lo esperado).
- `PING` por USB → `PONG SONAR-A 0.1.0`. Protocolo vivo confirmado por primera vez en hardware real (antes solo probado contra el simulador).
- Conexión Bluetooth con la App (APK) real — conectó bien, estable, sin resets durante la conexión.
- Con los servos ya conectados y alimentados: **se mueven correctamente comandados desde la App** vía Bluetooth real (antes solo probado en simulador/web).
- `TEST` por USB → secuencia completa de 5 posiciones (`(1,1) (20,1) (20,20) (1,20) (11,11)`), **TEST DONE**, sin resets esa corrida. El láser debía encender ~1,5 s en cada una (confirmar visualmente con Sebastián si quedó pendiente).

Esto cierra buena parte de "Control 1 con el hardware" de `docs/ESTADO.md` §6 (Bluetooth real + PING sí verificados; falta la precisión 5/5 dentro de 1 cm en una cuadrícula impresa real, que es un test aparte, más riguroso).

## 4. Conexiones documentadas/propuestas (ver `docs/02-electronica/PINOUT.md`, actualizado hoy)

- **Interruptor general**: mecánico, en serie con la entrada de 6 V, sin GPIO.
- **BTN_TEST** (ya existía en `config.h`): GPIO25 a GND, pull-up interno, sin resistencia externa.
- **Láser KY-008**: GPIO23 → 1 kΩ → base 2N2222A; 10 kΩ base-GND; emisor-GND; colector al GND del láser; VCC del láser a 5 V. **Aún no armado físicamente** (Sebastián confirmó que no tiene el transistor ni las resistencias todavía — pendiente de compra antes de probar el láser con su propio interruptor de GPIO; el `TEST` de hoy usó el camino ya cableado de fábrica, a confirmar).
- **Matriz LED decorativa (WS2812B)**, propuesta nueva: GPIO4 reservado, solo decorativa (feedback visual), **sin código, sin implementar**. Diferida a propósito: el propio análisis del proyecto (`docs/00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md`) ya había descartado matrices electrónicas por costar tiempo sin sumar puntos de rúbrica. Sebastián decidió priorizar lo que sí califica (test 5/5, app, prueba con contrincante) y dejar la matriz solo si sobra tiempo después del 20-nov.

## 5. Pendientes que quedan abiertos

- [ ] Confirmar si el láser prendió visualmente en las 5 posiciones del `TEST` de hoy.
- [ ] Comprar/armar fuente de 6 V dedicada para los servos (no pila de 9 V, no la pila actual ya débil).
- [ ] Comprar transistor 2N2222A + resistencias de 1 kΩ y 10 kΩ para el circuito del láser (confirmar si ya hay uno de fábrica distinto cableado en el banco actual).
- [ ] Precisión real 5/5 dentro de 1 cm en una cuadrícula impresa (Control 1 completo, pendiente con hardware real).
- [ ] Matriz LED decorativa: sin fecha, solo si sobra tiempo tras el 20-nov.
