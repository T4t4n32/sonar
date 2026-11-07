# Protocolo (contrato compartido)

Texto, **una línea por mensaje** (`\n`; se tolera `\r\n`). Máximo 64 caracteres. No distingue mayúsculas de minúsculas.
Lo habla igual el **Bluetooth** (SPP), el **USB** (115200) y el **Wi-Fi de mantenimiento** (`GET /cmd?l=<línea URL-codificada>` → respuesta en texto plano, una línea por respuesta).

## Celular → módulo

| Línea | Efecto | Respuestas |
|---|---|---|
| `(x,y)` | dispara a la celda; **los paréntesis son obligatorios**; x e y enteros 1–20; se aceptan espacios (`( 12 , 7 )`) | `OK (x,y)` al terminar el disparo · `ERR RANGE` · `ERR FORMAT` · `ERR LIMIT` · `ERR BUSY` · `ERR STOP` |
| `TEST` | rutina de 5 posiciones: (1,1) (20,1) (20,20) (1,20) (11,11) | `TEST START`, luego un `OK (x,y)` por posición, y `TEST DONE`. Si falla: `TEST ABORT` + el error |
| `STOP` | apaga el láser de inmediato y aborta | `OK STOP` |
| `PING` | comprobación | `PONG <nombre> <versión>` (p. ej. `PONG DUELO-A 0.1.0`) |
| `MARK HIT` / `MARK MISS` | el dueño marca el resultado: `HIT` enciende el LED 2 s | `OK MARK` |
| `CAL SHOW` | muestra la calibración: `x y h` = posición de la estación en mm; los trims, en grados; **2 decimales** | `CAL x y h panTrim tiltTrim` |
| `CAL SET x y h panTrim tiltTrim` | cambia la calibración en RAM (5 números; rangos: x −200…400, y −300…400, h 50…400, **trims −10…10°**) | `OK CAL` · `ERR RANGE` · `ERR FORMAT` |
| `CAL SAVE` | guarda en NVS | `OK SAVE` · `ERR STORE` |
| `CAL RESET` | vuelve a los valores por defecto y borra NVS | `OK RESET` |

Errores de sintaxis: `ERR EMPTY` (línea vacía), `ERR TOOLONG`, `ERR UNKNOWN` (palabra desconocida).

## Reglas

- **Un teléfono por módulo** (el Bluetooth clásico acepta uno a la vez). El **rival** se conecta al módulo que recibe el disparo.
- El módulo atiende **una orden a la vez**; si llega otra durante un disparo responde `ERR BUSY` (excepto `STOP`, que siempre se atiende).
- El láser **solo** está encendido entre el fin del movimiento (+ espera de asentamiento) y el fin del tiempo de permanencia.
- Origen de coordenadas: **(1,1)** = esquina posterior-izquierda de la matriz (la más cercana a la estación), x → derecha, y → hacia el frente.

## Modos

- **Juego:** solo Bluetooth (`DUELO-A` / `DUELO-B`).
- **Mantenimiento:** pin `MAINT` a GND al arrancar → red Wi-Fi `DUELO-A-MANT` (clave en `include/config.h`), `http://192.168.4.1/` sirve la interfaz web; USB siempre disponible.
- El pulsador `BTN_TEST` lanza la rutina `TEST` en cualquier modo.

## Detalles y casos límite

- **STOP** apaga el láser **de inmediato** (escribe el pin directamente) y siempre se atiende, aun con el módulo ocupado. El disparo interrumpido responde después `ERR STOP`; el cliente ve `OK STOP` y luego `ERR STOP`.
- **Ocupado:** mientras dura un disparo, un `TEST` o un `MARK HIT`, cualquier otra orden (incluido `PING`) recibe `ERR BUSY`; la página web lo interpreta como "conectado, ocupado". `MARK HIT` responde `OK MARK` **al terminar** sus 2 s.
- **Wi-Fi de mantenimiento:** `GET /cmd?l=...` no responde hasta que termina la orden (un disparo ≈ 2 s, un `TEST` ≈ 12 s) y el servidor atiende una petición a la vez, así que **el `STOP` por Wi-Fi no puede interrumpir un disparo**; por USB y por Bluetooth sí. Los `ERR` por HTTP responden 200.
- **Sintaxis:** los 64 caracteres no cuentan el salto de línea; palabra conocida con argumentos de más o de menos (`PING x`, `MARK`) → `ERR FORMAT`; subcomando desconocido (`CAL FOO`, `MARK FOO`) → `ERR UNKNOWN`; `(+5,6)` es válido y `(-1,5)` da `ERR RANGE`; un error de sintaxis gana a uno de rango (`(0,a)` → `ERR FORMAT`).
- **TEST:** `STOP` durante el `TEST` → `TEST ABORT` + `ERR STOP`. `CAL RESET` con fallo de NVS → `ERR STORE`.
- **Tiempos:** el láser permanece encendido ≈ `LASER_ON_MS` + `BEEP_MS` (el pitido ocurre con el láser encendido) y hay una pausa `TEST_GAP_MS` tras **cada** posición del `TEST`, también tras la última.
- **Calibración por defecto:** ninguna celda da `ERR LIMIT` (pan máx. 53,6° frente a 57°; tilt 33,0°–68,7° frente a 30°–72°); solo aparece con una calibración desplazada.

## Protocolo v2 (compatible hacia atrás; 2026-11-07)

Todo lo anterior sigue igual. Un cliente v1 no necesita nada de esto. Diseño y motivos: `docs/ARQUITECTURA_UNIVERSAL.md`.

| Línea | Efecto | Respuestas |
|---|---|---|
| `HELLO` | el módulo se presenta, para que la página se adapte | `HELLO SONAR 2 <fw> <nombre> <modo> <caps>` (`modo` = `BT` o `WIFI`; `caps` = lista con comas sin espacios, p. ej. `ws,stream`, o `-`) |
| `MODE` | consulta el modo con el que arrancó | `MODE BT` / `MODE WIFI` |
| `MODE BT` / `MODE WIFI` | pide cambiar de modo; el módulo guarda la preferencia y **reinicia** tras responder (~2 s) | `OK MODE <modo>` · `ERR STORE` si no pudo guardarla · `ERR UNKNOWN` si esta versión no lo soporta |
| `ARM` | consulta el armado remoto del láser (**solo físico**: ninguna orden lo activa; se pulsa el botón del módulo) | `ARM NOTREQ` (no se exige) · `ARM OFF` · `ARM ON <segundos>` |

- Con armado exigido (modo `WIFI`) y vencido, `(x,y)` y `TEST` responden **`ERR DISARMED`** sin mover nada. `STOP`, `PING`, `HELLO`, `MODE`, `ARM`, `CAL …` y `MARK …` nunca se bloquean.
- `MODE X` con `X` distinto de `BT`/`WIFI` → `ERR UNKNOWN`; argumentos de más en `HELLO`/`ARM`/`MODE BT WIFI` → `ERR FORMAT`.
- Líneas de evento no solicitadas (prefijo `EVT `) llegarán con el transporte WebSocket (aún no implementado).
