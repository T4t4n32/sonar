# Fundamentos — Batalla Naval · Planos y medidas

> **Estado (2026-11-08): VIGENTE (base de cotas).** Hoja de cotas desde el dibujo a mano; el concepto 3D v1 está en [cad/](../../cad/LEEME.md).
> Origen: vault `borradores/fundamentos/batalla-naval/Fundamentos - Batalla Naval - Planos y medidas.md` (movido al repositorio el 2026-11-08).

Lucky, 2026-11-03. Base: tu `planos_a_mano.pdf` y la rúbrica. Es una **hoja de medidas** para dibujar a mano y luego modelar en SolidWorks: tablas de coordenadas y cotas, sin figuras. Los cálculos de apuntado salen de `geometria-planos.py` (misma carpeta). **Todas las medidas en mm.** Las medidas de piezas compradas (servos, láser, ESP32) son nominales: **mídelas con la pieza real antes de cortar** (sección 9).

## 0. Cómo leí tu dibujo

- **Vista en planta:** dos tableros en línea, uno en cada extremo de la caja, con una división en el medio; en cada extremo hay un círculo flanqueado por dos rectángulos. Lo leí como **la estación de cada jugador detrás de su propio tablero**: el círculo es el eje de pan y los rectángulos, caja de electrónica y altavoz.
- **Perfil:** una base plana con extremos biselados y un **mástil alto** que sale del centro, con un círculo en su base. Lo leí como el **mástil de la estación**, que ya resuelve lo más difícil: el láser tiene que estar **alto** (explicación en la sección 1).
- **Isométrico:** el panel alto con el cilindro en la base lo leí como un **biombo plegable** en la bisagra central que oculta cada flota al rival. Si es otra cosa (por ejemplo la propia estación), dímelo y lo cambio.
- **Cambios que hago:** el mástil no va en el centro del tablero sino **detrás de su borde posterior** (65 mm detrás de la matriz): sobre el centro, el láser tendría que apuntar casi vertical y se pierde precisión.

## 1. "Horizontal" y "vertical", en simple

- **Horizontal:** el tablero está **acostado sobre la mesa**, como un tablero de ajedrez. Es el tuyo, y es lo que dice la rúbrica (elevado 5 cm sobre la base).
- **Vertical:** el tablero está **de pie**, como un cuadro o un caballete (es el de la diapositiva).
- **Por qué importa:** con el tablero acostado, un láser a ras de mesa llega casi paralelo y el punto se estira como una raya de varios centímetros. Por eso el láser **va alto, en el mástil**: con el eje a 180 mm sobre el tablero, el punto de 3 mm se estira solo ×1,8 en la celda más lejana (≈ 5,5 mm, cabe en la celda de 10 mm). Con h = 60 mm se estiraría más de ×4 y no cabría.

## 2. Marco de referencia

| Símbolo | Significado |
|---|---|
| **O** | esquina **posterior-izquierda de la matriz** (la más cercana a la estación, a la izquierda), sobre la cara superior del tablero |
| **x** | hacia la derecha, 0 → 200 |
| **y** | hacia el frente, **alejándose de la estación**, 0 → 200 |
| **z** | altura **sobre la superficie de apoyo** (la mesa) |
| Celda **(x,y)** | **1 → 20** en cada eje; **(1,1)** = celda de la esquina O. Centro de la celda i: `(i − 0,5) × 10` mm |

## 3. Plano 1 — Planta de un módulo

| Pieza | x (mm) | y (mm) | Tamaño |
|---|---|---|---|
| **Base** (P01) | −50 … 250 | −90 … 255 | 300 × 345, espesor **3** |
| **Tablero** (P03) | −50 … 250 | −50 … 250 | 300 × 300, espesor 3 |
| **Matriz** (cuadrícula) | 0 … 200 | 0 … 200 | 200 × 200; margen de **50** por los cuatro lados |
| **Bahía** (paredes P02) | −50 … 250 | −50 … 250 | paredes de 3 mm bajo el tablero |
| **Mástil** (P05) | 85 … 115 | −80 … −50 | 30 × 30 |
| **Eje de pan** | **100** | **−65** | centro del mástil |
| **Zona de estación** | −50 … 250 | −90 … −50 | franja de 40 mm detrás del tablero |

```
 y=-90 ┌──────────────────────────────────────┐
       │           zona de estación (40)      │
 y=-80 │                ┌───┐                 │
       │                │ ◉ │ mástil 30×30    │   ◉ = eje de pan (100, -65)
 y=-50 ├────────────────┴───┴─────────────────┤  ← borde posterior del tablero
       │  tablero 300 × 300                   │
       │     margen 50                        │
 y=0   │      ┌────────────────────┐          │
       │      │  matriz 20 × 20    │          │
       │      │ (1,1)        (20,1)│          │
       │      │ (1,20)      (20,20)│          │
 y=200 │      └────────────────────┘          │
 y=250 ├──────────────────────────────────────┤  ← borde frontal (bisagra)
 y=255 └──────────────────────────────────────┘
     x=-50          x=0             x=200   x=250
```

