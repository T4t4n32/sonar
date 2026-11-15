/** Seguimiento del tablero RIVAL a partir de los veredictos del testigo. Estado inmutable, funciones puras. */
import { FLEET_CELLS, FLEET_SPEC, inBoard, key, type Coord, type Orient, type Shot, type ShotResult } from './types'

export interface GameState { readonly startedAt: number; readonly shots: readonly Shot[] }
export type CellState = 'hit' | 'miss' | 'sunk' | 'pending'

export const newGame = (now: number = Date.now()): GameState => ({ startedAt: now, shots: [] })

export const hasShot = (s: GameState, c: Coord): boolean => s.shots.some(x => x.at.x === c.x && x.at.y === c.y)

/** Registra un disparo (pendiente de veredicto). Fuera del tablero o repetido -> devuelve el mismo estado. */
export function addShot(s: GameState, at: Coord, now: number = Date.now()): GameState {
  if (!inBoard(at) || !Number.isInteger(at.x) || !Number.isInteger(at.y) || hasShot(s, at)) return s
  return { ...s, shots: [...s.shots, { n: s.shots.length + 1, at: { x: at.x, y: at.y }, firedAt: now }] }
}

const isHit = (sh: Shot) => sh.result === 'hit' || sh.result === 'sunk'

/** Mapa casilla -> estado (hit/miss/sunk/pending). Las casillas de barcos hundidos se marcan 'sunk'. */
export function cellMap(s: GameState): Map<string, CellState> {
  const m = new Map<string, CellState>()
  for (const sh of s.shots) m.set(key(sh.at), sh.result === undefined ? 'pending' : sh.result === 'miss' ? 'miss' : 'hit')
  for (const sh of s.shots) if (sh.result === 'sunk') for (const c of sh.sunkCells ?? [sh.at]) m.set(key(c), 'sunk')
  return m
}

/** Casillas de aciertos que aún no pertenecen a un barco hundido. */
export function unexplainedHits(s: GameState): Coord[] {
  const m = cellMap(s)
  return s.shots.filter(sh => isHit(sh) && m.get(key(sh.at)) === 'hit').map(sh => sh.at)
}

/** Largos de barcos aún a flote, según los hundidos declarados (orden descendente). */
export function remainingShips(s: GameState): number[] {
  const rem = FLEET_SPEC.map(f => f.len)
  for (const sh of s.shots) {
    if (sh.result !== 'sunk' || sh.sunkLen === undefined) continue
    const i = rem.indexOf(sh.sunkLen)
    if (i >= 0) rem.splice(i, 1)
  }
  return rem.sort((a, b) => b - a)
}

/** Tramo contiguo recto (largo `len`) que contiene `at`, formado solo por aciertos sin hundir. */
function findRun(hits: Set<string>, at: Coord, len: number): { cells: Coord[]; orient: Orient } | null {
  for (const orient of ['H', 'V'] as Orient[]) {
    for (let off = 0; off < len; off++) {
      const cells: Coord[] = []
      for (let i = 0; i < len; i++) cells.push(orient === 'H' ? { x: at.x - off + i, y: at.y } : { x: at.x, y: at.y - off + i })
      if (cells.every(c => hits.has(key(c)))) return { cells, orient }
    }
  }
  return null
}

function runLenThrough(hits: Set<string>, at: Coord): number {
  let best = 1
  for (const [dx, dy] of [[1, 0], [0, 1]] as const) {
    let n = 1
    for (let k = 1; hits.has(key({ x: at.x + dx * k, y: at.y + dy * k })); k++) n++
    for (let k = 1; hits.has(key({ x: at.x - dx * k, y: at.y - dy * k })); k++) n++
    best = Math.max(best, n)
  }
  return best
}

/**
 * Fija el veredicto del disparo n. 'sunk' implica acierto; si no se da sunkLen se deduce del tramo de
 * aciertos que lo contiene (el mayor largo restante que quepa).
 */
export function setVerdict(s: GameState, shotN: number, result: ShotResult, sunkLen?: number, now: number = Date.now()): GameState {
  const idx = s.shots.findIndex(x => x.n === shotN)
  if (idx < 0) return s
  const cur = s.shots[idx]!
  const next: Shot = { ...cur, result, decidedMs: Math.max(0, now - cur.firedAt) }
  delete next.sunkLen
  delete next.sunkCells
  if (result === 'sunk') {
    const prior = { ...s, shots: s.shots.map((x, i) => (i === idx ? { ...next, result: 'hit' as const } : x)) }
    const hitSet = new Set(unexplainedHits(prior).map(key))
    let len = sunkLen
    if (len === undefined) {
      const run = runLenThrough(hitSet, cur.at)
      const rem = remainingShips(prior)
      len = rem.find(l => l <= run) ?? rem[rem.length - 1] ?? run
    }
    next.sunkLen = len
    const run = findRun(hitSet, cur.at, len)
    next.sunkCells = run ? run.cells : [cur.at]
  }
  return { ...s, shots: s.shots.map((x, i) => (i === idx ? next : x)) }
}

