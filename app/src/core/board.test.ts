import { describe, expect, it } from 'vitest'
import { addShot, cellMap, exportCsv, fromJSON, isVictory, newGame, remainingShips, setVerdict, stats, suggestSunk, toJSON, type GameState } from './board'
import { key, type Coord, type ShotResult } from './types'

/** Aplica una serie de disparos con veredicto; reloj determinista (cada disparo +1000 ms, decisión +500 ms). */
function play(list: [number, number, ShotResult, number?][], start: GameState = newGame(0)): GameState {
  let s = start
  let t = 1000
  for (const [x, y, r, len] of list) {
    s = addShot(s, { x, y }, t)
    s = setVerdict(s, s.shots.length, r, len, t + 500)
    t += 1000
  }
  return s
}

describe('addShot', () => {
  it('numera consecutivamente y no muta', () => {
    const g0 = newGame(0)
    const g1 = addShot(g0, { x: 3, y: 4 }, 10)
    const g2 = addShot(g1, { x: 5, y: 6 }, 20)
    expect(g0.shots).toHaveLength(0)
    expect(g2.shots.map(s => s.n)).toEqual([1, 2])
    expect(g2.shots[1]).toMatchObject({ at: { x: 5, y: 6 }, firedAt: 20 })
    expect(g2.shots[1]!.result).toBeUndefined()
  })
  it('ignora repetidos y fuera de tablero', () => {
    const g = addShot(newGame(0), { x: 3, y: 4 })
    expect(addShot(g, { x: 3, y: 4 })).toBe(g)
    expect(addShot(g, { x: 0, y: 4 })).toBe(g)
    expect(addShot(g, { x: 21, y: 4 })).toBe(g)
  })
})

describe('setVerdict', () => {
  it('registra resultado y tiempo de decisión', () => {
    const s = play([[1, 1, 'miss']])
    expect(s.shots[0]).toMatchObject({ result: 'miss', decidedMs: 500 })
  })
  it('sunk implica acierto y marca las casillas del barco', () => {
    const s = play([[5, 5, 'hit'], [6, 5, 'sunk', 2]])
    const m = cellMap(s)
    expect(m.get('5,5')).toBe('sunk')
    expect(m.get('6,5')).toBe('sunk')
    expect(stats(s).hits).toBe(2)
  })
  it('sunk sin largo declarado lo deduce del tramo', () => {
    const s = play([[2, 2, 'hit'], [2, 3, 'hit'], [2, 4, 'hit'], [2, 5, 'sunk']])
    expect(s.shots[3]!.sunkLen).toBe(4)
    expect(remainingShips(s)).toEqual([4, 2, 2, 2])
  })
  it('número de disparo inexistente no cambia nada', () => {
    const s = play([[1, 1, 'miss']])
    expect(setVerdict(s, 99, 'hit')).toBe(s)
  })
  it('se puede corregir un veredicto', () => {
    let s = play([[1, 1, 'hit']])
    s = setVerdict(s, 1, 'miss', undefined, 5000)
    expect(s.shots[0]!.result).toBe('miss')
    expect(stats(s).hits).toBe(0)
  })
})

describe('remainingShips', () => {
  it('flota completa al inicio', () => expect(remainingShips(newGame(0))).toEqual([4, 4, 2, 2, 2]))
  it('descuenta los hundidos declarados', () => {
    const s = play([[1, 1, 'hit'], [2, 1, 'sunk', 2], [9, 9, 'hit'], [9, 10, 'hit'], [9, 11, 'hit'], [9, 12, 'sunk', 4]])
    expect(remainingShips(s)).toEqual([4, 2, 2])
  })
  it('no descuenta más de los que existen', () => {
    const s = play([[1, 1, 'hit'], [1, 2, 'sunk', 2], [5, 1, 'hit'], [5, 2, 'sunk', 2], [9, 1, 'hit'], [9, 2, 'sunk', 2], [12, 1, 'hit'], [12, 2, 'sunk', 2]])
    expect(remainingShips(s)).toEqual([4, 4])
  })
})

describe('stats', () => {
  it('estado vacío', () => {
    expect(stats(newGame(0))).toMatchObject({ shots: 0, hits: 0, precision: 0, streak: 0, maxStreak: 0, avgDecisionMs: 0 })
  })
  it('precisión, rachas y tiempo medio', () => {
    const s = play([[1, 1, 'hit'], [2, 1, 'hit'], [3, 1, 'miss'], [4, 1, 'hit'], [5, 1, 'miss'], [6, 1, 'hit'], [7, 1, 'hit']])
    expect(stats(s)).toMatchObject({ shots: 7, decided: 7, hits: 5, misses: 2, precision: 71.4, streak: 2, maxStreak: 2, avgDecisionMs: 500 })
  })
  it('racha máxima distinta de la actual', () => {
    const s = play([[1, 1, 'hit'], [2, 1, 'hit'], [3, 1, 'hit'], [4, 1, 'miss'], [5, 1, 'hit']])
    expect(stats(s)).toMatchObject({ streak: 1, maxStreak: 3 })
  })
  it('los pendientes no cuentan en precisión', () => {
    let s = play([[1, 1, 'hit']])
    s = addShot(s, { x: 2, y: 2 }, 9999)
    expect(stats(s)).toMatchObject({ shots: 2, decided: 1, precision: 100 })
  })
})

