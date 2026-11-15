"""Duracion de una partida: IA 'caza y destruccion' (paridad + objetivo) contra flotas sin contacto."""
import random, statistics, sys

STD = [5, 4, 3, 3, 2]


def place(n, fleet, rng):
    occ = {}  # celda -> indice de barco
    ships = []
    for k, ln in enumerate(sorted(fleet, reverse=True)):
        for _ in range(10000):
            horiz = rng.random() < 0.5
            i = rng.randrange(n - (0 if horiz else ln - 1))
            j = rng.randrange(n - (ln - 1 if horiz else 0))
            cells = [(i, j + t) if horiz else (i + t, j) for t in range(ln)]
            ok = True
            for (a, b) in cells:
                for da in (-1, 0, 1):
                    for db in (-1, 0, 1):
                        if (a + da, b + db) in occ:
                            ok = False
            if ok:
                for c in cells:
                    occ[c] = k
                ships.append(cells)
                break
        else:
            raise RuntimeError("no cabe")
    return occ, ships


def play(n, fleet, rng):
    occ, ships = place(n, fleet, rng)
    left = [len(s) for s in ships]
    shot, hits_open = set(), []
    shots = 0
    sunk = 0
    nb = lambda c: [(c[0] + a, c[1] + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= c[0] + a < n and 0 <= c[1] + b < n]
    while sunk < len(ships):
        cand = []
        if hits_open:
            if len(hits_open) >= 2:  # extender la linea
                for c in hits_open:
                    for d in hits_open:
                        if c < d and (c[0] == d[0] or c[1] == d[1]):
                            di, dj = d[0] - c[0], d[1] - c[1]
                            step = (0 if di == 0 else di // abs(di), 0 if dj == 0 else dj // abs(dj))
                            for e in ((c[0] - step[0], c[1] - step[1]), (d[0] + step[0], d[1] + step[1])):
                                if 0 <= e[0] < n and 0 <= e[1] < n and e not in shot:
                                    cand.append(e)
            if not cand:
                cand = [x for c in hits_open for x in nb(c) if x not in shot]
        if not cand:
            free = [(i, j) for i in range(n) for j in range(n) if (i, j) not in shot]
            par = [c for c in free if (c[0] + c[1]) % 2 == 0]
            cand = par or free
        t = rng.choice(cand)
        shot.add(t)
        shots += 1
        if t in occ:
            k = occ[t]
            left[k] -= 1
            hits_open.append(t)
            if left[k] == 0:
                sunk += 1
                for c in ships[k]:
                    if c in hits_open:
                        hits_open.remove(c)
    return shots


rng = random.Random(7)
for n, fleet, label in ((10, STD, "10x10 flota 5-4-3-3-2 (17 celdas)"), (20, STD * 2, "20x20 flota 2x(5-4-3-3-2) (34 celdas)"), (20, STD, "20x20 flota 5-4-3-3-2 (17 celdas)")):
    r = [play(n, fleet, rng) for _ in range(300)]
    r.sort()
    print(f"{label:<40} media={statistics.mean(r):6.1f}  mediana={r[150]:4d}  p95={r[285]:4d}  max={r[-1]:4d}  (azar puro ~{round(sum(fleet)/(sum(fleet)+1)*(n*n+1))})")
