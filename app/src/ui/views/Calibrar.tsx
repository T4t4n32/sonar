import { useEffect, useRef } from 'preact/hooks'
import { app } from '../../state'
import { CALIB_STEPS, CORNERS_INFO, type JogDir } from '../../state/calib'
import { key, N } from '../../core/types'
import '../../styles/calib.css'
import { cellFromPointer, XLab, YLab } from '../Board'

const REPEAT_MS = 250
const STEP_LABEL: Record<number, string> = { 5: '5°', 1: '1°', 0.2: '0,2°', 0.05: '0,05°' }
const deg = (v: number | null): string => (v === null ? '—' : v.toFixed(2))
const mmss = (s: number): string => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

/** Botón de la cruceta: un toque = un paso; mantenido repite ~4 veces por segundo (los pasos se unen en el módulo). */
function JogBtn(p: { dir: JogDir; label: string; aria: string; disabled: boolean }) {
  const timer = useRef<number | undefined>(undefined)
  const stop = () => { if (timer.current !== undefined) { window.clearInterval(timer.current); timer.current = undefined } }
  useEffect(() => stop, [])
  useEffect(() => { if (p.disabled) stop() }, [p.disabled])
  const down = (e: PointerEvent) => {
    e.preventDefault()
    try { (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId) } catch { /* sin captura */ }
    app.calib.jog(p.dir)
    stop()
    timer.current = window.setInterval(() => app.calib.jog(p.dir), REPEAT_MS)
  }
  const keyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); app.calib.jog(p.dir) }
  }
  return (
    <button type="button" class={`jogb ${p.dir}`} id={`jog-${p.dir}`} aria-label={p.aria} disabled={p.disabled}
      onPointerDown={down} onPointerUp={stop} onPointerCancel={stop} onLostPointerCapture={stop} onKeyDown={keyDown}>{p.label}</button>
  )
}

function CalBoard() {
  const c = app.calib
  const v = c.verified.value
  const mapped = c.mapMode.value === 'GRID' && !c.stale.value
  const corners = new Set(CORNERS_INFO.slice(0, 4).map(i => key(i.cell)))
  const cells = []
  for (let y = N; y >= 1; y--) for (let x = 1; x <= N; x++) {   // (1,1) abajo, igual que el radar
    let cls = 'c'
    if (v && v.x === x && v.y === y) cls += ' sel'
    if (corners.has(key({ x, y }))) cls += ' cornc'
    cells.push(<div class={cls} />)
  }
  const tap = (e: PointerEvent) => { void c.verify(cellFromPointer(e)) }
  return (
    <div class="field calfield">
      <div class="stage">
        <div class="bw" id="calBoard" role="application" aria-label="Tablero para verificar. Toca una celda: el láser apunta ahí con el mapa actual." onPointerDown={tap}>
          <YLab y={v?.y} />
          <div class="board" aria-hidden="true">{cells}</div>
        </div>
        <div class="band slim under"><XLab x={v?.x} /></div>
      </div>
      <p class="hint" id="calBoardHint">{mapped ? 'Toca una celda: el láser apunta ahí con el mapa calculado.' : 'Toca una celda para probar (sin mapa calculado apunta con la geometría de fábrica).'}</p>
    </div>
  )
}

