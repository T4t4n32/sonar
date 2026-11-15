# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Plano conceptual v2 de SONAR (maletín tipo juguete plegable) en PDF, A3 apaisado, 3 hojas, unidades mm.
Cotas editables arriba del archivo. Es una PROPUESTA a replicar a mano en SolidWorks."""
import sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else "PLANO_SONAR_concepto_v2.pdf"
# ---------------- cotas (mm) ----------------
BAND = 340      # bandeja, lado exterior
PARED = 4       # espesor de paredes y piso
ALTO = 75       # altura de la bandeja
TABLERO = 300   # tablero de posicionamiento (rúbrica)
MATRIZ = 200    # zona de batalla 20x20 cm (rúbrica)
ELEV = 50       # elevación del tablero sobre el piso (rúbrica: 5 cm)
ESP_T = 4       # espesor de la placa del tablero
POSTE = 12      # diámetro de poste
DIV_ALTO = 260  # alto del panel central sobre el borde de la bandeja
DIV_ESP = 30    # espesor del panel central
INT = BAND - 2 * PARED
K, G = "#111", "#777"

def par(lines, w=100):
    return (chr(10)).join(textwrap.fill(l, w, subsequent_indent="   ") if l else "" for l in lines)

def cota(ax, p1, p2, off, txt, vert=False, fs=8):
    (x1, y1), (x2, y2) = p1, p2
    if not vert:
        y = max(y1, y2) + off
        for x, yy in ((x1, y1), (x2, y2)): ax.plot([x, x], [yy + (2 if off > 0 else -2), y + (2 if off > 0 else -2)], color=G, lw=.5)
        ax.annotate("", xy=(x1, y), xytext=(x2, y), arrowprops=dict(arrowstyle="<->", color=K, lw=.7))
        ax.text((x1 + x2) / 2, y + (3 if off > 0 else -3), txt, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:
        x = max(x1, x2) + off
        for xx, y in ((x1, y1), (x2, y2)): ax.plot([xx + (2 if off > 0 else -2), x + (2 if off > 0 else -2)], [y, y], color=G, lw=.5)
        ax.annotate("", xy=(x, y1), xytext=(x, y2), arrowprops=dict(arrowstyle="<->", color=K, lw=.7))
        ax.text(x + (3 if off > 0 else -3), (y1 + y2) / 2, txt, ha="left" if off > 0 else "right", va="center", fontsize=fs, rotation=90)

def rect(ax, x, y, w, h, lw=1.3, ls="-", fill=None, hatch=None, ec=K):
    ax.add_patch(Rectangle((x, y), w, h, fill=fill is not None, fc=fill or "none", ec=ec, lw=lw, ls=ls, hatch=hatch))

def vista(ax, titulo, escala, lim):
    ax.set_aspect("equal"); ax.set_xlim(*lim[:2]); ax.set_ylim(*lim[2:]); ax.axis("off")
    ax.text(lim[0], lim[3], f"{titulo}   (esc. {escala})", fontsize=9.5, fontweight="bold", va="top")

def cajetin(fig, hoja, total, titulo):
    ax = fig.add_axes([.60, .02, .38, .11]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, ec=K, lw=1.2, transform=ax.transAxes))
    ax.plot([0, 1], [.5, .5], color=K, lw=.8, transform=ax.transAxes); ax.plot([.62, .62], [0, .5], color=K, lw=.8, transform=ax.transAxes)
    ax.text(.02, .72, "SONAR · BATALLA NAVAL — PLANO CONCEPTUAL v2", fontsize=10.5, fontweight="bold", va="center")
    ax.text(.02, .27, titulo, fontsize=8.5, va="center")
    ax.text(.64, .35, f"Hoja {hoja}/{total}\n2026-11-08 · unidades: mm", fontsize=8, va="center")
    ax.text(.64, .12, "PROPUESTA: cotas a confirmar con las piezas reales", fontsize=6.5, color="#a00", va="center")

def hoja(titulo, n):
    fig = plt.figure(figsize=(16.54, 11.69))
    fig.add_artist(Rectangle((.012, .012), .976, .976, fill=False, ec=K, lw=1.6, transform=fig.transFigure))
    fig.text(.03, .955, titulo, fontsize=15, fontweight="bold", va="center")
    cajetin(fig, n, 3, titulo); return fig

pdf = PdfPages(OUT)

# =========================== HOJA 1: concepto ===========================
fig = hoja("CONCEPTO GENERAL — maletín portátil tipo «Batalla Naval»", 1)
# (a) frontal cerrado
ax = fig.add_axes([.03, .52, .27, .38]); L = 2 * ALTO + DIV_ESP
vista(ax, "A · Frente, CERRADO", "1:5", (-40, BAND + 40, -50, L + 120))
rect(ax, 0, 0, BAND, L, fill="#e9edf2")
ax.plot([0, BAND], [ALTO, ALTO], color=K, lw=.8, ls=(0, (6, 3))); ax.plot([0, BAND], [ALTO + DIV_ESP, ALTO + DIV_ESP], color=K, lw=.8, ls=(0, (6, 3)))
ax.add_patch(FancyBboxPatch((BAND / 2 - 80, L / 2 - 22), 160, 44, boxstyle="round,pad=2", fc="#fff", ec=K, lw=1.1)); ax.text(BAND / 2, L / 2, "SONAR", ha="center", va="center", fontsize=15, fontweight="bold")
rect(ax, BAND / 2 - 55, L - 3, 110, 14, ls="-", fill="#cfd5dc"); ax.text(BAND / 2, L + 22, "asa oculta (se despliega)", ha="center", fontsize=7.5)
for x in (40, BAND - 40): rect(ax, x - 12, ALTO + 6, 24, 18, fill="#999")
ax.text(BAND / 2, ALTO + 36, "cierres", ha="center", fontsize=7)
cota(ax, (0, 0), (BAND, 0), -22, f"{BAND}"); cota(ax, (0, 0), (0, L), -25, f"{L}", vert=True)
# (b) planta abierta
ax = fig.add_axes([.33, .52, .64, .38]); vista(ax, "B · Planta, ABIERTO PLANO (dos bandejas y panel central)", "1:7", (-30, 2 * BAND + DIV_ESP + 30, -45, BAND + 60))
for x0, lbl in ((0, "JUGADOR A"), (BAND + DIV_ESP, "JUGADOR B")):
    rect(ax, x0, 0, BAND, BAND, fill="#e9edf2"); rect(ax, x0 + (BAND - TABLERO) / 2, (BAND - TABLERO) / 2, TABLERO, TABLERO, fill="#cfd8e3")
    rect(ax, x0 + (BAND - MATRIZ) / 2, (BAND - MATRIZ) / 2, MATRIZ, MATRIZ, lw=1.8, fill="#1b4d3e")
    ax.text(x0 + BAND / 2, BAND / 2, "zona de\nbatalla\n20×20 cm", color="#fff", ha="center", va="center", fontsize=8)
    ax.text(x0 + BAND / 2, BAND + 14, lbl, ha="center", fontweight="bold", fontsize=9)
rect(ax, BAND, 0, DIV_ESP, BAND, fill="#b9c3d0"); ax.text(BAND + DIV_ESP / 2, BAND / 2, "PANEL CENTRAL + bisagra", rotation=90, ha="center", va="center", fontsize=8)
ax.add_patch(Rectangle((BAND + DIV_ESP / 2 - 30, BAND - 5), 60, 14, fc="#e8791e", ec=K)); ax.text(BAND + DIV_ESP / 2, BAND + 30, "torreta A/B", ha="center", fontsize=7.5)
cota(ax, (0, 0), (BAND, 0), -22, f"{BAND}"); cota(ax, (BAND, 0), (BAND + DIV_ESP, 0), -22, f"{DIV_ESP}"); cota(ax, (0, 0), (0, BAND), -25, f"{BAND}", vert=True)
# (c) perfil abierto con torreta
ax = fig.add_axes([.03, .06, .52, .42]); vista(ax, "C · Perfil, ABIERTO (corte por el centro)", "1:4", (-60, BAND + DIV_ESP + 90, -45, ALTO + DIV_ALTO + 90))
rect(ax, 0, 0, BAND, PARED, fill="#8a93a0"); rect(ax, 0, 0, PARED, ALTO, fill="#8a93a0"); rect(ax, BAND - PARED, 0, PARED, ALTO, fill="#8a93a0")
for px in (30, BAND - 30): rect(ax, px - POSTE / 2, PARED, POSTE, ELEV, fill="#9aa3b0")
rect(ax, (BAND - TABLERO) / 2, PARED + ELEV, TABLERO, ESP_T, fill="#23262b")
rect(ax, BAND, 0, DIV_ESP, ALTO + DIV_ALTO, fill="#b9c3d0"); rect(ax, BAND - 8, ALTO + DIV_ALTO - 20, 8 + DIV_ESP, 20, fill="#e8791e")
ax.add_patch(Circle((BAND - 4, ALTO + DIV_ALTO - 8), 4, fc="#fff", ec=K)); ax.add_patch(Circle((BAND + 18, 40), 6, fc="#fff", ec=K)); ax.text(BAND + 36, 40, "bisagra", fontsize=7.5, va="center")
tilt = (BAND - 6, ALTO + DIV_ALTO - 8); ax.plot([tilt[0], 70], [tilt[1], PARED + ELEV + ESP_T], color="#d92b2b", lw=1.2, ls="--"); ax.text(150, 150, "rayo láser", color="#d92b2b", fontsize=8, rotation=-34)
ax.text(BAND + 30, ALTO + DIV_ALTO + 10, "torreta pan-tilt (2× MG996R) + láser", ha="right", fontsize=8)
cota(ax, (0, 0), (0, ALTO), -28, f"{ALTO}", vert=True); cota(ax, (BAND, 0), (BAND, ALTO + DIV_ALTO), 72, f"{ALTO + DIV_ALTO}", vert=True)
cota(ax, (35, PARED), (35, PARED + ELEV), -38, f"{ELEV} (rúbrica)", vert=True, fs=7); ax.text(BAND / 2, ALTO + 14, "cavidad bajo el tablero: batería, ESP32, reductores", ha="center", fontsize=8, color="#555")
# (d) notas
ax = fig.add_axes([.58, .17, .40, .32]); ax.axis("off")
ax.text(0, 1, "LO QUE ENTENDÍ DE TUS BOCETOS (a confirmar)", fontsize=10, fontweight="bold", va="top")
ax.text(0, .9, par(["1  Dos bandejas (una por jugador) y un panel central doble que se pliega: como el juguete.",
 "2  La torreta va ARRIBA del panel central, apuntando hacia abajo a la matriz del tablero.",
 "3  Cerrado es un maletín de mano con asa oculta, cierres y la placa «SONAR» al frente.",
 "4  Bajo el tablero (elevado 50 mm) queda una cavidad para electrónica y batería.",
 "5  Recortes laterales: interruptor y conector de carga (tus rectángulos pequeños).",
 "", "CONFIRMA: ¿una torreta por lado del panel (A y B) o una sola que gira?",
 "CONFIRMA: ¿el panel central lleva además una cuadrícula vertical (como el juguete)?"]), fontsize=8.5, va="top", linespacing=1.5)
pdf.savefig(fig); fig.savefig(OUT.replace(".pdf", "_h1.png"), dpi=70); plt.close(fig)

# =========================== HOJA 2: la bandeja (base) ===========================
fig = hoja("LA BASE — BANDEJA (pieza a imprimir) · vistas acotadas", 2)
ax = fig.add_axes([.03, .36, .46, .56]); vista(ax, "PLANTA", "1:3", (-40, BAND + 60, -55, BAND + 45))
rect(ax, 0, 0, BAND, BAND, lw=1.8); rect(ax, PARED, PARED, INT, INT, lw=.9, ls=(0, (5, 3)))
rect(ax, (BAND - TABLERO) / 2, (BAND - TABLERO) / 2, TABLERO, TABLERO, lw=1, ls=(0, (2, 2)), ec=G)
rect(ax, (BAND - MATRIZ) / 2, (BAND - MATRIZ) / 2, MATRIZ, MATRIZ, lw=1.4, fill="#dfeee8")
for i in range(1, 20): ax.plot([(BAND - MATRIZ) / 2 + i * 10] * 2, [(BAND - MATRIZ) / 2, (BAND + MATRIZ) / 2], color="#9bc", lw=.3); ax.plot([(BAND - MATRIZ) / 2, (BAND + MATRIZ) / 2], [(BAND - MATRIZ) / 2 + i * 10] * 2, color="#9bc", lw=.3)
for px in (25, BAND - 25):
    for py in (25, BAND - 25): ax.add_patch(Circle((px, py), POSTE / 2, fc="#9aa3b0", ec=K, lw=.8))
ax.plot([BAND / 2] * 2, [-8, BAND + 8], color="#c33", lw=.7, ls="-.", alpha=.8); ax.plot([-8, BAND + 8], [BAND / 2] * 2, color="#c33", lw=.7, ls="-.", alpha=.8)
ax.text(BAND / 2 + 4, BAND + 14, "cortes de impresión (4 piezas)", color="#c33", fontsize=7.5)
rect(ax, BAND / 2 - 55, -2, 110, 12, fill="#cfd5dc"); ax.text(BAND / 2, -22, "bolsillo del asa", ha="center", fontsize=7.5)
rect(ax, -2, 70, 12, 40, fill="#cfd5dc"); rect(ax, -2, 220, 12, 22, fill="#cfd5dc"); ax.text(-8, 90, "interruptor", rotation=90, ha="right", va="center", fontsize=7); ax.text(-8, 231, "carga", rotation=90, ha="right", va="center", fontsize=7)
rect(ax, BAND - 8, 40, 14, BAND - 80, ls=(0, (4, 2)), fill="#e8d8c8"); ax.text(BAND + 12, BAND / 2, "borde de bisagra (panel central)", rotation=90, fontsize=7.5, va="center")
cota(ax, (0, 0), (BAND, 0), -38, f"{BAND} exterior"); cota(ax, (PARED, 0), (BAND - PARED, 0), -30, f"{INT} interior")
cota(ax, (0, 0), (0, BAND), -34, f"{BAND}", vert=True); cota(ax, ((BAND - TABLERO) / 2, BAND + 4), ((BAND + TABLERO) / 2, BAND + 4), 18, f"{TABLERO} tablero")
cota(ax, ((BAND - MATRIZ) / 2, (BAND + MATRIZ) / 2 - 1), ((BAND + MATRIZ) / 2, (BAND + MATRIZ) / 2 - 1), 52, f"{MATRIZ} matriz (20×20 cm)", fs=7.5)
# frente
ax = fig.add_axes([.52, .64, .45, .28]); vista(ax, "FRENTE (corte)", "1:3", (-25, BAND + 55, -35, ALTO + 45))
rect(ax, 0, 0, BAND, ALTO, lw=1.6); rect(ax, PARED, PARED, INT, ALTO, lw=.8, ls=(0, (5, 3)))
for px in (25, BAND - 25): rect(ax, px - POSTE / 2, PARED, POSTE, ELEV, fill="#9aa3b0")
rect(ax, (BAND - TABLERO) / 2, PARED + ELEV, TABLERO, ESP_T, fill="#23262b"); rect(ax, (BAND - MATRIZ) / 2, PARED + ELEV + ESP_T, MATRIZ, 1.5, fill="#1b4d3e")
cota(ax, (0, 0), (0, ALTO), -22, f"{ALTO}", vert=True); cota(ax, (BAND, PARED), (BAND, PARED + ELEV), 22, f"{ELEV}", vert=True); cota(ax, (BAND, 0), (BAND, PARED), 40, f"{PARED}", vert=True, fs=7)
ax.text(BAND / 2, ALTO + 20, f"tablero {TABLERO}×{TABLERO}×{ESP_T} sobre 4 postes Ø{POSTE}", ha="center", fontsize=8)
# impresión
ax = fig.add_axes([.52, .06, .45, .52]); ax.axis("off")
ax.text(0, 1, "IMPRESIÓN (esta semana)", fontsize=11, fontweight="bold", va="top")
ax.text(0, .93, par([f"• La bandeja mide {BAND}×{BAND}: NO cabe en una impresora común (≈ 220–300 mm de cama).",
 f"• Opción 1 (recomendada): cortar en 4 cuadrantes de {BAND // 2}×{BAND // 2} con unión de cola de milano + 4 tornillos M4; se imprime en cualquier impresora.",
 "• Opción 2: servicio de impresión de formato grande (≥ 360 mm): una sola pieza.",
 "• Material: PETG (más resistente que PLA); paredes de 3-4 mm; relleno 25 %; sin soportes si el piso va abajo.",
 f"• Imprime primero UN cuadrante de prueba para ajustar tolerancias (0,2-0,3 mm en uniones).",
 "• Los postes del tablero y el tablero van aparte (placa de 300×300×4: acrílico o MDF cortado).",
 "", "PIEZAS DE LA BASE: 4 cuadrantes de bandeja · 4 postes · placa del tablero · bolsillo de asa ·",
 "marco de bisagra para el panel central · recortes de interruptor y conector de carga.",
 "", "Medidas de referencia ya definidas por la rúbrica: tablero 300 × 300, matriz 200 × 200, elevación 50."]), fontsize=8.8, va="top", linespacing=1.55)
pdf.savefig(fig); fig.savefig(OUT.replace(".pdf", "_h2.png"), dpi=70); plt.close(fig)

# =========================== HOJA 3: asa oculta y marca ===========================
fig = hoja("ASA OCULTA · PLACA «SONAR» · MARCA", 3)
ax = fig.add_axes([.03, .50, .45, .40]); vista(ax, "ASA OCULTA — opción 1: gira 90° (vista lateral, replegada y desplegada)", "1:1", (-20, 200, -80, 70))
rect(ax, 0, 0, 170, 22, lw=1.3, fill="#cfd5dc"); ax.text(85, 11, "bolsillo 170×22×18 en el costado", ha="center", fontsize=8, va="center")
ax.add_patch(Circle((12, 11), 4, fc="#fff", ec=K)); ax.add_patch(Circle((158, 11), 4, fc="#fff", ec=K)); ax.text(85, 35, "pasadores Ø4 (eje de giro)", ha="center", fontsize=7.5)
rect(ax, 12, 7, 146, 8, fill="#8a93a0", lw=1.0); ax.text(85, -4, "REPLEGADA: al ras (imán Ø6×2 la sostiene)", ha="center", fontsize=7.5)
ax.plot([12, 12], [11, -62], color=K, lw=2.2); ax.plot([158, 158], [11, -62], color=K, lw=2.2); ax.plot([12, 158], [-62, -62], color=K, lw=3)
ax.text(85, -72, "DESPLEGADA 90°: se jala del lado y baja", ha="center", fontsize=7.5)
cota(ax, (12, 11), (158, 11), 44, "146 (barra de agarre, Ø10)", fs=7.5); cota(ax, (12, -62), (12, 11), -14, "≈ 73", vert=True, fs=7)
ax = fig.add_axes([.52, .50, .45, .40]); ax.axis("off")
ax.text(0, 1, "TRES MECANISMOS POSIBLES PARA EL ASA", fontsize=10.5, fontweight="bold", va="top")
ax.text(0, .9, par(["1  GIRATORIA (dibujada): barra con 2 pasadores en un bolsillo; imán la deja al ras. La más simple de imprimir.",
 "2  DESLIZANTE: asa en riel (2 varillas de 5 mm) que sale 40 mm con tope y resorte; más rígida, más piezas.",
 "3  PLEGABLE EN U: dos patas articuladas que se acuestan en el bolsillo; más vistosa, más frágil.",
 "", "RECOMENDACIÓN: la 1 para esta entrega. La asa debe soportar el peso del maletín (est. 3-5 kg):",
 "pasadores de acero Ø4, no de plástico, y la barra de PETG de 10 mm o varilla de aluminio."]), fontsize=8.8, va="top", linespacing=1.55)
ax = fig.add_axes([.03, .06, .45, .38]); vista(ax, "PLACA «SONAR» (frente del maletín)", "1:2", (-10, 190, -45, 100))
ax.add_patch(FancyBboxPatch((0, 0), 170, 70, boxstyle="round,pad=2", fc="#10161d", ec=K, lw=1.3)); ax.text(85, 44, "SONAR", color="#46f0b5", ha="center", va="center", fontsize=26, fontweight="bold")
ax.text(85, 14, "APUNTA · DISPARA · HUNDE", color="#9fd8c8", ha="center", va="center", fontsize=9)
cota(ax, (0, 0), (170, 0), -22, "170"); cota(ax, (0, 0), (0, 70), -20, "70", vert=True)
ax = fig.add_axes([.52, .06, .45, .38]); ax.axis("off")
ax.text(0, 1, "BRANDING — lemas para elegir", fontsize=10.5, fontweight="bold", va="top")
ax.text(0, .9, par(["•  «Apunta. Dispara. Hunde.»", "•  «Escucha el océano. Hunde la flota.»", "•  «Tu flota, tu estrategia, tu rayo.»",
 "•  «Radar en mano, victoria al instante.»", "•  «El duelo de coordenadas que se lleva en maletín.»",
 "", "Placa: acrílico negro con grabado/impresión en verde sonar (#46F0B5), igual que la web.",
 "Fijación: 4 tornillos M3 o adhesivo; hueco 172×72×3 en la tapa frontal.",
 "", "Colores del maletín: negro mate o café (tipo ejecutivo); detalles en acero y verde sonar."]), fontsize=8.8, va="top", linespacing=1.55)
pdf.savefig(fig); fig.savefig(OUT.replace(".pdf", "_h3.png"), dpi=70); plt.close(fig)
pdf.close(); print("ok", OUT)
