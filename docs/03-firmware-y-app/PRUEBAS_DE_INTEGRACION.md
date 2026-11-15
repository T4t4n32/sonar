# Fundamentos — Batalla Naval · Pruebas de integración

> **Estado (2026-11-08): PARCIAL.** Plan de integración original; falta ejecutarlo en hardware.
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Pruebas de integracion.md` (movido al repositorio el 2026-11-08).

> [!warning] Parcialmente superado (2026-11-03)
> La rúbrica (`TRABAJO CORTE FINAL.pdf`) cambió el alcance: **Bluetooth + app propia**, tablero de **30×30 elevado 5 cm** con matriz de 20×20, **test de 5 posiciones**, coordenadas **(x,y)**, entrega el **martes 24-nov**, y **no califica** Hall, LED por celda, fototransistores ni PCB. Lo que contradiga a [Cumplimiento de la rubrica y huecos](../00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) queda superado; el resto sigue como referencia (precisión de apuntado, seguridad del láser, y la *capa de autodetección Hall* como extra opcional).

Lucky, 2026-10-27. Una prueba de integración verifica que **piezas ya probadas funcionan juntas**. Cada IT lista sus prerrequisitos de [las unitarias](PRUEBAS_UNITARIAS.md); no se corre una IT si sus UT no están en ✔.

Estado: ☐ pendiente · ✔ aprobada · ✘ falló. Parámetros: **2 módulos** (A maestro, B esclavo), cada uno con tablero 20×20 en 4 losas, celda 10 mm y flota 2×(5-4-3-3-2). Con retirada por niveles (*Plan de trabajo*), los umbrales se aplican a las losas y módulos activos.

**Modo simulación**: el firmware debe tener una bandera que deja la FSM, el juego y el protocolo corriendo **sin mover servos ni encender el láser**. Permite adelantar IT-6 e IT-7 antes de tener la torreta.

| ID | Integración | Requiere | Procedimiento | Aprueba si | Est. |
|---|---|---|---|---|---|
| IT-1 | **Potencia** — los dos módulos conectados | UT-HW-02, 10, 11, 12, 15, 16, 17 | Enciende todo con las 8 losas. Provoca el peor caso a la vez: una torreta moviéndose (la otra sin PWM), LED animados al tope del limitador, Hall en rotación, Wi-Fi con clientes y audio sonando. Mide con el INA219 o el multímetro: **entrada de 12 V**, riel de 5 V **en la losa más lejana** y riel de 6 V, durante 10 min. Repite con la torreta bloqueada con la mano (stall breve) | Sin reinicios de ningún ESP32 · riel de 5 V ≥ 4,6 V y de 6 V ≥ 5,4 V en el peor punto · **corriente de entrada ≤ 80 % del adaptador** (≤ 6,4 A) · ningún PTC ni fusible se dispara · convertidores y adaptador razonables al tacto · lo medido coincide con *Diseño de potencia* §4 dentro de ±25 % | ☐ |
| IT-2 | **Torreta + láser + calibración** (en cada módulo) | UT-HW-03/04/05, UT-SW-02/04/05/06/16 | Fija una hoja cuadriculada de 20×20 celdas de 10 mm bajo la torreta (mástil de 150–180 mm). Calibra (4 esquinas → 3 parámetros). Dispara a las 4 esquinas y a **40 celdas aleatorias** | **≥ 90 %** de los 40 disparos caen dentro de la celda ordenada y **100 %** a ≤ 1 celda · punto ≤ 1,5 celdas (H4) · la calibración sobrevive a un reinicio | ☐ |
| IT-3 | **Matriz Hall** (detección de la flota) — **primero la losa 1 (IT-3a), luego el resto del tablero (IT-3b), luego el otro módulo** | UT-HW-06/08/09/13/14, UT-SW-08/09/17/18/19 | Coloca 20 despliegues distintos de la flota 2×(5-4-3-3-2) (incluye 5 inválidos a propósito: diagonal, pegados, faltante…); barcos cruzando el borde entre losas. Imanes en celdas vecinas para buscar lecturas fantasma. Levanta un barco y mide la latencia | 20/20 lecturas exactas · 5/5 inválidos rechazados con el error correcto · **0 lecturas fantasma** · ciclo completo de las 4 losas ≤ 400 ms · levantar un barco se detecta en < 1 s · **nunca hay dos losas con el riel de Hall encendido a la vez** | ☐ |
| IT-4 | **Lazo óptico de verificación** | IT-2, UT-HW-07, UT-SW-07 | En celdas con fototransistor poblado (las 8 de referencia o cualquiera): 20 disparos con luces del salón encendidas y apagadas; 10 disparos más apuntando a una celda vecina | 20/20 detectados · 0/10 falsos positivos · funciona con luz ambiente | ☐ |
| IT-5 | **Retroalimentación** (LED + sonido) | IT-1, UT-HW-10/12, UT-SW-13 | Cadena completa de **400 LED**. Dispara los 3 eventos (agua, tocado, hundido) 10 veces cada uno; mide con video a 60 fps | Color y sonido correctos en 30/30 · desfase LED–sonido ≤ 200 ms · cuadro de LED a ≥ 30 fps · corriente bajo el tope | ☐ |
| IT-6 | **Servidor web + WebSocket** | UT-SW-15, UT-HW-01 | 1 y luego 2 celulares conectados al SoftAP. Envía 50 disparos, mensajes inválidos y reconexiones (apaga el Wi-Fi del celular a mitad de turno y vuelve) | Latencia de ida y vuelta < 100 ms · inválidos rechazados sin caída · tras reconectar el estado del tablero se restaura | ☐ |
| IT-7 | **FSM de punta a punta** (partida entre dos jugadores, modo demo) | UT-SW-11/12/14, IT-3, IT-6, IT-12 | Con flota inválida en un tablero, "Iniciar Partida" debe estar deshabilitado. Con ambas flotas válidas, habilitado. Dos celulares juegan una partida en **modo demo** (D6) hasta su tope; también contra la IA; reinicia | INIT→…→END sin saltos ni bloqueos · botón correcto en ambos casos · el reinicio deja el sistema como nuevo · la partida demo dura ≤ el tiempo asignado para presentar | ☐ |
| IT-8 | **Seguridad del láser** | IT-2, UT-SW-10, UT-HW-05 | (a) Arranque y reinicio con el láser a la vista del celular; (b) forzar un objetivo fuera del tablero; (c) levantar un barco en pleno juego; (d) desconectar al cliente por > T; (e) abrir la tapa (si hay reed); (f) cortar el Wi-Fi durante un disparo | El láser **nunca** emite fuera de PLAY/DISPARO con límites OK · se apaga en (c)–(f) en < 500 ms · apagado al arrancar | ☐ |
| IT-9 | **Resistencia (soak)** | IT-1 a IT-8 | **1 partida completa** (≈ 200 disparos, ~10–13 min) y 2 partidas demo seguidas. Tras la última repite 20 de los disparos de IT-2 | Cero reinicios · deriva de puntería < 1 celda · temperatura de servos, láser y reguladores razonable al tacto | ☐ |
| IT-10 | **Ensayo de presentación** | todas | Armado completo en condiciones del salón (iluminación, tomacorriente, red de otros celulares cerca). Cronométralo 3 veces con el guion del profe y de la rúbrica (cuando la tengan) | 3/3 sin fallos · cabe en el tiempo asignado · hay plan B (modo simulación) si algo físico falla | ☐ |
| IT-11 | **Retirada por losas** | UT-SW-17, IT-3a | Desactiva las losas 3–4 con la máscara: juega una partida demo en 20×10. Luego solo la losa 1: partida demo en 10×10. Misma versión de firmware, sin recompilar | Ambas partidas completas y sin errores · el límite de la torreta y la validación de flota respetan el área activa · tarda < 1 min en cambiar de configuración | ☐ |
| IT-12 | **Enlace entre módulos** (A↔B) | UT-SW-15, IT-1 | Con los dos módulos armados: 50 disparos cruzados; corta el cable de datos a mitad de turno y vuelve a conectarlo; reinicia solo el esclavo; reinicia solo el maestro | Latencia de ida y vuelta < 150 ms · al perder el enlace ambos **pausan y apagan el láser** < 500 ms · al reconectar el estado se restaura sin duplicar disparos | ☐ |

## Orden y dependencias

```
UT-SW (todas) ──────────────► IT-6 ─► IT-7
UT-HW-01..04 ─► IT-2 ──────► IT-4 ─► IT-8
UT-HW-06..09 ─► IT-3 ──────────────► IT-7
UT-HW-02,10..12,15..17 ─► IT-1 ─► IT-5
UT-HW-13,14 ─► IT-3a (losa 1) ─► IT-3b (resto) ─► IT-11
UT-SW-15 ─► IT-12 (enlace A↔B) ─► IT-7
                  IT-1..IT-8 ─► IT-9 ─► IT-10
```

## Reglas de operación

- **Una falla no se salta**: se anota en la tabla, se corrige y se repite la IT completa; si arrastra una UT, se repite también.
- Tras cada cambio de firmware se repiten las UT-SW (5 s) antes de volver a mover hardware.
- **Congelar firmware el 2026-11-22**; después solo correcciones críticas con la IT afectada repetida.
- IT-8 va **antes** de cualquier demo ante terceros.
- Si algo físico falla el día de la presentación: el modo simulación + el video de IT-5 son el plan B.

## Lo que falta para cerrar este plan

- La **rúbrica** de Almario: mapea cada IT a un criterio y ajusta los umbrales.
- Decisiones D2–D6 de la [evaluación](../archivo/EVALUACION_PLAN_V1.md) (D1, el 20×20, ya está decidida).
- Ver [el plan](../00-proyecto/PLAN_DE_TRABAJO_V1.md): IT-3a debe pasar antes de poblar las losas 2–4, y IT-11 certifica el plan de retirada.
