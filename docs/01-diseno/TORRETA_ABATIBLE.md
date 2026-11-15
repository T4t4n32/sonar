# Torreta que se acuesta y se levanta (maletín) — factibilidad (2026-11-07)

Idea de Sebas: la torreta pan-tilt va **acostada** dentro del maletín y, al encender, un servomotor en la base la **levanta**; al apagar, se **agacha** para que todo quepa.

## Veredicto: factible, con tres condiciones
1. **Un tope mecánico duro y un seguro.** El servo solo no repite la posición: un MG996R tiene banda muerta de ~5 µs (≈ 0,45° con 11 µs/°, est.) más holgura de engranajes. Con casillas de 1 cm a ~30 cm, la tolerancia es ±atan(0,5/30) = **±0,95°**; con casillas de 2 cm, ±1,9°. Un error de levante se suma directo al error de apuntado. La torreta debe **apoyarse en un tope** y quedar trabada (pestillo o articulación «sobre el centro»), no «sostenida por el servo».
2. **El par alcanza, pero con poco margen.** Masa estimada 0,25 kg (2 servos + láser + soporte de aluminio) a 15-20 cm de la bisagra → **3,75-5 kg·cm** en el momento de más esfuerzo (acostada). El MG996R declara ~9,4 kg·cm a 4,8 V y ~11 kg·cm a 6 V (de hoja de datos; los clones rinden menos). Regla práctica: ≤ 50 % del máximo en continuo → hace falta un **resorte de ayuda o contrapeso**, o acortar la palanca.
3. **«Al apagarse se agacha» no puede ser literal:** sin energía el servo no se mueve. Hay dos salidas: (a) **interruptor suave**: el botón pide apagar, el firmware pliega la torreta y *luego* corta la alimentación con un MOSFET; (b) una orden/botón **PLEGAR** antes de apagar. Además, si se cierra la tapa con la torreta levantada, se **fuerza el servo desde fuera y puede dañar los engranajes**: hace falta un tope de seguridad o una tapa que no cierre sin plegar.

## Tres formas de hacerlo (de más a menos riesgo para el test de 5 posiciones)
| Opción | Cómo funciona | A favor | En contra |
|---|---|---|---|
| **A. Levante con servo** (lo que propones) | servo en la bisagra de la base + tope + pestillo | efecto «wow», autónomo | un servo más (otro 2,5 A de pico), secuencia en firmware, riesgo de repetibilidad |
| **B. Mecanismo con la tapa** | un cuadrilátero articulado: al abrir la tapa a 90° la torreta se levanta sola | sin motor, repetible por los topes, plegado automático | diseño mecánico más fino (SolidWorks lo permite con estudio de movimiento) |
| **C. Abatible a mano** | se levanta a mano y encaja en un pestillo | el más simple y repetible | menos «wow» |
**Recomendación:** diseñar la base con el **anclaje listo para A** pero entregar el test con **C o B** (máxima repetibilidad), y activar A solo si sobra tiempo. El test de 5 posiciones vale 2,0 de 5.

## Firmware (si se hace A)
Estados `PLEGADA → LEVANTANDO → LISTA → PLEGANDO`; órdenes `DEPLOY` / `STOW` en el protocolo v2; láser siempre apagado mientras algo se mueve (ya lo exige el controlador); levantar **antes** de habilitar pan y tilt (nunca los tres servos a la vez, por la fuente).
