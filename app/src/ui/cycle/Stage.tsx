import { signal } from '@preact/signals'
import { useEffect, useRef } from 'preact/hooks'
import { app } from '../../state'
import { Fx, prefersReducedMotion, type FxPhase } from './fx'
import type { Coord } from '../../core/types'

const IconHit = () => (
  <svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 3l4.6 12.2L40 9.5l-5.2 11.6L46 24l-11.2 3L40 38.5l-11.4-5.7L24 45l-4.6-12.2L8 38.5l5.2-11.5L2 24l11.2-3L8 9.5l11.4 5.7z" /><circle cx="24" cy="24" r="6" /></svg>
)
const IconMiss = () => (
  <svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 5C17 16 11 22 11 30a13 13 0 0 0 26 0c0-8-6-14-13-25z" /><path d="M18 31a6 6 0 0 0 6 6" class="hl" /></svg>
)

const PHASE_FX: Record<string, FxPhase> = { flying: 'flying', verdict: 'verdict', splash: 'splash', explosion: 'explosion' }

/** Capa de efectos (canvas) que cubre el escenario del radar: proyectil, congelado, gota y explosión. */
export function CycleFx() {
  const ref = useRef<HTMLCanvasElement>(null)
  const fx = useRef<Fx | null>(null)
  const lastAt = useRef<Coord>({ x: 10, y: 10 })
  const cy = app.cycle.value
  const cancel = app.cancelFx.value
  if (cy.at) lastAt.current = cy.at
  useEffect(() => {
    if (!ref.current) return
    fx.current = new Fx(ref.current, prefersReducedMotion())
    return () => fx.current?.destroy()
  }, [])
  useEffect(() => {
    const f = fx.current
    if (!f) return
    f.setPhase(PHASE_FX[cy.phase] ?? 'idle', cy.at ?? lastAt.current, app.timing.flight)
  }, [cy.phase, cy.n])
  useEffect(() => {
    const f = fx.current
    if (!f || !cancel) return
    f.setPhase('cancel', lastAt.current)
    const h = setTimeout(() => f.setPhase('idle', lastAt.current), 600)
    return () => clearTimeout(h)
  }, [cancel?.id])
  return <canvas ref={ref} class="cyc-canvas" aria-hidden="true" />
}

/** Avisa de que el disparo se canceló (error del módulo, STOP, enlace caído). Sobrio y breve. */
export function CancelNotice() {
  const c = app.cancelFx.value
  if (!c) return null
  return <div key={c.id} class="cyc-cancel" role="alert"><b>DISPARO CANCELADO</b><span>{c.text}</span></div>
}

const stopNow = () => { void app.stop() }

