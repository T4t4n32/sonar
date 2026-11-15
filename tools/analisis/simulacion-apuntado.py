"""Error de calibracion por tramos (k x k puntos de control) vs. cinematica inversa exacta."""
import math

BOARD = 200.0


def ik(x, y, t):
    tx, ty, h = t
    dx, dy = x - tx, y - ty
    return math.atan2(dy, dx), math.atan2(h, math.hypot(dx, dy))


def fk(pan, tilt, t):
    tx, ty, h = t
    r = h / math.tan(tilt)
    return tx + r * math.cos(pan), ty + r * math.sin(pan)


def piecewise(n, k, t):
    d = BOARD / n
    c = lambda m: (m + 0.5) * d
    # indices de celda usados como puntos de control (equiespaciados, incluye esquinas)
    idx = [round(m * (n - 1) / (k - 1)) for m in range(k)]
    ctrl = {(a, b): ik(c(idx[b]), c(idx[a]), t) for a in range(k) for b in range(k)}
    errs = []
    for i in range(n):
        for j in range(n):
            # tramo que contiene (i, j)
            a = max(m for m in range(k - 1) if idx[m] <= i) if i < idx[-1] else k - 2
            b = max(m for m in range(k - 1) if idx[m] <= j) if j < idx[-1] else k - 2
            y = (i - idx[a]) / (idx[a + 1] - idx[a])
            x = (j - idx[b]) / (idx[b + 1] - idx[b])
            q00, q10, q01, q11 = ctrl[(a, b)], ctrl[(a, b + 1)], ctrl[(a + 1, b)], ctrl[(a + 1, b + 1)]
            f = [(1 - x) * (1 - y) * q00[m] + x * (1 - y) * q10[m] + (1 - x) * y * q01[m] + x * y * q11[m] for m in (0, 1)]
            px, py = fk(f[0], f[1], t)
            errs.append(math.hypot(px - c(j), py - c(i)))
    return max(errs), sum(errs) / len(errs), d


for label, t in [("a 25 mm del borde, h=150", (100, -25, 150)), ("a 100 mm del borde, h=150", (100, -100, 150))]:
    for n in (10, 20):
        row = []
        for k in (2, 3, 5):
            mx, mean, d = piecewise(n, k, t)
            row.append(f"k={k}: max {mx:5.1f} mm ({mx/d:4.2f} celdas)")
        print(f"{label:<28} N={n:<2} " + " | ".join(row))
print("IK analitica con (tx,ty,h) calibrados: error ~0 (limitado por holgura mecanica)")
