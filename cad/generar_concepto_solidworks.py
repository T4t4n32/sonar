import os, math, sys, pythoncom, win32com.client
from win32com.client import VARIANT
OUT = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 20        # N = casillas por lado de la matriz de 200 mm
PITCH = 200.0 / N
sw = win32com.client.Dispatch("SldWorks.Application"); sw.Visible = True
sw.CloseAllDocuments(True)
model = sw.NewDocument(sw.GetUserPreferenceStringValue(8), 0, 0, 0)
nul = VARIANT(pythoncom.VT_DISPATCH, None)
mm = lambda v: v / 1000.0
visto = set(); cuerpos = []
def color(rgb):
    try:
        for b in model.GetBodies2(0, False):
            if b.Name not in visto:
                visto.add(b.Name)
                b.MaterialPropertyValues = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [rgb[0]/255, rgb[1]/255, rgb[2]/255, 0.6, 0.8, 0.5, 0.3, 0, 0])
    except Exception as e:
        print("color:", e)
def boss(plano, dibujar, inicio, largo, rgb):
    model.ClearSelection2(True)
    model.Extension.SelectByID2(plano, "PLANE", 0, 0, 0, False, 0, nul, 0)
    sk = model.SketchManager; sk.InsertSketch(True); dibujar(sk); sk.InsertSketch(True)
    f = model.FeatureManager.FeatureExtrusion2(True, False, False, 0, 0, mm(largo), mm(largo), False, False, False, False, 0, 0, False, False, False, False, False, True, True, 3, mm(inicio), False)
    if f is None: print("FALLÓ una operación", plano, inicio, largo)
    try:
        sf = model.FeatureByPositionReverse(1); sf.Select2(False, 0); model.BlankSketch()
    except Exception: pass
    color(rgb); return f
def rect(sk, cx, cy, w, h): sk.CreateCenterRectangle(mm(cx), mm(cy), 0, mm(cx + w/2), mm(cy + h/2), 0)
TOP, FRONT = "Planta", "Alzado"     # Planta: croquis x=X, y=-Z, extruye hacia +Y · Alzado: x=X, y=Y, extruye hacia +Z
GRIS, NEGRO, AZUL, NARANJA, ROJO, ACERO, VERDE = (70,74,82), (28,30,34), (46,84,130), (230,120,30), (220,30,30), (150,158,168), (30,110,80)
# ---- bandeja (base del maletín): 380 x 440, alto 75 ; z de -220 a +220
boss(TOP, lambda s: rect(s, 0, 0, 380, 440), 0, 4, GRIS)
def anillo(s, ow, oh, iw, ih, cx=0, cy=0): rect(s, cx, cy, ow, oh); rect(s, cx, cy, iw, ih)
boss(TOP, lambda s: anillo(s, 380, 440, 372, 432), 4, 71, GRIS)
# ---- tablero de posicionamiento: 4 postes + placa 300x300 a 50 mm sobre la base, matriz de N x N agujeros
for (px, pz) in ((-135, 90), (135, 90), (-135, -170), (135, -170)):
    boss(TOP, lambda s, px=px, pz=pz: s.CreateCircleByRadius(mm(px), mm(-pz), 0, mm(6)), 4, 50, ACERO)
def placa_matriz(s, cx, cy, lado, n, paso, rad):
    rect(s, cx, cy, lado, lado)
    for i in range(n):
        for j in range(n):
            s.CreateCircleByRadius(mm(cx - 100 + paso/2 + i*paso), mm(cy - 100 + paso/2 + j*paso), 0, mm(rad))
boss(TOP, lambda s: placa_matriz(s, 0, 40, 300, N, PITCH, min(3.0, PITCH*0.3)), 54, 4, NEGRO)      # centro del tablero en z=+40 -> y=-40
# ---- tapa abierta a 90° (fondo, z>0): panel + aro, matriz vertical 220x220 con N x N agujeros y tira LED roja
boss(FRONT, lambda s: rect(s, 0, 75 + 220, 380, 440), -226, 4, AZUL)
boss(FRONT, lambda s: anillo(s, 380, 440, 372, 432, 0, 75 + 220), -222, 36, AZUL)
for (px, py) in ((-95, 84), (95, 84), (-95, 304), (95, 304)):
    boss(FRONT, lambda s, px=px, py=py: s.CreateCircleByRadius(mm(px), mm(py), 0, mm(5)), -222, 16, ACERO)
boss(FRONT, lambda s: placa_matriz(s, 0, 194, 220, N, PITCH, min(3.0, PITCH*0.3)), -206, 6, NEGRO)
boss(FRONT, lambda s: rect(s, 0, 75 + 440 - 18, 340, 8), -209, 4, ROJO)
# ---- torreta (levantada), frente z=-170: base con articulación, mástil, servo pan, soporte, servo tilt, láser
boss(TOP, lambda s: rect(s, 0, -170, 70, 50), 4, 14, ACERO)                    # base + pestillo
boss(TOP, lambda s: rect(s, 0, -170, 30, 30), 18, 104, NARANJA)               # mástil (se abate sobre el tablero: opción B/C)
boss(TOP, lambda s: rect(s, 0, -170, 41, 20), 122, 43, NEGRO)                  # servo MG996R (pan)
boss(TOP, lambda s: rect(s, 0, -170, 56, 34), 165, 4, ACERO)                   # placa del soporte pan-tilt
boss(TOP, lambda s: rect(s, -22, -170, 4, 30), 169, 46, ACERO)                 # soporte U (lado izq.)
boss(TOP, lambda s: rect(s, 22, -170, 4, 30), 169, 46, ACERO)                  # soporte U (lado der.)
boss(FRONT, lambda s: rect(s, 0, 194, 20, 43), 149, 41, NEGRO)               # servo tilt, eje en y=194 (centro de la matriz)
boss(FRONT, lambda s: s.CreateCircleByRadius(0, mm(194), 0, mm(3)), 118, 30, ROJO)   # módulo láser Ø6 apuntando a la tapa (+Z)
# ---- cajas de electrónica y batería (frente), asa
boss(TOP, lambda s: rect(s, 125, -160, 100, 90), 4, 50, VERDE)
boss(TOP, lambda s: rect(s, -125, -160, 100, 90), 4, 50, VERDE)
boss(TOP, lambda s: rect(s, 0, -233, 160, 14), 30, 14, GRIS)
model.ViewZoomtofit2()
try:
    model.ViewDisplayShaded(); model.ShowNamedView2("*Isométrica", 7); model.ViewZoomtofit2()
except Exception as e: print("vista:", e)
r = model.SaveAs3(OUT + ".SLDPRT", 0, 2)
print("guardado:", r, os.path.exists(OUT + ".SLDPRT"), os.path.getsize(OUT + ".SLDPRT") // 1024, "KB", flush=True)
model.SaveAs3(OUT + "_iso.png", 0, 1)
try:
    model.ShowNamedView2("*Superior", 5); model.ViewZoomtofit2(); model.SaveAs3(OUT + "_planta.png", 0, 1)
    model.ShowNamedView2("*Derecha", 4); model.ViewZoomtofit2(); model.SaveAs3(OUT + "_perfil.png", 0, 1)
    model.ShowNamedView2("*Isométrica", 7); model.ViewZoomtofit2()
except Exception as e: print("vistas extra:", e)
print("cuerpos:", len(model.GetBodies2(0, False)), flush=True)
