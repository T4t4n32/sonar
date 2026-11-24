"""Sintetiza los efectos de sonido del video (sin derechos de autor: se generan aquí). Uso: uv run --with numpy --with scipy python gen_sfx.py"""
import os
import wave

import numpy as np
from scipy import signal

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos", "sfx")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def wav(name, x, peak=0.9):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) or 1.0
    x = x / m * peak
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def bp(x, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=4):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=4):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def reverb(x, tail=1.2, mix=0.3):
    n = int(SR * tail)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * tail / 5))
    ir = lp(ir, 5000)
    y = signal.fftconvolve(x, ir)[: len(x) + n]
    y = y / (np.max(np.abs(y)) or 1) * (np.max(np.abs(x)) or 1)
    out = np.zeros(len(y))
    out[: len(x)] += x * (1 - mix)
    out += y * mix
    return out


# 1. estática de radio (bucle de 8 s)
t = t_(8)
n = bp(rng.standard_normal(len(t)), 600, 4800)
am = 0.65 + 0.35 * np.sin(2 * np.pi * 0.7 * t + np.sin(2 * np.pi * 0.13 * t) * 3) * np.sin(2 * np.pi * 3.1 * t) ** 2
crack = (rng.random(len(t)) > 0.9993) * rng.standard_normal(len(t)) * 5
wav("estatica", n * am + hp(crack, 1500), 0.7)

# 2. squelch de entrada (kssh) y roger de salida
t = t_(0.28)
sq = hp(rng.standard_normal(len(t)), 900) * np.exp(-t * 14) * (1 - np.exp(-t * 400))
wav("squelch_in", sq)
t = t_(0.7)
b1 = np.sin(2 * np.pi * 1760 * t) * ((t > 0.0) & (t < 0.09))
b2 = np.sin(2 * np.pi * 1320 * t) * ((t > 0.11) & (t < 0.2))
tail = hp(rng.standard_normal(len(t)), 900) * np.exp(-(t - 0.22).clip(0) * 18) * (t > 0.22)
wav("roger_out", (b1 + b2) * 0.7 + tail * 0.8)

# 3. whoosh (barrido con filtro móvil simulado por mezcla de bandas)
def whoosh(d, f0, f1, nombre, tono=1.0):
    t = t_(d)
    nz = rng.standard_normal(len(t))
    y = np.zeros(len(t))
    k = 14
    for i in range(k):
        f = f0 * (f1 / f0) ** (i / (k - 1))
        c = (i + 0.5) / k
        env = np.exp(-((t / d - c) ** 2) / (2 * 0.06**2))
        y += bp(nz, max(60, f * 0.8), min(SR / 2 - 100, f * 1.25), 2) * env
    y *= np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.8
    wav(nombre, reverb(y * tono, 0.5, 0.25))


whoosh(0.9, 300, 4500, "whoosh")
whoosh(0.6, 600, 3000, "whoosh_corto")
whoosh(1.4, 200, 2500, "whoosh_largo")

# 4. impacto / boom (título)
t = t_(3.2)
sub = np.sin(2 * np.pi * (48 * np.exp(-t * 0.8) + 28) * t) * np.exp(-t * 1.6)
thump = lp(rng.standard_normal(len(t)), 180) * np.exp(-t * 7)
crack = hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 45) * 0.5
wav("boom", reverb(sub * 1.1 + thump * 0.9 + crack, 2.0, 0.35), 0.95)

# 5. riser (4 s)
t = t_(4.0)
f = 150 + 700 * (t / 4) ** 2.2
ph = 2 * np.pi * np.cumsum(f) / SR
r = np.sin(ph) * 0.3 + np.sin(ph * 1.5) * 0.12
nz = bp(rng.standard_normal(len(t)), 800, 6000) * (t / 4) ** 2
wav("riser", (r + nz * 0.8) * (t / 4) ** 1.5)

# 6. tecla de máquina de escribir y estampa
t = t_(0.07)
wav("tecla", hp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 120) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 90) * 0.5)
t = t_(1.0)
st = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 9) + lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 30) + hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 80) * 0.3
wav("estampa", reverb(st, 0.6, 0.2))

# 7. ping de sonar y pitido de disparo
t = t_(2.2)
png = np.sin(2 * np.pi * 1450 * t) * np.exp(-t * 3.2)
wav("ping", reverb(png, 1.2, 0.4))
t = t_(0.17)
wav("pitido", np.sin(2 * np.pi * 1000 * t) * np.minimum(1, t * 400) * np.minimum(1, (0.17 - t) * 400), 0.8)

# 8. redoble de tambor (acelera) y golpe de caja
def snare_hit(d=0.35):
    t = t_(d)
    return (bp(rng.standard_normal(len(t)), 900, 7000) * np.exp(-t * 28) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 35) * 0.6)


dur = 3.2
out = np.zeros(int(SR * (dur + 0.5)))
tt = 0.0
gap = 0.16
while tt < dur:
    h = snare_hit(0.22) * (0.35 + 0.65 * tt / dur)
    i = int(tt * SR)
    out[i : i + len(h)] += h
    tt += gap
    gap = max(0.028, gap * 0.9)
wav("redoble", reverb(out, 1.0, 0.25))
wav("caja", reverb(snare_hit(0.5), 0.9, 0.3))

# 9. ráfaga de glitch/estática corta (transición de radio)
t = t_(0.35)
g = bp(rng.standard_normal(len(t)), 400, 6000) * (rng.random(len(t)) > 0.15) * np.exp(-t * 6)
wav("glitch", g)

# 10. latido grave (tensión)
t = t_(1.6)
lat = np.zeros(len(t))
for d0 in (0.0, 0.28, 0.9, 1.18):
    m = t >= d0
    lat[m] += np.sin(2 * np.pi * 52 * (t[m] - d0)) * np.exp(-(t[m] - d0) * 11)
wav("latido", lat)

print("OK", OUT, sorted(os.listdir(OUT)))