/** «Calibrar apuntado»: se mueve el láser con la cruceta hasta cada esquina real y el módulo aprende dónde está cada celda. */
export function Calibrar() {
  const c = app.calib
  const on = app.connected.value
  const supported = c.supported.value
  useEffect(() => { if (on && supported) void c.refresh() }, [on, supported])
  if (!on) return null

  if (!supported) {
    return (
      <section class="card calib" aria-label="Calibrar apuntado" id="calib">
        <div class="cardhead"><h2>Calibrar apuntado</h2></div>
        <div class="notice" id="calNoGrid"><span>Este firmware no trae la calibración de apuntado (no anuncia <b>grid</b> en HELLO). Carga la versión nueva del módulo.</span></div>
      </section>
    )
  }

  const p = c.prefs.value
  const busy = app.busy.value
  const off = busy
  const laser = c.laserOn.value
  const fitErr = c.fitErr.value
  const map = c.mapMode.value
  const done = c.corners.value
  const angles = c.cornerAngles.value
  const fitText = !c.cornersDone.value ? 'Registra las 4 esquinas para poder calcular.'
    : c.stale.value ? 'Falta calcular con las esquinas actuales.'
    : map === 'GRID' ? (fitErr === null || fitErr === undefined ? 'Mapa calculado (sin punto de control).' : `Mapa calculado · error del control: ${fitErr.toFixed(2)}°`)
    : 'Listo para calcular.'

  return (
    <section class="card calib" aria-label="Calibrar apuntado" id="calib">
      <div class="cardhead"><h2>Calibrar apuntado</h2>
        <span class="sub" id="calMap">{map === 'GRID' ? 'mapa: calculado' : map === 'GEO' ? 'mapa: de fábrica' : 'mapa: …'}</span>
      </div>
      <p class="sub calintro">Enciende el láser, llévalo con la cruceta a cada esquina real de la matriz y registra cada una. Mira siempre el punto en tu tablero físico.</p>

      <div class="seg" role="group" aria-label="Tamaño del paso">
        {CALIB_STEPS.map(s => <button type="button" id={`step-${String(s).replace('.', '_')}`} aria-pressed={p.step === s} onClick={() => c.setPrefs({ step: s })}>{STEP_LABEL[s]}</button>)}
      </div>

      <div class="dpad" role="group" aria-label="Mover el láser">
        <JogBtn dir="up" label="↑" aria="Subir el láser" disabled={off} />
        <JogBtn dir="left" label="←" aria="Mover a la izquierda" disabled={off} />
        <button type="button" class="btn jogmid" id="calCenter" aria-label="Centrar los servos a 90 grados" disabled={off} onClick={() => void c.center()}>90°</button>
        <JogBtn dir="right" label="→" aria="Mover a la derecha" disabled={off} />
        <JogBtn dir="down" label="↓" aria="Bajar el láser" disabled={off} />
      </div>
      <div class="calread" id="calAngles" aria-live="off">Pan <b>{deg(c.pan.value)}°</b> · Tilt <b>{deg(c.tilt.value)}°</b></div>

      <div class="grid2" style={{ marginTop: '10px' }}>
        <button type="button" class={`btn ${laser ? 'laseron' : ''}`} id="calLaser" aria-pressed={laser} disabled={off} onClick={() => void c.toggleLaser()}>
          {laser ? `ENCENDIDO · ${mmss(c.laserLeft.value)}` : 'ENCENDER LÁSER'}
        </button>
        <button type="button" class="stop" id="calStop" onClick={() => void app.stop()} aria-label="Detener el láser (STOP)">STOP</button>
      </div>

      <div class="grid2 calinv">
        <label><input type="checkbox" id="inv-h" checked={p.invertH} onChange={e => c.setPrefs({ invertH: (e.currentTarget as HTMLInputElement).checked })} /> Invertir ← →</label>
        <label><input type="checkbox" id="inv-v" checked={p.invertV} onChange={e => c.setPrefs({ invertV: (e.currentTarget as HTMLInputElement).checked })} /> Invertir ↑ ↓</label>
      </div>

      <ul class="cornerlist" aria-label="Esquinas">
        {CORNERS_INFO.map(ci => {
          const ok = done[ci.n - 1]
          const a = angles[ci.n - 1]
          return (
            <li class={ok ? 'ok' : ''}>
              <button type="button" class="btn sm" id={`corner-${ci.n}`} disabled={off} onClick={() => void c.recordCorner(ci.n)}>{ci.label}</button>
              <span class="cmark" id={`cmark-${ci.n}`} title={a ? `pan ${a.pan.toFixed(2)}° · tilt ${a.tilt.toFixed(2)}°` : ''}>{ok ? '✓' : ci.optional ? '○' : '·'}</span>
            </li>
          )
        })}
      </ul>

      <button type="button" class="btn pri calfit" id="calFit" disabled={off || !c.cornersDone.value} onClick={() => void c.compute()}>CALCULAR</button>
      <p class="sub calres" id="calFitRes" role="status">{fitText}</p>

      <CalBoard />

      <div class="grid2" style={{ marginTop: '10px' }}>
        <button type="button" class="btn pri" id="calSave" disabled={off || !c.canSave.value} onClick={() => void c.save()}>GUARDAR EN EL MÓDULO</button>
        <button type="button" class="btn warn" id="calReset" disabled={off} onClick={() => void app.calibResetMap()}>REINICIAR MAPA</button>
      </div>
      <p class="msg calmsg" id="calibMsg" role="status" aria-live="polite">{c.msg.value || ' '}</p>
    </section>
  )
}
