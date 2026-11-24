"""Infografías del video (Pillow). Cada gráfico tiene varios ESTADOS que se van revelando al ritmo de la voz.
Uso: python graficos.py   ->   recursos/graficos/igN_x.png (1920x1080)
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos", "graficos")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
BG = (28, 35, 20)
PANEL = (44, 56, 33)
PANEL2 = (58, 72, 43)
GOLD = (196, 150, 52)
CREAM = (239, 233, 216)
RED = (214, 58, 46)
GREEN = (120, 205, 130)
BLUE = (95, 175, 210)
GREY = (150, 156, 138)
FONT_D = r"C:\Windows\Fonts\courbd.ttf"
FONT_B = r"C:\Windows\Fonts\arialbd.ttf"
FONT_R = r"C:\Windows\Fonts\arial.ttf"


def F(size, kind="b"):
    return ImageFont.truetype({"d": FONT_D, "b": FONT_B, "r": FONT_R}[kind], size)


def fondo(titulo, sub=""):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(34, 42, 25), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(34, 42, 25), width=1)
    # viñeta
    v = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(v)
    vd.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), (10, 13, 7))
    im = Image.composite(im, dark, v)
    d = ImageDraw.Draw(im)
    d.rectangle([60, 56, 70, 150], fill=GOLD)
    d.text((92, 52), titulo, font=F(58, "d"), fill=CREAM)
    if sub:
        d.text((94, 120), sub, font=F(30, "r"), fill=GREY)
    d.line([(60, H - 70), (W - 60, H - 70)], fill=GOLD, width=2)
    d.text((60, H - 56), "ESCUADRÓN SONAR  ·  MISIÓN: CERO PUNTO DOS", font=F(22, "d"), fill=GREY)
    return im, d


def guardar(im, nombre):
    im.save(os.path.join(OUT, nombre + ".png"))


def flecha(d, a, b, color=GOLD, w=6, punta=22):
    d.line([a, b], fill=color, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - punta * math.cos(ang - 0.45), b[1] - punta * math.sin(ang - 0.45))
    p2 = (b[0] - punta * math.cos(ang + 0.45), b[1] - punta * math.sin(ang + 0.45))
    d.polygon([b, p1, p2], fill=color)


def etiqueta(d, xy, texto, size=32, color=CREAM, fondo_=None, anchor="la", kind="b"):
    f = F(size, kind)
    if fondo_:
        bb = d.textbbox(xy, texto, font=f, anchor=anchor)
        d.rounded_rectangle([bb[0] - 14, bb[1] - 8, bb[2] + 14, bb[3] + 8], 10, fill=fondo_)
    d.text(xy, texto, font=f, fill=color, anchor=anchor)


def panel(d, box, color=PANEL, borde=GOLD, w=3):
    d.rounded_rectangle(box, 22, fill=color, outline=borde, width=w)


def chip(d, x, y, w, h, texto, sub="", color=PANEL2, brillo=False):
    for i in range(7):
        px = x + 30 + i * (w - 60) / 6
        d.rectangle([px - 5, y - 18, px + 5, y], fill=GOLD)
        d.rectangle([px - 5, y + h, px + 5, y + h + 18], fill=GOLD)
    for i in range(5):
        py = y + 30 + i * (h - 60) / 4
        d.rectangle([x - 18, py - 5, x, py + 5], fill=GOLD)
        d.rectangle([x + w, py - 5, x + w + 18, py + 5], fill=GOLD)
    d.rounded_rectangle([x, y, x + w, y + h], 14, fill=color, outline=(GREEN if brillo else CREAM), width=5 if brillo else 3)
    d.text((x + w / 2, y + h / 2 - (14 if sub else 0)), texto, font=F(46, "d"), fill=CREAM, anchor="mm")
    if sub:
        d.text((x + w / 2, y + h / 2 + 34), sub, font=F(26, "r"), fill=GREY, anchor="mm")


def servo(d, cx, cy, texto, eje="h", brillo=False):
    d.rounded_rectangle([cx - 90, cy - 55, cx + 90, cy + 55], 10, fill=(35, 38, 36), outline=(GREEN if brillo else GREY), width=5 if brillo else 3)
    d.ellipse([cx + 40, cy - 28, cx + 96, cy + 28], fill=PANEL2, outline=CREAM, width=3)
    d.line([(cx + 68, cy), (cx + 68 + (70 if eje == "h" else 0), cy - (0 if eje == "h" else 70))], fill=GOLD, width=12)
    if eje == "h":
        d.arc([cx + 10, cy - 90, cx + 190, cy + 90], 305, 55, fill=GOLD, width=5)
    else:
        d.arc([cx - 40, cy - 190, cx + 160, cy + 10], 215, 325, fill=GOLD, width=5)
    d.text((cx, cy + 105), texto, font=F(30, "b"), fill=CREAM, anchor="mm")


def telefono(d, x, y, w=140, h=250, texto="APP", color=PANEL2):
    d.rounded_rectangle([x, y, x + w, y + h], 22, fill=(20, 24, 18), outline=CREAM, width=4)
    d.rounded_rectangle([x + 12, y + 28, x + w - 12, y + h - 28], 8, fill=color)
    d.text((x + w / 2, y + h / 2), texto, font=F(34, "d"), fill=CREAM, anchor="mm")


def laser(d, x, y, haz=True, largo=340):
    d.rounded_rectangle([x, y - 26, x + 120, y + 26], 8, fill=(35, 38, 36), outline=GREY, width=3)
    d.rectangle([x + 120, y - 14, x + 150, y + 14], fill=GOLD)
    if haz:
        d.line([(x + 150, y), (x + 150 + largo, y)], fill=RED, width=5)
        d.ellipse([x + 150 + largo - 14, y - 14, x + 150 + largo + 14, y + 14], fill=RED)


def pilas(d, x, y, brillo=False):
    d.rounded_rectangle([x, y, x + 250, y + 150], 14, fill=(32, 34, 30), outline=(GREEN if brillo else GREY), width=5 if brillo else 3)
    for i in range(4):
        d.rounded_rectangle([x + 14 + i * 58, y + 22, x + 62 + i * 58, y + 128], 8, fill=(196, 150, 52), outline=(30, 30, 30), width=2)
        d.text((x + 38 + i * 58, y + 75), "AA", font=F(24, "b"), fill=(40, 30, 10), anchor="mm")
    d.text((x + 125, y + 178), "4 PILAS AA = 6 V", font=F(30, "b"), fill=CREAM, anchor="mm")


def capacitor(d, x, y, brillo=False):
    d.rounded_rectangle([x, y, x + 90, y + 170], 14, fill=(30, 32, 40), outline=(GREEN if brillo else GREY), width=5 if brillo else 3)
    d.rectangle([x + 8, y + 10, x + 24, y + 160], fill=(150, 156, 138))
    d.text((x + 58, y + 85), "1000\nµF", font=F(24, "b"), fill=CREAM, anchor="mm", align="center")
    d.line([(x + 22, y + 170), (x + 22, y + 220)], fill=GOLD, width=5)
    d.line([(x + 68, y + 170), (x + 68, y + 220)], fill=GOLD, width=5)


# ====================================================================== IG1 · EL CAMPO
def ig1():
    for estado in ("a", "b"):
        im, d = fondo("I · EL CAMPO", "tablero de posicionamiento de flota")
        # vista superior
        x0, y0, s = 260, 250, 600
        d.rectangle([x0, y0, x0 + s, y0 + s], fill=PANEL2, outline=CREAM, width=6)
        etiqueta(d, (x0 + s / 2, y0 + s + 46), "30 cm", 40, GOLD, anchor="mm")
        flecha(d, (x0 + s / 2 - 120, y0 + s + 46), (x0, y0 + s + 46), GOLD, 4, 16)
        flecha(d, (x0 + s / 2 + 120, y0 + s + 46), (x0 + s, y0 + s + 46), GOLD, 4, 16)
        etiqueta(d, (x0 - 56, y0 + s / 2), "30 cm", 40, GOLD, anchor="mm")
        d.text((x0 + s / 2, y0 - 36), "TABLERO · VISTA SUPERIOR", font=F(30, "d"), fill=GREY, anchor="mm")
        if estado == "b":
            m = 400  # 20 cm -> 400 px  (escala 20 px/cm)
            mx, my = x0 + 100, y0 + 100
            d.rectangle([mx, my, mx + m, my + m], fill=(24, 32, 18), outline=GREEN, width=4)
            for i in range(1, 20):
                d.line([(mx + i * 20, my), (mx + i * 20, my + m)], fill=(52, 82, 52), width=1)
                d.line([(mx, my + i * 20), (mx + m, my + i * 20)], fill=(52, 82, 52), width=1)
            etiqueta(d, (mx + m / 2, my + m / 2), "20 × 20 cm", 44, GREEN, anchor="mm")
            d.text((mx - 8, my + m + 24), "(1,1)", font=F(26, "d"), fill=GOLD, anchor="rm")
            d.text((mx + m + 8, my - 24), "(20,20)", font=F(26, "d"), fill=GOLD, anchor="lm")
            panel(d, [1000, 300, 1760, 560])
            d.text((1040, 330), "400 CASILLAS", font=F(64, "d"), fill=GREEN)
            d.text((1040, 420), "de 1 cm × 1 cm", font=F(44, "b"), fill=CREAM)
            d.text((1040, 485), "20 columnas × 20 filas  ·  (x, y)", font=F(32, "r"), fill=GREY)
        # vista lateral
        lx, ly = 1060, 760
        d.line([(lx, ly + 100), (lx + 640, ly + 100)], fill=GREY, width=8)
        d.text((lx + 320, ly + 138), "BASE DE INSTALACIÓN", font=F(26, "d"), fill=GREY, anchor="mm")
        for px in (lx + 40, lx + 600):
            d.rectangle([px, ly + 20, px + 22, ly + 100], fill=GREY)
        d.rectangle([lx, ly, lx + 640, ly + 20], fill=PANEL2, outline=CREAM, width=3)
        flecha(d, (lx + 330, ly + 100), (lx + 330, ly + 26), GOLD, 5, 18)
        etiqueta(d, (lx + 380, ly + 60), "5 cm", 40, GOLD, anchor="lm")
        d.text((lx + 320, ly - 40), "VISTA LATERAL · ELEVADO", font=F(30, "d"), fill=GREY, anchor="mm")
        guardar(im, f"ig1_{estado}")


# ====================================================================== IG2 · LA TROPA
def ig2():
    # a: el cerebro
    im, d = fondo("II · LA TROPA", "El Cerebro: ESP32")
    chip(d, 330, 330, 560, 360, "ESP32", "WROOM-32 · placa de desarrollo", brillo=True)
    panel(d, [1100, 280, 1780, 760])
    d.text((1140, 310), "EL CEREBRO", font=F(52, "d"), fill=GOLD)
    for i, t in enumerate(["Procesador de 2 núcleos a 240 MHz", "Bluetooth clásico (SPP) integrado", "Wi-Fi integrado (mantenimiento)", "Memoria NVS: guarda la calibración", "Un solo programa para los 2 módulos"]):
        d.text((1150, 400 + i * 66), "•  " + t, font=F(34, "b"), fill=CREAM)
    guardar(im, "ig2_a")
    # b: servos y láser
    im, d = fondo("II · LA TROPA", "Las Torres y el Ojo")
    servo(d, 520, 380, "SERVO PAN · GPIO 18", "h", True)
    servo(d, 520, 700, "SERVO TILT · GPIO 19", "v", True)
    laser(d, 980, 540, True, 520)
    etiqueta(d, (1040, 440), "LÁSER ROJO 650 nm · GPIO 23", 34, RED, anchor="lm")
    etiqueta(d, (520, 255), "gira de lado a lado", 30, GOLD, anchor="mm", kind="r")
    etiqueta(d, (520, 840), "sube y baja", 30, GOLD, anchor="mm", kind="r")
    guardar(im, "ig2_b")
    # c y d: energía
    for estado in ("c", "d"):
        im, d = fondo("II · LA TROPA", "El Sustento: energía separada, tierra común")
        pilas(d, 140, 230, estado == "c")
        d.rounded_rectangle([470, 280, 590, 360], 12, fill=PANEL2, outline=CREAM, width=3)
        d.text((530, 320), "SW", font=F(34, "d"), fill=CREAM, anchor="mm")
        flecha(d, (390, 320), (470, 320), RED, 8, 20)
        flecha(d, (590, 320), (840, 320), RED, 8, 20)
        etiqueta(d, (720, 270), "+6 V", 34, RED, anchor="mm")
        servo(d, 960, 330, "SERVOS", "h", estado == "c")
        # USB
        d.rounded_rectangle([140, 560, 330, 650], 12, fill=PANEL2, outline=CREAM, width=3)
        d.text((235, 605), "USB 5 V", font=F(36, "d"), fill=CREAM, anchor="mm")
        flecha(d, (330, 605), (840, 605), BLUE, 8, 20)
        chip(d, 860, 530, 330, 150, "ESP32", "", brillo=(estado == "c"))
        # GND común
        d.line([(120, 800), (1500, 800)], fill=GREY, width=10)
        d.text((130, 830), "GND COMÚN", font=F(32, "d"), fill=GREY)
        for xx in (270, 960, 1020):
            d.line([(xx, 720 if xx == 270 else 800 - 0), (xx, 800)], fill=GREY, width=6)
        d.line([(1020, 660), (1020, 800)], fill=GREY, width=6)
        d.line([(960, 395), (960, 800)], fill=GREY, width=6)
        d.line([(275, 650), (275, 800)], fill=GREY, width=6)
        if estado == "c":
            panel(d, [1280, 240, 1800, 520])
            d.text((1310, 270), "¿POR QUÉ APARTE?", font=F(36, "d"), fill=GOLD)
            for i, t in enumerate(["Los servos piden picos de", "corriente al arrancar y", "reiniciarían al ESP32."]):
                d.text((1310, 340 + i * 50), t, font=F(32, "b"), fill=CREAM)
        else:
            capacitor(d, 1090, 330, True)
            etiqueta(d, (1135, 300), "CAPACITOR", 28, GREEN, anchor="mm")
            d.line([(1112, 550), (1112, 800)], fill=GREY, width=5)
            d.line([(1158, 550), (1158, 340)], fill=RED, width=5)
            panel(d, [1280, 240, 1860, 700])
            d.text((1310, 262), "RESERVA DE ENERGÍA", font=F(32, "d"), fill=GOLD)
            gx, gy, gw, gh = 1320, 330, 500, 300
            d.line([(gx, gy + gh), (gx + gw, gy + gh)], fill=GREY, width=3)
            d.line([(gx, gy), (gx, gy + gh)], fill=GREY, width=3)
            # sin capacitor (cae) y con capacitor (estable)
            pts_sin = [(gx + i * 10, gy + 60 + (150 if 20 < i < 30 else 0) * math.exp(-abs(i - 24) / 6) * (1 if 22 < i < 34 else 0.2)) for i in range(0, 50)]
            d.line(pts_sin, fill=RED, width=5)
            pts_con = [(gx + i * 10, gy + 60 + (28 if 22 < i < 34 else 0) * math.exp(-abs(i - 26) / 8)) for i in range(0, 50)]
            d.line(pts_con, fill=GREEN, width=5)
            d.text((gx + 10, gy + gh + 18), "voltaje al arrancar los servos", font=F(24, "r"), fill=GREY)
            d.text((gx + 20, gy + 200), "sin capacitor", font=F(26, "b"), fill=RED)
            d.text((gx + 20, gy + 236), "con capacitor", font=F(26, "b"), fill=GREEN)
        guardar(im, f"ig2_{estado}")


# ====================================================================== IG3 · EL MAPA
def tablero_vacio(d, x, y, s, n=20, marc=True):
    d.rectangle([x, y, x + s, y + s], fill=(24, 32, 18), outline=CREAM, width=4)
    c = s / n
    for i in range(1, n):
        d.line([(x + i * c, y), (x + i * c, y + s)], fill=(52, 82, 52), width=1)
        d.line([(x, y + i * c), (x + s, y + i * c)], fill=(52, 82, 52), width=1)


def ig3():
    cx0, cy0, s = 230, 250, 640
    cor = [(cx0, cy0 + s, "1", "(1,1)"), (cx0 + s, cy0 + s, "2", "(20,1)"), (cx0 + s, cy0, "3", "(20,20)"), (cx0, cy0, "4", "(1,20)")]
    # a: cuatro esquinas
    im, d = fondo("III · EL MAPA", "El láser visita las 4 esquinas de la tablilla")
    tablero_vacio(d, cx0, cy0, s)
    for (px, py, n, lab) in cor:
        d.ellipse([px - 26, py - 26, px + 26, py + 26], fill=RED, outline=CREAM, width=4)
        d.text((px, py), n, font=F(32, "d"), fill=CREAM, anchor="mm")
        d.text((px + (-40 if px == cx0 else 40), py + (44 if py > cy0 + 5 else -44)), lab, font=F(28, "d"), fill=GOLD, anchor=("rm" if px == cx0 else "lm"))
    panel(d, [1000, 300, 1800, 740])
    d.text((1040, 330), "MEMORIZA LOS ÁNGULOS", font=F(40, "d"), fill=GOLD)
    for i, (px, py, n, lab) in enumerate(cor):
        d.text((1060, 420 + i * 72), f"esquina {n}  {lab}", font=F(34, "b"), fill=CREAM)
        d.text((1500, 420 + i * 72), f"pan{n}°  tilt{n}°", font=F(34, "d"), fill=GREEN)
    guardar(im, "ig3_a")
    # b: homografía
    im, d = fondo("III · EL MAPA", "Homografía: de casilla (x, y) a ángulos de servo")
    tablero_vacio(d, 150, 280, 520)
    d.text((410, 240), "CASILLAS (x, y)", font=F(30, "d"), fill=GREY, anchor="mm")
    flecha(d, (720, 540), (1010, 540), GOLD, 10, 28)
    d.rounded_rectangle([730, 440, 1000, 520], 14, fill=PANEL2, outline=GOLD, width=3)
    d.text((865, 480), "H · (x, y)", font=F(40, "d"), fill=CREAM, anchor="mm")
    # cuadrícula proyectada (cuadrilátero)
    q = [(1100, 330), (1700, 300), (1760, 790), (1060, 700)]

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    for i in range(21):
        t = i / 20
        d.line([lerp(q[0], q[1], t), lerp(q[3], q[2], t)], fill=(70, 110, 70), width=1)
        d.line([lerp(q[0], q[3], t), lerp(q[1], q[2], t)], fill=(70, 110, 70), width=1)
    d.polygon(q, outline=GREEN, width=4)
    d.text((1420, 250), "ÁNGULOS (pan°, tilt°)", font=F(30, "d"), fill=GREY, anchor="mm")
    etiqueta(d, (960, 880), "Con 4 puntos medidos se calculan las 400 casillas", 40, CREAM, anchor="mm")
    guardar(im, "ig3_b")
    # c: control
    im, d = fondo("III · EL MAPA", "El centro: punto de control")
    tablero_vacio(d, cx0, cy0, s)
    px, py = cx0 + s / 2, cy0 + s / 2
    d.ellipse([px - 22, py - 22, px + 22, py + 22], fill=RED, outline=CREAM, width=4)
    d.ellipse([px - 56, py - 56, px + 56, py + 56], outline=GREEN, width=5)
    d.text((px + 80, py), "(11,11)", font=F(30, "d"), fill=GOLD, anchor="lm")
    panel(d, [1000, 320, 1800, 700])
    d.text((1040, 350), "COMPROBACIÓN", font=F(44, "d"), fill=GOLD)
    d.text((1040, 440), "error de control", font=F(40, "b"), fill=CREAM)
    d.text((1040, 500), "< 0,5°", font=F(110, "d"), fill=GREEN)
    d.text((1040, 640), "= calibración válida", font=F(36, "b"), fill=CREAM)
    guardar(im, "ig3_c")
    # d: memoria
    im, d = fondo("III · EL MAPA", "Se guarda en la memoria del ESP32")
    chip(d, 330, 360, 480, 300, "NVS", "memoria no volátil", brillo=True)
    d.rounded_rectangle([1000, 400, 1700, 620], 20, fill=PANEL2, outline=GOLD, width=4)
    d.text((1350, 460), "APAGAR  →  ENCENDER", font=F(48, "d"), fill=CREAM, anchor="mm")
    d.text((1350, 545), "el mapa sigue ahí", font=F(48, "d"), fill=GREEN, anchor="mm")
    guardar(im, "ig3_d")


# ====================================================================== IG4 · EL PULSO SERENO
def ig4():
    # a: perfil de velocidad
    im, d = fondo("IV · EL PULSO SERENO", "Movimiento suave y sincronizado")
    gx, gy, gw, gh = 230, 260, 1000, 560
    d.line([(gx, gy + gh), (gx + gw, gy + gh)], fill=GREY, width=4)
    d.line([(gx, gy), (gx, gy + gh)], fill=GREY, width=4)
    d.text((gx + gw / 2, gy + gh + 44), "tiempo", font=F(30, "r"), fill=GREY, anchor="mm")
    d.text((gx - 20, gy - 24), "velocidad", font=F(30, "r"), fill=GREY, anchor="lm")
    brusco = [(gx, gy + gh), (gx + 30, gy + 80), (gx + 470, gy + 80), (gx + 500, gy + gh), (gx + 530, gy + 80), (gx + gw - 40, gy + 80), (gx + gw - 10, gy + gh)]
    d.line(brusco, fill=RED, width=6)
    suave = [(gx + i * 10, gy + gh - 470 * math.sin(math.pi * i / 100) ** 2) for i in range(0, 101)]
    d.line(suave, fill=GREEN, width=8)
    d.text((gx + 770, gy + 60), "BRUSCO", font=F(36, "d"), fill=RED)
    d.text((gx + 420, gy + 170), "SUAVE", font=F(44, "d"), fill=GREEN)
    panel(d, [1330, 300, 1800, 780])
    d.text((1360, 330), "LOS DOS EJES", font=F(40, "d"), fill=GOLD)
    for i, t in enumerate(["salen juntos", "llegan juntos", "arrancan suave", "frenan suave", "menos tirones", "menos corriente"]):
        d.text((1370, 410 + i * 60), "•  " + t, font=F(34, "b"), fill=CREAM)
    guardar(im, "ig4_a")
    # b: holgura y último tramo lento
    im, d = fondo("IV · EL PULSO SERENO", "El último tramo: lento y siempre subiendo")
    base_y = 760
    d.line([(200, base_y), (1100, base_y)], fill=GREY, width=4)
    d.text((200, base_y + 36), "ángulo del servo", font=F(28, "r"), fill=GREY)
    # camino
    d.line([(260, base_y - 520), (700, base_y - 120)], fill=GOLD, width=8)
    flecha(d, (700, base_y - 120), (700, base_y - 120), GOLD)
    d.line([(700, base_y - 120), (780, base_y - 230)], fill=GREEN, width=10)
    flecha(d, (760, base_y - 205), (792, base_y - 247), GREEN, 10, 26)
    d.ellipse([688, base_y - 134, 712, base_y - 106], fill=RED)
    d.ellipse([768, base_y - 244, 800, base_y - 214], outline=GREEN, width=5, fill=PANEL)
    etiqueta(d, (700, base_y - 70), "punto intermedio (−2°)", 30, RED, anchor="mm")
    etiqueta(d, (870, base_y - 270), "destino", 32, GREEN, anchor="lm")
    etiqueta(d, (430, base_y - 380), "rápido", 34, GOLD, anchor="mm", kind="d")
    etiqueta(d, (930, base_y - 175), "despacio", 34, GREEN, anchor="lm", kind="d")
    panel(d, [1250, 300, 1800, 740])
    d.text((1280, 330), "¿POR QUÉ?", font=F(44, "d"), fill=GOLD)
    for i, t in enumerate(["Los engranes tienen", "un poco de juego.", "Llegando siempre por", "el mismo lado, el", "láser cae siempre", "en el mismo punto."]):
        d.text((1285, 410 + i * 52), t, font=F(34, "b"), fill=CREAM)
    guardar(im, "ig4_b")
    # c: interlock
    im, d = fondo("IV · EL PULSO SERENO", "El láser nunca se enciende mientras algo se mueve")
    x0, x1 = 280, 1500
    d.text((x0 - 30, 400), "SERVOS", font=F(36, "d"), fill=CREAM, anchor="rm")
    d.text((x0 - 30, 600), "LÁSER", font=F(36, "d"), fill=CREAM, anchor="rm")
    d.rectangle([x0, 370, x1, 430], fill=(36, 44, 28))
    d.rectangle([x0, 570, x1, 630], fill=(36, 44, 28))
    for (a, b) in ((330, 640), (940, 1180)):
        d.rectangle([a, 370, b, 430], fill=GOLD)
    for (a, b) in ((640, 940), (1180, 1480)):
        d.rectangle([a, 570, b, 630], fill=RED)
    d.text((485, 340), "se mueven", font=F(28, "r"), fill=GOLD, anchor="mm")
    d.text((790, 540), "quieto: láser ON", font=F(28, "r"), fill=RED, anchor="mm")
    d.text((1060, 340), "se mueven", font=F(28, "r"), fill=GOLD, anchor="mm")
    d.text((1330, 540), "láser ON", font=F(28, "r"), fill=RED, anchor="mm")
    panel(d, [280, 720, 880, 900])
    d.text((310, 745), "STOP", font=F(46, "d"), fill=RED)
    d.text((310, 815), "apaga el láser al instante", font=F(32, "b"), fill=CREAM)
    panel(d, [940, 720, 1540, 900])
    d.text((970, 745), "120 s", font=F(46, "d"), fill=GREEN)
    d.text((970, 815), "si se olvida, se apaga solo", font=F(32, "b"), fill=CREAM)
    guardar(im, "ig4_c")


# ====================================================================== IG5 · LA RADIO
def ig5():
    # a: flujo de un disparo
    im, d = fondo("V · LA RADIO", "Un disparo, de la app al láser")
    telefono(d, 140, 400, 170, 300, "APP")
    chip(d, 620, 400, 330, 220, "ESP32", "«SONAR-A»", brillo=True)
    servo(d, 1230, 470, "SERVOS", "h")
    laser(d, 1480, 620, True, 250)
    flecha(d, (320, 480), (590, 480), BLUE, 8, 22)
    d.rounded_rectangle([340, 380, 570, 450], 30, fill=BLUE, outline=CREAM, width=3)
    d.text((455, 415), "( x , y )", font=F(40, "d"), fill=(10, 20, 30), anchor="mm")
    d.text((455, 520), "Bluetooth", font=F(30, "b"), fill=BLUE, anchor="mm")
    flecha(d, (990, 500), (1110, 500), GOLD, 8, 22)
    flecha(d, (1360, 560), (1470, 620), GOLD, 8, 22)
    d.text((780, 700), "calcula los ángulos", font=F(30, "b"), fill=GOLD, anchor="mm")
    d.text((1230, 360), "se mueven", font=F(30, "b"), fill=GOLD, anchor="mm")
    d.text((1650, 700), "láser + pitido", font=F(34, "b"), fill=RED, anchor="mm")
    d.text((960, 880), "primero la x, luego la y", font=F(48, "d"), fill=CREAM, anchor="mm")
    guardar(im, "ig5_a")
    # b: cinco plantillas
    im, d = fondo("V · LA RADIO", "Cinco cartas de flota, numeradas")
    ships = [
        [(3, 12, 4, "V"), (11, 4, 4, "H"), (16, 15, 2, "H"), (8, 9, 2, "V"), (5, 3, 2, "H")],
        [(2, 17, 4, "H"), (17, 5, 4, "V"), (10, 12, 2, "V"), (6, 7, 2, "H"), (13, 18, 2, "H")],
        [(18, 13, 4, "V"), (4, 9, 4, "H"), (10, 3, 2, "H"), (13, 10, 2, "V"), (2, 3, 2, "V")],
        [(9, 16, 4, "H"), (3, 4, 4, "V"), (15, 9, 2, "H"), (11, 7, 2, "V"), (17, 2, 2, "H")],
        [(6, 13, 4, "V"), (13, 13, 4, "H"), (1, 8, 2, "V"), (9, 6, 2, "H"), (19, 5, 2, "V")],
    ]
    s, gap = 270, 40
    x_start = (W - (5 * s + 4 * gap)) // 2
    for k, fl in enumerate(ships):
        x = x_start + k * (s + gap)
        y = 330
        tablero_vacio(d, x, y, s)
        c = s / 20
        for (sx, sy, n, o) in fl:
            w_, h_ = (n * c, c) if o == "H" else (c, n * c)
            px, py = x + (sx - 1) * c, y + s - (sy - 1) * c - h_
            d.rectangle([px, py, px + w_, py + h_], fill=BLUE if n == 2 else GREEN, outline=CREAM, width=2)
        d.text((x + s / 2, y + s + 44), f"PLANTILLA {k + 1}", font=F(32, "d"), fill=GOLD, anchor="mm")
    d.text((960, 790), "3 embarcaciones de 2  +  2 submarinos de 4", font=F(40, "b"), fill=CREAM, anchor="mm")
    d.text((960, 860), "partida 1 → plantilla 1  ·  partida 2 → plantilla 2  ·  …", font=F(34, "r"), fill=GREY, anchor="mm")
    guardar(im, "ig5_b")
    # c: un toque hunde el barco
    im, d = fondo("V · LA RADIO", "Cualquier casilla del barco lo hunde")
    c = 110
    x, y = 330, 420
    for i in range(4):
        d.rectangle([x + i * c, y, x + (i + 1) * c, y + c], fill=GREEN if i != 2 else RED, outline=CREAM, width=4)
    d.text((x + 2.5 * c, y - 40), "SUBMARINO · 4 CASILLAS", font=F(36, "d"), fill=GREY, anchor="mm")
    d.text((x + 2.5 * c, y + c / 2), "✕", font=F(70, "b"), fill=CREAM, anchor="mm") if False else None
    d.line([(x + 2 * c + 25, y + 25), (x + 3 * c - 25, y + c - 25)], fill=CREAM, width=8)
    d.line([(x + 3 * c - 25, y + 25), (x + 2 * c + 25, y + c - 25)], fill=CREAM, width=8)
    d.text((x + 2.5 * c, y + c + 56), "impacto", font=F(32, "b"), fill=RED, anchor="mm")
    flecha(d, (880, 475), (1030, 475), GOLD, 10, 28)
    for i in range(4):
        d.rectangle([1100 + i * c * 0.9, y, 1100 + (i + 1) * c * 0.9, y + c * 0.9], fill=(70, 80, 70), outline=RED, width=4)
    d.text((1100 + 2 * c * 0.9, y - 40), "¡HUNDIDO!", font=F(46, "d"), fill=RED, anchor="mm")
    d.text((1100 + 2 * c * 0.9, y + c * 0.9 + 56), "la app dice dónde estaba", font=F(32, "b"), fill=CREAM, anchor="mm")
    d.text((960, 850), "la regla del profesor: cualquier casilla alcanzada", font=F(40, "b"), fill=CREAM, anchor="mm")
    guardar(im, "ig5_c")


# ====================================================================== IG6 · LA PRUEBA DE FUEGO
def ig6():
    cx0, cy0, s = 1130, 300, 560
    pts = [(cx0, cy0 + s), (cx0 + s, cy0 + s), (cx0 + s, cy0), (cx0, cy0), (cx0 + s / 2, cy0 + s / 2)]
    nombres = ["(1,1)", "(20,1)", "(20,20)", "(1,20)", "(11,11)"]
    for k in range(0, 6):
        im, d = fondo("VI · LA PRUEBA DE FUEGO", "TEST de 5 posiciones")
        tablero_vacio(d, cx0, cy0, s)
        for i, (px, py) in enumerate(pts):
            hecho = i < k
            actual = i == k - 1
            col = GREEN if hecho else (60, 70, 55)
            d.ellipse([px - 24, py - 24, px + 24, py + 24], fill=col, outline=(RED if actual else CREAM), width=6 if actual else 3)
            d.text((px, py), str(i + 1), font=F(28, "d"), fill=(10, 20, 10) if hecho else CREAM, anchor="mm")
        d.text((140, 360), "POSICIONES", font=F(40, "d"), fill=GOLD)
        for i, n in enumerate(nombres):
            d.text((150, 450 + i * 70), f"{i + 1}.  {n}", font=F(40, "d"), fill=(GREEN if i < k else GREY))
            if i < k:
                d.text((420, 450 + i * 70), "✓", font=F(40, "b"), fill=GREEN) if False else d.line([(430, 468 + i * 70), (445, 486 + i * 70), (475, 452 + i * 70)], fill=GREEN, width=7)
        d.text((140, 860), "cuatro esquinas y el centro", font=F(34, "r"), fill=GREY)
        guardar(im, f"ig6_{k}")


if __name__ == "__main__":
    ig1(); ig2(); ig3(); ig4(); ig5(); ig6()
    print("OK", sorted(os.listdir(OUT)))
