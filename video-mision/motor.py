"""Motor de montaje del video «MISIÓN: CERO PUNTO DOS» (ffmpeg + Pillow).

Piezas:
  - Escena = una base (clip, secuencia o tarjeta) + capas superpuestas (PNG con alfa, fotos, gráficos, videos de evidencia, PIP del presentador)
    + audios locales (voces con su cadena de efectos, SFX). Cada escena se renderiza a video mudo de duración exacta.
  - Ensamble = cadena de xfade entre escenas (transición elegida por par) + mezcla de audio en 3 buses (diálogo, SFX, música)
    con la música agachándose bajo la voz (sidechain) y normalización final.
Todo se calcula con tiempos absolutos, así cada voz, cada toma y cada efecto entran en su instante exacto.
"""
import glob
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(ROOT, "recursos")
WORK = os.path.join(ROOT, "_trabajo")
FPS = 30
FONT_D = r"C:\Windows\Fonts\courbd.ttf"
FONT_B = r"C:\Windows\Fonts\arialbd.ttf"
FONT_R = r"C:\Windows\Fonts\arial.ttf"
CREMA = (239, 233, 216)
ORO = (196, 150, 52)
ROJO = (214, 58, 46)
OLIVA = (46, 58, 34)

K = 1.0          # escala de resolución (1.0 = 1080p; 0.333 = vista previa)
W, H = 1920, 1080


def conf(preview):
    global K, W, H
    K = 1 / 3 if preview else 1.0
    W, H = int(1920 * K), int(1080 * K)
    os.makedirs(WORK, exist_ok=True)


def S(v):
    return int(round(v * K))


def run(cmd, cwd=None, quiet=True):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("ERROR:", " ".join(str(c) for c in cmd)[:700])
        print(r.stderr[-2500:])
        sys.exit(1)
    return r


def dur(p):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p])
    return float(json.loads(r.stdout)["format"]["duration"])


def A(rel):
    """Resuelve un recurso (ruta relativa a video-mision/). None si no existe."""
    p = os.path.join(ROOT, rel)
    return p if os.path.exists(p) else None


def fnt(size, kind="d"):
    return ImageFont.truetype({"d": FONT_D, "b": FONT_B, "r": FONT_R}[kind], S(size))


# ====================================================================== PNG con alfa (texto, rótulos)
def _cache(nombre):
    return os.path.join(WORK, f"{nombre}-{int(K * 100)}.png")


def png_texto(texto, size=90, color=CREMA, kind="d", borde=True, sombra=True):
    h = hashlib.md5(f"{texto}{size}{color}{kind}".encode()).hexdigest()[:10]
    out = _cache("t" + h)
    if os.path.exists(out):
        return out
    f = fnt(size, kind)
    lineas = texto.split("\n")
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    anchos = [tmp.textbbox((0, 0), l, font=f)[2] for l in lineas]
    lh = int(f.size * 1.25)
    w, hh = max(anchos) + S(60), lh * len(lineas) + S(40)
    im = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lineas):
        x = (w - anchos[i]) // 2
        y = S(20) + i * lh
        if sombra:
            for dx, dy in ((4, 4), (0, 5), (5, 0)):
                d.text((x + S(dx), y + S(dy)), l, font=f, fill=(0, 0, 0, 170))
        if borde:
            for dx in (-2, 0, 2):
                for dy in (-2, 0, 2):
                    d.text((x + S(dx), y + S(dy)), l, font=f, fill=(0, 0, 0, 200))
        d.text((x, y), l, font=f, fill=color + (255,))
    im.save(out)
    return out


def png_rotulo(texto, sub=None):
    """Rótulo técnico: caja oscura translúcida + barra dorada."""
    h = hashlib.md5(f"rot{texto}{sub}".encode()).hexdigest()[:10]
    out = _cache("r" + h)
    if os.path.exists(out):
        return out
    f1, f2 = fnt(40, "d"), fnt(26, "r")
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w1 = tmp.textbbox((0, 0), texto, font=f1)[2]
    w2 = tmp.textbbox((0, 0), sub or " ", font=f2)[2]
    w = max(w1, w2) + S(70)
    hh = S(84) if not sub else S(124)
    im = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w, hh], S(6), fill=(8, 10, 6, 168))
    d.rectangle([0, 0, S(7), hh], fill=ORO + (255,))
    d.text((S(30), S(14)), texto, font=f1, fill=CREMA + (255,))
    if sub:
        d.text((S(30), S(70)), sub, font=f2, fill=(190, 190, 170, 255))
    im.save(out)
    return out


