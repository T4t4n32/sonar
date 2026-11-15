/**
 * Máquina de estados del CICLO DE DISPARO (APP_SONAR §1c). Pura: no hay temporizadores ni E/S aquí;
 * el store la maneja y dispara los eventos de fin de animación.
 *
 *   aim ─fire→ flying ─landed→ verdict ─miss→ splash ─done→ aim
 *                    │                └hit→ explosion ─done→ locate ─located→ aim | sunk
 *                    └landed (directo)→ explosion ─done→ aim | sunk
 *   sunk ─done→ aim | won          cancel: flying/verdict → aim          reset: cualquiera → aim
 */
import type { Coord } from '../core/types'

export type Phase = 'aim' | 'flying' | 'verdict' | 'splash' | 'explosion' | 'locate' | 'sunk' | 'won'

export interface Cycle {
  phase: Phase
  /** casilla del ciclo en curso (null en aim / won) */
  at: Coord | null
  /** nº de disparo en la partida */
  n: number | null
  /** impacto directo: la casilla es de un barco ya ubicado, no se pregunta */
  direct: boolean
}

export type CycleEvent =
  | { t: 'fire'; at: Coord; n: number; direct: boolean }
  | { t: 'landed' }
  | { t: 'miss' }
  | { t: 'hit' }
  /** fin de la animación (splash / explosión / hundido). `sunk`: el impacto completó un barco; `won`: flota hundida */
  | { t: 'done'; sunk?: boolean; won?: boolean }
  | { t: 'located'; sunk: boolean }
  | { t: 'skip' }
  | { t: 'relocate'; at: Coord; n: number }
  | { t: 'cancel' }
  | { t: 'reset' }

export const IDLE: Cycle = { phase: 'aim', at: null, n: null, direct: false }

const to = (c: Cycle, phase: Phase, extra: Partial<Cycle> = {}): Cycle => ({ ...c, phase, ...extra })

export function next(c: Cycle, ev: CycleEvent): Cycle {
  if (ev.t === 'reset') return IDLE
  switch (c.phase) {
    case 'aim':
      if (ev.t === 'fire') return { phase: 'flying', at: ev.at, n: ev.n, direct: ev.direct }
      if (ev.t === 'relocate') return { phase: 'locate', at: ev.at, n: ev.n, direct: false }
      return c
    case 'flying':
      if (ev.t === 'landed') return c.direct ? to(c, 'explosion') : to(c, 'verdict')
      if (ev.t === 'cancel') return IDLE
      return c
    case 'verdict':
      if (ev.t === 'miss') return to(c, 'splash')
      if (ev.t === 'hit') return to(c, 'explosion')
      if (ev.t === 'cancel') return IDLE
      return c
    case 'splash':
      return ev.t === 'done' ? IDLE : c
    case 'explosion':
      if (ev.t !== 'done') return c
      if (ev.sunk) return to(c, 'sunk')
      return c.direct ? IDLE : to(c, 'locate')
    case 'locate':
      if (ev.t === 'located') return ev.sunk ? to(c, 'sunk') : IDLE
      if (ev.t === 'skip') return IDLE
      return c
    case 'sunk':
      if (ev.t !== 'done') return c
      return ev.won ? to(c, 'won', { at: null, n: null, direct: false }) : IDLE
    case 'won':
      return c
  }
}

/** Fases en las que el ciclo bloquea disparar de nuevo. */
export const isBusyPhase = (p: Phase): boolean => p !== 'aim'
/** Fases en las que aún se puede cancelar con STOP / error del módulo (el veredicto no se ha dado). */
export const isCancellable = (p: Phase): boolean => p === 'flying' || p === 'verdict'
