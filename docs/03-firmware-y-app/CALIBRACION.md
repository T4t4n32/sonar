# Calibrar el apuntado (6 pasos, ~3 minutos)

La puntería depende de **cómo quedó montado** el cardán frente a la matriz. En vez de medir distancias, se apunta el láser a las 4 esquinas reales y el módulo calcula todas las celdas (protocolo v3, [`PROTOCOLO.md`](PROTOCOLO.md)).

## Antes
- Servos **centrados** y brazos montados (herramienta `servo_centrar`, [`tools/servo_centrar`](../../tools/servo_centrar/main.cpp)).
- Matriz **fija** (cartón rígido, cinta). Si algo se mueve después, se repite la calibración.
- Módulo con el firmware `modulo_a` cargado y emparejado como **SONAR-A**.
- Sala con poca luz: el punto láser se ve mejor.

## En la app (pestaña **Enlace → Calibrar apuntado**)
1. **LÁSER ON.** Se enciende el láser de apuntado (se apaga solo a los 120 s; STOP lo apaga).
2. Con la cruceta, lleva el punto a la **esquina (1,1)** de la matriz (abajo-izquierda, vista desde la estación). Pasos grandes para acercarte (5°, 1°), finos para afinar (0,2°, 0,05°). Pulsa **«Esta es la esquina (1,1)»**.
3. Repite con **(20,1)** abajo-derecha, **(20,20)** arriba-derecha y **(1,20)** arriba-izquierda.
4. Opcional pero recomendado: lleva el punto al **centro (11,11)** y regístralo como punto de **control**.
5. **Calcular.** Si hay control, muestra el error en grados: ≲ 0,3° es muy bueno; si pasa de 1°, una esquina quedó mal apuntada → repítela y vuelve a calcular.
6. **Verificar** tocando celdas del mini-tablero (el láser queda encendido y va a cada una), y **Guardar en el módulo**. Queda en la memoria del ESP32: sobrevive a apagarlo.

Cuando la matriz definitiva esté montada, se repite el proceso una vez y se juega.

## Sin la app (por USB serie, 115200; también sirve para Hermes)
```
LASER ON
JOG 2 0          (mueve; repite hasta estar sobre la esquina)
CORNER 1         (guarda el punto 1 = (1,1))
...              (CORNER 2, 3, 4; CORNER 5 = centro, opcional)
CAL FIT          (OK FIT 0.12)
AIM 10 10        (comprueba una celda)
CAL SAVE         (OK SAVE)
```
`CAL MAP` responde `MAP GRID` cuando el disparo usa el mapa; `CAL RESET` lo borra y vuelve a la geometría de `config.h`.

## Si algo no cuadra
- **← → o ↑ ↓ van al revés:** en la app, «invertir ← →» / «invertir ↑ ↓» (depende de cómo giraron los brazos). No afecta a la calibración.
- **`ERR LIMIT`:** el servo llegaría a menos de 15° o más de 165°; recentra el brazo en su estriado (se ve al centrar a 90°).
- **`ERR FIT`:** esquinas casi iguales o alineadas; revisa que cada una sea distinta.
- **El error de control es grande:** el cardán no es ideal (el láser no sale por el cruce de los ejes) o una esquina se registró mal; repite esa esquina, aproximándote siempre desde el mismo lado.
- **Aproximarse siempre desde el mismo lado:** el firmware ya lo hace al mover; no cambia el método.