## 4. Plano 2 — Perfil (corte en x = 100)

| Cota | z (mm sobre la mesa) |
|---|---|
| Cara inferior de la base | **0** |
| Cara superior de la base (piso de la bahía) | 3 |
| Cara inferior del tablero | 50 |
| **Cara superior del tablero (la matriz)** | **53** = **50 sobre la base** ← los "5 cm" |
| Cara superior de la placa del mástil | 168 |
| **Eje de tilt (origen del rayo)** | **233** (180 sobre la matriz) |

- **Bahía:** 47 mm libres (de 3 a 50). Ahí van el ESP32, el convertidor, el conector de la fuente y el altavoz.
- **Mástil:** de 3 a 168 → **165 mm**, con ranuras de ajuste de ±10 mm en la placa superior.
- **"5 cm":** nadie sabe aún desde dónde se miden. El diseño **cumple las dos lecturas con 3 mm de diferencia**: **50 mm desde la cara superior de la base** ("la base donde se instala") y **53 mm desde la mesa**, por eso la base es delgada (3 mm). Hay que preguntarle a Almario (sección 12).

```
 z=233  ●────────────── eje de tilt (láser)
        │╲
 z=168 ─┴┐ ╲   placa del mástil (pan servo)
         │M ╲  rayo hacia (20,20) a 330 mm
         │M   ╲
 z=53  ──┴──────╲──────────────────────────── tablero (matriz de 200 mm)
         │ bahía (47 libres)                 │
 z=3   ──┴────────────────────────────────────┴── base
 z=0 ═══ mesa
         y=-65                      y=0 ........ y=200
```

## 5. Plano 3 — Tablero y matriz

| Elemento | Medida |
|---|---|
| Superficie | placa de 300 × 300, **mate y oscura** (sin brillo: es láser de clase 3R) con cuadrícula clara |
| Matriz | 200 × 200, centrada; **20 × 20 celdas de 10 × 10** |
| Líneas | 0,4–0,5 mm; borde exterior de 1 mm |
| Numeración | **1–20** en los cuatro bordes de la matriz, dentro del margen, altura de cifra 4 mm; eje x arriba y abajo, eje y a izquierda y derecha |
| Origen | marca "(1,1)" en la esquina O |
| **Marcas de calibración** | cruz de 6 mm en el centro de (1,1), (20,1), (1,20), (20,20) y en el centro de la matriz **(100, 100)**; trazo de 0,3 mm |
| Acabado | vinilo o papel impreso pegado sobre la placa (más fácil de rehacer que grabar) |

**Fichas de la flota (P09):** ancho **8 mm**, largo `10·n − 2` mm (n = 2, 3, 3, 4, 5 → 18, 28, 28, 38, 48), alto 6 mm; que quepan dentro de las celdas sin tocar las líneas. La flota que se use no la fija la rúbrica: la tabla es para la de 5-4-3-3-2.

## 6. Plano 4 — Estación

| Elemento | Medida / posición |
|---|---|
| Eje de pan (vertical) | **(x = 100, y = −65)**; alinear **el eje de salida del servo**, no el centro de su cuerpo (el eje de salida queda desplazado en el cuerpo) |
| Servo de pan | MG996R, **de pie**, con el eje hacia arriba, sobre la placa del mástil (60 × 40 × 4 mm) |
| Eje de tilt (horizontal) | **z = 233**; servo MG90S en una ménsula sobre el cuerno del pan |
| Láser KY-008 | cilindro Ø6 en una abrazadera rígida sobre el cuerno del tilt. **El rayo debe pasar por el cruce de los ejes de pan y tilt** (tolerancia ≤ 2 mm) |
| Cables | 3 hilos de servo × 2 + 3 del láser, por **dentro del mástil** (hueco 24 × 24) hasta la bahía; **15 cm de holgura** para que el giro de ±57° no los tense |
| Pila de alturas (nominal) | servo de pan ≈ 43 mm + cuerno ≈ 4 mm + ménsula de tilt ≈ 18 mm = 65 → placa del mástil a 168 si el tilt queda en 233 |

### Estructura del mástil (¿trípode o marco?)

**No hace falta trípode ni marco.** Lo que mencioné fue un **mástil** (o arco) para subir el láser; con esta carga basta una **columna de caja con brida y dos cartelas**.

