"""Genera la cuadrícula 20x20 (casillas de 1 cm) para imprimir a tamaño real.
(1,1) abajo-izquierda, x a la derecha, y hacia arriba: igual que la app y el firmware.
Uso: uv run --with reportlab tools/cuadricula_matriz.py [salida.pdf]
"""
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm

out = sys.argv[1] if len(sys.argv) > 1 else "docs/impresos/cuadricula-matriz-20x20.pdf"
W, H = landscape(letter)            # 279.4 x 215.9 mm
N, C = 20, 10 * mm / 10 * 10        # 20 casillas de 10 mm
C = 10 * mm
x0 = (W - N * C) / 2
y0 = (H - N * C) / 2
c = canvas.Canvas(out, pagesize=(W, H))
c.setTitle("SONAR - cuadricula 20x20")

# rejilla
for i in range(N + 1):
    major = i % 5 == 0
    c.setStrokeGray(0.0 if major else 0.55)
    c.setLineWidth(0.7 if major else 0.25)
    c.line(x0 + i * C, y0, x0 + i * C, y0 + N * C)
    c.line(x0, y0 + i * C, x0 + N * C, y0 + i * C)

def centro(x, y):
    return x0 + (x - 0.5) * C, y0 + (y - 0.5) * C

# puntos centro de cada casilla (el láser se ve mejor sobre una marca)
c.setFillGray(0.35)
for x in range(1, N + 1):
    for y in range(1, N + 1):
        cx, cy = centro(x, y)
        c.circle(cx, cy, 0.35, stroke=0, fill=1)

# esquinas de calibración y control
for (x, y), nom in {(1, 1): "1", (20, 1): "2", (20, 20): "3", (1, 20): "4", (11, 11): "5 control"}.items():
    cx, cy = centro(x, y)
    c.setStrokeGray(0); c.setLineWidth(0.8)
    c.circle(cx, cy, 3 * mm, stroke=1, fill=0)
    c.line(cx - 4 * mm, cy, cx + 4 * mm, cy)
    c.line(cx, cy - 4 * mm, cx, cy + 4 * mm)

# numeración
c.setFillGray(0)
c.setFont("Helvetica", 6)
for i in range(1, N + 1):
    cx, cy = centro(i, i)
    c.drawCentredString(cx, y0 - 3.2 * mm, str(i))
    c.drawCentredString(cx, y0 + N * C + 1.6 * mm, str(i))
    c.drawRightString(x0 - 1.5 * mm, cy - 2, str(i))
    c.drawString(x0 + N * C + 1.5 * mm, cy - 2, str(i))

# textos laterales (margen izquierdo de ~30 mm)
c.setFont("Helvetica-Bold", 8)
c.drawString(6 * mm, H - 12 * mm, "SONAR 20x20")
c.setFont("Helvetica", 6.5)
for k, t in enumerate([
    "Casillas de 1 cm.", "(1,1) abajo-izq.", "x a la derecha,", "y hacia arriba.", "",
    "Circulos 1-4:", "esquinas de", "calibracion.", "Circulo 5:", "control (11,11).", "",
    "IMPRIMIR AL 100 %", "(sin ajustar", "a la pagina)."]):
    c.drawString(6 * mm, H - (18 + 3.8 * k) * mm, t)
c.setLineWidth(0.8)
c.line(6 * mm, 40 * mm, 36 * mm, 40 * mm)
c.drawString(6 * mm, 36 * mm, "= 3 cm exactos")
c.setFont("Helvetica-Bold", 7)
c.drawString(x0 + N * C + 6 * mm, y0 - 1 * mm, "ESTACION")
c.drawString(x0 + N * C + 6 * mm, y0 - 5 * mm, "abajo")
c.save()
print(out)
