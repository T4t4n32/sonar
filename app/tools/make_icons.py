#!/usr/bin/env python3
"""Genera el icono SONAR (adaptativo + legacy + monocromo) en android/app/src/main/res/mipmap-*.

Uso (reproducible):  uv run --with pillow tools/make_icons.py
Motivo: fondo #040a0f, arcos de radar y barrido en #46F0B5.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

BG = (4, 10, 15, 255)
FG = (70, 240, 181)
RES = Path(__file__).resolve().parent.parent / "android" / "app" / "src" / "main" / "res"

# densidad: (px adaptativo 108dp, px legacy 48dp)
DENS = {"mdpi": (108, 48), "hdpi": (162, 72), "xhdpi": (216, 96), "xxhdpi": (324, 144), "xxxhdpi": (432, 192)}
SS = 4  # supersampling


def radar(size: int, mono: bool = False) -> Image.Image:
    """Motivo en un lienzo transparente size×size; todo dentro de la zona segura (círculo ~61 %)."""
    n = size * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    col = (255, 255, 255) if mono else FG
    cx, cy = n * 0.5, n * 0.65
    w = max(2, int(n * 0.028))

    def px(a):
        return int(255 * a)

    # barrido: cuña con desvanecimiento hacia atrás (muchas rebanadas finas)
    sweep = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sweep)
    r_out = n * 0.30
    a_head = -52.0  # grados (0 = derecha, negativo = arriba)
    steps = 40
    for i in range(steps):
        a0 = a_head - 50 * (i + 1) / steps
        a1 = a_head - 50 * i / steps
        alpha = (1 - i / steps) ** 1.6 * (0.55 if not mono else 0.8)
        sd.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out], a0, a1 + 0.6, fill=col + (px(alpha),))
    img = Image.alpha_composite(img, sweep)
    d = ImageDraw.Draw(img)

    # arcos concéntricos (semicírculos superiores)
    for r, a in ((0.30, 0.55), (0.20, 0.8), (0.10, 1.0)):
        rr = n * r
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 180, 360, fill=col + (px(a),), width=w)
        # remates redondos
        for ang in (180, 360):
            ex, ey = cx + rr * math.cos(math.radians(ang)), cy + rr * math.sin(math.radians(ang))
            d.ellipse([ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2], fill=col + (px(a),))
    # línea de barrido
    ex = cx + r_out * math.cos(math.radians(a_head))
    ey = cy + r_out * math.sin(math.radians(a_head))
    d.line([cx, cy, ex, ey], fill=col + (255,), width=int(w * 1.15))
    d.ellipse([ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2], fill=col + (255,))
    # origen y eco (blip)
    o = w * 1.1
    d.ellipse([cx - o, cy - o, cx + o, cy + o], fill=col + (255,))
    bx = cx + n * 0.17 * math.cos(math.radians(-40))
    by = cy + n * 0.17 * math.sin(math.radians(-40))
    b = w * 0.9
    d.ellipse([bx - b, by - b, bx + b, by + b], fill=col + (255,))
    return img.resize((size, size), Image.LANCZOS)


def legacy(size: int, circle: bool) -> Image.Image:
    n = size * SS
    base = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    if circle:
        d.ellipse([0, 0, n - 1, n - 1], fill=BG)
    else:
        d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=BG)
    base = base.resize((size, size), Image.LANCZOS)
    # el motivo ocupa el 61 % del adaptativo; para legacy lo ampliamos a ~86 %
    m = radar(size)
    k = 1.42
    big = m.resize((int(size * k), int(size * k)), Image.LANCZOS)
    off = (size - big.width) // 2
    base.alpha_composite(big, (off, off))
    return base


def main() -> None:
    for dens, (adp, leg) in DENS.items():
        out = RES / f"mipmap-{dens}"
        out.mkdir(parents=True, exist_ok=True)
        radar(adp).save(out / "ic_launcher_foreground.png")
        radar(adp, mono=True).save(out / "ic_launcher_monochrome.png")
        legacy(leg, circle=False).save(out / "ic_launcher.png")
        legacy(leg, circle=True).save(out / "ic_launcher_round.png")
    # vista previa grande para revisar a ojo (no va al APK)
    prev = Image.new("RGBA", (512, 512), BG)
    prev.alpha_composite(radar(512))
    prev.save(Path(__file__).resolve().parent / "icon-preview.png")
    # adaptativo: fondo sólido + foreground + monocromo (Android 13 icono temático)
    xml = RES / "mipmap-anydpi-v26"
    xml.mkdir(parents=True, exist_ok=True)
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background"/>\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
        '    <monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>\n'
        '</adaptive-icon>\n'
    )
    (xml / "ic_launcher.xml").write_text(body, encoding="utf-8")
    (xml / "ic_launcher_round.xml").write_text(body, encoding="utf-8")
    print("Iconos generados en", RES)


if __name__ == "__main__":
    main()