def png_capitulo(num, titulo):
    h = hashlib.md5(f"cap{num}{titulo}".encode()).hexdigest()[:10]
    out = _cache("c" + h)
    if os.path.exists(out):
        return out
    f1, f2 = fnt(30, "d"), fnt(54, "d")
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = max(tmp.textbbox((0, 0), titulo, font=f2)[2], tmp.textbbox((0, 0), num, font=f1)[2]) + S(60)
    im = Image.new("RGBA", (w, S(130)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, S(6), S(8), S(118)], fill=ORO + (255,))
    d.text((S(28), S(0)), num, font=f1, fill=ORO + (255,))
    for dx, dy in ((3, 3), (0, 4)):
        d.text((S(28 + dx), S(40 + dy)), titulo, font=f2, fill=(0, 0, 0, 170))
    d.text((S(28), S(40)), titulo, font=f2, fill=CREMA + (255,))
    im.save(out)
    return out


# ====================================================================== gradación y cadenas de video
def cover(w=None, h=None):
    w, h = w or W, h or H
    return f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}"


GRADOS = {
    "sebas": ("hqdn3d=2.5:2:4:3,unsharp=5:5:0.7:5:5:0.0,eq=contrast=1.12:brightness=-0.04:saturation=0.82:gamma=0.96,"
              "colorbalance=rs=-0.04:gs=0.02:bs=-0.08:rm=-0.06:gm=0.02:bm=-0.08:rh=-0.03:bh=-0.07,curves=all='0/0.02 0.5/0.47 1/0.96',vignette=PI/3.4"),
    "jj": ("hqdn3d=2:1.5:3:2.5,unsharp=5:5:0.6:5:5:0.0,eq=contrast=1.1:brightness=-0.03:saturation=0.8:gamma=0.96,"
           "colorbalance=rs=-0.05:gs=0.03:bs=-0.09:rm=-0.04:gm=0.02:bm=-0.07:rh=-0.02:bh=-0.06,vignette=PI/3.2"),
    "demo": ("hqdn3d=3:2:5:4,eq=gamma=1.7:brightness=0.05:contrast=1.15:saturation=0.8,colorbalance=bm=-0.05:bs=-0.04:rm=0.03,"
             "unsharp=5:5:0.6:5:5:0.0,vignette=PI/3.0"),
    "flow": "eq=contrast=1.05:saturation=0.95,vignette=PI/3.6",
    "mate": "eq=contrast=1.04",
    "none": "null",
}
GRANO = "noise=alls=6:allf=t"


def escala_aspecto(modo):
    """Cadena que lleva un stream a W×H: 'cover' recorta, 'contain' lo deja entero sobre fondo difuminado (se resuelve aparte)."""
    return cover() if modo == "cover" else f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black"


