/**
 * Barcos UBICADOS por el estudiante (la flota real de Sebas, descubierta durante la partida).
 * Cuando un disparo acierta, el estudiante traza en pantalla las casillas del barco; este módulo valida
 * el trazo, guarda el barco y lleva la cuenta de impactos / hundidos. Funciones puras e inmutables.
 */
import { cellMap, remainingShips, setVerdict, type GameState } from './board'
import { FLEET_SPEC, inBoard, key, N, type Coord, type Orient, type ShipKind } from './types'

export interface KnownShip { id: string; kind: ShipKind; len: number; orient: Orient; cells: Coord[] }

export const KIND_NAME: Record<ShipKind, string> = { embarcacion: 'Embarcación', submarino: 'Submarino' }
const kindOf = (len: number): ShipKind | null => (len === 2 ? 'embarcacion' : len === 4 ? 'submarino' : null)
const cap = (len: number) => FLEET_SPEC.filter(f => f.len === len).length

export const knownShipAt = (known: readonly KnownShip[], c: Coord): KnownShip | undefined =>
  known.find(s => s.cells.some(k => k.x === c.x && k.y === c.y))

/** Cuántos barcos de cada largo faltan por ubicar (cupo 3×2 y 2×4 menos los ya ubicados). */
export function toLocate(known: readonly KnownShip[]): { len2: number; len4: number } {
  return { len2: cap(2) - known.filter(s => s.len === 2).length, len4: cap(4) - known.filter(s => s.len === 4).length }
}

export interface LocationCheck {
  ok: boolean
  errors: string[]
  len: number
  kind: ShipKind | null
  orient: Orient | null
  /** etiqueta viva: «Submarino · 4 casillas», «Embarcación · 2 casillas», «3 casillas» … */
  label: string
}

const sortCells = (cells: readonly Coord[]): Coord[] => [...cells].map(c => ({ x: c.x, y: c.y })).sort((a, b) => a.x - b.x || a.y - b.y)

/** Valida el trazo `cells` como barco que contiene `hitCell`. Errores en español. */
export function validateLocation(state: GameState, known: readonly KnownShip[], hitCell: Coord, cells: readonly Coord[]): LocationCheck {
  const errors: string[] = []
  const cs = sortCells(cells)
  const len = cs.length
  if (len === 0) return { ok: false, errors: ['Arrastra el dedo sobre las casillas del barco.'], len: 0, kind: null, orient: null, label: 'Sin trazo' }

  let orient: Orient | null = null
  if (cs.some(c => !inBoard(c) || !Number.isInteger(c.x) || !Number.isInteger(c.y))) errors.push('Hay casillas fuera del tablero.')
  const sameY = cs.every(c => c.y === cs[0]!.y)
  const sameX = cs.every(c => c.x === cs[0]!.x)
  if (len > 1) {
    if (sameY && !sameX) orient = 'H'
    else if (sameX && !sameY) orient = 'V'
    else errors.push(sameX && sameY ? 'Hay casillas repetidas.' : 'El barco debe ser una línea recta, horizontal o vertical.')
  }
  if (orient) {
    const along = orient === 'H' ? 'x' : 'y'
    if (!cs.every((c, i) => i === 0 || c[along] === cs[i - 1]![along] + 1)) errors.push('Las casillas deben ser contiguas, sin huecos.')
  }
  const kind = kindOf(len)
  if (!kind) errors.push(len === 1 ? 'Un barco ocupa 2 o 4 casillas.' : `Con ${len} casillas no es un barco: miden 2 o 4.`)
  if (!cs.some(c => c.x === hitCell.x && c.y === hitCell.y)) errors.push(`Debe incluir la casilla del impacto (${hitCell.x},${hitCell.y}).`)
  const taken = new Set(known.flatMap(s => s.cells.map(key)))
  if (cs.some(c => taken.has(key(c)))) errors.push('Se cruza con un barco que ya ubicaste.')
  const map = cellMap(state)
  const wet = cs.find(c => map.get(key(c)) === 'miss')
  if (wet) errors.push(`Pasa por (${wet.x},${wet.y}), donde fue agua.`)
  if (kind) {
    const left = toLocate(known)
    if (kind === 'embarcacion' && left.len2 <= 0) errors.push(`Ya ubicaste las ${cap(2)} embarcaciones.`)
    if (kind === 'submarino' && left.len4 <= 0) errors.push(`Ya ubicaste los ${cap(4)} submarinos.`)
  }
  const label = kind ? `${KIND_NAME[kind]} · ${len} casillas` : len === 1 ? '1 casilla' : `${len} casillas`
  return { ok: errors.length === 0, errors, len, kind, orient, label }
}

