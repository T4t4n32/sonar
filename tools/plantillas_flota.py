"""Plantillas de flota: 5 disposiciones numeradas, una hoja imprimible por cada una y el mismo dato para la app.

Fuente única de las plantillas (aquí). Genera:
  - docs/impresos/plantillas-flota-1-a-5.pdf   5 hojas (carta horizontal) con la matriz 20x20 cm a tamaño real
  - app/src/core/plantillas.ts                 las mismas 5 disposiciones, numeradas, para la app
Uso:  uv run --with reportlab python tools/plantillas_flota.py

Flota (consigna del profesor): 3 embarcaciones de 2 casillas (E1-E3) + 2 submarinos de 4 (S1-S2), horizontal o vertical.
(x,y) con x a la derecha e y hacia arriba; (1,1) abajo-izquierda. `x,y` es la casilla ancla (la de menor x o y).
"""
import os
import sys

# id, tipo, largo, x, y, orientación
PLANTILLAS = [
    [("S1", 4, 3, 12, "V"), ("S2", 4, 11, 4, "H"), ("E1", 2, 16, 15, "H"), ("E2", 2, 8, 9, "V"), ("E3", 2, 5, 3, "H")],
    [("S1", 4, 2, 17, "H"), ("S2", 4, 17, 5, "V"), ("E1", 2, 10, 12, "V"), ("E2", 2, 6, 7, "H"), ("E3", 2, 13, 18, "H")],
    [("S1", 4, 18, 13, "V"), ("S2", 4, 4, 9, "H"), ("E1", 2, 10, 3, "H"), ("E2", 2, 13, 10, "V"), ("E3", 2, 2, 3, "V")],
    [("S1", 4, 9, 16, "H"), ("S2", 4, 3, 4, "V"), ("E1", 2, 15, 9, "H"), ("E2", 2, 11, 7, "V"), ("E3", 2, 17, 2, "H")],
    [("S1", 4, 6, 13, "V"), ("S2", 4, 13, 13, "H"), ("E1", 2, 1, 8, "V"), ("E2", 2, 9, 6, "H"), ("E3", 2, 19, 5, "V")],
]


def cells(s):
    _, n, x, y, o = s
    return [(x + i, y) if o == "H" else (x, y + i) for i in range(n)]


def validar():
    for k, fleet in enumerate(PLANTILLAS, 1):
        ids = sorted(s[0] for s in fleet)
        assert ids == ["E1", "E2", "E3", "S1", "S2"], (k, ids)
        occ = {}
        for s in fleet:
            assert s[1] == (4 if s[0][0] == "S" else 2), (k, s)
            for c in cells(s):
                assert 1 <= c[0] <= 20 and 1 <= c[1] <= 20, (k, s, c)
                assert c not in occ, (k, "solape", s, occ.get(c))
                occ[c] = s[0]
        for s in fleet:  # sin barcos pegados (ni en diagonal): se pinta sin dudas
            for (x, y) in cells(s):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        o = occ.get((x + dx, y + dy))
                        assert o in (None, s[0]), (k, s[0], "toca a", o)
        assert len(occ) == 14, (k, len(occ))


def ts():
    out = ["// GENERADO por tools/plantillas_flota.py: no editar a mano. Las mismas 5 disposiciones que las hojas impresas.",
           "import type { PlacedShip } from './types'", "",
           "export interface PlantillaFlota { n: number; nombre: string; barcos: PlacedShip[] }", "",
           "const B = (id: string, len: number, x: number, y: number, orient: 'H' | 'V'): PlacedShip =>",
           "  ({ id, kind: id.startsWith('S') ? 'submarino' : 'embarcacion', len, x, y, orient })", "",
           "export const PLANTILLAS: PlantillaFlota[] = ["]
    for k, fleet in enumerate(PLANTILLAS, 1):
        bs = ", ".join(f"B('{i}', {n}, {x}, {y}, '{o}')" for (i, n, x, y, o) in fleet)
        out.append(f"  {{ n: {k}, nombre: 'Plantilla {k}', barcos: [{bs}] }},")
    out.append("]")
    return "\n".join(out) + "\n"


