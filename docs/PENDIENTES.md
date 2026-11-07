# Pendientes

Lista viva de Lucky. Estado al 2026-11-06 (web rehecha); lo anterior sigue vigente.

## Hecho y verificado

- [x] `pio test -e native` → **48/48** (MinGW instalado con scoop).
- [x] `pio run -e modulo_a` y `-e modulo_b` → SUCCESS (RAM 18,0 %, Flash 50,4 %).
- [x] `tools/sim_phone.py selftest` → **20/20** por HTTP y por TCP contra `tools/fake_device.py`.
- [x] Página `web/index.html` abierta en un navegador a 375×812 contra el simulador: conecta, selecciona (20,20), dispara y registra `→ (20,20)` / `← OK (20,20)`.
- [x] **Trims limitados a ±10°** (`CAL SET` → `ERR RANGE` si se pasa): con el límite de tilt nominal de 33,0° el rayo nunca queda por encima de la horizontal. Cambiado en `controller.cpp`, `controller.h`, pruebas, simulador y `PROTOCOLO.md`.
- [x] Aclaraciones de protocolo cerradas en `docs/PROTOCOLO.md` (STOP inmediato, ocupado, Wi-Fi, casos límite, tiempos). `PING` ocupado se queda como `ERR BUSY`.
- [x] Archivo sobrante `geometry.d` borrado.

- [x] **Web «SONAR · Batalla Naval» rehecha** (2026-11-06): radar con barrido y eco, disparo en 2 toques, TEST con 5 objetivos, calibración con rangos, bitácora descargable, modo simulado, tema claro/oscuro, accesible por teclado. `tools/e2e_web.py` → 29/29, capturas en `registro/2026-11-06/`. Diseño: `docs/DISENO_WEB.md`. Contra el **simulador**; no contra un ESP32 real.
- [x] `sim_phone.py selftest` → 20/20 (el «0/19» que se reportó era un simulador viejo colgado en el puerto 8080).

## Pendiente con hardware (nada de esto está probado en un ESP32 real)

- [ ] Que la inicialización estática del láser deje el pin en LOW **antes de `setup()`**; la forma del pulso PWM de los servos; el emparejamiento Bluetooth (PIN heredado, 1234 por defecto); la NVS.
- [ ] `docs/BRINGUP.md` completo: calibración, aproximación desde un lado, tiempo de asentamiento, **TEST 5/5 tres veces seguidas**.
- [ ] Confirmar la clase del KY-008 por la etiqueta del módulo (no asumir 3R).

## Pendiente de la web (solo se puede comprobar con el ESP32 real)

- [ ] Que el ESP32 sirva los ~43 KB de `index.html` por `send_P` sin cortar (el simulador lo sirve sin problema).
- [ ] Que el PING cada 5 s no se mezcle con un disparo: la página no lo envía mientras hay una orden suya en curso, pero otro cliente sí podría.
- [ ] Probar la web en el celular real (Android/Chrome) por el Wi-Fi `DUELO-A-MANT`: arrastre sobre el radar, vibración y sonido.
- [ ] Ajustar los textos si el nombre definitivo del proyecto cambia (hoy: «SONAR · Batalla Naval»; el Wi-Fi sigue siendo `DUELO-A-MANT`).

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

## Estado al 2026-11-07 (tarde) — ver `docs/ARQUITECTURA_UNIVERSAL.md`

- [x] Repositorio pasado a **privado** (estuvo público 4→7-nov; 15 clonaciones únicas). Publicación **programada** el 2026-11-24 20:00 (`tools/publicar.py`, tarea «SONAR Publicar 24-nov»): solo publica sin hallazgos ALTA y con todo subido.
- [x] Protocolo v2 en el núcleo (`HELLO`, `MODE`, `ARM`, `ERR DISARMED`): **52/52** pruebas nativas; simulador y selftest **24/24**; `docs/PROTOCOLO.md` actualizado. `HELLO` ya responde el modo real en el firmware; `MODE`/`ARM` quedan sin manejador (v1 intacto, para el control 1).
- [x] `docs/CONTROL1.md`: lista para el domingo 8-nov. `pio run -e modulo_a` compila (flash 51,4 %).
- [x] APK v0 (`app/`, Capacitor): `com.sonar.batallanaval`, permisos de Bluetooth, 4,1 MB; **solo envuelve la web**, sin transporte Bluetooth todavía.
- [x] Spike S1: servidor asíncrono + WebSocket + DNS + BluetoothSerial compilan juntos (RAM 18,0 %, flash 50,1 %).
- [ ] **Decisión de Sebas y Jader:** nombres completos en `docs/` y en el plano (ver `registro/preflight-2026-11-07.md`).
- [ ] Mover `WIFI_PASS_MAINT` a `include/secrets.h` (+ `secrets.example.h`) y cambiar la clave en los módulos reales.
- [ ] Commit y push al repositorio **privado** (sin eso, la publicación programada se detiene a propósito).
- [ ] F1 firmware: modo guardado en NVS + `MODE`, armado físico, `WsTransport` + portal cautivo en un entorno aparte (`modulo_a` no se toca antes del control 1).
- [ ] F1 web: transporte WebSocket (TEST en vivo, STOP que corta) y transporte Bluetooth nativo para el APK.
- [ ] Hardware: spikes S2-S5 (heap, portal en A04s/13C/iPhone, emparejamiento sin PIN, latencia de STOP).
- [ ] El plugin de Bluetooth añadió `ACCESS_COARSE_LOCATION` sin límite de versión: revisar si se puede quitar.
