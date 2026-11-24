"""Director del video «MISIÓN: CERO PUNTO DOS» — guion técnico con tiempos exactos.

    python armar_final.py --vista-previa        # 640x360, para revisar tiempos y orden
    python armar_final.py                        # versión final 1080p
    python armar_final.py --solo titulo,orden    # renderiza solo esas escenas (con --vista-previa)

Los tiempos de cada capa salen de la transcripción por palabras de cada toma (Whisper) y de la detección de silencios.
Las voces de Bravo en el final son PROVISIONALES (la guía grabada por Sebas): si Juan José entrega las suyas, basta ponerlas en
voz/bravo-1.m4a, bravo-2.m4a, bravo-3.m4a y se usan en su lugar.
"""
import argparse
import glob
import os
import sys

import motor as M
from motor import A, Escena, S, png_texto

R = "recursos"
SEB = "tomas/sebastian_videos"
JJ = "tomas/j_jose_videos"

# ------------------------------------------------------------------ cadenas de audio
CAD_SEBAS = ("highpass=f=85,afftdn=nr=14:nf=-28,equalizer=f=220:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1:g=2.5,"
             "acompressor=threshold=-20dB:ratio=3.2:attack=6:release=90:makeup=4,loudnorm=I=-17:TP=-2:LRA=7")
CAD_JJ = ("highpass=f=85,afftdn=nr=10:nf=-30,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1:g=2,"
          "acompressor=threshold=-20dB:ratio=3:attack=6:release=90:makeup=3,loudnorm=I=-17:TP=-2:LRA=7")
RADIO = ("highpass=f=380,lowpass=f=3200,equalizer=f=1500:t=q:w=1.2:g=4,acompressor=threshold=-24dB:ratio=6:attack=3:release=60:makeup=5,"
         "asoftclip=type=tanh:threshold=0.55,volume=0dB")
CAD_GENERAL = "highpass=f=90,afftdn=nr=12:nf=-30,loudnorm=I=-17:TP=-2:LRA=7," + RADIO + ",aecho=0.6:0.4:35:0.25"
CAD_BRAVO = "highpass=f=90,afftdn=nr=12:nf=-28,rubberband=pitch=1.10:formant=preserved,loudnorm=I=-17:TP=-2:LRA=7," + RADIO


def fade_voz(d, fo=0.12):
    return f",afade=t=out:st={max(0, d - fo):.3f}:d={fo}"


def seq_starts(durs, x):
    t = 0.0
    out = []
    for d in durs:
        out.append(t)
        t += d - x
    return out


FLOW = lambda n: A(f"clips-flow/{n}.mp4")
APP = A(f"{SEB}/Grabacion_celular_uso_app.mp4")
DEMO = A(f"{SEB}/demostracion_apuntado_laser.mp4")
BOTON = A(f"{SEB}/encendido_boton.mp4")
LASER = A(f"{SEB}/encendido_laser.mp4")
IG = lambda n: A(f"{R}/graficos/{n}.png")
EV = lambda n: A(f"evidencia/{n}")


def img_recurso(*claves):
    """Primera imagen descargada (recursos/imagenes) cuyo nombre contenga alguna de las claves."""
    for c in claves:
        g = sorted(glob.glob(os.path.join(M.ROOT, R, "imagenes", f"*{c}*")))
        if g:
            return g[0]
    return None


# ====================================================================== ESCENAS
def escena_frio():
    sobre, mesa = FLOW("sobre"), FLOW("mesa")
    e = Escena("frio", 15.2, dict(t="seq", clips=[(sobre, 0.0, 8.0, "flow"), (mesa, 0.0, 7.7, "flow")], xf=0.9, tr="fadeblack"), ("fadeblack", 0.5))
    # texto sobre la voz del General (voz en local 1.5 s; palabras del archivo + 1.5)
    for a, b, tx in [(3.5, 5.3, "ESCUADRÓN SONAR"), (5.4, 7.9, "HAY NÚMEROS QUE NO SE PIERDEN:\nESPERAN"),
                     (8.0, 10.7, "DOS DÉCIMAS QUEDARON\nEN EL CAMPO DE LA ESTÉTICA"), (10.9, 12.5, "EL CINCO NO SE NEGOCIA"), (12.6, 14.6, "TIENEN UN INFORME QUE DAR")]:
        e.texto(tx, a, b, size=62, y=f"H-h-{S(150)}", slide=14, fade=0.35)
    e.png(png_texto("ORDEN DEL GENERAL", 40, M.ORO, "d", borde=False), 1.6, 14.6, x=str(S(70)), y=str(S(60)), fade=0.6)
    gen = A("voz/P1_sebas.ogg")
    e.sfx("estatica", 0.0, gain=-20, d=14.6, cadena="afade=t=in:st=0:d=0.8,afade=t=out:st=13.4:d=1.2")
    e.sfx("latido", 0.5, gain=-14)
    e.sfx("latido", 2.4, gain=-16)
    e.sfx("squelch_in", 1.2, gain=-7)
    e.voz(gen, 1.5, cadena=CAD_GENERAL, d=12.9, gain=0)
    e.sfx("roger_out", 14.45, gain=-9)
    e.sfx("riser", 10.6, gain=-12, d=4.5)
    return e


