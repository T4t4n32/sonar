# Registro de pruebas — web SONAR

Fecha: 2026-11-06 20:29 · `tools/e2e_web.py` contra `tools/fake_device.py` (simulado, **sin hardware**).

**Resultado: 29/29 pruebas correctas.**

| prueba | estado | detalle |
|---|---|---|
| peso del archivo ≤ 60 KB (va embebido en el ESP32) | PASS | 44.1 KB |
| conecta con el módulo y muestra su nombre | PASS | Conectado · DUELO-FAKE |
| DISPARAR empieza deshabilitado sin objetivo | PASS |  |
| 1 toque fija el objetivo (13,7) | PASS | (13, 7) |
| DISPARAR visible sin desplazar (dock fijo) | PASS | y=705 |
| el rayo se dibuja durante el disparo | PASS |  |
| disparo completado: 2 toques en total (celda + DISPARAR) | PASS |  |
| la celda queda marcada como disparada | PASS |  |
| TOCADO/AGUA se habilitan tras el disparo | PASS |  |
| marcar TOCADO cambia la celda | PASS |  |
| TEST: los 5 objetivos pulsan «en curso» | PASS |  |
| TEST: 5 de 5 posiciones confirmadas | PASS |  |
| calibración: valor fuera de rango se rechaza en la página | PASS |  |
| calibración: APLICAR y LEER devuelven el valor | PASS | 1.50 |
| la bitácora se descarga como .txt | PASS |  |
| sin desplazamiento horizontal a 320 px | PASS | 0px |
| sin desplazamiento horizontal a 375 px | PASS | 0px |
| sin desplazamiento horizontal a 414 px | PASS | 0px |
| sin desplazamiento horizontal a 768 px | PASS | 0px |
| existe tema claro (Carta náutica) y se activa con el botón | PASS |  |
| sin enlace: muestra instrucciones y reintentar | PASS |  |
| sin enlace: DISPARAR deshabilitado | PASS |  |
| modo simulado: insignia visible y sin red | PASS |  |
| modo simulado: dispara y responde OK | PASS |  |
| teclado: flechas mueven el objetivo | PASS | (11, 13) |
| teclado: Intro dispara | PASS |  |
| teclado: Esc envía STOP | PASS |  |
| todos los botones tienen nombre accesible | PASS | 0 sin nombre |
| consola sin errores ni avisos | PASS |  |

## Capturas

- `escritorio-01.png`
- `escritorio-02-claro.png`
- `movil-01-inicio.png`
- `movil-02-objetivo.png`
- `movil-03-disparando.png`
- `movil-04-disparo-completado.png`
- `movil-05-tocado.png`
- `movil-06-test-en-curso.png`
- `movil-07-test-5de5.png`
- `movil-08-calibracion.png`
- `movil-09-bitacora.png`
- `movil-10-tema-claro.png`
- `movil-11-sin-enlace.png`
- `movil-12-simulado.png`
