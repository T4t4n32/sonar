# Flujo del juego «SONAR · Batalla Naval» (borrador v0 — dictado por Sebas, 2026-11-07)

Estado: **especificación en borrador**. Lo marcado con **[SUPUESTO]** lo rellenó Claude y falta que Sebas lo confirme. Las decisiones abiertas están al final.

## El flujo (lo que dijo Sebas)
1. Cada jugador abre la aplicación. Son **parejas**: se **vinculan a una misma partida**.
2. Cada uno **escoge bando: rojo o azul**.
3. El juego **elige al azar** quién **posiciona primero sus barcos** (y por tanto quién empieza a disparar).
4. Ese jugador coloca su flota (**5 o 6 barcos**, «según el juego original») sobre el tablero (el que está acostado, abajo).
5. El **ESP32 guarda las posiciones de ambos bandos**; solo el ESP32 las conoce y se las comparte (entre módulos). Las posiciones del rival **no** llegan al celular del otro.
6. Cuando todo está **sincronizado y listo**, empieza la partida con el jugador que colocó primero.
7. En su turno, el jugador **escribe la coordenada** donde cree que hay un barco y la manda.
8. Si **falla**: animación + indicación de **«fallaste»** en su celular, y las **tiras LED rojas** se encienden indicando el fallo.
9. Al **bando contrario le llega la coordenada** que mandó el atacante (se ve el disparo recibido).
10. Se alternan los turnos hasta que **uno acabe con la flota del otro**.
11. Al final se muestra **ganador y perdedor** y las **estadísticas**.

## Máquina de estados (lo que implica)
`SIN_PARTIDA → VINCULANDO → ESCOGIENDO_BANDO → SORTEO → COLOCANDO_A → COLOCANDO_B [SUPUESTO: el otro también coloca, sin mirar] → SINCRONIZANDO → TURNO_A ⇄ TURNO_B → FIN → ESTADÍSTICAS`
Transiciones extra necesarias: desconexión/reconexión de un celular (la partida vive en el ESP32), pausa, abandono, tiempo máximo por turno [SUPUESTO], reinicio.

## Quién sabe qué (secreto)
- Los **celulares son solo pantalla y teclado**: nunca reciben la flota rival (salvo al final, para mostrarla).
- Los **módulos son el árbitro**: cada disparo se resuelve en el hardware y responde `AGUA`, `TOCADO` o `HUNDIDO` (+ barco) [SUPUESTO].
- Enlace **módulo ↔ módulo** (ESP-NOW, sin router) y **celular ↔ su módulo** por Bluetooth (lo que pide la rúbrica).

## Pantallas de la aplicación
Lobby (crear / unirse con código) → Bando (rojo/azul) → Sorteo → Colocar flota → Esperando al rival → Batalla (radar propio + radar de disparos) → Fin (ganador/perdedor) → Estadísticas.

## Estadísticas [SUPUESTO]
Disparos, aciertos, fallos, precisión, racha máxima de aciertos, barcos hundidos y en qué turno, duración total y por turno.

## Decisiones de Sebas (2026-11-07, segunda ronda) — **mandan sobre lo anterior**
- **Rúbrica fija (Almario): matriz de 20×20, cada casilla de 1 cm × 1 cm.** No se reduce la zona de juego (se retira la idea de 10×10 con bloques de 2×2).
- **Cama de abajo = matriz de fotorresistencias (LDR)** donde se colocan **barcos físicos**; el ESP32 detecta las posiciones solo. La colocación **no** es virtual en la app (quitaría dinamismo).
- **Matriz vertical = la que apunta el láser**, con **fotodetectores** (fotoeléctrico) para detectar el punto al instante y **medir el tiempo**.
- **Árbitro:** los **dos ESP32 conocen internamente las posiciones de ambos bandos**; no se preguntan nada tras cada disparo.
- **Dos láseres:** cada módulo tiene el suyo; cuando un bando apunta a `(x,y)`, **ambos láseres apuntan a esa zona** de la matriz vertical.

