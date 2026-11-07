# SONAR: Batalla Naval Automatizada con ESP32, Pan-Tilt y Láser

Duelo de coordenadas con láser: cada jugador tiene un tablero de 30×30 cm (matriz de 20×20) y una estación pan-tilt con láser que apunta a la celda `(x,y)` que manda el rival desde el celular. Dos módulos idénticos con un ESP32 cada uno.

## Estructura

| Ruta | Qué es |
|---|---|
| `include/config.h` | constantes, límites, tiempos y pines |
| `lib/core/` | **lógica pura** (protocolo, geometría, calibración, controlador): sin Arduino, probada en el PC |
| `lib/hal_esp32/` | hardware real del ESP32 (servos por LEDC, láser, zumbador, LED, NVS, reloj) |
| `src/` | `main.cpp` y los transportes (Bluetooth, USB, Wi-Fi de mantenimiento) |
| `web/index.html` | **SONAR · Batalla Naval**: panel de mando web (radar 20×20, disparo en 2 toques, TEST, calibración, bitácora, modo simulado, tema claro/oscuro). Un solo archivo de ~43 KB que sirve el ESP32 en modo mantenimiento; también corre en el PC con `tools/fake_device.py`. Diseño: `docs/DISENO_WEB.md` |
| `tools/` | simulador de módulo (`fake_device.py`), "celular" de pruebas (`sim_phone.py`) y prueba de la web de punta a punta con capturas (`e2e_web.py` → `registro/`) |
| `test/test_core/` | pruebas Unity de `lib/core` |
| `docs/` | `PROTOCOLO.md`, `PINOUT.md`, `APP_INVENTOR.md`, `BRINGUP.md` , y `PROPUESTA_TABLERO_LDR.md` |

## Comandos (PlatformIO)

```bash
pio run -e modulo_a            # compilar el módulo A
pio run -e modulo_a -t upload  # cargarlo (el B: -e modulo_b)
pio device monitor             # monitor serie a 115200
pio test -e native             # pruebas de lib/core en el PC (requiere compilador de C++)

# sin hardware: la web contra el módulo simulado
python tools/fake_device.py                                   # http://127.0.0.1:8080/
python tools/sim_phone.py --http http://127.0.0.1:8080 selftest   # protocolo, 20/20
uv run --script tools/e2e_web.py                              # web de punta a punta → registro/<fecha>/
```

Si `pio` no está en el PATH: `%USERPROFILE%\.platformio\penv\Scripts\platformio.exe`.

## Requisito de hardware

- **Microcontrolador**: ESP32 clásico (WROOM-32 / NodeMCU-32S). Requiere soporte de Bluetooth clásico (SPP).