# ====================================================================== escena
class Escena:
    def __init__(self, id_, dur_, base, trans_out=("dissolve", 0.5)):
        self.id, self.dur, self.base, self.trans = id_, dur_, base, trans_out
        self.capas = []          # superposiciones
        self.audio = []          # audios locales
        self.archivo = None

    # --- capas
    def png(self, src, a, b, x="(W-w)/2", y="(H-h)/2", fade=0.35, slide=0, pip=False):
        self.capas.append(dict(t="png", src=src, a=a, b=b, x=x, y=y, fade=fade, slide=slide, pip=pip))

    def foto(self, src, a, b, fit="contain", drift=0.06, fade=0.35, pip=True, rot=None, sub=None, borde=False):
        self.capas.append(dict(t="foto", src=src, a=a, b=b, fit=fit, drift=drift, fade=fade, pip=pip, rot=rot, sub=sub, borde=borde))

    def video(self, src, a, b, ss=0.0, fit="cover", grade="none", fade=0.35, pip=True, rot=None, sub=None, speed=1.0, borde=False):
        self.capas.append(dict(t="video", src=src, a=a, b=b, ss=ss, fit=fit, grade=grade, fade=fade, pip=pip, rot=rot, sub=sub, speed=speed, borde=borde))

    def texto(self, txt, a, b, size=90, color=CREMA, y="(H-h)/2", slide=22, fade=0.4, kind="d"):
        self.png(png_texto(txt, size, color, kind), a, b, y=y, fade=fade, slide=S(slide))

    def rotulo(self, txt, a, b, sub=None, x=60, y=None):
        self.png(png_rotulo(txt, sub), a, b, x=str(S(x)), y=(y or f"H-h-{S(110)}"), fade=0.3, slide=S(14))

    def capitulo(self, num, titulo, a=0.3, b=3.4):
        self.png(png_capitulo(num, titulo), a, b, x=str(S(70)), y=str(S(60)), fade=0.4, slide=S(16))

    # --- audio local: kind = 'archivo' (fuente externa con cadena) | 'sfx'
    def voz(self, src, t0, ss=0.0, d=None, cadena="", bus="dlg", gain=0.0):
        self.audio.append(dict(src=src, t0=t0, ss=ss, d=d, cadena=cadena, bus=bus, gain=gain))

    def sfx(self, nombre, t0, gain=-10.0, cadena="", d=None, bus="sfx"):
        p = A(f"recursos/sfx/{nombre}.wav") or A(f"recursos/sfx/{nombre}")
        if p:
            self.audio.append(dict(src=p, t0=t0, ss=0.0, d=d, cadena=cadena, bus=bus, gain=gain))

    # ------------------------------------------------------------------ render
    def render(self):
        out = os.path.join(WORK, f"esc-{self.id}-{int(K * 100)}.mp4")
        entradas, filtros = [], []
        n = 0

        def inp(args):
            nonlocal n
            entradas.extend(args)
            n += 1
            return n - 1

        b = self.base
        d = self.dur
        # ---- base
        if b["t"] == "clip":
            i = inp(["-ss", f"{b.get('ss', 0):.3f}", "-t", f"{d * b.get('speed', 1.0) + 0.5:.3f}", "-i", b["src"]])
            sp = b.get("speed", 1.0)
            zoom = b.get("zoom", 0.06)
            ch = f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},{GRADOS[b.get('grade', 'none')]},"
            ch += f"scale={int(W * (1 + zoom))}:{int(H * (1 + zoom))}:flags=lanczos," if zoom else f"scale={W}:{H}:flags=lanczos,"
            if zoom:
                fx = b.get("pan", (0.5, 0.5, 0.5, 0.5))
                ch += (f"crop={W}:{H}:x='(iw-ow)*({fx[0]}+({fx[2]}-{fx[0]})*t/{d})':y='(ih-oh)*({fx[1]}+({fx[3]}-{fx[1]})*t/{d})',")
            ch += f"{GRANO},format=yuv420p,trim=0:{d:.3f},setpts=PTS-STARTPTS[base]"
            filtros.append(ch)
        elif b["t"] == "seq":
            ids = []
            for k, cl in enumerate(b["clips"]):
                src, ss, dd, gr = cl[:4]
                sp = cl[4] if len(cl) > 4 else 1.0
                i = inp(["-ss", f"{ss:.3f}", "-t", f"{dd * sp + 0.3:.3f}", "-i", src])
                zz = b.get("zoom", 0.0)
                escala = f"scale={int(W * (1 + zz))}:{int(H * (1 + zz))}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}" if True else cover()
                filtros.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},{escala},{GRADOS[gr]},{GRANO},format=yuv420p,trim=0:{dd:.3f},setpts=PTS-STARTPTS[s{k}]")
                ids.append((k, dd))
            acc, tacc = "s0", ids[0][1]
            for k, dd in ids[1:]:
                x = b.get("xf", 0.7)
                filtros.append(f"[{acc}][s{k}]xfade=transition={b.get("tr", "fadeblack")}:duration={x}:offset={tacc - x:.3f}[x{k}]")
                acc = f"x{k}"
                tacc = tacc + dd - x
            filtros.append(f"[{acc}]trim=0:{d:.3f},setpts=PTS-STARTPTS[base]")
        elif b["t"] == "card":
            bg = b.get("bg")
            if bg:
                i = inp(["-stream_loop", "-1", "-t", f"{d:.3f}", "-i", bg])
                filtros.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS},{cover()},eq=brightness=-0.3:saturation=0.72:contrast=1.08,vignette=PI/4,{GRANO},format=yuv420p,trim=0:{d:.3f}[base]")
            else:
                i = inp(["-f", "lavfi", "-t", f"{d:.3f}", "-i", f"color=c=0x2E3A22:s={W}x{H}:r={FPS}"])
                filtros.append(f"[{i}:v]vignette=PI/4,{GRANO},format=yuv420p[base]")
        # ---- PIP: ventanas donde el presentador queda en una esquina mientras se muestra evidencia
        pips = [(c["a"], c["b"]) for c in self.capas if c.get("pip")]
        ult = "base"
        if pips:
            k = len(pips)
            filtros.append(f"[base]split={k + 1}[b0]" + "".join(f"[p{j}]" for j in range(k)))
            ult = "b0"
        # ---- capas
        etiqueta = 0
        for c in self.capas:
            etiqueta += 1
            a_, b_ = c["a"], c["b"]
            dd = b_ - a_
            fade = c.get("fade", 0.35)
            if c["t"] == "png":
                i = inp(["-loop", "1", "-framerate", str(FPS), "-t", f"{dd + 0.1:.3f}", "-i", c["src"]])
                ch = f"[{i}:v]format=rgba,fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={dd - fade:.3f}:d={fade}:alpha=1,setpts=PTS-STARTPTS+{a_}/TB[L{etiqueta}]"
                filtros.append(ch)
                sl = c.get("slide", 0)
                yexp = c["y"]
                if sl:
                    yexp = f"({c['y']})+{sl}*(1-min(1,(t-{a_})/0.45))"
                filtros.append(f"[{ult}][L{etiqueta}]overlay=x={c['x']}:y='{yexp}':format=auto:eof_action=pass:enable='between(t,{a_},{b_})'[o{etiqueta}]")
                ult = f"o{etiqueta}"
            else:
                if c["t"] == "foto":
                    i = inp(["-loop", "1", "-framerate", str(FPS), "-t", f"{dd + 0.1:.3f}", "-i", c["src"]])
                    pre = "format=rgb24"
                else:
                    sp = c.get("speed", 1.0)
                    i = inp(["-ss", f"{c['ss']:.3f}", "-t", f"{dd * sp + 0.3:.3f}", "-i", c["src"]])
                    pre = f"setpts=(PTS-STARTPTS)/{sp},fps={FPS},{GRADOS[c.get('grade', 'none')]}"
                dr = c.get("drift", 0.05) if c["t"] == "foto" else 0.0
                if c["fit"] in ("cover", "fill"):
                    z = 1 + max(dr, 0.0)
                    ch = (f"[{i}:v]{pre},scale={int(W * z)}:{int(H * z)}:force_original_aspect_ratio=increase:flags=lanczos,"
                          f"crop={W}:{H}:x='(iw-ow)*(0.5+0.4*t/{dd})':y='(ih-oh)*0.5'[m{etiqueta}]")
                else:  # contain sobre fondo difuminado
                    fw, fh = int(W * 0.84), int(H * 0.86)
                    ch = (f"[{i}:v]{pre},split[q1][q2];[q1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur={max(2, S(26))}:2,eq=brightness=-0.32:saturation=0.8[bgq];"
                          f"[q2]scale={fw}:{fh}:force_original_aspect_ratio=decrease:flags=lanczos")
                    if c.get("borde"):
                        ch += f",pad=iw+{S(10)}:ih+{S(10)}:{S(5)}:{S(5)}:color=0xC49634"
                    ch += f"[fgq];[bgq][fgq]overlay=(W-w)/2:(H-h)/2-{S(12)}[m{etiqueta}]"
                filtros.append(ch)
                # rótulo incrustado en la capa
                fin = f"[m{etiqueta}]format=yuva420p,fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={dd - fade:.3f}:d={fade}:alpha=1,setpts=PTS-STARTPTS+{a_}/TB[L{etiqueta}]"
                filtros.append(fin)
                filtros.append(f"[{ult}][L{etiqueta}]overlay=0:0:format=auto:eof_action=pass:enable='between(t,{a_},{b_})'[o{etiqueta}]")
                ult = f"o{etiqueta}"
                if c.get("rot"):
                    rp = png_rotulo(c["rot"], c.get("sub"))
                    j = inp(["-loop", "1", "-framerate", str(FPS), "-t", f"{dd + 0.1:.3f}", "-i", rp])
                    etiqueta += 1
                    filtros.append(f"[{j}:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={dd - 0.3:.3f}:d=0.3:alpha=1,setpts=PTS-STARTPTS+{a_ + 0.15}/TB[R{etiqueta}]")
                    filtros.append(f"[{ult}][R{etiqueta}]overlay=x={S(60)}:y=H-h-{S(110)}:format=auto:eof_action=pass:enable='between(t,{a_ + 0.15},{b_})'[o{etiqueta}]")
                    ult = f"o{etiqueta}"
        # ---- PIP encima de todo (si hubo capas con pip)
        if pips:
            pw = S(400)
            for j, (a_, b_) in enumerate(pips):
                filtros.append(f"[p{j}]scale={pw}:-2,pad=iw+{S(8)}:ih+{S(8)}:{S(4)}:{S(4)}:color=0xC49634,format=rgba,"
                               f"fade=t=in:st={a_ + 0.1:.3f}:d=0.3:alpha=1,fade=t=out:st={b_ - 0.35:.3f}:d=0.3:alpha=1[pp{j}]")
                filtros.append(f"[{ult}][pp{j}]overlay=x=W-w-{S(48)}:y={S(30)}:format=auto:eof_action=pass:enable='between(t,{a_},{b_})'[pq{j}]")
                ult = f"pq{j}"
        filtros.append(f"[{ult}]fade=t=in:st=0:d=0.001,format=yuv420p[vout]")
        sc = os.path.join(WORK, f"fg-{self.id}.txt")
        with open(sc, "w", encoding="utf-8") as f:
            f.write(";\n".join(filtros))
        run(["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-/filter_complex", sc, "-map", "[vout]", "-t", f"{d:.3f}", "-r", str(FPS), "-an",
                                                                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "17" if K > 0.5 else "26", "-pix_fmt", "yuv420p", out])
        self.archivo = out
        return out


