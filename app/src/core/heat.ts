/** Asistente de tiro: mapa de probabilidad por conteo de ubicaciones legales. Determinista. */
import { cellMap, remainingShips, unexplainedHits, type GameState } from './board'
import type { Rng } from './fleet'
import { N, idx, key, type Coord, type Heat } from './types'

/** Peso por acierto sin explicar que cubre una ubicación (x20 por cada uno: 2 aciertos alineados pesan 400). */
export const HIT_BOOST = 20

export function heatMap(s: GameState): Heat {
  const heat: Heat = new Array(N * N).fill(0)
  const m = cellMap(s)
  const unexplained = new Set(unexplainedHits(s).map(key))
  for (const len of remainingShips(s)) {
    for (const orient of ['H', 'V'] as const) {
      const maxX = orient === 'H' ? N - len + 1 : N
      const maxY = orient === 'V' ? N - len + 1 : N
      for (let y = 1; y <= maxY; y++) for (let x = 1; x <= maxX; x++) {
        const cells: Coord[] = []
        let legal = true
        let covered = 0
        for (let i = 0; i < len; i++) {
          const c = orient === 'H' ? { x: x + i, y } : { x, y: y + i }
          const st = m.get(key(c))
          if (st === 'miss' || st === 'sunk') { legal = false; break }
          if (unexplained.has(key(c))) covered++
          cells.push(c)
        }
        if (!legal) continue
        const w = HIT_BOOST ** covered
        for (const c of cells) heat[idx(c)]! += w
      }
    }
  }
  for (const sh of s.shots) heat[idx(sh.at)] = 0 // ya disparadas
  return heat
}

/** Mejor celda a disparar; empate -> primera (o la que elija `rng`). null si no queda ninguna. */
export function bestShot(s: GameState, rng?: Rng): Coord | null {
  const heat = heatMap(s)
  let max = 0
  for (const v of heat) if (v > max) max = v
  let pool: number[] = []
  if (max > 0) heat.forEach((v, i) => { if (v === max) pool.push(i) })
  else {
    // sin ubicaciones legales (estado inconsistente): cualquier casilla no disparada
    const shot = new Set(s.shots.map(x => key(x.at)))
    heat.forEach((_, i) => { if (!shot.has(key({ x: (i % N) + 1, y: Math.floor(i / N) + 1 }))) pool.push(i) })
  }
  if (!pool.length) return null
  const pick = pool[rng ? Math.min(pool.length - 1, Math.floor(rng() * pool.length)) : 0]!
  return { x: (pick % N) + 1, y: Math.floor(pick / N) + 1 }
}
