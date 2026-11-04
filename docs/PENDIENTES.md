# Pendientes

Lista viva de Lucky. Estado al 2026-11-03, después de integrar los 4 frentes.

## Hecho y verificado

- [x] `pio test -e native` → **48/48** (MinGW instalado con scoop).
- [x] `pio run -e modulo_a` y `-e modulo_b` → SUCCESS (RAM 18,0 %, Flash 50,4 %).
- [x] `tools/sim_phone.py selftest` → **20/20** por HTTP y por TCP contra `tools/fake_device.py`.
- [x] Página `web/index.html` abierta en un navegador a 375×812 contra el simulador: conecta, selecciona (20,20), dispara y registra `→ (20,20)` / `← OK (20,20)`.
- [x] **Trims limitados a ±10°** (`CAL SET` → `ERR RANGE` si se pasa): con el límite de tilt nominal de 33,0° el rayo nunca queda por encima de la horizontal. Cambiado en `controller.cpp`, `controller.h`, pruebas, simulador y `PROTOCOLO.md`.
- [x] Aclaraciones de protocolo cerradas en `docs/PROTOCOLO.md` (STOP inmediato, ocupado, Wi-Fi, casos límite, tiempos). `PING` ocupado se queda como `ERR BUSY`.
- [x] Archivo sobrante `geometry.d` borrado.

## Pendiente con hardware (nada de esto está probado en un ESP32 real)

- [ ] Que la inicialización estática del láser deje el pin en LOW **antes de `setup()`**; la forma del pulso PWM de los servos; el emparejamiento Bluetooth (PIN heredado, 1234 por defecto); la NVS.
- [ ] `docs/BRINGUP.md` completo: calibración, aproximación desde un lado, tiempo de asentamiento, **TEST 5/5 tres veces seguidas**.
- [ ] Confirmar la clase del KY-008 por la etiqueta del módulo (no asumir 3R).

## Mejoras decididas pero no hechas

- [ ] **Comandos de calibración:** no hay forma de mover un servo suelto (la guía exige un probador de servos externo). Evaluar `SERVO <pan> <tilt>` (grados de servo, recortados al rango seguro, láser forzado a OFF) y `LASER ON|OFF` con tope de 5 s, solo por USB o en modo mantenimiento.
- [ ] **Arranque:** los servos quedan sueltos y el firmware asume 90°/90°; el primer disparo puede dar un salto si el brazo no está centrado. Opciones: comando `CENTER` o rampa lenta en el primer movimiento.
- [ ] `TILT_HORIZ_SERVO_DEG` y `tiltTrim` suman lo mismo (redundantes): dejar uno de fábrica y el otro como ajuste fino.
- [ ] La pausa `TEST_GAP_MS` también se espera tras la última posición del TEST (1,5 s de más).
- [ ] El pulsador `BTN_TEST` solo reporta el resultado por USB.
- [ ] **STOP por Wi-Fi** no interrumpe un disparo (`WebServer` de Arduino atiende una petición a la vez): solo si se necesita, pasar a un servidor asíncrono.
- [ ] El paquete `framework-arduinoespressif32` instalado no trae `variants/`; el frente 2 añadió una copia local (`variants/esp32/pins_arduino.h` + `board_build.variants_dir`). Si se repara el paquete (`pio pkg install -g -f`), se puede borrar.
- [ ] La rama de `ledc*` para Arduino-ESP32 3.x no está compilada ni probada (el instalado es 2.0.17).

## Guías

- [ ] `docs/APP_INVENTOR.md`: verificar en App Inventor los bloques marcados *verificar* (`ReceiveTextUntilDelimiter`, `BytesAvailableToReceive`, `AddressesAndNames`, formato de `Connect`, salto de línea, trim/contains/split, `PositionChanged` del Slider, `BeforePicking`, `Vibrate`, nombre exacto de `DelimiterByte`).
- [ ] `docs/BRINGUP.md`: comprobar contra el firmware real los puntos *verificar* (nombre del puerto, eco del monitor, fin de línea).
- [ ] Un `ERR` durante un `TEST` deja a la app sin modo: aclararlo en la guía.