def escena_titulo():
    e = Escena("titulo", 6.2, dict(t="card", bg=None), ("fadeblack", 0.7))
    e.texto("MISIÓN:", 0.5, 6.0, size=120, y=str(S(300)), slide=24, fade=0.6)
    e.texto("CERO PUNTO DOS", 1.2, 6.0, size=146, y=str(S(450)), slide=24, fade=0.6)
    e.texto("Escuadrón SONAR  ·  Batalla Naval", 3.4, 6.0, size=44, color=(190, 190, 170), y=str(S(680)), kind="b", slide=10, fade=0.7)
    e.capas.append(dict(t="png", src=png_texto("", 10), a=0, b=0.01, x="0", y="0", fade=0.01, slide=0, pip=False)) if False else None
    e.sfx("boom", 0.0, gain=-3)
    e.sfx("ping", 2.4, gain=-14)
    return e


def tarjeta(id_, linea1, linea2, bg, dur=3.0, trans=("dissolve", 0.5), sfx="whoosh_corto"):
    e = Escena(id_, dur, dict(t="card", bg=FLOW(bg)), trans)
    e.texto(linea1, 0.25, dur - 0.2, size=64, color=M.ORO, y=str(S(380)), slide=14, fade=0.4)
    e.texto(linea2, 0.6, dur - 0.2, size=118 if len(linea2) < 14 else 88, y=str(S(480)), slide=18, fade=0.45)
    e.sfx(sfx, 0.0, gain=-14)
    return e


def escena_orden():
    src = A(f"{SEB}/1er-video.mp4")
    d = 31.4
    e = Escena("orden", d, dict(t="clip", src=src, ss=0.0, grade="sebas", zoom=0.07, pan=(0.35, 0.5, 0.62, 0.5)), ("pixelize", 0.55))
    e.rotulo("CAPITÁN ALFA", 3.2, 7.2, sub="Sebastián · jefe del escuadrón")
    # texto cinético sobre las palabras clave
    e.texto("4,8", 9.8, 11.5, size=230, color=M.CREMA, y=f"(H-h)/2-{S(80)}", slide=0, fade=0.3)
    e.texto("−0,2", 11.8, 14.2, size=230, color=M.ROJO, y=f"(H-h)/2-{S(80)}", slide=0, fade=0.3)
    e.texto("LA TRINCHERA DE LA ESTÉTICA", 13.4, 15.6, size=74, y=f"H-h-{S(170)}", slide=14)
    e.texto("EXPLICAR LA CAMPAÑA", 19.3, 22.9, size=86, y=f"H-h-{S(170)}", slide=14)
    e.texto("EL CINCO SAGRADO", 25.3, 27.8, size=118, color=M.ORO, y=f"(H-h)/2-{S(60)}", slide=16, fade=0.45)
    # cortes (la voz continúa): el sobre cuando dice «una sola orden», la radio al pasar el mando
    sobre, radio = FLOW("sobre"), FLOW("radio")
    e.video(sobre, 17.9, 20.2, ss=4.2, fit="cover", grade="flow", pip=True, fade=0.3)
    e.video(radio, 29.3, 31.4, ss=0.4, fit="cover", grade="flow", pip=False, fade=0.25, rot="HACIA EL SARGENTO BRAVO", sub="cambio de mando por radio")
    e.voz(src, 0.0, cadena=CAD_SEBAS + fade_voz(d, 0.3), d=d)
    e.sfx("squelch_in", 29.2, gain=-9)
    e.sfx("glitch", 30.6, gain=-9)
    e.sfx("ping", 3.2, gain=-20)
    return e