| Elemento | Medida |
|---|---|
| Columna | sección **30 × 30**, pared **≥ 3 mm** (MDF o PLA grueso) o tubo cuadrado de aluminio de 2 mm |
| **Brida** (P05b) | **60 × 60 × 3**, atornillada a la base con **4 × M3**, centrada en (100, −65) |
| **Cartelas** (P05c) | **2 triángulos de 40 × 40 × 3**, uno a cada lado de la columna (en x), pegados y atornillados |
| Unión a la placa superior | **4 × M3** con tuerca; las ranuras de ±10 mm de altura quedan en la placa |

- **Por qué basta:** el enemigo no es que el mástil se doble, sino que **se tuerza** con la reacción del servo de pan (eje vertical). Estimación con MDF de pared de 3 mm: giro ≈ **0,2°** con el servo **bloqueado** y ≈ **0,02°** en operación normal. **Es una estimación: se comprueba mirando el punto láser mientras se mueve el pan.**
- **Esperar el asentamiento:** el láser no se enciende hasta ≈ 200–300 ms después de que el servo se detiene (se mide en las pruebas).
- **Si en la prueba el punto "baila":** subir la pared a 4 mm, agrandar la brida a 80 × 80 o añadir un travesaño de 30 × 30 × 3 a media altura.
- **Trípode o marco en A:** solo si el mástil de caja no alcanza; dos patas inclinadas desde la brida hasta la placa superior (en el plano x–z) resisten mejor la torsión. No es necesario para empezar.

## 7. Plano 5 — Bahía y perforaciones

| Elemento | Medida | Dónde |
|---|---|---|
| Paso de cables al mástil | ranura 20 × 8 | pared posterior de la bahía, centrada en x = 100 |
| USB del ESP32 | 14 × 8 | pared lateral derecha, a 20 mm del piso |
| Conector de la fuente | Ø8 a Ø11 (según el jack) | pared posterior, a x = 30 |
| Interruptor | Ø12 | pared posterior, a x = 170 |
| Altavoz de 40 mm | Ø36 + 4 agujeros M3 | pared lateral izquierda |
| LED de estado | Ø5 | pared lateral derecha |
| Ventilación | 4 × Ø5 | pared lateral izquierda y derecha |
| Puerta de acceso | 120 × 35 | pared posterior (opcional) |

Cada módulo lleva **su propio ESP32** (con Bluetooth equivale al Arduino + módulo HC-05 de la diapositiva). **Alimentación:** una entrada de 6 V por módulo (jack o bornera); un adaptador de 6 V/4 A por módulo, o uno de 6 V/8 A con cable en Y por la bisagra. El ESP32 va **lejos del metal y del servo** (la antena no debe quedar tapada por el convertidor ni por cables de servo) y el altavoz tiene su propio retorno a masa.

## 8. Plano 6 — Conjunto de dos módulos (maletín, opcional)

| Elemento | Medida |
|---|---|
| Disposición | dos módulos **girados 180°** y unidos por el borde frontal (y = 255); cada estación queda en un extremo |
| **Largo abierto** | 345 + 345 = **690** mm |
| Ancho | **300** mm |
| **Biombo** (P08) | 300 × **120** × 3, en la bisagra central, plegable hacia uno de los tableros |
| Bisagra | tipo piano, 300 mm de largo |
| **Cerrado** | **345 × 300 × 118** mm (2 × 53 de módulo + 12 de separación entre tableros; mástiles **desmontados** y guardados en la bahía: 30 × 30 × 165 caben en 47 de alto) |
| Cierre y asa | sobre un lado largo |

La rúbrica **no pide** el maletín (la estética vale 0,5): decide si vale el costo.

## 9. Geometría de apuntado (con estas medidas)

Estación en **(100, −65)**, eje de tilt a **h = 180** sobre la matriz.

| Celda (x,y) | Pan (0° = al frente, + derecha) | Tilt (bajo la horizontal) | Distancia | Ángulo de 1 cm |
|---|---|---|---|---|
| (1,1) | −53,6° | 56,8° | 215 mm | 2,66° |
| (20,1) | +53,6° | 56,8° | 215 mm | 2,66° |
| (1,20) | −20,1° | 33,0° | 330 mm | 1,73° |
| (20,20) | +20,1° | 33,0° | 330 mm | 1,73° |
| centro (11,11) | +1,7° | 46,6° | 248 mm | 2,31° |
| (10,1) | −4,1° | 68,7° | 193 mm | 2,96° |
| (10,20) | −1,1° | 34,7° | 316 mm | 1,81° |