describe('isVictory', () => {
  const ships: [number, number, number][][] = [
    [[1, 1, 0], [2, 1, 0]],
    [[1, 3, 0], [2, 3, 0]],
    [[1, 5, 0], [2, 5, 0]],
  ]
  it('false con 13 aciertos, true con 14', () => {
    const list: [number, number, ShotResult][] = []
    for (let i = 0; i < 13; i++) list.push([(i % 10) + 1, Math.floor(i / 10) + 1, 'hit'])
    const s13 = play(list)
    expect(stats(s13).hits).toBe(13)
    expect(isVictory(s13)).toBe(false)
    expect(isVictory(play([...list, [14, 14, 'hit']]))).toBe(true)
  })
  it('true cuando se declararon hundidos los 5 barcos', () => {
    const list: [number, number, ShotResult, number?][] = []
    ships.forEach(([a, b], i) => { list.push([a![0]!, a![1]!, 'hit'], [b![0]!, b![1]!, 'sunk', 2]); void i })
    list.push([10, 1, 'hit'], [11, 1, 'hit'], [12, 1, 'hit'], [13, 1, 'sunk', 4])
    list.push([10, 10, 'hit'], [11, 10, 'hit'], [12, 10, 'hit'], [13, 10, 'sunk', 4])
    const s = play(list)
    expect(remainingShips(s)).toEqual([])
    expect(isVictory(s)).toBe(true)
  })
  it('false al inicio', () => expect(isVictory(newGame(0))).toBe(false))
})

describe('suggestSunk', () => {
  it('2 aciertos horizontales acotados por agua y borde -> embarcación', () => {
    const s = play([[1, 5, 'hit'], [2, 5, 'hit'], [3, 5, 'miss']])
    expect(suggestSunk(s)).toEqual([{ len: 2, orient: 'H', cells: [{ x: 1, y: 5 }, { x: 2, y: 5 }] }])
  })
  it('tramo vertical de 4 acotado por agua en ambos extremos', () => {
    const s = play([[7, 3, 'hit'], [7, 4, 'hit'], [7, 5, 'hit'], [7, 6, 'hit'], [7, 2, 'miss'], [7, 7, 'miss']])
    const r = suggestSunk(s)
    expect(r).toHaveLength(1)
    expect(r[0]).toMatchObject({ len: 4, orient: 'V' })
    expect(r[0]!.cells.map(key)).toEqual(['7,3', '7,4', '7,5', '7,6'])
  })
  it('extremo abierto (casilla sin disparar) no sugiere', () => {
    expect(suggestSunk(play([[5, 5, 'hit'], [6, 5, 'hit'], [4, 5, 'miss']]))).toEqual([])
  })
  it('largo que no existe entre los restantes no sugiere (3 aciertos)', () => {
    const s = play([[5, 5, 'hit'], [6, 5, 'hit'], [7, 5, 'hit'], [4, 5, 'miss'], [8, 5, 'miss']])
    expect(suggestSunk(s)).toEqual([])
  })
  it('un acierto solo no sugiere', () => {
    expect(suggestSunk(play([[5, 5, 'hit'], [4, 5, 'miss'], [6, 5, 'miss'], [5, 4, 'miss'], [5, 6, 'miss']]))).toEqual([])
  })
  it('tras declarar el hundido ya no se sugiere', () => {
    const s = play([[1, 5, 'hit'], [2, 5, 'sunk', 2], [3, 5, 'miss']])
    expect(suggestSunk(s)).toEqual([])
  })
  it('aciertos vecinos de lado vuelven ambiguo el tramo', () => {
    const s = play([[1, 5, 'hit'], [2, 5, 'hit'], [1, 6, 'hit'], [3, 5, 'miss'], [1, 4, 'miss'], [1, 7, 'miss']])
    expect(suggestSunk(s).some(x => x.orient === 'H' && x.len === 2)).toBe(false)
  })
})

describe('serialización', () => {
  const s = play([[1, 1, 'hit'], [2, 1, 'sunk', 2], [9, 9, 'miss']])
  it('toJSON/fromJSON es ida y vuelta exacta', () => expect(fromJSON(toJSON(s))).toEqual(s))
  it('fromJSON rechaza basura', () => {
    expect(() => fromJSON('{}')).toThrow()
    expect(() => fromJSON('no es json')).toThrow()
    expect(() => fromJSON(JSON.stringify({ v: 1, startedAt: 0, shots: [{ n: 1, at: { x: 99, y: 1 }, firedAt: 0 }] }))).toThrow()
  })
  it('exportCsv: cabecera y una fila por disparo', () => {
    const lines = exportCsv(s).trim().split('\n')
    expect(lines[0]).toBe('n,x,y,resultado,largo_hundido,disparo_ms,decision_ms')
    expect(lines).toHaveLength(4)
    expect(lines[2]).toBe('2,2,1,sunk,2,2000,500')
    expect(lines[3]).toBe('3,9,9,miss,,3000,500')
  })
  it('exportCsv marca pendientes', () => {
    const p = addShot(newGame(0), { x: 4, y: 4 }, 7)
    expect(exportCsv(p)).toContain('1,4,4,pendiente,,7,')
  })
})

describe('tipos auxiliares', () => {
  it('Coord se usa como texto estable', () => {
    const c: Coord = { x: 3, y: 4 }
    expect(key(c)).toBe('3,4')
  })
})
