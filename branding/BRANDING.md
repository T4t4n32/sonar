# Identidad visual de SONAR

Una sola idea: **un puente de mando de submarino**. Oscuro, técnico, preciso; el verde sonar es la única voz fuerte y el rojo/cian se reservan para el combate.

## Motivo
Radar de **tres arcos** con un **barrido** y un punto de origen: la estación que apunta. Es el logotipo, el icono de la app (`app/tools/make_icons.py`), el favicon y el splash. Nunca se dibuja de otra forma.

| Archivo | Uso |
|---|---|
| `sonar-mark.svg` / `-light.svg` | marca sola, sobre fondo oscuro / claro |
| `sonar-logo.svg` / `-light.svg` (+ `.png` @2x) | horizontal: marca + SONAR + BATALLA NAVAL |
| `sonar-icon.svg` / `sonar-icon-512.png` | icono cuadrado (tienda, avatar) |
| `banner.svg` / `banner.png` | cabecera del README |
| `social-preview.png` (1280×640) | vista previa al compartir el repositorio |

Se regeneran con `uv run --with playwright python branding/generar_branding.py`.

## Paleta
| Token | Hex | Uso |
|---|---|---|
| Fondo | `#040a0f` | fondo base (siempre oscuro) |
| Panel | `#0a1822` | tarjetas y paneles |
| Línea | `#16384a` | rejillas y bordes |
| **Sonar** | **`#46f0b5`** | acento principal, marca, botón DISPARAR |
| Eco | `#5ad6ff` | agua, enlace, información |
| Impacto | `#ff5d4d` | acierto, explosión, STOP |
| Aviso | `#ffc24a` | ocupado, atención |
| Texto | `#d9f3ee` · apagado `#86adae` | texto principal y secundario |
Sobre fondo claro: tinta `#0b2a33` y acento `#007a5a` (variantes `-light`).

## Tipografía
- **Rótulos y marca:** Bahnschrift (peso 600–700, espaciado de letras amplio: `SONAR` a +0,2 em). En la app, la pila `system-ui`.
- **Cotas, coordenadas y bitácora:** monoespaciada (`Consolas` / `ui-monospace`). Toda coordenada se escribe `(x, y)` con x primero.

## Movimiento (motivos)
**Barrido** (giro lento del radar), **eco** (anillos que se expanden: agua), **cota** (retícula con números). Curva `cubic-bezier(.23,1,.32,1)`. Con `prefers-reduced-motion` todo queda estático.

## Voz
Directa, de verbo corto, en español: «Apunta. Dispara. Hunde.» (lema vigente; alternativas en `docs/01-diseno/planos/`). Sin signos de exclamación decorativos ni jerga militar.

## Reglas
- Espacio libre alrededor del logotipo: la altura del punto de origen del barrido.
- Tamaño mínimo de la marca: 24 px. Del logotipo horizontal: 120 px de ancho.
- No cambiar los colores de los arcos, no rotar, no poner sobre fotografías sin velo oscuro.
- Verde sonar nunca como color de texto largo; solo rótulos, cifras y acciones.
