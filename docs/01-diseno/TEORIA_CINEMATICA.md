# Teoría, Cinemática y Geometría del Sistema SONAR

Este documento formaliza las bases matemáticas y geométricas implementadas en el núcleo de software (`lib/core`) del proyecto **SONAR** (Batalla Naval con ESP32, Pan-Tilt y Láser) para la asignatura de **Fundamentos de Mecatrónica (UAO)**.

---

## 1. Sistema de Coordenadas y Marco de Referencia

El espacio de juego se modela en un plano cartesiano tridimensional $(X, Y, Z)$ con unidades en milímetros ($\text{mm}$):

- **Origen $(0, 0, 0)$**: Esquina posterior-izquierda de la matriz del tablero, exactamente en la intersección de la primera fila y la primera columna de celdas orientada hacia la base de la torreta.
- **Eje $X$**: Se extiende horizontalmente de izquierda a derecha (valores crecientes conforme nos alejamos del borde izquierdo).
- **Eje $Y$**: Se extiende longitudinalmente desde la parte posterior (cercana a la torreta) hacia el frente (valores positivos crecientes al alejarse).
- **Eje $Z$**: Altura perpendicular desde el plano del tablero hacia arriba.

### Dimensiones de la Matriz y Celdas
- Número de celdas por lado: $N = 20$ (Total de $400$ casillas).
- Tamaño de cada celda: $\text{CELL\_MM} = 10.0\text{ mm}$ ($1\text{ cm}$).
- Posición del centro de una celda $(x, y)$ donde $x, y \in \{1, 2, \dots, 20\}$:
  $$X_c = (x - 0.5) \cdot \text{CELL\_MM}$$
  $$Y_c = (y - 0.5) \cdot \text{CELL\_MM}$$

---

## 2. Posición de la Estación Pan-Tilt

La torreta se encuentra montada fuera o en el borde posterior de la matriz, definida por la estructura:
- Posición del eje de rotación de Pan: $\text{STATION\_X\_MM} = 100.0\text{ mm}$, $\text{STATION\_Y\_MM} = -65.0\text{ mm}$.
- Altura del eje de Tilt sobre el plano del tablero: $\text{TILT\_H_MM} = 180.0\text{ mm}$.

---

## 3. Cinemática Inversa: De Coordenadas Cartesianas a Ángulos de Pan y Tilt

Para que el láser láser apunte exactamente al centro de la celda objetivo $(X_c, Y_c)$, el sistema calcula las distancias relativas desde el centro de giro del Pan:
$$\Delta X = X_c - \text{STATION\_X\_MM}$$
$$\Delta Y = Y_c - \text{STATION\_Y\_MM}$$

### Ángulo de Pan ($\theta_{pan}$)
Corresponde a la orientación horizontal (azimut) de la torreta:
$$\theta_{pan} = \text{atan2}(\Delta X, \Delta Y)$$
Convertido a grados:
$$\theta_{pan, deg} = \theta_{pan} \cdot \frac{180.0}{\pi}$$
*Convención*: $0^\circ$ apunta exactamente al frente (paralelo al eje $Y$), valores positivos giran a la derecha.

### Ángulo de Tilt ($\theta_{tilt}$)
Corresponde a la elevación vertical. La distancia horizontal proyectada desde el eje hasta el objetivo es:
$$d_{horiz} = \sqrt{(\Delta X)^2 + (\Delta Y)^2}$$
El ángulo de declinación vertical (ángulo bajo la horizontal) es:
$$\theta_{tilt} = \text{atan2}(\text{TILT\_H\_MM}, d_{horiz})$$
Convertido a grados:
$$\theta_{tilt, deg} = \theta_{tilt} \cdot \frac{180.0}{\pi}$$

---

## 4. Compensación de Holgura (Backlash)

Los servomotores y trenes de engranajes mecánicos sufren de histéresis o juego mecánico (backlash). Para evitar errores de posicionamiento al cambiar de dirección:
- El firmware calcula la diferencia entre la posición actual y la posición objetivo.
- Si el movimiento requiere reducir el ángulo ($\text{target} < \text{current}$), el sistema realiza un **overshoot** preliminar superando el objetivo por $\text{OVERSHOOT\_DEG} = 2.0^\circ$ y luego regresa a la posición exacta desde la misma dirección mecánica. Esto tensa los engranajes de forma idéntica en cada disparo.

---

## 5. Calibración y Persistencia NVS

La calibración de fábrica y los ajustes finos individuales de cada torreta (trims angulares) se guardan en la memoria no volátil (NVS Flash) del ESP32 mediante un bloque binario protegido por **CRC16-CCITT**:
- Estructura serializada de $25$ bytes: Magic (`'D'`, `'L'`), versión ($1$), estación $(X, Y, H)$, trims de Pan y Tilt, y checksum CRC16.