# ====================================================================== ensamble
def ensamblar(escenas, musica, salida, titulo_meta="MISIÓN: CERO PUNTO DOS"):
    # --- tiempos absolutos
    starts = []
    t = 0.0
    for i, e in enumerate(escenas):
        starts.append(t)
        ov = e.trans[1] if i < len(escenas) - 1 else 0.0
        t += e.dur - ov
    total = t + (escenas[-1].trans[1] if False else 0.0)
    total = starts[-1] + escenas[-1].dur
    # --- video: cadena de xfade
    entradas = []
    filtros = []
    for i, e in enumerate(escenas):
        entradas += ["-i", e.archivo]
    acc = "0:v"
    for i in range(1, len(escenas)):
        tr, dd = escenas[i - 1].trans
        filtros.append(f"[{acc}][{i}:v]xfade=transition={tr}:duration={dd}:offset={starts[i]:.3f}[x{i}]")
        acc = f"x{i}"
    sc = os.path.join(WORK, "ensamble.txt")
    with open(sc, "w", encoding="utf-8") as f:
        f.write(";\n".join(filtros) if filtros else "[0:v]null[x0]")
    video = os.path.join(WORK, f"video-mudo-{int(K * 100)}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-/filter_complex", sc, "-map", f"[{acc}]" if filtros else "[x0]", "-r", str(FPS),
                                                          "-c:v", "libx264", "-preset", "veryfast" if K < 0.5 else "medium", "-crf", "17" if K > 0.5 else "26", "-pix_fmt", "yuv420p", video])
    # --- audio: procesar cada elemento y colocarlo en su instante absoluto
    buses = {"dlg": [], "sfx": []}
    for e, t0 in zip(escenas, starts):
        for k, a in enumerate(e.audio):
            if not a["src"]:
                continue
            w = os.path.join(WORK, f"a-{e.id}-{k}.wav")
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a['ss']:.3f}"]
            if a["d"]:
                cmd += ["-t", f"{a['d']:.3f}"]
            cmd += ["-i", a["src"], "-vn", "-ac", "2", "-ar", "48000"]
            ch = a["cadena"]
            if a["gain"]:
                ch = (ch + "," if ch else "") + f"volume={a['gain']}dB"
            if ch:
                cmd += ["-af", ch]
            cmd += [w]
            run(cmd)
            buses[a["bus"]].append((w, t0 + a["t0"]))
    def bus_wav(nombre, items):
        if not items:
            return None
        ins, fl = [], []
        for i, (w, t0) in enumerate(items):
            ins += ["-i", w]
            ms = max(0, int(round(t0 * 1000)))
            fl.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        fl.append("".join(f"[a{i}]" for i in range(len(items))) + f"amix=inputs={len(items)}:normalize=0:duration=longest,apad=whole_dur={total + 1:.2f},atrim=0:{total + 1:.2f}[o]")
        sc2 = os.path.join(WORK, f"bus-{nombre}.txt")
        open(sc2, "w", encoding="utf-8").write(";\n".join(fl))
        out = os.path.join(WORK, f"bus-{nombre}.wav")
        run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-/filter_complex", sc2, "-map", "[o]", "-ar", "48000", out])
        return out
    dlg = bus_wav("dlg", buses["dlg"])
    sfx = bus_wav("sfx", buses["sfx"])
    # --- música: tramos con fundidos (lista de dicts: src, t0, t1, ss, gain, fi, fo)
    mus_items = []
    for m in musica:
        if not m.get("src") or not os.path.exists(m["src"]):
            continue
        w = os.path.join(WORK, f"m-{len(mus_items)}.wav")
        d = m["t1"] - m["t0"]
        af = f"aloop=loop=-1:size=2e9,atrim=0:{d:.2f},afade=t=in:st=0:d={m.get('fi', 2)},afade=t=out:st={max(0, d - m.get('fo', 3)):.2f}:d={m.get('fo', 3)},volume={m.get('gain', -8)}dB"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{m.get('ss', 0):.2f}", "-i", m["src"], "-vn", "-ac", "2", "-ar", "48000", "-af", af, w])
        mus_items.append((w, m["t0"]))
    mus = None
    if mus_items:
        ins, fl = [], []
        for i, (w, t0) in enumerate(mus_items):
            ins += ["-i", w]
            ms = int(t0 * 1000)
            fl.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        fl.append("".join(f"[a{i}]" for i in range(len(mus_items))) + f"amix=inputs={len(mus_items)}:normalize=0:duration=longest,apad=whole_dur={total + 1:.2f},atrim=0:{total + 1:.2f}[o]")
        sc3 = os.path.join(WORK, "bus-mus.txt")
        open(sc3, "w", encoding="utf-8").write(";\n".join(fl))
        mus = os.path.join(WORK, "bus-mus.wav")
        run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-/filter_complex", sc3, "-map", "[o]", "-ar", "48000", mus])
    # --- mezcla final: música agachada por la voz
    ins, fl, lab = [], [], []
    k = 0
    if dlg:
        ins += ["-i", dlg]
        if mus:
            fl.append(f"[{k}:a]asplit=2[dA][dB]")
            lab.append("[dA]")
        else:
            lab.append(f"[{k}:a]")
        k += 1
    if sfx:
        ins += ["-i", sfx]
        lab.append(f"[{k}:a]")
        k += 1
    if mus:
        ins += ["-i", mus]
        if dlg:
            fl.append(f"[{k}:a][dB]sidechaincompress=threshold=0.015:ratio=9:attack=25:release=600:makeup=1[md]")
        else:
            fl.append(f"[{k}:a]anull[md]")
        lab.append("[md]")
        k += 1
    fl.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0:duration=longest,alimiter=limit=0.93,loudnorm=I=-15:TP=-1.5:LRA=11,atrim=0:{total:.2f}[mix]")
    sc4 = os.path.join(WORK, "mezcla.txt")
    open(sc4, "w", encoding="utf-8").write(";\n".join(fl))
    mixw = os.path.join(WORK, "mezcla.wav")
    run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-/filter_complex", sc4, "-map", "[mix]", "-ar", "48000", mixw])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", mixw, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
         "-metadata", f"title={titulo_meta}", "-t", f"{total:.2f}", salida])
    return total, starts