# ------------------------------------------------------------------ Juan José
def jj_clip(n):
    return A(f"{JJ}/{n}.mp4")


def escena_jj(n, d, trans, titulo, num, capas):
    src = jj_clip(n)
    e = Escena(f"jj{n}", d, dict(t="clip", src=src, ss=0.0, grade="jj", zoom=0.05, pan=(0.45, 0.5, 0.55, 0.5)), trans)
    e.capitulo(num, titulo, 0.35, 3.6)
    e.sfx("tecla", 0.35, gain=-18)
    e.sfx("tecla", 0.43, gain=-20)
    e.sfx("tecla", 0.5, gain=-18)
    e.sfx("whoosh_corto", 0.0, gain=-18)
    e.voz(src, 0.0, cadena=CAD_JJ + fade_voz(d, 0.25), d=d)
    capas(e)
    return e


def jj1(e):
    ig_a, ig_b = IG("ig1_a"), IG("ig1_b")
    e.foto(ig_a, 0.9, 6.0, fit="fill", drift=0.03, pip=True)
    e.foto(ig_b, 6.0, 11.9, fit="fill", drift=0.03, pip=True)
    e.video(APP, 12.0, 15.9, ss=17.0, fit="contain", grade="none", pip=True, rot="LA APP SE CONECTA POR BLUETOOTH", sub="el rival maneja TU tablero · módulo «SONAR-A»", borde=True)
    e.video(APP, 16.0, 22.8, ss=28.0, fit="contain", grade="none", pip=True, rot="LA COORDENADA (x, y)", sub="x primero, luego y", borde=True)


def jj2(e):
    e.foto(EV("crop-esp32.png"), 0.5, 3.4, fit="contain", drift=0.05, pip=True, rot="EL CEREBRO · ESP32", sub="nuestra placa, ya montada", borde=True)
    e.foto(IG("ig2_a"), 3.4, 5.4, fit="fill", drift=0.03, pip=True)
    e.foto(IG("ig2_b"), 5.4, 7.6, fit="fill", drift=0.03, pip=True)
    e.foto(EV("crop-servos.png"), 7.6, 11.3, fit="contain", drift=0.05, pip=True, rot="LAS DOS TORRES · PAN Y TILT", sub="nuestro cardán con el láser encima", borde=True)
    e.video(LASER, 11.4, 13.4, ss=5.2, fit="cover", grade="demo", pip=True, rot="EL OJO · LÁSER ROJO 650 nm", fade=0.25)
    e.video(BOTON, 13.4, 15.0, ss=0.3, fit="cover", grade="flow", pip=True, rot="INTERRUPTOR GENERAL", fade=0.25)
    e.foto(EV("crop-pilas.png"), 15.0, 16.1, fit="contain", drift=0.04, pip=True, rot="6 V · 4 PILAS AA", borde=True, fade=0.25)
    e.foto(IG("ig2_c"), 16.1, 21.0, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig2_d"), 21.0, 28.6, fit="fill", drift=0.02, pip=True)
    e.foto(EV("crop-capacitor.png"), 22.9, 25.0, fit="contain", drift=0.05, pip=True, rot="CAPACITOR DE 1000 µF", sub="nuestro montaje", borde=True, fade=0.3)


def jj3(e):
    e.video(APP, 0.6, 3.8, ss=143.0, fit="contain", pip=True, rot="CALIBRAR APUNTADO", sub="la cruceta lleva el láser a cada esquina", borde=True)
    e.foto(IG("ig3_a"), 3.8, 7.6, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig3_b"), 7.6, 17.0, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig3_c"), 17.0, 22.9, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig3_d"), 22.9, 28.0, fit="fill", drift=0.02, pip=True)


def jj4(e):
    e.foto(IG("ig4_a"), 0.5, 6.4, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig4_b"), 6.4, 15.0, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig4_c"), 15.0, 25.6, fit="fill", drift=0.02, pip=True)
    e.video(APP, 18.8, 22.4, ss=106.0, fit="contain", pip=True, rot="STOP EN LA APP", sub="apaga el láser al instante", borde=True)