## Evaluación técnica de Claude (propuesta, por validar con un prototipo)
Cifras marcadas «est.» son estimaciones mías, no mediciones.
1. **Árbitro replicado (adoptado):** los dos módulos ejecutan el **mismo motor de reglas determinista** con los mismos eventos (mapas de flota + disparos, ordenados por un módulo «secuenciador»). Sin consulta por disparo; con número de secuencia, confirmación y huella periódica del estado para detectar desajustes. Es lógica pura y se prueba aquí sin hardware.
2. **Lazo cerrado (la gran ventaja de tus fotodetectores):** si la matriz vertical dice dónde cayó el punto, el test de 5 posiciones se **valida solo** (PASS/FAIL por celda) y se puede **autocalibrar** el apuntado. Eso ataca los 2,0 puntos del test.
3. **Matriz vertical (detectar el punto al instante):** fototransistor + resistencia por celda, lectura **digital** con una cadena de registros de desplazamiento (p. ej. 50 × 74HC165 = 400 bits; lectura completa en ~decenas de µs, est.). Sin multiplexores ni ADC; el umbral lo da el contraste del láser frente a la luz de la sala (diferencial láser apagado/encendido).
4. **Cama de barcos (presencia):** LDR + divisor por celda leído analógico con multiplexores (el plan eléctrico ya prevé 25 × CD74HC4067, salida común en alta impedancia; ~40 ms por barrido, est.). Riesgos: sombras de manos y luz ambiente (se mitiga con calibración «tablero vacío», lectura estable ~1-2 s y confirmación), derrame de luz entre casillas de 1 cm. **Alternativa por comparar en el prototipo:** contacto (matriz de teclado con diodos y pastillas de cobre bajo la base del barco), inmune a la luz.
5. **Geometría:** el núcleo hoy apunta a un tablero **horizontal** con la estación arriba. Una matriz **vertical** exige un modelo nuevo (plano a distancia `d`: pan = atan((x−xs)/d), tilt = atan((z−zs)/…)); con **dos estaciones** en posiciones distintas, **cada una con su calibración** hacia el mismo punto. Se prueba con pruebas unitarias.
6. **Duración de partida en 20×20 de 1 cm (simulación, jugador «listo», 3 s por disparo, est.):** 2 barcos ≈ 118 disparos (12 min), 3 barcos ≈ 135 (14 min), 5 barcos clásicos ≈ 175 (18 min), 8 barcos ≈ 208 (21 min) — solo tiempo de láser, sin pensar. **Añadir barcos casi no la acorta**: lo que la acorta son mecánicas (p. ej. «ping de sonar» limitado que avisa de barcos a ≤ 2 casillas, o turno extra al acertar). Falta decidir si se quiere.

## Riesgo de calendario (hechos de la agenda)
Control 2 = 15-nov (sistema completo pasa el test 5/5 tres veces) · control 3 = 20-nov (contrincante + video) · congelar 22-nov · entrega 24-nov. Cada matriz son **400 sensores** (800 puntos de soldadura mínimo); con la vertical compartida serían ~1 200 sensores, con una vertical por bando ~1 600. Una placa (PCB) encargada fuera llega, est., en 2-4 semanas: **no llega**. Por eso se propone construir por **capas con puertas de decisión**:
- **Capa 0 (rúbrica, intocable):** un módulo con láser + app pasa el test 5/5. Debe estar sólida el 15-nov.
- **Capa 1:** dos módulos, dos láseres al mismo punto, motor de reglas replicado, partida completa **con colocación manual de respaldo** (si la cama no está lista, los barcos se marcan en la app solo para no perder la demo).
- **Capa 2:** matriz vertical con fotodetectores (lazo cerrado y tiempo).
- **Capa 3:** cama de LDR con detección automática de barcos.
- **Puerta de decisión 10-nov:** prototipo de **un mosaico de 5×5** (LDR y fototransistores) con medidas reales; con eso se decide si el tablero completo cabe en el tiempo.

## Decisiones abiertas
1. ¿La matriz vertical es **una sola compartida** por los dos bandos o **una por bando**? (cambia 400 vs 800 fotodetectores y la geometría de los dos láseres).
2. **Tiras LED rojas:** ¿en qué módulo se encienden al fallar, de qué tipo y de qué largo? (no están en `PLAN_ELECTRONICO.md`; revisar alimentación).
3. **Vinculación** de las dos parejas (recomendado: código de 4 dígitos).
4. ¿Se quiere una mecánica que acorte la partida (ping de sonar / turno extra)?
5. Qué hace el modo «demostración» para el video y la sustentación (flota de 2 barcos, p. ej.).
