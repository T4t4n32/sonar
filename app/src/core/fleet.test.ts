import { describe, expect, it } from 'vitest'
import { fleetCoordinatesList, moveShip, placeShip, randomFleet, resolveShot, rotateShip, seededRng, shipCells, validateFleet } from './fleet'
import { FLEET_CELLS, FLEET_SPEC, key, type PlacedShip } from './types'

const base = (): PlacedShip[] => [
  { id: 'E1', kind: 'embarcacion', len: 2, x: 1, y: 1, orient: 'H' },
  { id: 'E2', kind: 'embarcacion', len: 2, x: 1, y: 3, orient: 'H' },
  { id: 'E3', kind: 'embarcacion', len: 2, x: 1, y: 5, orient: 'V' },
  { id: 'S1', kind: 'submarino', len: 4, x: 5, y: 7, orient: 'V' },
  { id: 'S2', kind: 'submarino', len: 4, x: 10, y: 10, orient: 'H' },
]
const withShip = (id: string, patch: Partial<PlacedShip>) => base().map(s => (s.id === id ? { ...s, ...patch } : s))

describe('shipCells', () => {
  it('horizontal crece en x, vertical en y', () => {
    expect(shipCells({ x: 3, y: 4, len: 3, orient: 'H' })).toEqual([{ x: 3, y: 4 }, { x: 4, y: 4 }, { x: 5, y: 4 }])
    expect(shipCells({ x: 3, y: 4, len: 2, orient: 'V' })).toEqual([{ x: 3, y: 4 }, { x: 3, y: 5 }])
  })
})

describe('validateFleet', () => {
  it('flota correcta es válida y suma 14 casillas', () => {
    expect(validateFleet(base())).toEqual({ ok: true, issues: [] })
    expect(base().flatMap(shipCells)).toHaveLength(FLEET_CELLS)
  })
  it('falta un barco', () => {
    const r = validateFleet(base().slice(0, 4))
    expect(r.ok).toBe(false)
    expect(r.issues.map(i => i.code)).toEqual(expect.arrayContaining(['missing', 'count']))
  })
  it('barco repetido / de más', () => {
    const r = validateFleet([...base(), { id: 'S3', kind: 'submarino', len: 4, x: 15, y: 15, orient: 'H' }])
    expect(r.issues.some(i => i.code === 'extra' && i.shipId === 'S3')).toBe(true)
  })
  it('largo incorrecto para su id', () => {
    const r = validateFleet(withShip('S1', { len: 3 }))
    expect(r.ok).toBe(false)
  })
  it('fuera del tablero por derecha y abajo', () => {
    expect(validateFleet(withShip('S2', { x: 18 })).issues.some(i => i.code === 'bounds' && i.shipId === 'S2')).toBe(true)
    expect(validateFleet(withShip('S1', { y: 18 })).issues.some(i => i.code === 'bounds')).toBe(true)
    expect(validateFleet(withShip('E1', { x: 0 })).ok).toBe(false)
  })
  it('borde exacto es válido (x=17 con len 4, y=19 con len 2)', () => {
    expect(validateFleet(withShip('S2', { x: 17, y: 10 })).ok).toBe(true)
    expect(validateFleet(withShip('E3', { x: 15, y: 19, orient: 'V' })).ok).toBe(true)
  })
  it('solape detectado', () => {
    const r = validateFleet(withShip('E2', { x: 1, y: 1 }))
    expect(r.issues.some(i => i.code === 'overlap')).toBe(true)
  })
  it('cruz H/V solapada en una casilla', () => {
    const r = validateFleet(withShip('E1', { x: 4, y: 8, orient: 'H' })) // cruza S1 (5,7..10) en (5,8)
    expect(r.issues.some(i => i.code === 'overlap')).toBe(true)
  })
  it('adyacencia permitida por defecto, rechazable por opción', () => {
    const adj = withShip('E2', { x: 1, y: 2 }) // pegada a E1 (fila 1)
    expect(validateFleet(adj).ok).toBe(true)
    const r = validateFleet(adj, { allowTouching: false })
    expect(r.ok).toBe(false)
    expect(r.issues.some(i => i.code === 'touching')).toBe(true)
  })
})