- **Rango de servos:** pan **−54° a +54°**, tilt **33° a 69°**. **Límites de software: pan ±57°, tilt de 30° a 72°** — con tilt ≥ 30° el rayo **nunca sale del tablero hacia arriba**.
- **Resolución necesaria:** en la celda más lejana, 1 cm = 1,73°; **±5 mm = ±0,87°**. La banda muerta del MG996R es 0,45–0,9° [hoja]: **alcanza, pero justo**. Por eso: calibrar con tabla medida, acercarse siempre desde el mismo lado y punto de 3 mm.
- **Altura del eje de tilt (h)** y punto resultante: h = 150 → 6,3 mm · **h = 180 → 5,5 mm** · h = 200 → 5,1 mm. Subir h mejora el punto pero estira el mástil; **180 es el equilibrio**.
- **Test de 5 posiciones sugerido** (esquinas + centro, las más exigentes): (1,1), (20,1), (20,20), (1,20), (11,11).

## 10. Piezas y cortes por módulo

| Código | Pieza | Medida (mm) | Cant. | Material |
|---|---|---|---|---|
| P01 | Base | 300 × 345 × 3 | 1 | MDF o acrílico |
| P02a | Pared lateral de la bahía | 300 × 47 × 3 | 2 | MDF o acrílico |
| P02b | Pared frontal / posterior | 294 × 47 × 3 | 2 | MDF o acrílico |
| P03 | Tablero | 300 × 300 × 3 | 1 | MDF mate y oscuro |
| P04 | Cuadrícula impresa | 300 × 300 | 1 | vinilo o papel |
| P05 | Mástil | 30 × 30 × 165, hueco 24 × 24 | 1 | tubo o 4 tablas de 3 |
| P05b | Brida del mástil | 60 × 60 × 3 | 1 | MDF o acrílico |
| P05c | Cartelas del mástil | triángulo 40 × 40 × 3 | 2 | MDF o acrílico |
| P06 | Placa superior del mástil | 60 × 40 × 4, con ranuras ±10 | 1 | acrílico o aluminio |
| P07 | Ménsula de tilt y abrazadera del láser | según el servo y el láser | 1 | impresa 3D |
| P08 | Biombo (opcional) | 300 × 120 × 3 | 1 por maletín | MDF o acrílico |
| P09 | Fichas de flota | 8 × (18 · 28 · 28 · 38 · 48) × 6 | 5 por flota | PLA |
| P10 | Bisagra tipo piano (opcional) | 300 | 1 por maletín | metal |

## 11. Medidas que hay que verificar con las piezas reales

- [ ] Dimensiones del **MG996R** y del **MG90S** (largo, ancho, alto) y **dónde queda su eje de salida** respecto del cuerpo.
- [ ] Largo y diámetro del **KY-008** y de su abrazadera; qué tan rígida es.
- [ ] Tamaño de la **placa del ESP32** y de la **fuente/convertidor**; que entren en 47 mm de alto.
- [ ] **Espesor real** del MDF o acrílico comprado (los 3 mm son nominales).
- [ ] Con el prototipo de la estación: **posición real del eje de pan** y **altura real del eje de tilt**; se usan en la calibración.
- [ ] **De dónde se miden los 5 cm** (sección 12): el diseño cumple 50 mm desde la base y 53 desde la mesa.

## 12. Decisiones tomadas y puntos abiertos

**Decididas (Sebas, 3-nov):**

- **Numeración 1 a 20** en los dos ejes, con (1,1) en la esquina más cercana a la estación.
- **Cada tablero tiene su propio puntero**: dos estaciones, **un ESP32 por módulo**.
- **Comunicación:** lo dicho por Almario es **Arduino con módulo Bluetooth**; el **ESP32 se permite porque trae Bluetooth y Wi-Fi integrados**. Línea base = **Bluetooth + app propia** (como la rúbrica escrita). La página web por Wi-Fi queda como extra opcional.

**Abiertos:**

1. **"5 cm":** ¿desde la base o desde la mesa? El diseño cumple las dos lecturas (50 y 53 mm).
2. **Tu dibujo:** ¿el panel alto es el biombo? ¿qué son los dos rectángulos junto al círculo en la planta?
3. **¿Tu celular (y el del compañero) es Android o iPhone?** El Bluetooth clásico (el equivalente a un HC-05) solo lo hablan los Android; un iPhone obligaría a otro tipo de Bluetooth (BLE).
4. **¿Con qué haces la app?** MIT App Inventor es lo más rápido; una app nativa es más defendible ante "software original". Ver *Cumplimiento de la rúbrica y huecos*.
5. **¿Quién dispara sobre qué tablero?** Lo leo como "cada estación apunta a su propio tablero con la coordenada que manda el rival"; confirmarlo con Almario junto a lo de los 5 cm.
