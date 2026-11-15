import { describe, expect, it } from 'vitest'
import { addShot, isVictory, newGame, remainingShips, setVerdict, type GameState } from './board'
import { applySunk, fleetLeft, knownShipAt, locateShip, pendingLocate, reconcileSunk, shipsProgress, toLocate, unshotKnownCells, validateLocation, type KnownShip } from './known'
import type { Coord } from './types'

const col = (x: number, y0: number, n: number): Coord[] => Array.from({ length: n }, (_, i) => ({ x, y: y0 + i }))
const row = (y: number, x0: number, n: number): Coord[] => Array.from({ length: n }, (_, i) => ({ x: x0 + i, y }))
const G0 = newGame(1000)
function shoot(g: GameState, c: Coord, r: 'hit' | 'miss'): GameState {
  const a = addShot(g, c, 1000)
  return setVerdict(a, a.shots.length, r, undefined, 1500)
}
function locate(g: GameState, known: KnownShip[], hit: Coord, cells: Coord[]) {
  const r = locateShip(g, known, hit, cells)
  if (!r.ok) throw new Error(r.errors.join(' | '))
  return r.known
}

describe('validateLocation', () => {
  it('ejemplo del profe: submarino (10,12)-(10,15) con impacto en (10,15)', () => {
    const v = validateLocation(G0, [], { x: 10, y: 15 }, col(10, 12, 4))
    expect(v).toMatchObject({ ok: true, len: 4, kind: 'submarino', orient: 'V', label: 'Submarino · 4 casillas' })
  })
  it('embarcación horizontal de 2', () => {
    const v = validateLocation(G0, [], { x: 3, y: 3 }, row(3, 3, 2))
    expect(v).toMatchObject({ ok: true, kind: 'embarcacion', orient: 'H', label: 'Embarcación · 2 casillas' })
  })
  it('rechaza: vacío, diagonal, hueco, largo 3, sin la casilla del impacto, fuera del tablero', () => {
    expect(validateLocation(G0, [], { x: 1, y: 1 }, []).ok).toBe(false)
    expect(validateLocation(G0, [], { x: 1, y: 1 }, [{ x: 1, y: 1 }, { x: 2, y: 2 }]).errors.join()).toContain('línea recta')
    expect(validateLocation(G0, [], { x: 1, y: 1 }, [{ x: 1, y: 1 }, { x: 1, y: 3 }]).errors.join()).toContain('contiguas')
    expect(validateLocation(G0, [], { x: 1, y: 1 }, col(1, 1, 3)).errors.join()).toContain('2 o 4')
    expect(validateLocation(G0, [], { x: 1, y: 1 }, [{ x: 1, y: 1 }]).errors.join()).toContain('2 o 4')
    expect(validateLocation(G0, [], { x: 5, y: 5 }, col(1, 1, 2)).errors.join()).toContain('casilla del impacto')
    expect(validateLocation(G0, [], { x: 20, y: 19 }, col(20, 19, 4)).errors.join()).toContain('fuera del tablero')
  })
  it('rechaza solapar un barco ya ubicado o pasar por agua', () => {
    const known = locate(G0, [], { x: 10, y: 15 }, col(10, 12, 4))
    expect(validateLocation(G0, known, { x: 9, y: 13 }, row(13, 9, 2)).errors.join()).toContain('ya ubicaste')
    const g = shoot(G0, { x: 5, y: 6 }, 'miss')
    expect(validateLocation(g, [], { x: 5, y: 5 }, col(5, 5, 2)).errors.join()).toContain('agua')
  })
  it('respeta el cupo: 3 embarcaciones y 2 submarinos', () => {
    let known: KnownShip[] = []
    for (let i = 0; i < 3; i++) known = locate(G0, known, { x: 1 + i * 3, y: 1 }, row(1, 1 + i * 3, 2))
    expect(toLocate(known)).toEqual({ len2: 0, len4: 2 })
    expect(validateLocation(G0, known, { x: 1, y: 5 }, row(5, 1, 2)).errors.join()).toContain('3 embarcaciones')
    known = locate(G0, known, { x: 1, y: 5 }, row(5, 1, 4))
    known = locate(G0, known, { x: 1, y: 7 }, row(7, 1, 4))
    expect(toLocate(known)).toEqual({ len2: 0, len4: 0 })
    expect(validateLocation(G0, known, { x: 1, y: 9 }, row(9, 1, 4)).errors.join()).toContain('2 submarinos')
  })
})

