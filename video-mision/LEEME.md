# Video «MISIÓN: CERO PUNTO DOS» — montaje automático

`python armar_video.py --nombres "Sebastián y [Compañero]"` arma todo el video con ffmpeg (tarjetas de título animadas, orden del guion, voz, música, sonido normalizado, MP4 1080p en `salida/`).
`python armar_video.py --vista-previa` hace lo mismo en 640×360, en segundos, para revisar el orden.

## Qué poner en cada carpeta (vale .mp4 .mov .mkv .m4v)
| Carpeta | Archivos |
|---|---|
| `clips-flow/` | `sobre` · `mesa` · `radio` · `sello` · `amanecer` (los clips de Flow; `mesa`, `radio`, `amanecer` y `sello` son fondo de las tarjetas) |
| `tomas/` | `01-orden` (Sebas) · `02-campo` · `03-tropa` · `04-mapa` · `05-pulso` · `06-radio` · `07-prueba` (el compañero) · `08-regreso` (los dos) |
| `voz/` | `00-general` (.m4a/.mp3/.wav): la voz del General que suena sobre el sobre |
| `musica/` | un .mp3 libre de derechos (opcional; suena al 10 %) |

Si falta una toma, el montaje pone una tarjeta «FALTA: …» y sigue. Cada toma se puede regrabar y volver a correr el script.
Los archivos de video de esta carpeta no se suben a git (ver `.gitignore`).