/** Hoja del veredicto: el tiempo está congelado y los estudiantes dicen SÍ o NO tras mirar su tablero físico. */
export function VerdictSheet() {
  const cy = app.cycle.value
  if (cy.phase !== 'verdict' || !cy.at) return null
  const { x, y } = cy.at
  const conflict = app.conflict.value
  const busy = app.busy.value
  return (
    <div class="vsheet" role="dialog" aria-label="Veredicto del disparo">
      <div class="vin">
        <div class="vhead">
          <button type="button" id="bStop2" class="stop vstop" onClick={stopNow} aria-label="Detener el láser (STOP)">STOP</button>
          <div class="vq"><small>{busy ? 'LÁSER EN CURSO' : 'LÁSER LISTO'}</small><b id="vCoord">({x}, {y})</b></div>
        </div>
        {conflict ? (
          <div class="vconf" role="alertdialog" aria-label="Conflicto">
            <p><b>La {app.settings.value.plantillas ? app.plantilla.value.nombre : 'flota'} marca un barco en esa casilla.</b> ¿Seguro que NO le dio?</p>
            <div class="vbtns two">
              <button type="button" id="vConfirmMiss" class="vb no" onClick={() => app.answer(false, true)}><IconMiss />SÍ, FUE AGUA</button>
              <button type="button" id="vKeep" class="vb ghostb" onClick={() => app.dismissConflict()}>VOLVER</button>
            </div>
          </div>
        ) : (
          <>
            <p class="vask">¿Le dio al barco? Mira tu tablero físico.</p>
            <div class="vbtns">
              <button type="button" id="vYes" class="vb yes" onClick={() => app.answer(true)}><IconHit />SÍ LE DIO</button>
              <button type="button" id="vNo" class="vb no" onClick={() => app.answer(false)}><IconMiss />NO LE DIO</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

const Boat = () => (
  <svg viewBox="0 0 120 56" aria-hidden="true"><path d="M8 34h104l-14 16H24z" /><path d="M44 34V18h26v16M70 24h16l6 10" /><path d="M56 18V8" class="mast" /></svg>
)
const Sub = () => (
  <svg viewBox="0 0 200 60" aria-hidden="true"><path d="M10 34c0-9 20-16 60-16h60c40 0 60 7 60 16s-20 16-60 16H70c-40 0-60-7-60-16z" /><path d="M84 18v-9h30v9M104 9V3h12" /><circle cx="60" cy="34" r="4" class="hl" /><circle cx="90" cy="34" r="4" class="hl" /><path d="M190 34l8-10v20z" /></svg>
)

/** ¡HUNDIDO!: el barco se hunde con burbujas y el marcador de flota restante. */
export function SunkOverlay() {
  const cy = app.cycle.value
  if (cy.phase !== 'sunk') return null
  const ship = app.lastSunk.value
  const left = app.left.value
  return (
    <div class="sunkov" role="alert" aria-label="Hundido">
      <div class="sunk-in">
        <div class="sunk-stage" aria-hidden="true">
          <div class={`sunk-ship ${ship?.kind === 'submarino' ? 'sub' : 'boat'}`}>{ship?.kind === 'submarino' ? <Sub /> : <Boat />}</div>
          <div class="sunk-water">{[0, 1, 2, 3, 4, 5, 6].map(i => <i style={{ '--i': i }} />)}</div>
        </div>
        <h2>¡HUNDIDO!</h2>
        <p class="sunk-name">{ship ? `${ship.kind === 'submarino' ? 'Submarino' : 'Embarcación'} ${ship.id.slice(1)}` : 'Barco'}</p>
        {ship && <p class="sunk-name" id="sunkPos">{`en (${ship.cells[0]!.x},${ship.cells[0]!.y}) a (${ship.cells[ship.cells.length - 1]!.x},${ship.cells[ship.cells.length - 1]!.y})`}</p>}
        <p class="sunk-left">Quedan <b>{left.embarcaciones}</b> embarcaciones · <b>{left.submarinos}</b> submarinos</p>
      </div>
    </div>
  )
}

const seeRadar = signal(false)

export function WonOverlay() {
  const cy = app.cycle.value
  useEffect(() => { if (cy.phase !== 'won') seeRadar.value = false }, [cy.phase])
  if (cy.phase !== 'won' || seeRadar.value) return null
  const n = app.game.value.shots.length
  return (
    <div class="overlay won" role="alertdialog" aria-label="Victoria">
      <div class="box">
        <div class="confetti" aria-hidden="true">{Array.from({ length: 16 }, (_, i) => <i style={{ '--i': i }} />)}</div>
        <h2>VICTORIA</h2>
        <p>Flota hundida en {n} disparos.</p>
        <button type="button" class="btn pri" id="bNewMatch" onClick={() => app.newMatch()}>Nueva partida</button>
        <button type="button" class="ghost" id="bSeeRadar" onClick={() => { seeRadar.value = true }}>Ver radar</button>
        {app.undoCount.value > 0 && <button type="button" class="ghost" onClick={() => app.undo()}>Deshacer último</button>}
      </div>
    </div>
  )
}

/** Marcador de flota restante: puntos llenos = a flote, tachados = hundidos. */
export function FleetMarker() {
  const left = app.left.value
  const pips = (total: number, alive: number, cls: string) => Array.from({ length: total }, (_, i) => <i class={`pip ${cls} ${i < alive ? '' : 'dead'}`} />)
  return (
    <section class="fmark" aria-label="Flota rival restante" id="fleetLeft">
      <div><span class="pips">{pips(3, left.embarcaciones, 'e')}</span><b>{left.embarcaciones}</b><small>embarcaciones</small></div>
      <div><span class="pips">{pips(2, left.submarinos, 's')}</span><b>{left.submarinos}</b><small>submarinos</small></div>
    </section>
  )
}
