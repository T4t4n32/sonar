# Brief — web «SONAR: BATALLA NAVAL» (para Lucky/Hermes)

Escrito 2026-11-06 por Claude Code a pedido de Sebas. **Cumplido el mismo día por Claude Code** (no por Hermes): ver `docs/01-diseno/DISENO_WEB.md`,
`web/index.html` y `registro/2026-11-06/RESUMEN.md`. Se conserva como referencia del encargo original.

## Antes de escribir una línea
1. Leer `wiki/concepts/guia-diseno-interfaces.md` (regla general) y, solo como calibración de calidad, `patrones-diseno-dinamico.md`. Los motivos de SONAR son los de abajo, no los de otros proyectos. Skills: `wiki/entities/t4os-skills-hub.md`.
2. Abrir las skills del Hub (`t4os-skills-hub`): `emil-design-eng`, `review-animations`, `web-design-engineer`, `design-md`.
3. Leer `docs/03-firmware-y-app/PROTOCOLO.md` (contrato) y `tools/fake_device.py` (simulador). **El protocolo no se cambia.**

## Filosofía (una frase, la vara de cada pantalla)
«Puente de mando de un submarino: oscuro, preciso, el sonar late.» Si una pieza no se explica con eso, sobra.

## Tres motivos (no mezclar con otros)
- **Barrido** — línea de radar que gira sobre el tablero 20×20 (logo, cargando, conectando).
- **Eco** — onda concéntrica que nace donde se dispara; el impacto (`MARK HIT`) y el agua (`MARK MISS`) se distinguen por color y forma.
- **Cota** — líneas finas de plano que miden y separan (coherente con el plano de la carcasa).

## Tokens (nada de colores sueltos)
Fondo abisal casi negro; verde sonar para vivo/ok; ámbar para ocupado/calibración; rojo solo para HIT/STOP/ERR. Definir en `:root`
y variante clara. Un solo botón de acento por pantalla: **DISPARAR**.

## Reglas de uso
- Disparar en **≤ 3 toques** desde que abre: tocar celda → (se arma sola) → DISPARAR. Sin botón «Siguiente».
- Títulos ≤ 8 palabras y una línea de apoyo. Registro de comunicaciones (tx/rx con hora) siempre visible pero plegable.
- Calibración (`CAL SHOW/SET/SAVE/RESET`) en un panel aparte con rangos del protocolo (trims ±10°).
- Honestidad: lo no probado en hardware se muestra «Simulado» / «Por confirmar»; nada finge funcionar. `STOP` por Wi-Fi no interrumpe un disparo: decirlo en la UI.
- Estados: conectado, ocupado (`ERR BUSY`), error, desconectado; cada uno con su animación y su texto.
- Móvil primero (375×812); sin dependencias externas ni CDN (la página va embebida en el ESP32: ≤ ~60 KB si es posible, un solo archivo).
- Movimiento: explica, confirma o guía; 0,2–0,6 s; respetar `prefers-reduced-motion`.

## Cómo se verifica (medido, no dicho)
1. `python tools/fake_device.py` y abrir `http://127.0.0.1:8080/` **en un navegador real**; leer la consola: 0 errores.
2. `python tools/sim_phone.py selftest` → debe dar 20/20 (hoy el simulador falla `/cmd`: arreglarlo primero o reportarlo).
3. Capturas a 375×812 y 1280×800 de: inicio, tablero con celda armada, disparo en curso, HIT, MISS, error, calibración. Guardarlas en `registro/2026-11-DD/`.
4. Revisar con `review-animations` y reportar qué cambió por su culpa.

## Entrega
Cierre con HECHO (rutas + prueba) / FALTA / SIGUIENTE. Si el modelo no puede con el diseño en una pasada, delegar a Claude Sonnet con
`delegate_task` pasando este brief. Anotar qué modelo lo hizo y si cumplió (ver `wiki/concepts/pruebas-modelos-hermes.md`).
