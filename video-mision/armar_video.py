"""Arma el video «MISIÓN: CERO PUNTO DOS» automáticamente con ffmpeg.

Qué hace: lee los clips y tomas de las carpetas, genera las tarjetas de título (con texto animado, viñeta y grano), las une en el
orden del guion, mezcla la voz y la música, normaliza el sonido y exporta un MP4 1080p. Si falta una toma, mete una tarjeta
«FALTA: …» para que veas qué falta sin que el montaje se rompa.

Uso (desde esta carpeta):
    python armar_video.py                      # usa lo que haya
    python armar_video.py --nombres "Sebastián y [Compañero]"
    python armar_video.py --vista-previa       # 640x360, rápido, para revisar el orden
Requiere: ffmpeg y ffprobe en el PATH.

Carpetas (poner los archivos con estos nombres; vale .mp4 .mov .mkv .m4v):
    clips-flow/   sobre  mesa  radio  sello  amanecer           (los 5 clips generados en Flow)
    tomas/        01-orden  02-campo  03-tropa  04-mapa  05-pulso  06-radio  07-prueba  08-regreso
    voz/          00-general   (la voz del General, para el sobre del inicio; .m4a .mp3 .wav)
    musica/       cualquier .mp3/.m4a/.wav libre de derechos (se usa el primero)
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
EXT_V = (".mp4", ".mov", ".mkv", ".m4v", ".webm")
EXT_A = (".m4a", ".mp3", ".wav", ".aac", ".ogg")
FUENTE = r"C:\Windows\Fonts\courbd.ttf"
W, H, FPS = 1920, 1080, 30
BG = "0x2E3A22"
CREMA = "0xEFE9D8"
ORO = "0xB8892B"
ROJO = "0x8C2B22"

# --- el guion: (tipo, id, datos). Las tarjetas «bg» usan un clip de Flow como fondo oscurecido.
ESCENAS = [
    ("frio", "sobre", {"voz": "00-general"}),
    ("tarjeta", "titulo", {"dur": 6.0, "bg": None, "lineas": [("MISIÓN:", 110, 330, 0.6), ("CERO PUNTO DOS", 130, 480, 1.4)],
                           "sub": ("Escuadrón SONAR", 44, 660, 3.6), "linea_roja": True}),
    ("tarjeta", "acto1", {"dur": 3.2, "bg": "mesa", "lineas": [("ACTO I", 70, 400, 0.4), ("LA ORDEN", 130, 500, 0.9)]}),
    ("toma", "01-orden", {}),
    ("tarjeta", "acto2", {"dur": 3.2, "bg": "radio", "lineas": [("ACTO II", 70, 380, 0.4), ("EL INFORME DE CAMPO", 105, 480, 0.9)]}),
    ("tarjeta", "c1", {"dur": 3.0, "bg": None, "lineas": [("I · EL CAMPO", 90, 430, 0.3)],
                       "sub": ("«El terreno es honesto. Solo miente quien lo mide mal.»", 40, 600, 1.0)}),
    ("toma", "02-campo", {}),
    ("tarjeta", "c2", {"dur": 3.0, "bg": None, "lineas": [("II · LA TROPA", 90, 430, 0.3)],
                       "sub": ("«Una tropa pequeña, bien alimentada, vale por un regimiento.»", 40, 600, 1.0)}),
    ("toma", "03-tropa", {}),
    ("tarjeta", "c3", {"dur": 3.0, "bg": None, "lineas": [("III · EL MAPA DE LAS CUATRO ESQUINAS", 70, 430, 0.3)],
                       "sub": ("«Ningún mapa se dibuja desde la oficina. Se camina el terreno.»", 40, 600, 1.0)}),
    ("toma", "04-mapa", {}),
    ("tarjeta", "c4", {"dur": 3.0, "bg": None, "lineas": [("IV · EL PULSO SERENO", 90, 430, 0.3)],
                       "sub": ("«Quien dispara con la mano temblorosa, falla dos veces: la primera al apuntar.»", 38, 600, 1.0)}),
    ("toma", "05-pulso", {}),
    ("tarjeta", "c5", {"dur": 3.0, "bg": None, "lineas": [("V · LA RADIO", 90, 430, 0.3)],
                       "sub": ("«Una orden clara vale más que mil soldados.»", 40, 600, 1.0)}),
    ("toma", "06-radio", {}),
    ("tarjeta", "c6", {"dur": 3.0, "bg": None, "lineas": [("VI · LA PRUEBA DE FUEGO", 90, 430, 0.3)],
                       "sub": ("«Al final, todo mapa se juzga en el terreno.»", 40, 600, 1.0)}),
    ("toma", "07-prueba", {}),
    ("tarjeta", "acto3", {"dur": 3.2, "bg": "amanecer", "lineas": [("ACTO III", 70, 400, 0.4), ("EL REGRESO", 130, 500, 0.9)]}),
    ("toma", "08-regreso", {}),
    ("tarjeta", "fin", {"dur": 7.0, "bg": "sello", "lineas": [("MISIÓN CUMPLIDA", 120, 330, 0.6)],
                        "sub": ("Los números no se pierden.", 46, 520, 2.0), "sub2": ("Esperan a que alguien los explique.", 46, 590, 2.8),
                        "nombres": True}),
]


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("ERROR ffmpeg:", " ".join(cmd)[:400])
        print(r.stderr[-1500:])
        sys.exit(1)
    return r


def buscar(carpeta, nombre, exts):
    for e in exts:
        for p in glob.glob(os.path.join(AQUI, carpeta, nombre + "*" + e)) + glob.glob(os.path.join(AQUI, carpeta, nombre.upper() + "*" + e)):
            return p
    return None


def duracion(p):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p])
    return float(json.loads(r.stdout)["format"]["duration"])


def tiene_audio(p):
    r = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "json", p])
    return bool(json.loads(r.stdout)["streams"])


class Montaje:
    def __init__(self, trabajo, ancho, alto, nombres):
        self.t = trabajo
        self.w, self.h = ancho, alto
        self.k = ancho / 1920.0
        self.nombres = nombres
        self.n = 0
        self.partes = []
        shutil.copy(FUENTE, os.path.join(trabajo, "f.ttf"))

    def sal(self, etiqueta):
        self.n += 1
        return f"{self.n:02d}-{etiqueta}.mp4"

    def vf_base(self):
        return (f"scale={self.w}:{self.h}:force_original_aspect_ratio=decrease,pad={self.w}:{self.h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setsar=1,fps={FPS},format=yuv420p")

    def codec(self, salida):
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", salida]

    # ---------------------------------------------------------------- tarjeta
    def tarjeta(self, id_, d):
        out = self.sal("tarjeta-" + id_)
        dur = d["dur"]
        bgp = buscar("clips-flow", d["bg"], EXT_V) if d.get("bg") else None
        entradas = (["-stream_loop", "-1", "-i", bgp] if bgp else ["-f", "lavfi", "-i", f"color=c={BG}:s={self.w}x{self.h}:r={FPS}"])
        ajuste = "eq=brightness=-0.28:saturation=0.75:contrast=1.08," if bgp else ""
        vf = [f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h},fps={FPS},"
              f"{ajuste}vignette=PI/4,noise=alls=7:allf=t"]
        textos = list(d["lineas"])
        if d.get("sub"):
            textos.append(d["sub"])
        if d.get("sub2"):
            textos.append(d["sub2"])
        if d.get("nombres") and self.nombres:
            textos.append((self.nombres, 36, 760, 4.2))
        for i, (txt, tam, y, t0) in enumerate(textos):
            arch = f"t-{id_}-{i}.txt"
            with open(os.path.join(self.t, arch), "w", encoding="utf-8") as f:
                f.write(txt)
            color = ORO if i == 0 and len(d["lineas"]) > 1 and tam < 80 else CREMA
            vf.append(f"drawtext=fontfile=f.ttf:textfile={arch}:fontsize={int(tam * self.k)}:fontcolor={color}:"
                      f"x=(w-text_w)/2:y={int(y * self.k)}:alpha='if(lt(t,{t0}),0,min(1,(t-{t0})/0.7))'")
        if d.get("linea_roja"):
            vf.append(f"drawbox=x=(iw-{int(1100 * self.k)})/2:y={int(620 * self.k)}:w='min({int(1100 * self.k)},max(0,(t-2.6)*1400))':h={max(2, int(8 * self.k))}:color={ROJO}:t=fill")
        vf.append(f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5}:d=0.5,format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(dur),
                                                                    "-vf", ",".join(vf), "-shortest"] + self.codec(out)
        run(cmd, cwd=self.t)
        self.partes.append(out)

    # ---------------------------------------------------------------- tomas
    def toma(self, id_, p):
        out = self.sal("toma-" + id_)
        vf = self.vf_base() + ",fade=t=in:st=0:d=0.25"
        if tiene_audio(p):
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-vf", vf, "-af", "aresample=48000,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.1"] + self.codec(out)
        else:
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-shortest"] + self.codec(out)
        run(cmd, cwd=self.t)
        self.partes.append(out)

    def falta(self, id_, que):
        d = {"dur": 2.5, "bg": None, "lineas": [("FALTA", 100, 380, 0.1)], "sub": (que, 44, 560, 0.3)}
        self.tarjeta("falta-" + id_, d)

    def frio(self, id_, d):
        clip = buscar("clips-flow", id_, EXT_V)
        voz = buscar("voz", d["voz"], EXT_A) if d.get("voz") else None
        if not clip:
            return self.falta(id_, f"clips-flow/{id_}.mp4 (clip del sobre)")
        out = self.sal("frio-" + id_)
        vd = duracion(clip)
        vf = self.vf_base() + ",eq=brightness=-0.1:saturation=0.85,fade=t=in:st=0:d=0.8"
        if voz:
            ad = duracion(voz)
            T = max(vd, ad + 0.8)
            vf += f",tpad=stop_mode=clone:stop_duration={max(0.0, T - vd):.2f},fade=t=out:st={T - 0.6:.2f}:d=0.6"
            af = "aresample=48000,aformat=channel_layouts=stereo,adelay=700|700,apad,highpass=f=300,lowpass=f=3400,volume=1.6"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-i", voz, "-vf", vf, "-af", af, "-map", "0:v", "-map", "1:a", "-t", f"{T:.2f}"] + self.codec(out)
        else:
            vf += f",fade=t=out:st={vd - 0.6:.2f}:d=0.6"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-shortest"] + self.codec(out)
        run(cmd, cwd=self.t)
        self.partes.append(out)


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
    faltan = []
    with tempfile.TemporaryDirectory() as tmp:
        m = Montaje(tmp, ancho, alto, a.nombres)
        for tipo, id_, d in ESCENAS:
            if tipo == "tarjeta":
                m.tarjeta(id_, d)
            elif tipo == "frio":
                if not buscar("clips-flow", id_, EXT_V):
                    faltan.append(f"clips-flow/{id_}")
                m.frio(id_, d)
            else:
                p = buscar("tomas", id_, EXT_V)
                if p:
                    m.toma(id_, p)
                else:
                    faltan.append(f"tomas/{id_}")
                    m.falta(id_, f"tomas/{id_}.mp4")
            print("  listo:", id_)
        lista = os.path.join(tmp, "lista.txt")
        with open(lista, "w", encoding="utf-8") as f:
            for p in m.partes:
                f.write(f"file '{p}'\n")
        unido = os.path.join(tmp, "unido.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "lista.txt", "-c", "copy", "unido.mp4"], cwd=tmp)
        total = duracion(unido)
        musica = None
        for e in EXT_A:
            g = glob.glob(os.path.join(AQUI, "musica", "*" + e))
            if g:
                musica = g[0]
                break
        af = "loudnorm=I=-16:TP=-1.5:LRA=11"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", unido]
        if musica:
            cmd += ["-stream_loop", "-1", "-i", musica, "-filter_complex",
                    f"[1:a]volume=0.10,afade=t=in:st=0:d=2,afade=t=out:st={max(0, total - 3):.1f}:d=3,atrim=0:{total:.1f}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,{af}[a]",
                    "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-af", af]
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.salida]
        run(cmd, cwd=tmp)
    print(f"\nListo: {a.salida}\nDuración: {int(total // 60)}:{int(total % 60):02d}" + ("  (¡pasa de 6:00!)" if total > 360 else ""))
    if faltan:
        print("Faltan (se pusieron tarjetas «FALTA»):", ", ".join(faltan))
    if not musica:
        print("Sin música: pon un .mp3 en musica/ si quieres (volumen automático al 10 %).")


if __name__ == "__main__":
    main()