def pdf(path):
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    W, H = landscape(letter)
    N, C = 20, 10 * mm
    x0, y0 = (W - N * C) / 2, (H - N * C) / 2
    c = canvas.Canvas(path, pagesize=(W, H))
    c.setTitle("SONAR - plantillas de flota 1 a 5")

    def cen(x, y):
        return x0 + (x - 0.5) * C, y0 + (y - 0.5) * C

    for k, fleet in enumerate(PLANTILLAS, 1):
        # contorno de cada barco (para pintar dentro)
        for (i, n, x, y, o) in fleet:
            w, h = (n * C, C) if o == "H" else (C, n * C)
            c.setFillGray(0.88 if i[0] == "S" else 0.94)
            c.rect(x0 + (x - 1) * C, y0 + (y - 1) * C, w, h, stroke=0, fill=1)
        # rejilla
        for i in range(N + 1):
            major = i % 5 == 0
            c.setStrokeGray(0.0 if major else 0.55)
            c.setLineWidth(0.7 if major else 0.25)
            c.line(x0 + i * C, y0, x0 + i * C, y0 + N * C)
            c.line(x0, y0 + i * C, x0 + N * C, y0 + i * C)
        # contornos gruesos y rótulo de cada barco
        for (i, n, x, y, o) in fleet:
            w, h = (n * C, C) if o == "H" else (C, n * C)
            c.setStrokeGray(0.0)
            c.setLineWidth(1.6)
            c.rect(x0 + (x - 1) * C, y0 + (y - 1) * C, w, h, stroke=1, fill=0)
            cx, cy = cen(x, y)
            c.setFillGray(0.25)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 2, i)
        # numeración
        c.setFillGray(0)
        c.setFont("Helvetica", 6)
        for i in range(1, N + 1):
            cx, cy = cen(i, i)
            c.drawCentredString(cx, y0 - 3.2 * mm, str(i))
            c.drawCentredString(cx, y0 + N * C + 1.6 * mm, str(i))
            c.drawRightString(x0 - 1.5 * mm, cy - 2, str(i))
            c.drawString(x0 + N * C + 1.5 * mm, cy - 2, str(i))
        # marcas de esquina (alinear la hoja con la matriz física)
        c.setLineWidth(0.8)
        for (x, y) in ((1, 1), (20, 1), (20, 20), (1, 20)):
            cx, cy = cen(x, y)
            c.circle(cx, cy, 3 * mm, stroke=1, fill=0)
        # panel izquierdo
        c.setFillGray(0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(6 * mm, H - 20 * mm, f"PLANTILLA {k}")
        c.setFont("Helvetica", 6.5)
        lines = ["Pinta SOLO los barcos", "(azul o verde, NO negro:", "el laser rojo debe verse).", "",
                 "S = submarino de 4", "E = embarcacion de 2", "", "(x,y): x derecha, y arriba", "(1,1) abajo-izquierda", ""]
        for (i, n, x, y, o) in fleet:
            fin = (x + n - 1, y) if o == "H" else (x, y + n - 1)
            lines.append(f"{i}: ({x},{y}) a ({fin[0]},{fin[1]})")
        lines += ["", "IMPRIMIR AL 100 %", "(sin ajustar a la pagina)."]
        for j, t in enumerate(lines):
            c.drawString(6 * mm, H - (30 + 3.9 * j) * mm, t)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x0 + N * C + 6 * mm, y0 - 1 * mm, "ESTACION")
        c.drawString(x0 + N * C + 6 * mm, y0 - 5 * mm, "abajo")
        c.showPage()
    c.save()


if __name__ == "__main__":
    validar()
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    with open(os.path.join(root, "app", "src", "core", "plantillas.ts"), "w", encoding="utf-8", newline="\n") as f:
        f.write(ts())
    os.makedirs(os.path.join(root, "docs", "impresos"), exist_ok=True)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "docs", "impresos", "plantillas-flota-1-a-5.pdf")
    pdf(out)
    print("OK", out)
