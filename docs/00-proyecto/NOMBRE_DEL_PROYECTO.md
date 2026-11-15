# Nombre del proyecto — descripción y candidatos

> **Estado (2026-11-08): VIGENTE.** Candidatos de nombre; el nombre de trabajo de la interfaz hoy es «SONAR · Batalla Naval».
> Origen: vault `borradores/fundamentos/batalla-naval/Nombre del proyecto.md` (movido al repositorio el 2026-11-08).

Lucky, 2026-11-03. El nombre de trabajo del repositorio es `duelo-laser` (`I:\repository\duelo-laser`). Esta página sirve para elegir el definitivo.

## Descripción (para pegar en un generador de nombres)

> Es un juego de duelo de coordenadas en el que dos jugadores se enfrentan sin verse el tablero. Cada jugador tiene una plataforma de 30×30 cm con una matriz de 20×20 casillas de 1 cm donde esconde su flota. Sobre cada plataforma hay un mástil con una torreta de dos servomotores que sostiene un láser rojo: el rival le manda desde su celular, por Bluetooth, una coordenada `(x,y)` y la torreta gira y se inclina hasta que el punto de luz aparece exactamente en esa casilla, con un sonido. Es un proyecto de Ingeniería Mecatrónica de primer semestre que combina mecánica (el mástil y la torreta), electrónica (dos ESP32), control (cálculo de ángulos y calibración) y software (una app propia). Tono: preciso, técnico pero con un toque juguetón; nada de "batalla", "naval", "láser" ni "strike" en el nombre; que suene bien en español, se escriba fácil y sirva como nombre de app y de red Bluetooth (sin tildes, máximo ~10 letras).

## Qué evitar

"Batalla Naval", "Laser Battle", "Sea Strike", "Hundir la Flota", "Torpedo", "Naval Laser" y cualquier mezcla de inglés genérico. El nombre debe salir de **lo que hace el sistema**: apuntar con ángulos.

## Candidatos

| Nombre | Qué significa | Por qué encaja | Frase |
|---|---|---|---|
| **Azimut** | el ángulo horizontal que mide un instrumento al apuntar (el *pan* de la torreta; el *tilt* es la elevación) | es literalmente lo que controla el sistema; poco usado; suena a navegación | "Azimut: la luz llega a la coordenada." |
| **Teodolito** | instrumento topográfico que mide ángulos horizontales y verticales | la estación es un teodolito al revés: en vez de medir, apunta | "Teodolito: duelo de ángulos." |
| **Tino** | "tener buen tino" = tener buena puntería | corto, cálido, colombiano; sirve de mascota | "Tino: el que tiene tino, gana." |
| **Diana** | el blanco al que se apunta, y también un nombre | juego de palabras con la casilla objetivo | "Diana: acierta la casilla." |
| **Alidada** | regla con mira que gira para apuntar a un punto | rara, técnica, memorable | "Alidada: mira, gira, acierta." |
| **Astrolabio** | instrumento antiguo para ubicarse por coordenadas | une navegación, coordenadas y mecánica | "Astrolabio: ubica el punto." |
| **Heliógrafo** | telégrafo que manda señales con un haz de luz reflejada | comunicación por luz, con aire histórico | "Heliógrafo: mensajes de luz." |
| **Centella** | chispa o destello | corta y fuerte; evoca el punto de luz | "Centella: un destello, una casilla." |
| **Cuadrante** | instrumento que mide ángulos y también "cuadrante" del tablero | doble sentido con la matriz de casillas | "Cuadrante: apunta al cuadrante." |
| **Mira** | el visor con el que se apunta; y "mira" como orden | muy corto; se pronuncia igual en todos los acentos | "Mira: donde mires, la luz llega." |

## Mi recomendación

1. **Azimut** — el más defendible en la sustentación ("el nombre es el ángulo que controlo") y casi nadie lo usará.
2. **Teodolito** — igual de técnico, con más personalidad; algo largo para una app.
3. **Tino** — si quieres un nombre cercano y con carácter; cuenta una historia en la demostración ("¿quién tiene mejor tino?").

## Al elegir

Cambiar: la carpeta `I:\repository\duelo-laser`, el título del `README.md`, `DEVICE_NAME` y `WIFI_SSID_MAINT` (`include/config.h` y `platformio.ini`; p. ej. `AZIMUT-A` y `AZIMUT-B`), el nombre de la app y del `.aia`, y el título de `web/index.html`. Lucky lo hace en un solo paso cuando lo decidas.
