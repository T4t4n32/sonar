#!/usr/bin/env python3
"""Genera la identidad visual de SONAR (SVG + PNG) en esta carpeta.

Uso:  uv run --with playwright python branding/generar_branding.py
Fuente única del motivo: radar de 3 arcos + barrido. Paleta y reglas: BRANDING.md.
"""
import glob
import math
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent

# ---- paleta (la misma que la app: app/src/styles/app.css)
BG, BG2, PANEL, LINE = "#040a0f", "#071119", "#0a1822", "#16384a"
TXT, MUT = "#d9f3ee", "#86adae"
SONAR, ECHO, HIT, WARN = "#46f0b5", "#5ad6ff", "#ff5d4d", "#ffc24a"
INK_L, SONAR_L = "#0b2a33", "#007a5a"  # variante para fondos claros
FONT = "Bahnschrift, 'Segoe UI', 'Helvetica Neue', Arial, system-ui, sans-serif"
MONO = "Consolas, 'Cascadia Mono', Menlo, monospace"


def mark(x, y, s, col=SONAR, extra=""):
    """Motivo en un cuadrado s×s con origen (x,y). Viewbox interno 100×100."""
    a = math.radians(58)
    ex, ey = 50 + 34 * math.cos(a), 64 - 34 * math.sin(a)
    return (
        f'<g transform="translate({x},{y}) scale({s / 100})" fill="none" stroke="{col}" '
        f'stroke-linecap="round" {extra}>'
        f'<path d="M4 64A46 46 0 0 1 96 64" stroke-width="5.5" opacity=".42"/>'
        f'<path d="M18 64A32 32 0 0 1 82 64" stroke-width="5.5" opacity=".7"/>'
        f'<path d="M32 64A18 18 0 0 1 68 64" stroke-width="5.5"/>'
        f'<path d="M50 64L{ex:.1f} {ey:.1f}" stroke-width="6.5"/>'
        f'<circle cx="50" cy="64" r="7" fill="{col}" stroke="none"/></g>'
    )


def svg(w, h, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f"<defs>{defs}</defs>{body}</svg>"
    )


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- marca y logos
write("sonar-mark.svg", svg(100, 100, mark(0, 0, 100)))
write("sonar-mark-light.svg", svg(100, 100, mark(0, 0, 100, SONAR_L)))
write(
    "sonar-icon.svg",
    svg(512, 512, f'<rect width="512" height="512" rx="112" fill="{BG}"/>' + mark(96, 100, 320)),
)


def logo(ink, acc, bg=None):
    base = f'<rect width="640" height="160" fill="{bg}"/>' if bg else ""
    return svg(
        640,
        160,
        base
        + mark(10, 18, 124, acc)
        + f'<text x="160" y="96" font-family="{FONT}" font-weight="700" font-size="76" letter-spacing="20" fill="{ink}">SONAR</text>'
        + f'<text x="164" y="132" font-family="{FONT}" font-weight="600" font-size="22" letter-spacing="11" fill="{acc}">BATALLA NAVAL</text>',
    )


write("sonar-logo.svg", logo(TXT, SONAR))
write("sonar-logo-light.svg", logo(INK_L, SONAR_L))

# ---------------------------------------------------------------- banner 1280×640
CELL, GX, GY = 22, 800, 130


def cell_xy(cx, cy):
    return GX + (cx - 1) * CELL, GY + (cy - 1) * CELL


