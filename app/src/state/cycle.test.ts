import { describe, expect, it } from 'vitest'
import { IDLE, isBusyPhase, isCancellable, next, type Cycle, type CycleEvent } from './cycle'

const at = { x: 10, y: 15 }
const run = (c: Cycle, ...evs: CycleEvent[]) => evs.reduce(next, c)
const fire = (direct = false): CycleEvent => ({ t: 'fire', at, n: 1, direct })

describe('máquina de estados del ciclo', () => {
  it('empieza en aim y solo FIRE la mueve', () => {
    expect(IDLE.phase).toBe('aim')
    expect(run(IDLE, { t: 'landed' }, { t: 'miss' }, { t: 'hit' }, { t: 'done' }).phase).toBe('aim')
    expect(next(IDLE, fire())).toMatchObject({ phase: 'flying', at, n: 1, direct: false })
  })
  it('agua: aim → flying → verdict → splash → aim', () => {
    const phases: string[] = []
    let c: Cycle = IDLE
    for (const ev of [fire(), { t: 'landed' }, { t: 'miss' }, { t: 'done' }] as CycleEvent[]) { c = next(c, ev); phases.push(c.phase) }
    expect(phases).toEqual(['flying', 'verdict', 'splash', 'aim'])
  })
  it('acierto: verdict → explosion → locate → aim (o sunk → aim / won)', () => {
    const c = run(IDLE, fire(), { t: 'landed' }, { t: 'hit' })
    expect(c.phase).toBe('explosion')
    const l = next(c, { t: 'done' })
    expect(l.phase).toBe('locate')
    expect(next(l, { t: 'located', sunk: false }).phase).toBe('aim')
    expect(next(l, { t: 'skip' }).phase).toBe('aim')
    const s = next(l, { t: 'located', sunk: true })
    expect(s.phase).toBe('sunk')
    expect(next(s, { t: 'done', won: false }).phase).toBe('aim')
    expect(next(s, { t: 'done', won: true }).phase).toBe('won')
  })
  it('impacto directo: no hay veredicto; explosión → aim, o sunk', () => {
    const e = run(IDLE, fire(true), { t: 'landed' })
    expect(e.phase).toBe('explosion')
    expect(next(e, { t: 'done' }).phase).toBe('aim')
    expect(next(e, { t: 'done', sunk: true }).phase).toBe('sunk')
  })
  it('cancel solo vale en flying/verdict; reset siempre vuelve a aim', () => {
    expect(run(IDLE, fire(), { t: 'cancel' })).toEqual(IDLE)
    expect(run(IDLE, fire(), { t: 'landed' }, { t: 'cancel' })).toEqual(IDLE)
    const ex = run(IDLE, fire(), { t: 'landed' }, { t: 'hit' })
    expect(next(ex, { t: 'cancel' })).toBe(ex)
    expect(next(ex, { t: 'reset' })).toEqual(IDLE)
    expect(isCancellable('flying') && isCancellable('verdict') && !isCancellable('explosion')).toBe(true)
  })
  it('eventos ilegales no cambian el estado (misma referencia)', () => {
    const v = run(IDLE, fire(), { t: 'landed' })
    expect(next(v, fire())).toBe(v)
    expect(next(v, { t: 'done' })).toBe(v)
    expect(next(v, { t: 'located', sunk: false })).toBe(v)
    expect(isBusyPhase('aim')).toBe(false)
    expect(isBusyPhase('verdict')).toBe(true)
  })
  it('relocate reabre «ubicar» desde aim', () => {
    expect(next(IDLE, { t: 'relocate', at, n: 4 })).toMatchObject({ phase: 'locate', at, n: 4 })
  })
})