describe('locateShip / progreso / hundido', () => {
  it('asigna ids libres por clase y los encuentra con knownShipAt', () => {
    const k1 = locate(G0, [], { x: 1, y: 1 }, row(1, 1, 2))
    const k2 = locate(G0, k1, { x: 5, y: 5 }, row(5, 5, 2))
    expect(k2.map(s => s.id)).toEqual(['E1', 'E2'])
    expect(knownShipAt(k2, { x: 6, y: 5 })?.id).toBe('E2')
    expect(knownShipAt(k2, { x: 7, y: 5 })).toBeUndefined()
  })
  it('un submarino se hunde cuando caen sus 4 casillas; el resto de la flota baja', () => {
    // impacto 1 en (10,15), ubicado; luego (10,14), (10,13), (10,12) son impactos directos
    let g = shoot(G0, { x: 10, y: 15 }, 'hit')
    const known = locate(g, [], { x: 10, y: 15 }, col(10, 12, 4))
    expect(shipsProgress(g, known)[0]).toMatchObject({ sunk: false, hits: [{ x: 10, y: 15 }] })
    expect(unshotKnownCells(g, known)).toHaveLength(3)
    for (const y of [14, 13]) g = shoot(g, { x: 10, y }, 'hit')
    expect(reconcileSunk(g, known).sunk).toHaveLength(0)
    g = shoot(g, { x: 10, y: 12 }, 'hit')
    const r = reconcileSunk(g, known, 2000)
    expect(r.sunk.map(s => s.id)).toEqual(['S1'])
    expect(r.state.shots.filter(s => s.result === 'sunk')).toHaveLength(1)
    expect(r.state.shots[3]!.sunkCells).toHaveLength(4)
    expect(remainingShips(r.state)).toEqual([4, 2, 2, 2])
    expect(fleetLeft(r.state)).toEqual({ embarcaciones: 3, submarinos: 1 })
    expect(reconcileSunk(r.state, known).sunk).toHaveLength(0) // idempotente
    expect(shipsProgress(r.state, known)[0]!.sunk).toBe(true)
  })
  it('ubicar un barco cuyos impactos ya cayeron lo hunde al instante', () => {
    let g = shoot(G0, { x: 3, y: 3 }, 'hit')
    g = shoot(g, { x: 4, y: 3 }, 'hit')
    expect(pendingLocate(g, [])).toHaveLength(2)
    const known = locate(g, [], { x: 4, y: 3 }, row(3, 3, 2))
    expect(pendingLocate(g, known)).toHaveLength(0)
    const r = reconcileSunk(g, known)
    expect(r.sunk).toHaveLength(1)
    expect(r.state.shots[1]!.result).toBe('sunk')
  })
  it('applySunk conserva decidedMs y usa las casillas del barco ubicado', () => {
    const g = shoot(G0, { x: 3, y: 3 }, 'hit')
    const ship = locate(g, [], { x: 3, y: 3 }, row(3, 3, 2))[0]!
    const g2 = applySunk(g, 1, ship, 99999)
    expect(g2.shots[0]!.decidedMs).toBe(500)
    expect(g2.shots[0]!.sunkLen).toBe(2)
    expect(g2.shots[0]!.sunkCells).toEqual(ship.cells)
  })
  it('hundir los 5 barcos es victoria', () => {
    let g = G0
    let known: KnownShip[] = []
    const layout: Coord[][] = [row(1, 1, 2), row(3, 1, 2), row(5, 1, 2), row(7, 1, 4), row(9, 1, 4)]
    for (const cells of layout) {
      g = shoot(g, cells[0]!, 'hit')
      known = locate(g, known, cells[0]!, cells)
      for (const c of cells.slice(1)) g = shoot(g, c, 'hit')
      g = reconcileSunk(g, known).state
    }
    expect(fleetLeft(g)).toEqual({ embarcaciones: 0, submarinos: 0 })
    expect(isVictory(g)).toBe(true)
  })
})