def jj5(e):
    e.video(APP, 0.8, 5.4, ss=121.0, fit="contain", pip=True, rot="CONECTADO A «SONAR-A»", sub="firmware 0.2.0 · Bluetooth", borde=True)
    e.foto(IG("ig5_a"), 5.4, 15.8, fit="fill", drift=0.02, pip=True)
    e.video(APP, 15.8, 19.2, ss=40.0, fit="contain", pip=True, rot="¿LE DIO?", sub="el testigo responde", borde=True)
    e.foto(IG("ig5_b"), 19.2, 24.1, fit="fill", drift=0.02, pip=True)
    e.foto(IG("ig5_c"), 24.1, 26.4, fit="fill", drift=0.02, pip=True)
    e.video(APP, 26.4, 29.5, ss=50.0, fit="contain", pip=True, rot="LA APP DICE DÓNDE ESTABA", sub="(10,12) a (10,15)", borde=True)


# ------------------------------------------------------------------ prueba de fuego
def escena_prueba():
    d = 27.0
    base = dict(t="clip", src=DEMO, ss=9.0, grade="demo", zoom=0.04, pan=(0.4, 0.5, 0.6, 0.5))
    e = Escena("prueba", d, base, ("fadeblack", 0.8))
    e.capitulo("VI", "LA PRUEBA DE FUEGO", 0.4, 4.0)
    e.sfx("redoble", 0.0, gain=-12)
    e.sfx("caja", 3.4, gain=-8)
    segs = [(9.5, 4.4), (21.0, 4.4), (33.0, 4.4), (47.0, 4.4), (61.0, 4.4)]
    t = 3.6
    for k, (ss, dd) in enumerate(segs):
        a, b = t, t + dd
        e.video(DEMO, a, b, ss=ss, fit="cover", grade="demo", pip=False, fade=0.25)
        e.foto(IG(f"ig6_{k + 1}"), a, b, fit="fill", drift=0.0, pip=False) if False else None
        # tablero-contador a la derecha (miniatura del gráfico)
        e.png(png_texto(f"POSICIÓN {k + 1} / 5", 54, M.CREMA, "d"), a + 0.2, b - 0.1, x=str(S(70)), y=f"H-h-{S(120)}", fade=0.25, slide=S(10))
        e.sfx("pitido", a + 0.1, gain=-10)
        e.sfx("ping", a + 0.1, gain=-22)
        t = b - 0.2
    e.foto(IG("ig6_5"), t, d, fit="fill", drift=0.0, pip=False, fade=0.5)
    e.texto("TEST COMPLETO", t + 0.4, d - 0.5, size=120, color=M.ORO, y=f"H-h-{S(150)}", fade=0.4)
    e.sfx("caja", t + 0.4, gain=-8)
    return e


# ------------------------------------------------------------------ regreso (Sebas + radio de Bravo)
def escena_regreso():
    fin = A(f"{SEB}/final-video.mp4")
    bak = A(f"{SEB}/reespaldo_audio_escena_finales.ogg")
    radio, sello = FLOW("radio"), FLOW("sello")
    x = 0.15
    D = [4.3, 4.3, 3.4, 6.2, 9.5, 2.7]
    S_ = seq_starts(D, x)
    clips = [(fin, 0.0, D[0], "sebas"), (radio, 0.0, D[1], "flow", 0.7), (fin, 6.3, D[2], "sebas"), (radio, 2.6, D[3], "flow", 0.7),
             (fin, 12.9, D[4], "sebas"), (sello, 0.0, D[5], "flow")]
    total = S_[-1] + D[-1]
    e = Escena("regreso", total, dict(t="seq", clips=clips, xf=x, tr="fade", zoom=0.05), ("fadeblack", 0.9))
    e.rotulo("SARGENTO BRAVO · TRANSMISIÓN", S_[1] + 0.2, S_[1] + D[1] - 0.2, sub="por radio")
    e.rotulo("SARGENTO BRAVO · TRANSMISIÓN", S_[3] + 0.2, S_[3] + D[3] - 0.3, sub="por radio")
    e.rotulo("SARGENTO BRAVO · TRANSMISIÓN", S_[5] + 0.1, S_[5] + D[5] - 0.2, sub="por radio")
    e.rotulo("CAPITÁN ALFA", 0.4, 3.0, sub="Sebastián")
    # Alfa (video + audio sincronizados con el mismo desfase)
    e.voz(fin, S_[0], ss=0.0, d=4.3, cadena=CAD_SEBAS + fade_voz(4.3, 0.15))
    e.voz(fin, S_[2] + 0.05, ss=6.35, d=3.05, cadena=CAD_SEBAS + fade_voz(3.05, 0.15))
    e.voz(fin, S_[4] + 0.10, ss=13.0, d=9.4, cadena=CAD_SEBAS + fade_voz(9.4, 0.25))
    # Bravo por radio (provisional: guía de Sebas; se reemplaza si llegan bravo-1/2/3.m4a)
    def bravo(n, ss, d_, t0):
        real = A(f"voz/bravo-{n}.m4a") or A(f"voz/bravo-{n}.mp3") or A(f"voz/bravo-{n}.ogg")
        src, s0, dd, cad = (real, 0.0, None, "highpass=f=90,afftdn=nr=10,loudnorm=I=-17:TP=-2:LRA=7," + RADIO) if real else (bak, ss, d_, CAD_BRAVO)
        e.sfx("squelch_in", t0 - 0.28, gain=-8)
        e.voz(src, t0, ss=s0, d=dd, cadena=cad + (fade_voz(d_, 0.1) if not real else ""))
        e.sfx("roger_out", t0 + d_ + 0.02, gain=-10)
    bravo(1, 1.15, 3.75, S_[1] + 0.55)
    bravo(2, 5.70, 5.40, S_[3] + 0.55)
    bravo(3, 11.35, 1.85, S_[5] + 0.45)
    e.sfx("estatica", S_[1], gain=-24, d=D[1] + 0.5, cadena="afade=t=in:st=0:d=0.3,afade=t=out:st=3.9:d=0.6")
    e.sfx("estatica", S_[3], gain=-24, d=D[3] + 0.5, cadena="afade=t=in:st=0:d=0.3,afade=t=out:st=5.8:d=0.6")
    e.sfx("caja", S_[4] + 0.1 + (21.1 - 13.0), gain=-7)
    e.sfx("estampa", S_[5] + 0.2, gain=-8)
    return e


