/** Flota: validación, colocación, aleatoria y adjudicación de disparos. Funciones puras. */
import { FLEET_SPEC, N, key, inBoard, type Coord, type Orient, type PlacedShip, type ShotResult } from './types'

export type Rng = () => number

/** PRNG determinista (mulberry32) para pruebas y semillas. */
export function seededRng(seed: number): Rng {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function shipCells(s: Pick<PlacedShip, 'x' | 'y' | 'len' | 'orient'>): Coord[] {
  const out: Coord[] = []
  for (let i = 0; i < s.len; i++) out.push(s.orient === 'H' ? { x: s.x + i, y: s.y } : { x: s.x, y: s.y + i })
  return out
}

export const shipFits = (s: PlacedShip): boolean => shipCells(s).every(inBoard)

export interface FleetIssue { code: 'count' | 'missing' | 'extra' | 'bounds' | 'overlap' | 'touching'; shipId?: string; message: string }
export interface FleetValidation { ok: boolean; issues: FleetIssue[] }

export function validateFleet(ships: PlacedShip[], opts: { allowTouching?: boolean } = {}): FleetValidation {
  const allowTouching = opts.allowTouching ?? true
  const issues: FleetIssue[] = []
  const remaining = [...FLEET_SPEC]
  for (const s of ships) {
    const i = remaining.findIndex(r => r.id === s.id && r.kind === s.kind && r.len === s.len)
    if (i < 0) issues.push({ code: 'extra', shipId: s.id, message: `Barco ${s.id} (${s.kind} de ${s.len}) no corresponde a la flota o está repetido.` })
    else remaining.splice(i, 1)
  }
  for (const r of remaining) issues.push({ code: 'missing', shipId: r.id, message: `Falta ${r.id} (${r.kind} de ${r.len}).` })
  if (ships.length !== FLEET_SPEC.length) issues.push({ code: 'count', message: `La flota debe tener ${FLEET_SPEC.length} barcos (hay ${ships.length}).` })
  const owner = new Map<string, string>()
  for (const s of ships) {
    if (!shipFits(s)) issues.push({ code: 'bounds', shipId: s.id, message: `${s.id} se sale del tablero 20×20.` })
    for (const c of shipCells(s)) {
      if (!inBoard(c)) continue
      const o = owner.get(key(c))
      if (o !== undefined && o !== s.id) issues.push({ code: 'overlap', shipId: s.id, message: `${s.id} se solapa con ${o} en (${c.x},${c.y}).` })
      else owner.set(key(c), s.id)
    }
  }
  if (!allowTouching) {
    for (const s of ships) for (const c of shipCells(s)) for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const o = owner.get(key({ x: c.x + dx, y: c.y + dy }))
      if (o !== undefined && o !== s.id && s.id < o) issues.push({ code: 'touching', shipId: s.id, message: `${s.id} toca a ${o}.` })
    }
  }
  return { ok: issues.length === 0, issues }
}

// ---- helpers puros de edición ----
export const placeShip = (ships: PlacedShip[], ship: PlacedShip): PlacedShip[] => [...ships.filter(s => s.id !== ship.id), ship]
export const removeShip = (ships: PlacedShip[], id: string): PlacedShip[] => ships.filter(s => s.id !== id)
export const moveShip = (s: PlacedShip, x: number, y: number): PlacedShip => ({ ...s, x, y })
/** Desplaza el ancla hacia dentro si el barco se saldría del tablero. */
export const ensureInside = (s: PlacedShip): PlacedShip => ({
  ...s,
  x: Math.max(1, Math.min(s.x, N - (s.orient === 'H' ? s.len - 1 : 0))),
  y: Math.max(1, Math.min(s.y, N - (s.orient === 'V' ? s.len - 1 : 0))),
})
/** Rota H<->V manteniendo la casilla ancla (ajustada para que quepa). */
export const rotateShip = (s: PlacedShip): PlacedShip => ensureInside({ ...s, orient: s.orient === 'H' ? 'V' : 'H' })

/** Flota aleatoria siempre válida (sin solapes; adyacencia permitida salvo allowTouching=false). */
export function randomFleet(rng: Rng = Math.random, opts: { allowTouching?: boolean } = {}): PlacedShip[] {
  const allowTouching = opts.allowTouching ?? true
  for (let attempt = 0; attempt < 1000; attempt++) {
    const placed: PlacedShip[] = []
    const used = new Set<string>()
    let ok = true
    for (const spec of [...FLEET_SPEC].sort((a, b) => b.len - a.len)) {
      let done = false
      for (let t = 0; t < 200 && !done; t++) {
        const orient: Orient = rng() < 0.5 ? 'H' : 'V'
        const x = 1 + Math.floor(rng() * (orient === 'H' ? N - spec.len + 1 : N))
        const y = 1 + Math.floor(rng() * (orient === 'V' ? N - spec.len + 1 : N))
        const ship: PlacedShip = { ...spec, x, y, orient }
        const cells = shipCells(ship)
        const blocked = cells.some(c => {
          if (used.has(key(c))) return true
          if (allowTouching) return false
          for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if (used.has(key({ x: c.x + dx, y: c.y + dy }))) return true
          return false
        })
        if (blocked) continue
        cells.forEach(c => used.add(key(c)))
        placed.push(ship)
        done = true
      }
      if (!done) { ok = false; break }
    }
    if (ok) return FLEET_SPEC.map(sp => placed.find(p => p.id === sp.id)!)
  }
  throw new Error('randomFleet: no se pudo colocar la flota')
}

const NAMES: Record<string, string> = { embarcacion: 'Embarcación', submarino: 'Submarino' }
/** Texto para colocar las piezas físicas: "Submarino 1: (5,7) → (5,10), vertical". */
export function fleetCoordinatesList(ships: PlacedShip[]): string {
  const order = (id: string) => FLEET_SPEC.findIndex(s => s.id === id)
  return [...ships].sort((a, b) => order(a.id) - order(b.id)).map(s => {
    const cells = shipCells(s)
    const a = cells[0]!, b = cells[cells.length - 1]!
    const n = s.id.replace(/\D/g, '')
    return `${NAMES[s.kind] ?? s.kind} ${n}: (${a.x},${a.y}) → (${b.x},${b.y}), ${s.orient === 'H' ? 'horizontal' : 'vertical'}`
  }).join('\n')
}

/** Barco que ocupa la casilla, si lo hay. */
export const shipAt = (ships: PlacedShip[], c: Coord): PlacedShip | undefined =>
  ships.find(s => shipCells(s).some(k => k.x === c.x && k.y === c.y))

/** Adjudica un disparo. 'sunk' si con él caen todas las casillas del barco; `already` = disparos previos
 *  (sin él, un barco de 2+ casillas nunca resulta 'sunk'). */
export function resolveShot(ships: PlacedShip[], c: Coord, already: Coord[] = []): ShotResult {
  const ship = shipAt(ships, c)
  if (!ship) return 'miss'
  const hits = new Set(already.map(key))
  hits.add(key(c))
  return shipCells(ship).every(k => hits.has(key(k))) ? 'sunk' : 'hit'
}
