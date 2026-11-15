import { describe, expect, it } from 'vitest'
import { addShot, newGame, setVerdict, type GameState } from './board'
import { seededRng } from './fleet'
import { bestShot, heatMap } from './heat'
import { N, idx, type ShotResult } from './types'

function play(list: [number, number, ShotResult, number?][]): GameState {
  let s = newGame(0)
  for (const [x, y, r, len] of list) {
    s = addShot(s, { x, y }, 0)
    s = setVerdict(s, s.shots.length, r, len, 1)
  }
  return s
}
const h = (heat: number[], x: number, y: number) => heat[idx({ x, y })]!

describe('heatMap', () => {
  it('tamaño 400, sin negativos y simétrico en tablero vacío', () => {
    const heat = heatMap(newGame(0))
    expect(heat).toHaveLength(N * N)
    expect(Math.min(...heat)).toBeGreaterThan(0)
    expect(h(heat, 1, 1)).toBe(h(heat, 20, 20))
    expect(h(heat, 1, 20)).toBe(h(heat, 20, 1))
  })
  it('el centro vale más que la esquina (más ubicaciones posibles)', () => {
    const heat = heatMap(newGame(0))
    expect(h(heat, 10, 10)).toBeGreaterThan(h(heat, 1, 1))
  })
  it('esquina vacía: conteo exacto (1 ubicación por barco por orientación contiene la esquina)', () => {
    // barcos restantes [4,4,2,2,2]; la celda (1,1) la cubre 1 ubicación H y 1 V por barco => 2 por barco => 10
    expect(h(heatMap(newGame(0)), 1, 1)).toBe(10)
  })
  it('celdas ya disparadas valen 0', () => {
    const s = play([[10, 10, 'miss'], [3, 3, 'hit']])
    const heat = heatMap(s)
    expect(h(heat, 10, 10)).toBe(0)
    expect(h(heat, 3, 3)).toBe(0)
  })
  it('agua bloquea ubicaciones: una celda rodeada de agua cae a 0', () => {
    const s = play([[5, 5, 'miss'], [7, 5, 'miss'], [6, 4, 'miss'], [6, 6, 'miss']])
    expect(h(heatMap(s), 6, 5)).toBe(0) // ningún barco (mín. 2) cabe en una casilla aislada
  })
  it('un acierto sin hundir favorece extender en línea sobre una celda lejana', () => {
    const s = play([[10, 10, 'hit']])
    const heat = heatMap(s)
    const far = h(heat, 3, 3)
    for (const [x, y] of [[11, 10], [9, 10], [10, 11], [10, 9]] as const) expect(h(heat, x, y)).toBeGreaterThan(far * 5)
    expect(h(heat, 11, 10)).toBeGreaterThan(h(heat, 11, 11)) // la diagonal no extiende
  })
  it('con agua a un lado, empuja al lado opuesto', () => {
    const s = play([[10, 10, 'hit'], [9, 10, 'miss'], [10, 9, 'miss'], [10, 11, 'miss']])
    const heat = heatMap(s)
    expect(h(heat, 11, 10)).toBeGreaterThan(0)
    expect(h(heat, 12, 10)).toBeGreaterThan(h(heat, 3, 3))
  })
  it('un acierto ya hundido no genera prioridad', () => {
    const s = play([[10, 10, 'hit'], [11, 10, 'sunk', 2]])
    const heat = heatMap(s)
    // las casillas hundidas son obstáculos: ninguna ubicación las cruza
    expect(h(heat, 10, 10)).toBe(0)
    expect(h(heat, 11, 10)).toBe(0)
    // sin aciertos pendientes todos los pesos son 1 por ubicación (máx. 28 en el centro)
    expect(Math.max(...heat)).toBeLessThanOrEqual(28)
  })
  it('sin barcos restantes el mapa es todo cero', () => {
    const list: [number, number, ShotResult, number?][] = [
      [1, 1, 'hit'], [2, 1, 'sunk', 2], [1, 3, 'hit'], [2, 3, 'sunk', 2], [1, 5, 'hit'], [2, 5, 'sunk', 2],
      [5, 1, 'hit'], [6, 1, 'hit'], [7, 1, 'hit'], [8, 1, 'sunk', 4],
      [5, 8, 'hit'], [6, 8, 'hit'], [7, 8, 'hit'], [8, 8, 'sunk', 4],
    ]
    expect(heatMap(play(list)).every(v => v === 0)).toBe(true)
  })
})

describe('bestShot', () => {
  it('tablero vacío: devuelve una celda central', () => {
    const c = bestShot(newGame(0))!
    expect(c.x).toBeGreaterThanOrEqual(4)
    expect(c.x).toBeLessThanOrEqual(17)
    expect(c.y).toBeGreaterThanOrEqual(4)
    expect(c.y).toBeLessThanOrEqual(17)
  })
  it('determinista sin rng', () => {
    expect(bestShot(newGame(0))).toEqual(bestShot(newGame(0)))
  })
  it('con rng inyectado elige entre empatados y es reproducible', () => {
    const a = bestShot(newGame(0), seededRng(1))
    const b = bestShot(newGame(0), seededRng(1))
    expect(a).toEqual(b)
    const many = new Set(Array.from({ length: 30 }, (_, i) => JSON.stringify(bestShot(newGame(0), seededRng(i + 1)))))
    expect(many.size).toBeGreaterThan(1)
  })
  it('tras un acierto dispara adyacente en línea (modo rematar)', () => {
    const s = play([[10, 10, 'hit']])
    const c = bestShot(s)!
    expect(Math.abs(c.x - 10) + Math.abs(c.y - 10)).toBe(1)
  })
  it('con dos aciertos alineados continúa la línea', () => {
    const s = play([[10, 10, 'hit'], [11, 10, 'hit']])
    const c = bestShot(s)!
    expect(c.y).toBe(10)
    expect([9, 12]).toContain(c.x)
  })
  it('nunca repite una celda ya disparada', () => {
    let s = newGame(0)
    for (let i = 0; i < 60; i++) {
      const c = bestShot(s)!
      expect(s.shots.some(x => x.at.x === c.x && x.at.y === c.y)).toBe(false)
      s = addShot(s, c, 0)
      s = setVerdict(s, s.shots.length, 'miss', undefined, 1)
    }
  })
})
