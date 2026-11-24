# Video «MISIÓN: CERO PUNTO DOS» — montaje automático (v2)

`python armar_video.py --nombres "Sebastián y Juan José"` arma todo el video con ffmpeg y lo deja en `salida/`.
`python armar_video.py --vista-previa` lo hace en 640×360 en poco tiempo, para revisar el orden.

Qué hace: tarjetas de título animadas · color unificado (verde oliva) en las tomas habladas · **cortes de evidencia** sobre lo que se explica (foto real del montaje, captura de la app, hoja impresa) con
rótulo técnico · texto cinético en la apertura · voz limpia y nivelada · música opcional · MP4 1080p. Si falta una toma pone una tarjeta «FALTA: …» y sigue.

## Carpetas (los videos y audios no se suben a git; ver `.gitignore`)
| Carpeta | Contenido |
|---|---|
| `clips-flow/` | `sobre` · `mesa` · `radio` · `sello` · `amanecer` (generados en Flow) |
| `tomas/` | `01-orden` (Sebas a cámara, opcional) · `02-campo` … `06-radio` · `07-prueba` · `08-regreso`. Si no están `02`–`06`, se usan `tomas/j_jose_videos/1–5.mp4` |
| `voz/` | `P1_sebas` o `00-general` (la voz del General, solo Sebas; suena una vez sobre el sobre) · `01-orden` (la orden de Alfa **dicha por Sebas**; si prefieres a cámara, `tomas/01-orden.mp4`). El montaje **nunca usa la voz de otra persona** para las partes de Sebas |
| `evidencia/` | fotos y capturas (ya incluidas) **y los videos reales de funcionamiento** (ver abajo) |
| `musica/` | un `.mp3`/`.m4a` libre de derechos (opcional; suena al 10 %) |

## Cómo se sustituyen las fotos por videos reales
Si pones en `evidencia/` un video con alguno de estos nombres, el montaje lo usa **en lugar de la foto fija** (cada corte continúa donde terminó el anterior del mismo video):
`pantalla-app.mp4` (radar, veredicto, hundido) · `calibracion.mp4` (las 4 pantallas de calibración) · `plantilla.mp4` · `maqueta.mp4` (servos) · `stop.mp4` · `laser.mp4`.
Y las tomas completas: `tomas/07-prueba.mp4` (el TEST) y `tomas/08-regreso.mp4` (los dos). La guía de cómo grabarlas es `GUIA-TOMAS-FUNCIONAMIENTO.pdf`.

## Otros archivos
- `HOJA-TOMAS-CAPITAN-ALFA.pdf` — qué dice y cómo se viste Sebas (`hoja_tomas_alfa.py`).
- `GUIA-TOMAS-FUNCIONAMIENTO.pdf` — cómo grabar las tomas de funcionamiento (`guia_tomas_funcionamiento.py`).
- Los tiempos de los cortes de cada toma hablada están en `armar_video.py` (diccionario `CORTES`), calculados con la transcripción de cada toma.
