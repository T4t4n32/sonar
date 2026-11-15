"""Geometria de un modulo (tablero plano de 30x30 con matriz de 20x20 elevada 50 mm + mastil trasero).
Marco: origen = esquina posterior izquierda de la matriz, x -> derecha, y -> hacia el frente (se aleja de la estacion),
z = altura sobre el plano de la matriz. La estacion (eje de pan) esta en (XS, YS) con el eje de tilt a H sobre el plano.
Unidades: mm y grados. Ejecutar: python -I geometria-planos.py
"""
import math

CELDA = 10.0
N = 20
XS, YS = 100.0, -65.0   # eje de pan: centro del ancho de la matriz y 65 mm detras de su borde posterior


def centro(i):  # indice 1..20 -> mm
    return (i - 0.5) * CELDA


def angulos(cx, cy, h):
    dx, dy = centro(cx) - XS, centro(cy) - YS
    r = math.hypot(dx, dy)
    pan = math.degrees(math.atan2(dx, dy))        # 0 = hacia el frente; + = derecha
    tilt = math.degrees(math.atan2(h, r))         # grados bajo la horizontal
    d3 = math.hypot(r, h)
    return pan, tilt, r, d3


def resumen(h):
    peor = min(angulos(cx, cy, h)[1] for cx in range(1, N + 1) for cy in range(1, N + 1))
    mejor = max(angulos(cx, cy, h)[1] for cx in range(1, N + 1) for cy in range(1, N + 1))
    pans = [angulos(cx, cy, h)[0] for cx in range(1, N + 1) for cy in range(1, N + 1)]
    return peor, mejor, min(pans), max(pans)


print("== Altura del eje de tilt sobre el plano de la matriz ==")
print(f"{'h (mm)':>7} {'tilt min':>9} {'tilt max':>9} {'pan min':>8} {'pan max':>8} {'punto x':>8} (alargamiento 1/sin(tilt min), laser de 3 mm)")
for h in (120, 150, 180, 200, 220):
    t0, t1, p0, p1 = resumen(h)
    print(f"{h:>7} {t0:>8.1f}° {t1:>8.1f}° {p0:>7.1f}° {p1:>7.1f}° {1 / math.sin(math.radians(t0)):>7.2f}  -> punto de {3 / math.sin(math.radians(t0)):.1f} mm")

H = 180.0
print(f"\n== Angulos de servo con h = {H:.0f} mm, eje de pan en (x={XS:.0f}, y={YS:.0f}) ==")
print(f"{'celda (x,y)':>12} {'pan':>8} {'tilt':>7} {'dist. 3D':>9} {'1 cm =':>8}")
pruebas = [(1, 1), (20, 1), (20, 20), (1, 20), (10, 10), (11, 11), (10, 1), (10, 20), (1, 10), (20, 10)]
for cx, cy in pruebas:
    pan, tilt, r, d3 = angulos(cx, cy, H)
    ang_cm = math.degrees(math.atan2(CELDA, d3))
    print(f"{f'({cx},{cy})':>12} {pan:>+7.1f}° {tilt:>6.1f}° {d3:>8.0f} {ang_cm:>7.2f}°")

print("\n== Resolucion necesaria (celda mas lejana (1,20) / (20,20)) ==")
pan, tilt, r, d3 = angulos(20, 20, H)
print(f"distancia 3D {d3:.0f} mm; 1 cm = {math.degrees(math.atan2(10, d3)):.2f}°; tolerancia +-5 mm = +-{math.degrees(math.atan2(5, d3)):.2f}°")
print(f"banda muerta MG996R 5 us -> 0,45° (500-2500 us) a 0,9° (1000-2000 us)")

print("\n== Limites de software sugeridos ==")
t0, t1, p0, p1 = resumen(H)
print(f"pan  {p0 - 3:+.0f}° a {p1 + 3:+.0f}° (matriz {p0:+.1f}° a {p1:+.1f}° + 3° de holgura)")
print(f"tilt {t0 - 3:.0f}° a {t1 + 3:.0f}° bajo la horizontal (matriz {t0:.1f}° a {t1:.1f}°); nunca menos de {t0 - 3:.0f}°: el rayo no puede salir del tablero hacia arriba")