# ------------------------------------------------------------------ cierre y créditos
def png_creditos(nombre, lineas, size=44, interlin=1.55):
    from PIL import Image, ImageDraw
    f_t, f_n = M.fnt(size + 6, "d"), M.fnt(size - 6, "b")
    im = Image.new("RGBA", (M.W, M.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = int(M.H * 0.22)
    for (rol, quien) in lineas:
        if quien is None:
            d.text((M.W // 2, y), rol, font=f_t, fill=M.ORO + (255,), anchor="mm")
            y += int(size * 2.0)
            continue
        d.text((M.W // 2 - S(30), y), rol, font=f_n, fill=(190, 190, 170, 255), anchor="rm")
        d.text((M.W // 2 + S(30), y), quien, font=f_n, fill=M.CREMA + (255,), anchor="lm")
        y += int(size * interlin)
    out = os.path.join(M.WORK, f"cred-{nombre}-{int(M.K * 100)}.png")
    im.save(out)
    return out


def escena_fin():
    d = 24.0
    e = Escena("fin", d, dict(t="card", bg=FLOW("amanecer")), ("fadeblack", 0.0))
    e.texto("MISIÓN CUMPLIDA", 0.6, 6.6, size=128, color=M.CREMA, y=str(S(320)), slide=20, fade=0.7)
    e.texto("Los números no se pierden.\nEsperan a que alguien los explique.", 2.4, 6.6, size=50, color=(210, 205, 185), y=str(S(520)), kind="b", slide=10, fade=0.7)
    e.sfx("boom", 0.4, gain=-9)
    c1 = png_creditos("a", [("EL ESCUADRÓN", None), ("CAPITÁN ALFA", "Sebastián"), ("SARGENTO BRAVO", "Juan José"), ("DIRECCIÓN, EDICIÓN Y POSTPRODUCCIÓN", "el escuadrón"), ("ASISTENCIA DE IA", "Claude (Anthropic)")])
    c2 = png_creditos("b", [("EL SISTEMA", None), ("CEREBRO", "ESP32 · firmware en C++"), ("MOVIMIENTO", "2 servos · láser 650 nm"), ("APP", "propia · Bluetooth (SPP)"), ("PRUEBAS", "71 pruebas automáticas")])
    cred = M.A(f"{R}/CREDITOS.md")
    c3_lineas = [("AGRADECIMIENTOS Y LICENCIAS", None), ("CLIPS DE FICCIÓN", "generados con Google Flow (IA)"), ("EFECTOS DE SONIDO", "sintetizados por el escuadrón")]
    for ln in CREDITOS_VIDEO:
        c3_lineas.append(ln)
    c3 = png_creditos("c", c3_lineas, size=38, interlin=1.5)
    for k, (c, a, b) in enumerate([(c1, 6.6, 11.8), (c2, 11.8, 16.6), (c3, 16.6, 23.6)]):
        e.png(c, a, b, x="0", y="0", fade=0.6, slide=0)
    return e


CREDITOS_VIDEO = []   # se rellena con las pistas/imágenes realmente usadas


# ====================================================================== PROGRAMA
def construir():
    E = {}
    E["frio"] = escena_frio()
    E["titulo"] = escena_titulo()
    E["acto1"] = tarjeta("acto1", "ACTO I", "LA ORDEN", "mesa", 3.0, ("dissolve", 0.5))
    E["orden"] = escena_orden()
    E["acto2"] = tarjeta("acto2", "ACTO II", "EL INFORME DE CAMPO", "radio", 3.0, ("dissolve", 0.5))
    E["jj1"] = escena_jj(1, 23.4, ("smoothleft", 0.6), "EL CAMPO", "I", jj1)
    E["jj2"] = escena_jj(2, 28.9, ("dissolve", 0.6), "LA TROPA", "II", jj2)
    E["jj3"] = escena_jj(3, 28.2, ("smoothleft", 0.6), "EL MAPA DE LAS CUATRO ESQUINAS", "III", jj3)
    E["jj4"] = escena_jj(4, 26.0, ("dissolve", 0.6), "EL PULSO SERENO", "IV", jj4)
    E["jj5"] = escena_jj(5, 29.8, ("fadeblack", 0.8), "LA RADIO", "V", jj5)
    E["prueba"] = escena_prueba()
    E["acto3"] = tarjeta("acto3", "ACTO III", "EL REGRESO", "amanecer", 3.0, ("dissolve", 0.5))
    E["regreso"] = escena_regreso()
    E["fin"] = escena_fin()
    # sonidos de transición adicionales
    E["jj1"].sfx("whoosh", 0.0, gain=-16)
    E["jj5"].sfx("riser", 24.0, gain=-14, d=5.8)
    return E


ORDEN = ["frio", "titulo", "acto1", "orden", "acto2", "jj1", "jj2", "jj3", "jj4", "jj5", "prueba", "acto3", "regreso", "fin"]


def plan_musica(starts, E):
    """Plan de música: lista de tramos. Se completa con las pistas elegidas (ver MUSICA)."""
    out = []
    for m in MUSICA:
        src = A(m["archivo"])
        if not src:
            continue
        t0 = starts[m["desde"]] + m.get("off", 0.0)
        t1 = (starts[m["hasta"]] + E[m["hasta"]].dur if m.get("fin", True) else starts[m["hasta"]]) + m.get("off_fin", 0.0)
        out.append(dict(src=src, t0=t0, t1=t1, ss=m.get("ss", 0), gain=m.get("gain", -10), fi=m.get("fi", 2.5), fo=m.get("fo", 3.5)))
    return out


MUSICA = []   # ver musica.py (se genera al elegir las pistas)

if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "musica_plan.py")):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import musica_plan
    MUSICA = musica_plan.MUSICA
    CREDITOS_VIDEO.extend(getattr(musica_plan, "CREDITOS", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vista-previa", action="store_true")
    ap.add_argument("--solo", default="")
    ap.add_argument("--salida", default="")
    a = ap.parse_args()
    M.conf(a.vista_previa)
    E = construir()
    orden = [x for x in ORDEN if (not a.solo or x in a.solo.split(","))]
    for k in orden:
        E[k].render()
        print("  escena", k, f"{E[k].dur:.1f}s", flush=True)
    if a.solo:
        return
    esc = [E[k] for k in ORDEN]
    starts_l = []
    t = 0.0
    for i, e in enumerate(esc):
        starts_l.append(t)
        t += e.dur - (e.trans[1] if i < len(esc) - 1 else 0)
    starts = dict(zip(ORDEN, starts_l))
    salida = a.salida or os.path.join(M.ROOT, "salida", "MISION-CERO-PUNTO-DOS_" + ("previa" if a.vista_previa else "1080p") + ".mp4")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    total, _ = M.ensamblar(esc, plan_musica(starts, E), salida)
    print(f"\nListo: {salida}\nDuración: {int(total // 60)}:{total % 60:04.1f}")
    for k in ORDEN:
        print(f"  {k:8s} empieza en {starts[k]:6.1f}s")


if __name__ == "__main__":
    main()