export interface Stats {
  shots: number; decided: number; hits: number; misses: number; sunk: number
  /** % de aciertos sobre disparos con veredicto (1 decimal) */
  precision: number
  streak: number; maxStreak: number
  avgDecisionMs: number
}

export function stats(s: GameState): Stats {
  const decided = s.shots.filter(x => x.result !== undefined)
  const hits = decided.filter(isHit).length
  let streak = 0, maxStreak = 0
  for (const sh of decided) {
    if (isHit(sh)) { streak++; maxStreak = Math.max(maxStreak, streak) } else streak = 0
  }
  const times = decided.map(x => x.decidedMs).filter((v): v is number => v !== undefined)
  return {
    shots: s.shots.length,
    decided: decided.length,
    hits,
    misses: decided.length - hits,
    sunk: decided.filter(x => x.result === 'sunk').length,
    precision: decided.length ? Math.round((hits / decided.length) * 1000) / 10 : 0,
    streak, maxStreak,
    avgDecisionMs: times.length ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : 0,
  }
}

export function isVictory(s: GameState): boolean {
  const hits = s.shots.filter(isHit).length
  return hits >= FLEET_CELLS || remainingShips(s).length === 0
}

export interface SunkSuggestion { len: number; cells: Coord[]; orient: Orient }

/**
 * Propone "HUNDIDO": tramos rectos de aciertos sin hundir cuyo largo iguala el de un barco restante y cuyos
 * extremos están acotados por borde, agua o casillas de barcos ya hundidos, sin aciertos vecinos de lado.
 */
export function suggestSunk(s: GameState): SunkSuggestion[] {
  const m = cellMap(s)
  const rem = remainingShips(s)
  const hits = new Set(unexplainedHits(s).map(key))
  const blocked = (c: Coord) => !inBoard(c) || m.get(key(c)) === 'miss' || m.get(key(c)) === 'sunk'
  const out: SunkSuggestion[] = []
  const seen = new Set<string>()
  for (const orient of ['H', 'V'] as Orient[]) {
    const [dx, dy] = orient === 'H' ? [1, 0] : [0, 1]
    for (const k of hits) {
      const [x, y] = k.split(',').map(Number) as [number, number]
      if (hits.has(key({ x: x - dx, y: y - dy }))) continue // no es el inicio del tramo
      const cells: Coord[] = []
      for (let c = { x, y }; hits.has(key(c)); c = { x: c.x + dx, y: c.y + dy }) cells.push(c)
      const len = cells.length
      if (len < 2 || !rem.includes(len)) continue
      const first = cells[0]!, last = cells[len - 1]!
      if (!blocked({ x: first.x - dx, y: first.y - dy }) || !blocked({ x: last.x + dx, y: last.y + dy })) continue
      // sin aciertos vecinos en el sentido perpendicular (serían de otro barco y hacen ambiguo el tramo)
      const side = cells.some(c => hits.has(key({ x: c.x + dy, y: c.y + dx })) || hits.has(key({ x: c.x - dy, y: c.y - dx })))
      if (side) continue
      const id = `${orient}:${cells.map(key).join('|')}`
      if (seen.has(id)) continue
      seen.add(id)
      out.push({ len, cells, orient })
    }
  }
  return out
}

// ---------- serialización ----------
export const toJSON = (s: GameState): string => JSON.stringify({ v: 1, startedAt: s.startedAt, shots: s.shots })

export function fromJSON(text: string): GameState {
  const o = JSON.parse(text) as { v?: number; startedAt?: unknown; shots?: unknown }
  if (!o || o.v !== 1 || typeof o.startedAt !== 'number' || !Array.isArray(o.shots)) throw new Error('Partida inválida')
  const shots = (o.shots as Shot[]).map(sh => {
    if (!sh || !sh.at || !inBoard(sh.at) || typeof sh.n !== 'number' || typeof sh.firedAt !== 'number') throw new Error('Disparo inválido')
    if (sh.result !== undefined && !['hit', 'miss', 'sunk'].includes(sh.result)) throw new Error('Resultado inválido')
    return sh
  })
  return { startedAt: o.startedAt, shots }
}

export function exportCsv(s: GameState): string {
  const rows = ['n,x,y,resultado,largo_hundido,disparo_ms,decision_ms']
  for (const sh of s.shots) {
    rows.push([sh.n, sh.at.x, sh.at.y, sh.result ?? 'pendiente', sh.sunkLen ?? '', sh.firedAt, sh.decidedMs ?? ''].join(','))
  }
  return rows.join('\n') + '\n'
}