export type LocateResult = { ok: true; known: KnownShip[]; ship: KnownShip } | { ok: false; errors: string[] }

/** Registra el barco ubicado (si el trazo es válido). El id es el primero libre de su clase (E1.., S1..). */
export function locateShip(state: GameState, known: readonly KnownShip[], hitCell: Coord, cells: readonly Coord[]): LocateResult {
  const v = validateLocation(state, known, hitCell, cells)
  if (!v.ok || !v.kind || !v.orient) return { ok: false, errors: v.errors }
  const id = FLEET_SPEC.find(f => f.kind === v.kind && !known.some(k => k.id === f.id))!.id
  const ship: KnownShip = { id, kind: v.kind, len: v.len, orient: v.orient, cells: sortCells(cells) }
  return { ok: true, known: [...known, ship], ship }
}

export interface ShipProgress { ship: KnownShip; hits: Coord[]; sunk: boolean }

/** Qué casillas de cada barco ubicado ya recibieron impacto; hundido cuando caen todas. */
export function shipsProgress(state: GameState, known: readonly KnownShip[]): ShipProgress[] {
  const map = cellMap(state)
  return known.map(ship => {
    const hits = ship.cells.filter(c => { const s = map.get(key(c)); return s === 'hit' || s === 'sunk' })
    return { ship, hits, sunk: hits.length === ship.len }
  })
}

/** Casillas del barco aún sin disparar (para el asistente y el radar). */
export function unshotKnownCells(state: GameState, known: readonly KnownShip[]): Coord[] {
  const shot = new Set(state.shots.map(s => key(s.at)))
  return known.flatMap(s => s.cells.filter(c => !shot.has(key(c))))
}

const sameSet = (a: readonly Coord[], b: readonly Coord[]) => a.length === b.length && a.every(c => b.some(d => d.x === c.x && d.y === c.y))
const isMarkedSunk = (state: GameState, ship: KnownShip) => state.shots.some(s => s.result === 'sunk' && s.sunkCells && sameSet(s.sunkCells, ship.cells))

/** Aciertos sin barco ubicado todavía (pendientes de «ubicar»). */
export function pendingLocate(state: GameState, known: readonly KnownShip[]): Coord[] {
  return state.shots.filter(s => s.result === 'hit' && !knownShipAt(known, s.at)).map(s => s.at)
}

/** Marca en el tablero (board.setVerdict 'sunk') el barco `ship` usando el disparo `shotN` como el que lo hunde. */
export function applySunk(state: GameState, shotN: number, ship: KnownShip, now: number = Date.now()): GameState {
  const before = state.shots.find(s => s.n === shotN)
  let s = setVerdict(state, shotN, 'sunk', ship.len, now)
  s = {
    ...s,
    shots: s.shots.map(x => {
      if (x.n !== shotN) return x
      const next = { ...x, sunkCells: ship.cells.map(c => ({ ...c })) }
      if (before?.decidedMs !== undefined) next.decidedMs = before.decidedMs
      return next
    }),
  }
  return s
}

/** Convierte en 'sunk' todo barco ubicado cuyas casillas ya recibieron todas impacto. Devuelve los recién hundidos. */
export function reconcileSunk(state: GameState, known: readonly KnownShip[], now: number = Date.now()): { state: GameState; sunk: KnownShip[] } {
  let s = state
  const sunk: KnownShip[] = []
  for (const p of shipsProgress(state, known)) {
    if (!p.sunk || isMarkedSunk(s, p.ship)) continue
    const last = Math.max(...p.ship.cells.map(c => s.shots.find(x => x.at.x === c.x && x.at.y === c.y)?.n ?? 0))
    if (last <= 0) continue
    s = applySunk(s, last, p.ship, now)
    sunk.push(p.ship)
  }
  return { state: s, sunk }
}

/** Flota que aún queda a flote según los hundidos: p. ej. { embarcaciones: 3, submarinos: 2 }. */
export function fleetLeft(state: GameState): { embarcaciones: number; submarinos: number } {
  const rem = remainingShips(state)
  return { embarcaciones: rem.filter(l => l === 2).length, submarinos: rem.filter(l => l === 4).length }
}

export const isKnownShip = (o: unknown): o is KnownShip => {
  const s = o as KnownShip
  return !!s && typeof s.id === 'string' && (s.len === 2 || s.len === 4) && Array.isArray(s.cells) && s.cells.length === s.len
    && s.cells.every(c => c && Number.isInteger(c.x) && Number.isInteger(c.y) && c.x >= 1 && c.x <= N && c.y >= 1 && c.y <= N)
    && (s.orient === 'H' || s.orient === 'V') && FLEET_SPEC.some(f => f.id === s.id)
}
