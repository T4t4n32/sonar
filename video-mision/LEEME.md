# Video «MISIÓN: CERO PUNTO DOS» — estudio de postproducción (v3)

El video final se arma con **`python armar_final.py`** (1080p) o **`python armar_final.py --vista-previa`** (640×360, para revisar tiempos).
`--solo titulo,orden` renderiza solo esas escenas (útil para iterar). Todo es reproducible: si cambia una toma, se vuelve a correr y sale el video completo.

## Cómo está hecho
| Pieza | Qué hace |
|---|---|
| `armar_final.py` | **Guion técnico**: las 14 escenas con sus tiempos exactos (calculados con la transcripción por palabras de cada toma y la detección de silencios), qué capa entra en cada palabra, qué audio y qué efecto. |
| `motor.py` | Motor ffmpeg + Pillow: escenas con capas (evidencia, gráficos, rótulos, presentador en ventana), transiciones `xfade`, tres buses de audio (diálogo / efectos / música) con la música que se agacha bajo la voz (sidechain) y normalización final (−15 LUFS). |
| `graficos.py` | 22 infografías en estados que se revelan al ritmo de la voz (el campo, la tropa, el mapa, el pulso sereno, la radio, la prueba de fuego). |
| `gen_sfx.py` | Sintetiza los efectos (estática, squelch y roger de walkie, whoosh, boom, riser, tecla, estampa, ping, pitido, redoble, glitch, latido). Sin derechos. |
| `musica_plan.py` | Qué pista suena en cada tramo y los créditos de la música. |
| `recursos/CREDITOS.md` | Autores, licencias y atribuciones de todo lo descargado. |

## Tratamiento de las tomas
- **Sebas** (`tomas/sebastian_videos`): reducción de ruido, nitidez, color oliva/arena unificado, grano y viñeta; voz con declipping, limpieza, EQ de presencia y compresión.
- **Juan José** (`tomas/j_jose_videos`): mismo look; voz limpia y nivelada. Su imagen queda en una ventana con borde dorado mientras se muestra la evidencia.
- **Radio:** la voz del General y la de Bravo pasan por filtro de walkie (banda 380–3200 Hz, saturación suave), con *squelch* de entrada y *roger* de salida y estática debajo.
- **Evidencia real:** láser sobre la hoja (`demostracion_apuntado_laser`), encendido del láser y del interruptor, grabación de pantalla de la app (**el audio de esa grabación nunca se usa**: trae una película).

## Lo que se puede reemplazar sin tocar el código
- **Voces de Bravo** (hoy son la guía de Sebas con el tono subido): poner `voz/bravo-1.m4a`, `bravo-2.m4a`, `bravo-3.m4a` (mismo orden que el guion: «Con 4,8, Capitán…», «0,2, Capitán…», «Señor, sí señor»). Se usan solas, con el efecto de radio.
- **Toma a cámara de la orden**: ya está (`1er-video.mp4`).
- **Más evidencia en video**: pon el archivo en `evidencia/` y apunta la capa correspondiente en `armar_final.py` (funciones `jj1`…`jj5`).

## Carpetas (los videos, la música y `_trabajo/` no se versionan)
`clips-flow/` (5 clips de Google Flow, generados con IA) · `tomas/` · `voz/` · `evidencia/` (fotos, capturas, recortes) · `recursos/` (`graficos/`, `sfx/`, `musica/`, `imagenes/`) · `salida/` · `_trabajo/` (intermedios).

*Archivos antiguos:* `armar_video.py` (montaje v2) queda como respaldo; la guía de tomas de funcionamiento y la hoja de Sebas siguen en sus PDFs.
