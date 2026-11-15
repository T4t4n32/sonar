import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
OUT = sys.argv[1]
# cajas (x0,x1, y0,y1, z0,z1) en mm; y = altura, +z = frente
GRIS, NEGRO, AZUL, NAR, ROJO, ACE, VERDE = "#5b6270", "#23262b", "#2f5f95", "#e8791e", "#d92b2b", "#9aa3b0", "#2d8a63"
B = []
def box(x0, x1, y0, y1, z0, z1, c, a=1.0): B.append((x0, x1, y0, y1, z0, z1, c, a))
box(-190, 190, 0, 4, -220, 220, GRIS)                                   # bandeja
for x0, x1, z0, z1 in ((-190, -186, -220, 220), (186, 190, -220, 220), (-190, 190, 216, 220), (-190, 190, -220, -216)): box(x0, x1, 4, 75, z0, z1, GRIS, .55)
for px, pz in ((-135, 90), (135, 90), (-135, -170), (135, -170)): box(px-6, px+6, 4, 54, pz-6, pz+6, ACE)
box(-150, 150, 54, 58, -190, 110, NEGRO)                                # tablero 30x30 a 50 mm
box(-100, 100, 58.2, 58.6, -140, 60, "#1c6b4a")                         # zona 20x20 de batalla
box(-190, 190, 75, 515, -226, -222, AZUL, .18)                               # tapa (abierta a 90°)
for x0, x1, y0, y1 in ((-190, -186, 75, 515), (186, 190, 75, 515), (-190, 190, 511, 515), (-190, 190, 75, 79)): box(x0, x1, y0, y1, -222, -186, AZUL, .6)
box(-110, 110, 84, 304, -206, -200, NEGRO)                              # matriz vertical 20x20 cm
box(-100, 100, 94, 294, -200.2, -199.8, "#1c6b4a")
for px, py in ((-95, 84), (95, 84), (-95, 304), (95, 304)): box(px-5, px+5, py-5, py+5, -222, -206, ACE)
box(-170, 170, 493, 501, -209, -205, ROJO)                              # tira LED roja
box(-35, 35, 4, 18, 145, 195, ACE); box(-15, 15, 18, 122, 155, 185, NAR) # base + mástil
box(-20.5, 20.5, 122, 165, 160, 180, NEGRO); box(-28, 28, 165, 169, 153, 187, ACE)
box(-24, -20, 169, 215, 155, 185, ACE); box(20, 24, 169, 215, 155, 185, ACE)
box(-10, 10, 172, 215, 149, 190, NEGRO); box(-3, 3, 191, 197, 118, 148, ROJO)   # servo tilt + láser
box(75, 175, 4, 54, 115, 205, VERDE); box(-175, -75, 4, 54, 115, 205, VERDE)    # electrónica y batería
box(-80, 80, 30, 44, 225, 240, GRIS)                                    # asa
box(-15, 15, 60, 80, -80, 160, NAR, .22)                                # mástil abatido sobre el tablero (fantasma)
fig = plt.figure(figsize=(15, 8.2), dpi=110); ax = fig.add_subplot(1, 2, 1, projection="3d")
def faces(x0, x1, y0, y1, z0, z1):
    P = lambda x, y, z: (x, -z, y)
    v = [P(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    i = lambda a, b, c: v[a*4 + b*2 + c]
    return [[i(0,0,0), i(1,0,0), i(1,1,0), i(0,1,0)], [i(0,0,1), i(1,0,1), i(1,1,1), i(0,1,1)], [i(0,0,0), i(0,1,0), i(0,1,1), i(0,0,1)],
            [i(1,0,0), i(1,1,0), i(1,1,1), i(1,0,1)], [i(0,0,0), i(1,0,0), i(1,0,1), i(0,0,1)], [i(0,1,0), i(1,1,0), i(1,1,1), i(0,1,1)]]
for x0, x1, y0, y1, z0, z1, c, a in sorted(B, key=lambda b: (b[4]+b[5])/2):
    ax.add_collection3d(Poly3DCollection(faces(x0, x1, y0, y1, z0, z1), facecolors=c, edgecolors="#10141a", linewidths=.25, alpha=a))
ax.plot([0, 0], [-118, 220], [194, 194], color="#ff4040", lw=1.4, ls="--")     # rayo láser hacia la matriz vertical
ax.set_xlim(-230, 230); ax.set_ylim(-260, 260); ax.set_zlim(0, 520); ax.set_box_aspect((460, 520, 520)); ax.view_init(elev=22, azim=-58)
ax.set_axis_off()
ax.text2D(0.01, 0.97, '1  Tapa abierta a 90°: matriz VERTICAL 20×20 cm + tira LED roja\n2  Tablero 30×30 cm a 50 mm; zona de batalla 20×20 cm (barcos)\n3  Torreta pan-tilt (2× MG996R + láser), se abate sobre el tablero\n4  Cajas de electrónica y batería (frente)\n- - -  rayo láser hacia la matriz vertical', transform=ax.transAxes, fontsize=8.8, va='top', bbox=dict(boxstyle='round', fc='#f4f4f4', ec='#999'))
ax.set_title("SONAR · Batalla Naval — concepto de maletín (abierto)", fontsize=13, pad=0)
bx = fig.add_subplot(1, 2, 2); bx.set_aspect("equal"); bx.set_xlim(-250, 250); bx.set_ylim(-10, 540)
# perfil lateral: eje horizontal = z (frente a la derecha), vertical = y
for x0, x1, y0, y1, z0, z1, c, a in B:
    if x0 <= 0 <= x1 or (x0 < 0 and x1 > 0): bx.add_patch(plt.Rectangle((-z1, y0), z1 - z0, y1 - y0, fc=c, ec="#10141a", lw=.4, alpha=min(1, a + .1)))
bx.invert_xaxis()
bx.annotate("", xy=(-203, 194), xytext=(-148, 194), arrowprops=dict(arrowstyle="->", color="#d92b2b", lw=1.6))
bx.text(-170, 215, "rayo", color="#d92b2b", fontsize=9, ha="center")
bx.text(0, 10, "D ≈ 350 mm del láser a la matriz  →  ±0,8° por casilla de 1 cm  ·  ±1,6° con casillas de 2 cm", fontsize=8.5, ha="center")
bx.text(215, 128, "mástil\n(se abate\nsobre el\ntablero)", fontsize=8, color="#b85a0a", ha="left")
bx.set_title("Perfil (corte por el centro): tapa a la izquierda, torreta al frente (derecha)", fontsize=10)
bx.set_xlabel("profundidad z (mm)"); bx.set_ylabel("altura (mm)"); bx.grid(alpha=.25)
plt.tight_layout(); plt.savefig(OUT); print("ok")
