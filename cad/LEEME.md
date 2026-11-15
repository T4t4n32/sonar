# CAD de SONAR (concepto v1, 2026-11-08)

- `SONAR_concepto_v1_vista.png` — vista conceptual limpia (3D + perfil con medidas). **Esta es la que se le muestra al compañero/profesor.**
- `SONAR_concepto_v1.SLDPRT` — modelo **nativo de SolidWorks 2026**, generado por API (`generar_concepto_solidworks.py`, N = casillas por lado). **En obra:** 22 cuerpos bien ubicados, pero **faltan 3 operaciones** (aro de la tapa, placa de la matriz vertical con sus agujeros y el módulo láser), no tiene colores y hay que ocultar croquis y ajustar la vista. Próximo paso: corregirlas y pasar a ensamblaje.
- `generar_vista_concepto.py` — dibuja la vista conceptual con las mismas medidas (matplotlib).
- Borradores de Sebas (en `Marco\` del archivo): `V1.SLDPRT` (placa 300 × 374 × 50 mm con hueco cuadrado y ranura oval) y `Tablero.SLDPRT` (marco 220 × 220 × 40 mm con 20 × 20 agujeros a 1 cm).

## Medidas del concepto (mm) — supuestos a confirmar
Bandeja 380 × 440 × 75 · tablero 300 × 300 a 50 mm sobre la base (rúbrica) con zona de batalla 20 × 20 cm · tapa de 380 × 440, abierta a 90° · matriz vertical 220 × 220 centrada a 194 mm de altura · torreta con eje de tilt a 194 mm (misma altura que el centro de la matriz: ángulos pequeños) · distancia láser → matriz ≈ 350 mm (±0,8° por casilla de 1 cm, ±1,6° con 2 cm) · mástil que se abate sobre el tablero (opción B/C de `TORRETA_ABATIBLE.md`).

## Para rehacer con otra rejilla
`python generar_concepto_solidworks.py <salida> 10` (10 × 10 casillas de 2 cm si Almario lo acepta).