def banner():
    defs = (
        f'<radialGradient id="g1" cx="78%" cy="30%" r="70%"><stop offset="0" stop-color="#0d2a36"/>'
        f'<stop offset="1" stop-color="{BG}"/></radialGradient>'
        f'<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SONAR}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{SONAR}" stop-opacity=".55"/></linearGradient>'
        f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>'
    )
    b = [f'<rect width="1280" height="640" fill="{BG}"/><rect width="1280" height="640" fill="url(#g1)"/>']
    # rejilla 20×20
    b.append(f'<rect x="{GX}" y="{GY}" width="{CELL * 20}" height="{CELL * 20}" rx="10" fill="{PANEL}" opacity=".7" stroke="{LINE}" stroke-width="2"/>')
    for i in range(1, 20):
        o = i * CELL
        b.append(f'<path d="M{GX + o} {GY}V{GY + CELL * 20}M{GX} {GY + o}H{GX + CELL * 20}" stroke="{LINE}" stroke-width="1" opacity=".75"/>')
    # submarino (10,12)-(10,15) con 2 impactos
    sx, sy = cell_xy(10, 12)
    b.append(f'<rect x="{sx + 2}" y="{sy + 2}" width="{CELL - 4}" height="{CELL * 4 - 4}" rx="9" fill="none" stroke="{ECHO}" stroke-width="2" stroke-dasharray="5 4"/>')
    for cy in (14, 15):
        hx, hy = cell_xy(10, cy)
        b.append(f'<rect x="{hx + 3}" y="{hy + 3}" width="{CELL - 6}" height="{CELL - 6}" rx="4" fill="{HIT}"/>')
    # agua (6,7): anillos
    mx, my = cell_xy(6, 7)
    for r, o in ((7, .95), (14, .55), (22, .28)):
        b.append(f'<circle cx="{mx + CELL / 2}" cy="{my + CELL / 2}" r="{r}" fill="none" stroke="{ECHO}" stroke-width="2" opacity="{o}"/>')
    # torreta y láser a (15,8)
    tx, ty = GX + CELL * 10, 78
    tcx, tcy = cell_xy(15, 8)
    tcx, tcy = tcx + CELL / 2, tcy + CELL / 2
    b.append(f'<line x1="{tx}" y1="{ty}" x2="{tcx}" y2="{tcy}" stroke="{SONAR}" stroke-width="8" opacity=".5" filter="url(#glow)"/>')
    b.append(f'<line x1="{tx}" y1="{ty}" x2="{tcx}" y2="{tcy}" stroke="url(#beam)" stroke-width="2.5"/>')
    b.append(f'<circle cx="{tx}" cy="{ty}" r="13" fill="{PANEL}" stroke="{SONAR}" stroke-width="3"/><circle cx="{tx}" cy="{ty}" r="4.5" fill="{SONAR}"/>')
    k = 17
    for sxn, syn in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        b.append(f'<path d="M{tcx + sxn * k} {tcy + syn * (k - 8)}V{tcy + syn * k}H{tcx + sxn * (k - 8)}" fill="none" stroke="{SONAR}" stroke-width="3" stroke-linecap="round"/>')
    b.append(f'<rect x="{tcx - 6}" y="{tcy - 6}" width="12" height="12" rx="2" fill="{SONAR}"/>')
    # cotas
    b.append(f'<text x="{tcx + 24}" y="{tcy - 22}" font-family="{MONO}" font-size="17" fill="{SONAR}" font-weight="700">(15, 8)</text>')
    hx, hy = cell_xy(10, 15)
    b.append(f'<text x="{hx + 32}" y="{hy + 17}" font-family="{MONO}" font-size="17" fill="{HIT}" font-weight="700">IMPACTO</text>')
    for n in (1, 5, 10, 15, 20):
        b.append(f'<text x="{GX + (n - 1) * CELL + CELL / 2}" y="{GY - 10}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUT}">{n}</text>')
        b.append(f'<text x="{GX - 10}" y="{GY + (n - 1) * CELL + CELL / 2 + 4}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUT}">{n}</text>')
    # texto de marca
    b.append(mark(76, 96, 132))
    b.append(f'<text x="70" y="322" font-family="{FONT}" font-weight="700" font-size="126" letter-spacing="26" fill="{TXT}">SONAR</text>')
    b.append(f'<text x="76" y="378" font-family="{FONT}" font-weight="600" font-size="34" letter-spacing="15" fill="{SONAR}">BATALLA NAVAL</text>')
    b.append(f'<text x="76" y="440" font-family="{FONT}" font-size="30" fill="{MUT}">Apunta. Dispara. Hunde.</text>')
    chips = [("ESP32", 120), ("BLUETOOTH", 178), ("LÁSER", 108), ("ANDROID", 148)]
    x = 76
    for t, w in chips:
        b.append(f'<rect x="{x}" y="490" width="{w}" height="44" rx="22" fill="none" stroke="{LINE}" stroke-width="2"/>')
        b.append(f'<text x="{x + w / 2}" y="518" text-anchor="middle" font-family="{FONT}" font-weight="600" font-size="17" letter-spacing="3" fill="{TXT}">{t}</text>')
        x += w + 14
    b.append(f'<rect x="0" y="0" width="1280" height="6" fill="{SONAR}"/>')
    return svg(1280, 640, "".join(b), defs)


write("banner.svg", banner())

# ---------------------------------------------------------------- rasterizar
def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        pat = os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), "chromium_headless_shell-*", "*", "chrome-headless-shell.exe")
        return p.chromium.launch(executable_path=sorted(glob.glob(pat))[-1])


def shot(br, svg_name, png_name, w, h, scale=1, transparent=False):
    pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
    pg.goto((OUT / svg_name).as_uri())
    pg.screenshot(path=str(OUT / png_name), omit_background=transparent)
    pg.close()


with sync_playwright() as p:
    br = launch(p)
    shot(br, "banner.svg", "banner.png", 1280, 640, 2)
    shot(br, "banner.svg", "social-preview.png", 1280, 640, 1)
    shot(br, "sonar-icon.svg", "sonar-icon-512.png", 512, 512, 1, True)
    shot(br, "sonar-logo.svg", "sonar-logo.png", 640, 160, 2, True)
    br.close()
print("branding generado en", OUT)