describe('helpers puros', () => {
  it('rotar H->V->H conserva el ancla y no muta', () => {
    const s = base()[3]!
    const r = rotateShip(s)
    expect(r.orient).toBe('H')
    expect(s.orient).toBe('V')
    expect(rotateShip(r)).toEqual(s)
  })
  it('rotar cerca del borde mete el barco en el tablero', () => {
    const s: PlacedShip = { id: 'S1', kind: 'submarino', len: 4, x: 19, y: 5, orient: 'V' }
    const r = rotateShip(s)
    expect(r.orient).toBe('H')
    expect(shipCells(r).every(c => c.x >= 1 && c.x <= 20)).toBe(true)
    expect(r.x).toBe(17)
  })
  it('moveShip y placeShip reemplazan por id', () => {
    const moved = moveShip(base()[0]!, 9, 9)
    expect(moved).toMatchObject({ x: 9, y: 9, id: 'E1' })
    const f = placeShip(base(), moved)
    expect(f).toHaveLength(5)
    expect(f.find(s => s.id === 'E1')).toMatchObject({ x: 9, y: 9 })
  })
})

describe('randomFleet', () => {
  it('siempre válida en 200 semillas y con la composición exacta', () => {
    for (let seed = 1; seed <= 200; seed++) {
      const f = randomFleet(seededRng(seed))
      expect(validateFleet(f).ok, `semilla ${seed}`).toBe(true)
      expect(f.map(s => s.id)).toEqual(FLEET_SPEC.map(s => s.id))
      expect(new Set(f.flatMap(shipCells).map(key)).size).toBe(FLEET_CELLS)
    }
  })
  it('es determinista con la misma semilla y varía con otra', () => {
    expect(randomFleet(seededRng(7))).toEqual(randomFleet(seededRng(7)))
    expect(randomFleet(seededRng(7))).not.toEqual(randomFleet(seededRng(8)))
  })
  it('allowTouching=false no deja barcos adyacentes', () => {
    for (let seed = 1; seed <= 30; seed++) expect(validateFleet(randomFleet(seededRng(seed), { allowTouching: false }), { allowTouching: false }).ok).toBe(true)
  })
  it('usa ambas orientaciones', () => {
    const o = new Set(Array.from({ length: 20 }, (_, i) => randomFleet(seededRng(i + 1)).map(s => s.orient)).flat())
    expect(o).toEqual(new Set(['H', 'V']))
  })
})

describe('fleetCoordinatesList', () => {
  it('formato legible con extremos y orientación', () => {
    const txt = fleetCoordinatesList(base())
    expect(txt).toContain('Submarino 1: (5,7) → (5,10), vertical')
    expect(txt).toContain('Submarino 2: (10,10) → (13,10), horizontal')
    expect(txt).toContain('Embarcación 1: (1,1) → (2,1), horizontal')
    expect(txt.split('\n')).toHaveLength(5)
  })
})

describe('resolveShot', () => {
  it('agua, acierto y hundido', () => {
    const f = base()
    expect(resolveShot(f, { x: 20, y: 20 })).toBe('miss')
    expect(resolveShot(f, { x: 1, y: 1 })).toBe('hit')
    expect(resolveShot(f, { x: 2, y: 1 }, [{ x: 1, y: 1 }])).toBe('sunk')
  })
  it('submarino de 4 solo se hunde con la última casilla', () => {
    const f = base()
    const prev = [{ x: 5, y: 7 }, { x: 5, y: 8 }, { x: 5, y: 9 }]
    expect(resolveShot(f, { x: 5, y: 10 }, prev)).toBe('sunk')
    expect(resolveShot(f, { x: 5, y: 10 }, prev.slice(0, 2))).toBe('hit')
  })
  it('disparos a otro barco no cuentan', () => {
    expect(resolveShot(base(), { x: 2, y: 1 }, [{ x: 1, y: 3 }, { x: 2, y: 3 }])).toBe('hit')
  })
})
