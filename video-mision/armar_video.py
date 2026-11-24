"""Arma el video «MISIÓN: CERO PUNTO DOS» automáticamente con ffmpeg (versión 2).

Lee los clips de Flow, las tomas habladas, las notas de voz y las fotos/capturas de evidencia, y monta todo en el orden del guion:
tarjetas animadas, color unificado (verde oliva), cortes de evidencia sobre lo que se explica (foto real, captura de la app, hoja impresa),
rótulos con el nombre técnico, texto cinético en la apertura, voz limpia, sonido normalizado y MP4 1080p.
Si falta una toma pone una tarjeta «FALTA: …» y sigue; en cuanto grabes la toma real, vuelve a correr el script.

    python armar_video.py                       # versión completa 1080p
    python armar_video.py --vista-previa        # 640x360, rápido
    python armar_video.py --nombres "Sebastián y Juan José"

Carpetas: clips-flow/ (sobre mesa radio sello amanecer) · tomas/ (01-orden 02-campo 03-tropa 04-mapa 05-pulso 06-radio 07-prueba 08-regreso;
si no están, se usan tomas/j_jose_videos/1..5.mp4) · voz/ (P1_sebas = voz del General, P1_juanJose = lectura de la orden) · evidencia/ · musica/
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
EXT_V = (".mp4", ".mov", ".mkv", ".m4v", ".webm")
EXT_A = (".m4a", ".mp3", ".wav", ".aac", ".ogg", ".opus")
FUENTE = r"C:\Windows\Fonts\courbd.ttf"
FPS = 30
BG = "0x2E3A22"
CREMA = "0xEFE9D8"
ORO = "0xB8892B"
ROJO = "0x8C2B22"

# color unificado: baja el blanco de la pared, tiñe a oliva/arena, viñeta y grano
GRADO = ("eq=contrast=1.08:brightness=-0.03:saturation=0.8,"
         "colorbalance=rs=-0.05:gs=0.03:bs=-0.09:rm=-0.04:gm=0.02:bm=-0.07:rh=-0.02:bh=-0.06,vignette=PI/3.2,noise=alls=6:allf=t")
LIMPIA_VOZ = "highpass=f=90,afftdn=nr=10:nf=-35"
VOZ_GENERAL = "highpass=f=300,lowpass=f=3400,volume=1.7"

# --- evidencia: nombre -> (archivo, recorte opcional (x0,y0,x1,y1) en píxeles)
EV = {
    "maqueta": ("foto-servos.jpg", None),
    "tablero": ("tablero.jpg", None),            # foto del tablero 30×30 elevado 5 cm con regla (si no existe, se usa la de la maqueta)
    "electronica": ("foto-electronica.jpg", None),
    "capacitor": ("foto-electronica.jpg", (230, 880, 560, 1130)),
    "pilas": ("foto-servos.jpg", (500, 780, 900, 1250)),
    "laser": ("img1.png", None),
    "hoja": ("hoja-cuadricula.png", None),
    "plantillas": ("hoja-plantillas.png", None),
    "radar": ("app-radar.png", None),
    "veredicto": ("app-pausa.png", None),
    "hundido": ("app-explosion.png", None),
    "stop": ("app-pausa.png", None),
    "cal-esquinas": ("cal-03-esquinas.png", (0, 0, 702, 1500)),
    "cal-calculado": ("cal-04-calculado.png", (0, 0, 702, 1500)),
    "cal-control": ("cal-05-verificar.png", (0, 0, 702, 1500)),
    "cal-guardado": ("cal-06-guardado.png", (0, 0, 702, 1500)),
}

# --- cortes de evidencia sobre cada toma hablada: (desde, hasta, evidencia, rótulo)
CORTES = {
    "02-campo": [(0.7, 5.5, "tablero", "TABLERO 30×30 CM · ELEVADO 5 CM"), (5.8, 11.5, "hoja", "MATRIZ 20×20 CM · 400 CASILLAS DE 1 CM"),
                 (11.9, 15.5, "radar", "APP PROPIA · BLUETOOTH"), (15.9, 22.4, "veredicto", "COORDENADA (x, y)")],
    "03-tropa": [(0.5, 5.0, "electronica", "ESP32 · EL CEREBRO"), (5.3, 9.6, "maqueta", "2 SERVOS · PAN Y TILT"), (9.8, 13.3, "laser", "LÁSER ROJO 650 NM · EL OJO"),
                 (13.6, 21.0, "pilas", "6 V DE PILAS · ESP32 POR USB · GND COMÚN"), (21.3, 28.4, "capacitor", "CAPACITOR 1000 µF")],
    "04-mapa": [(0.5, 6.8, "cal-esquinas", "CALIBRACIÓN · 4 ESQUINAS"), (7.0, 16.4, "cal-calculado", "HOMOGRAFÍA · 400 CASILLAS"),
                (17.0, 19.2, "cal-control", "PUNTO DE CONTROL"), (19.6, 27.0, "cal-guardado", "GUARDADO EN LA MEMORIA DEL ESP32")],
    "05-pulso": [(0.4, 14.4, "maqueta", "SERVOS SINCRONIZADOS · ARRANQUE Y FRENADO SUAVE"), (14.6, 18.2, "electronica", "LÁSER APAGADO MIENTRAS SE MUEVEN"),
                 (18.4, 25.5, "stop", "STOP · APAGA EL LÁSER AL INSTANTE")],
    "06-radio": [(0.9, 13.0, "radar", "APP + BLUETOOTH · SONAR-A"), (13.5, 19.7, "veredicto", "¿LE DIO? · EL TESTIGO RESPONDE"),
                 (19.9, 24.3, "plantillas", "5 PLANTILLAS DE FLOTA NUMERADAS"), (24.5, 29.5, "hundido", "UN TOQUE HUNDE EL BARCO")],
}
# nombre del video real de evidencia/ que sustituye a cada foto fija (si existe: evidencia/<nombre>.mp4)
ALIAS = {"radar": "pantalla-app", "veredicto": "pantalla-app", "hundido": "pantalla-app", "cal-esquinas": "calibracion", "cal-calculado": "calibracion",
         "cal-control": "calibracion", "cal-guardado": "calibracion", "plantillas": "plantilla", "laser": "laser"}
RESPALDO = {"02-campo": "1", "03-tropa": "2", "04-mapa": "3", "05-pulso": "4", "06-radio": "5"}   # tomas/j_jose_videos/N.mp4

# --- apertura: la orden leída por voz; texto cinético y cortes sobre la imagen (cuando no hay toma 01-orden a cámara)
ORDEN_TEXTOS = [(6.2, 8.4, "4,8", 220), (8.4, 11.7, "−0,2", 220), (11.7, 15.8, "TRINCHERA DE LA ESTÉTICA", 90),
                (15.8, 21.0, "EXPLICAR LA CAMPAÑA", 100), (21.0, 26.2, "EL CINCO SAGRADO", 110)]
ORDEN_CORTES = [(26.2, 29.0, "maqueta", "SARGENTO BRAVO · EL FRENTE ES SUYO")]
ORDEN_VISUAL = [("mesa", 8.0), ("radio", 8.0), ("sello", 8.0), ("amanecer", 6.0)]

ESCENAS = [
    ("frio", "sobre", {}),
    ("tarjeta", "titulo", {"dur": 6.0, "bg": None, "lineas": [("MISIÓN:", 110, 330, 0.6), ("CERO PUNTO DOS", 130, 480, 1.4)],
                           "sub": ("Escuadrón SONAR", 44, 660, 3.6), "linea_roja": True}),
    ("tarjeta", "acto1", {"dur": 3.2, "bg": "mesa", "lineas": [("ACTO I", 70, 400, 0.4), ("LA ORDEN", 130, 500, 0.9)]}),
    ("orden", "01-orden", {}),
    ("tarjeta", "acto2", {"dur": 3.2, "bg": "radio", "lineas": [("ACTO II", 70, 380, 0.4), ("EL INFORME DE CAMPO", 105, 480, 0.9)]}),
    ("tarjeta", "c1", {"dur": 3.0, "bg": None, "lineas": [("I · EL CAMPO", 90, 430, 0.3)], "sub": ("«El terreno es honesto. Solo miente quien lo mide mal.»", 40, 600, 1.0)}),
    ("hablada", "02-campo", {}),
    ("tarjeta", "c2", {"dur": 3.0, "bg": None, "lineas": [("II · LA TROPA", 90, 430, 0.3)], "sub": ("«Una tropa pequeña, bien alimentada, vale por un regimiento.»", 40, 600, 1.0)}),
    ("hablada", "03-tropa", {}),
    ("tarjeta", "c3", {"dur": 3.0, "bg": None, "lineas": [("III · EL MAPA DE LAS CUATRO ESQUINAS", 70, 430, 0.3)], "sub": ("«Ningún mapa se dibuja desde la oficina. Se camina el terreno.»", 40, 600, 1.0)}),
    ("hablada", "04-mapa", {}),
    ("tarjeta", "c4", {"dur": 3.0, "bg": None, "lineas": [("IV · EL PULSO SERENO", 90, 430, 0.3)], "sub": ("«Quien dispara con la mano temblorosa, falla dos veces: la primera al apuntar.»", 38, 600, 1.0)}),
    ("hablada", "05-pulso", {}),
    ("tarjeta", "c5", {"dur": 3.0, "bg": None, "lineas": [("V · LA RADIO", 90, 430, 0.3)], "sub": ("«Una orden clara vale más que mil soldados.»", 40, 600, 1.0)}),
    ("hablada", "06-radio", {}),
    ("tarjeta", "c6", {"dur": 3.0, "bg": None, "lineas": [("VI · LA PRUEBA DE FUEGO", 90, 430, 0.3)], "sub": ("«Al final, todo mapa se juzga en el terreno.»", 40, 600, 1.0)}),
    ("hablada", "07-prueba", {}),
    ("tarjeta", "acto3", {"dur": 3.2, "bg": "amanecer", "lineas": [("ACTO III", 70, 400, 0.4), ("EL REGRESO", 130, 500, 0.9)]}),
    ("hablada", "08-regreso", {}),
    ("tarjeta", "fin", {"dur": 7.0, "bg": "sello", "lineas": [("MISIÓN CUMPLIDA", 120, 330, 0.6)],
                        "sub": ("Los números no se pierden.", 46, 520, 2.0), "sub2": ("Esperan a que alguien los explique.", 46, 590, 2.8), "nombres": True}),
]


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("ERROR ffmpeg:", " ".join(str(c) for c in cmd)[:600])
        print(r.stderr[-1800:])
        sys.exit(1)
    return r


def buscar(carpeta, nombre, exts):
    for e in exts:
        g = glob.glob(os.path.join(AQUI, carpeta, nombre + "*" + e))
        if g:
            return g[0]
    return None


def duracion(p):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p])
    return float(json.loads(r.stdout)["format"]["duration"])


def tiene_audio(p):
    r = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "json", p])
    return bool(json.loads(r.stdout)["streams"])


class Montaje:
    def __init__(self, trabajo, ancho, alto, nombres):
        self.t, self.w, self.h, self.nombres = trabajo, ancho, alto, nombres
        self.k = ancho / 1920.0
        self.n = 0
        self.partes = []
        self.ntxt = 0
        self.voff = {}
        shutil.copy(FUENTE, os.path.join(trabajo, "f.ttf"))

    # ------------------------------------------------------------ utilidades
    def sal(self, etiqueta):
        self.n += 1
        return f"{self.n:02d}-{etiqueta}.mp4"

    def codec(self, salida):
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", salida]

    def ajustar(self):
        return f"scale={self.w}:{self.h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={self.w}:{self.h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS}"

    def txt(self, texto):
        self.ntxt += 1
        arch = f"x{self.ntxt}.txt"
        with open(os.path.join(self.t, arch), "w", encoding="utf-8") as f:
            f.write(texto)
        return arch

    def evidencia(self, nombre):
        """Compone la evidencia a 16:9 (fondo difuminado + imagen centrada) y devuelve el PNG."""
        arch, recorte = EV[nombre]
        if not os.path.exists(os.path.join(AQUI, "evidencia", arch)):
            arch, recorte = EV["maqueta"]
        im = Image.open(os.path.join(AQUI, "evidencia", arch)).convert("RGB")
        if recorte:
            im = im.crop(recorte)
        W, H = self.w, self.h
        fondo = im.copy()
        r = max(W / fondo.width, H / fondo.height)
        fondo = fondo.resize((int(fondo.width * r) + 1, int(fondo.height * r) + 1))
        fondo = fondo.crop(((fondo.width - W) // 2, (fondo.height - H) // 2, (fondo.width - W) // 2 + W, (fondo.height - H) // 2 + H))
        fondo = fondo.filter(ImageFilter.GaussianBlur(24 * self.k)).point(lambda v: int(v * 0.38))
        s = min(W * 0.84 / im.width, H * 0.86 / im.height)
        fg = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        fondo.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2 - int(14 * self.k)))
        out = os.path.join(self.t, f"ev-{nombre}.png")
        fondo.save(out)
        return out

    def corte(self, a, b, ev, rotulo):
        """Clip con alfa: evidencia con zoom lento y rótulo; dura b-a."""
        d = b - a
        if ev == "tablero" and not os.path.exists(os.path.join(AQUI, "evidencia", EV["tablero"][0])) and not glob.glob(os.path.join(AQUI, "evidencia", "tablero*.mp4")):
            rotulo = "ESTACIÓN DE ATAQUE · EL CAMPO"            # sin foto del tablero, no se afirma lo que no se ve
        self.n += 1
        out = f"cut{self.n:02d}.mkv"
        vid = next((g[0] for nom in (ev, ALIAS.get(ev, ev)) for e in EXT_V for g in [glob.glob(os.path.join(AQUI, "evidencia", nom + "*" + e))] if g), None)   # video real que reemplaza a la foto
        if vid:
            return self.corte_video(a, b, vid, rotulo, out)
        png = self.evidencia(ev)
        caja_w = int((len(rotulo) * 25.5 + 70) * self.k)
        arch = self.txt(rotulo)
        vf = (f"zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={self.w}x{self.h}:fps={FPS},format=yuva420p,"
              f"drawbox=x={int(60 * self.k)}:y={self.h - int(168 * self.k)}:w={caja_w}:h={int(76 * self.k)}:color=black@0.62:t=fill,"
              f"drawbox=x={int(60 * self.k)}:y={self.h - int(168 * self.k)}:w={max(2, int(6 * self.k))}:h={int(76 * self.k)}:color={ORO}:t=fill,"
              f"drawtext=fontfile=f.ttf:textfile={arch}:fontsize={int(42 * self.k)}:fontcolor={CREMA}:x={int(92 * self.k)}:y={self.h - int(150 * self.k)},"
              f"fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={d - 0.3:.2f}:d=0.3:alpha=1")
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", png, "-vf", vf, "-c:v", "ffv1", "-pix_fmt", "yuva420p", out], cwd=self.t)
        return out

    def corte_video(self, a, b, vid, rotulo, out):
        """Igual que `corte`, pero con un video real de evidencia (se ajusta a 16:9 con fondo difuminado)."""
        d = b - a
        caja_w = int((len(rotulo) * 25.5 + 70) * self.k)
        arch = self.txt(rotulo)
        W, H = self.w, self.h
        fc = (f"[0:v]split[x][y];[x]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur={int(24 * self.k)}:2,eq=brightness=-0.3[bg];"
              f"[y]scale={int(W * 0.9)}:{int(H * 0.86)}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-{int(14 * self.k)},fps={FPS},format=yuva420p,"
              f"drawbox=x={int(60 * self.k)}:y={H - int(168 * self.k)}:w={caja_w}:h={int(76 * self.k)}:color=black@0.62:t=fill,"
              f"drawbox=x={int(60 * self.k)}:y={H - int(168 * self.k)}:w={max(2, int(6 * self.k))}:h={int(76 * self.k)}:color={ORO}:t=fill,"
              f"drawtext=fontfile=f.ttf:textfile={arch}:fontsize={int(42 * self.k)}:fontcolor={CREMA}:x={int(92 * self.k)}:y={H - int(150 * self.k)},"
              f"fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={d - 0.3:.2f}:d=0.3:alpha=1[o]")
        ini = self.voff.get(vid, 0.0)          # cada corte sigue donde terminó el anterior del mismo video
        self.voff[vid] = (ini + d) % max(1.0, duracion(vid) - 0.5)
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ini:.2f}", "-stream_loop", "-1", "-i", vid, "-t", f"{d:.2f}", "-filter_complex", fc, "-map", "[o]", "-an", "-c:v", "ffv1", "-pix_fmt", "yuva420p", out], cwd=self.t)
        return out

    def textos_cineticos(self, textos):
        fs = []
        for a, b, tx, tam in textos:
            arch = self.txt(tx)
            al = f"if(lt(t,{a}),0,if(lt(t,{a + 0.35}),(t-{a})/0.35,if(lt(t,{b - 0.35}),1,max(0,({b}-t)/0.35))))"
            fs.append(f"drawtext=fontfile=f.ttf:textfile={arch}:fontsize={int(tam * self.k)}:fontcolor={CREMA}:borderw={max(2, int(5 * self.k))}:bordercolor=black@0.75:"
                      f"x=(w-text_w)/2:y=(h-text_h)/2:alpha='{al}':enable='between(t,{a},{b})'")
        return fs

    # ------------------------------------------------------------ tarjeta
    def tarjeta(self, id_, d):
        out = self.sal("tarjeta-" + id_)
        dur = d["dur"]
        bgp = buscar("clips-flow", d["bg"], EXT_V) if d.get("bg") else None
        entradas = (["-stream_loop", "-1", "-i", bgp] if bgp else ["-f", "lavfi", "-i", f"color=c={BG}:s={self.w}x{self.h}:r={FPS}"])
        ajuste = "eq=brightness=-0.28:saturation=0.75:contrast=1.08," if bgp else ""
        vf = [f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h},fps={FPS},{ajuste}vignette=PI/4,noise=alls=7:allf=t"]
        textos = list(d["lineas"])
        for k in ("sub", "sub2"):
            if d.get(k):
                textos.append(d[k])
        if d.get("nombres") and self.nombres:
            textos.append((self.nombres, 36, 760, 4.2))
        for i, (tx, tam, y, t0) in enumerate(textos):
            color = ORO if i == 0 and len(d["lineas"]) > 1 and tam < 80 else CREMA
            vf.append(f"drawtext=fontfile=f.ttf:textfile={self.txt(tx)}:fontsize={int(tam * self.k)}:fontcolor={color}:x=(w-text_w)/2:y={int(y * self.k)}:"
                      f"alpha='if(lt(t,{t0}),0,min(1,(t-{t0})/0.7))'")
        if d.get("linea_roja"):
            vf.append(f"drawbox=x=(iw-{int(1100 * self.k)})/2:y={int(620 * self.k)}:w='min({int(1100 * self.k)},max(0,(t-2.6)*1400))':h={max(2, int(8 * self.k))}:color={ROJO}:t=fill")
        vf.append(f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5}:d=0.5,format=yuv420p")
        run(["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(dur), "-vf", ",".join(vf), "-shortest"] + self.codec(out), cwd=self.t)
        self.partes.append(out)

    def falta(self, id_, que):
        self.tarjeta("falta-" + id_, {"dur": 2.5, "bg": None, "lineas": [("FALTA", 100, 380, 0.1)], "sub": (que, 44, 560, 0.3)})

    # ------------------------------------------------------------ compositor general
    def componer(self, etiqueta, visual, audio_f, voz, T, cortes, textos=(), gradar=True, audio_entrada=None):
        """visual: lista de (archivo, duración) o un archivo; voz: archivo de audio (o None para usar el audio del video en `visual`)."""
        out = self.sal(etiqueta)
        entradas, filtros = [], []
        piezas = visual if isinstance(visual, list) else [(visual, T)]
        for i, (f, d) in enumerate(piezas):
            entradas += ["-i", f]
            filtros.append(f"[{i}:v]trim=0:{d:.2f},setpts=PTS-STARTPTS,{self.ajustar()}{',' + GRADO if gradar else ''}[p{i}]")
        n = len(piezas)
        if n > 1:
            filtros.append("".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v0]")
        else:
            filtros.append("[p0]null[v0]")
        ult = "v0"
        # cortes de evidencia
        cuts = []
        for (a, b, ev, rot) in cortes:
            cuts.append((a, b, self.corte(a, b, ev, rot)))
        idx = n
        for j, (a, b, f) in enumerate(cuts):
            entradas += ["-i", os.path.join(self.t, f)]
            filtros.append(f"[{idx}:v]setpts=PTS-STARTPTS+{a}/TB[c{j}]")
            filtros.append(f"[{ult}][c{j}]overlay=format=auto:eof_action=pass:enable='between(t,{a},{b})'[o{j}]")
            ult = f"o{j}"
            idx += 1
        extra = self.textos_cineticos(textos)
        fin = ",".join(extra + [f"fade=t=in:st=0:d=0.4,fade=t=out:st={T - 0.5:.2f}:d=0.5,format=yuv420p"])
        filtros.append(f"[{ult}]{fin}[v]")
        # audio
        if voz:
            entradas += ["-i", voz]
            filtros.append(f"[{idx}:a]{audio_f}[a]")
        elif audio_entrada is not None:
            filtros.append(f"[{audio_entrada}:a]{audio_f}[a]")
        else:
            entradas += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            filtros.append(f"[{idx}:a]anull[a]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]", "-t", f"{T:.2f}"] + self.codec(out)
        run(cmd, cwd=self.t)
        self.partes.append(out)

    # ------------------------------------------------------------ escenas
    def frio(self):
        voz = buscar("voz", "P1_sebas", EXT_A)
        sobre, mesa = buscar("clips-flow", "sobre", EXT_V), buscar("clips-flow", "mesa", EXT_V)
        if not sobre:
            return self.falta("sobre", "clips-flow/sobre.mp4")
        vd = duracion(sobre)
        T = (duracion(voz) + 1.4) if voz else vd
        piezas = [(sobre, min(vd, T))]
        if mesa and T > vd:
            piezas.append((mesa, T - vd))
        af = f"aresample=48000,aformat=channel_layouts=stereo,adelay=900|900,{VOZ_GENERAL},apad" if voz else "anull"
        self.componer("frio", piezas, af, voz, T, [], gradar=False)

    def orden(self):
        toma = buscar("tomas", "01-orden", EXT_V)
        if toma:                                                     # Sebas a cámara
            return self.hablada_archivo("01-orden", toma, [])
        voz = buscar("voz", "P1_juanJose", EXT_A + EXT_V)
        if not voz:
            return self.falta("orden", "tomas/01-orden.mp4 o voz/P1_juanJose")
        T = duracion(voz) + 0.8
        piezas = []
        for nombre, d in ORDEN_VISUAL:
            p = buscar("clips-flow", nombre, EXT_V)
            if p:
                piezas.append((p, min(d, duracion(p))))
        tot = sum(d for _, d in piezas)
        if piezas and tot < T:                                       # alarga el último plano
            piezas[-1] = (piezas[-1][0], min(duracion(piezas[-1][0]), piezas[-1][1] + (T - tot)))
        if not piezas:
            return self.falta("orden", "clips-flow/*")
        af = f"{LIMPIA_VOZ},aresample=48000,aformat=channel_layouts=stereo,adelay=300|300,apad,loudnorm=I=-16:TP=-1.5"
        self.componer("orden", piezas, af, voz, min(T, sum(d for _, d in piezas)), ORDEN_CORTES, ORDEN_TEXTOS)

    def hablada(self, id_):
        p = buscar("tomas", id_, EXT_V)
        if not p and id_ in RESPALDO:
            g = glob.glob(os.path.join(AQUI, "tomas", "j_jose_videos", RESPALDO[id_] + ".*"))
            p = g[0] if g else None
        if not p:
            return self.falta(id_, f"tomas/{id_}.mp4")
        self.hablada_archivo(id_, p, CORTES.get(id_, []))

    def hablada_archivo(self, id_, p, cortes):
        T = duracion(p)
        af = f"{LIMPIA_VOZ},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5" if tiene_audio(p) else "anull"
        # el audio sale del propio archivo (entrada 0)
        self.componer("hablada-" + id_, p, af, None, T, cortes, audio_entrada=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombres", default="")
    ap.add_argument("--vista-previa", action="store_true")
    ap.add_argument("--salida", default=os.path.join(AQUI, "salida", "Mision-Cero-Punto-Dos_SONAR.mp4"))
    a = ap.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("Falta ffmpeg/ffprobe en el PATH")
    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    ancho, alto = (640, 360) if a.vista_previa else (1920, 1080)
    with tempfile.TemporaryDirectory() as tmp:
        m = Montaje(tmp, ancho, alto, a.nombres)
        for tipo, id_, d in ESCENAS:
            if tipo == "tarjeta":
                m.tarjeta(id_, d)
            elif tipo == "frio":
                m.frio()
            elif tipo == "orden":
                m.orden()
            else:
                m.hablada(id_)
            print("  listo:", id_, flush=True)
        with open(os.path.join(tmp, "lista.txt"), "w", encoding="utf-8") as f:
            for p in m.partes:
                f.write(f"file '{p}'\n")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "lista.txt", "-c", "copy", "unido.mp4"], cwd=tmp)
        total = duracion(os.path.join(tmp, "unido.mp4"))
        musica = next((g[0] for e in EXT_A for g in [glob.glob(os.path.join(AQUI, "musica", "*" + e))] if g), None)
        af = "loudnorm=I=-16:TP=-1.5:LRA=11"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", "unido.mp4"]
        if musica:
            cmd += ["-stream_loop", "-1", "-i", musica, "-filter_complex",
                    f"[1:a]volume=0.10,afade=t=in:st=0:d=2,afade=t=out:st={max(0, total - 3):.1f}:d=3,atrim=0:{total:.1f}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,{af}[a]",
                    "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-af", af]
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", os.path.abspath(a.salida)]
        run(cmd, cwd=tmp)
    print(f"\nListo: {a.salida}\nDuración: {int(total // 60)}:{int(total % 60):02d}" + ("  (¡pasa de 6:00!)" if total > 360 else ""))
    if not musica:
        print("Sin música: pon un .mp3 libre de derechos en musica/ (volumen automático al 10 %).")


if __name__ == "__main__":
    main()
