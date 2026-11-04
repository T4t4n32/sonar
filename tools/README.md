# Herramientas de prueba (sin hardware)

Solo biblioteca estándar de Python 3 (`python`). `pyserial` es opcional (ver `requirements.txt`).

| Archivo | Qué es |
|---|---|
| `fake_device.py` | Módulo **simulado**: sirve `web/index.html` y el protocolo de `docs/PROTOCOLO.md` por HTTP (y TCP opcional). |
| `sim_phone.py` | "Celular" de línea de comandos: `fire`, `test`, `ping`, `raw` y `selftest`. |
| `requirements.txt` | `pyserial`, solo para `sim_phone.py --serial`. |

## Simulador (`fake_device.py`)

```bash
python tools/fake_device.py                         # HTTP en http://127.0.0.1:8080/  (velocidad x5)
python tools/fake_device.py --port 8080 --tcp 5000  # además, TCP de líneas crudas en el 5000
python tools/fake_device.py --speed 1 --host 0.0.0.0  # tiempos reales, accesible desde la red
```

- `--speed` divide los tiempos reales (rampa de servos, asentamiento, láser 1,5 s, hueco del TEST 1,5 s, LED 2 s). Por defecto 5.
- Los límites de geometría (estación 100,-65,180; |pan| ≤ 57°; tilt 30–72°) producen `ERR LIMIT`.
- La calibración de `CAL SAVE` se guarda en un JSON temporal (`--nvs ARCHIVO` para elegir otro). `CAL RESET` lo borra.
- El registro de órdenes, láser y servos sale por stderr.

## Celular de pruebas (`sim_phone.py`)

```bash
python tools/sim_phone.py --http http://127.0.0.1:8080 fire 10 10
python tools/sim_phone.py --tcp 127.0.0.1:5000 test
python tools/sim_phone.py --http http://127.0.0.1:8080 raw "CAL SHOW"
python tools/sim_phone.py --http http://127.0.0.1:8080 selftest
python tools/sim_phone.py --serial COM5 selftest      # módulo real por USB (requiere pyserial)
```

- `selftest` envía la batería de PING, disparos válidos e inválidos, CAL, MARK, STOP y el TEST completo,
  comprueba las respuestas y, por TCP o HTTP, la conducta con el módulo ocupado (PING -> `ERR BUSY`,
  STOP en medio de un TEST -> `TEST ABORT` + `ERR STOP`). Imprime una tabla PASS/FAIL.
- Las celdas del TEST se leen de `include/config.h` (`cfg::TEST_CELLS`).
- Códigos de salida: `0` correcto, `1` respuesta de error o selftest con FAIL, `2` no hay conexión.

## Interfaz web

`web/index.html` se sirve en `/`. Con `fake_device.py` se abre en el navegador en `http://127.0.0.1:8080/`.
Usa `fetch('/cmd?l=...')`, así que funciona igual en el módulo real (modo mantenimiento, `http://192.168.4.1/`).
