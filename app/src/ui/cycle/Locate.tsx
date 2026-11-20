import { useRef, useState } from 'preact/hooks'
import { cellMap } from '../../core/board'
import { knownShipAt } from '../../core/known'
import { key, N, type Coord } from '../../core/types'
import { app } from '../../state'
import { say } from '../nav'

const NUMS = Array.from({ length: N }, (_, i) => i + 1)
const clampCell = (n: number) => Math.max(1, Math.min(N, n))
const same = (a: Coord, b: Coord) => a.x === b.x && a.y === b.y

/** Casilla bajo el dedo (sobre el tablero, con el dedo capturado fuera también se ajusta al borde). */
function cellAt(e: PointerEvent): Coord {
  const r = (e.currentTarget as HTMLElement).getBoundingClientRect()
  return { x: clampCell(Math.floor(((e.clientX - r.left) / r.width) * N) + 1), y: clampCell(N - Math.floor(((e.clientY - r.top) / r.height) * N)) }
}

/** Trazo «ajustado» a un eje: solo recta horizontal o vertical desde `a` hasta la proyección de `b`. */
export function snapLine(a: Coord, b: Coord): Coord[] {
  const dx = b.x - a.x, dy = b.y - a.y
  if (dx === 0 && dy === 0) return [a]
  const out: Coord[] = []
  if (Math.abs(dx) >= Math.abs(dy)) { const s = Math.sign(dx); for (let x = a.x; x !== b.x + s; x += s) out.push({ x, y: a.y }) }
  else { const s = Math.sign(dy); for (let y = a.y; y !== b.y + s; y += s) out.push({ x: a.x, y }) }
  return out
}

/** Pantalla «Ubica el barco»: tablero completo; el estudiante arrastra el dedo sobre las casillas del barco real. */
export function LocateScreen() {
  const cy = app.cycle.value
  const [sel, setSel] = useState<Coord[]>([])
  const drag = useRef<{ start: Coord } | null>(null)
  if (cy.phase !== 'locate' || !cy.at) return null
  const hit = cy.at
  const g = app.game.value
  const map = cellMap(g)
  const known = app.known.value
  const check = app.checkLocation(sel)
  const showCheck = sel.length > 0
  const preview = new Set(sel.map(key))

  const update = (cells: Coord[]) => {
    if (cells.length !== sel.length || cells.some((c, i) => !same(c, sel[i]!))) {
      if (cells.length > sel.length) app.fx('tick')
      setSel(cells)
    }
  }
  const down = (e: PointerEvent) => {
    e.preventDefault()
    try { (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId) } catch { /* sin captura */ }
    const c = cellAt(e)
    drag.current = { start: c }
    app.fx('tick')
    setSel([c])
  }
  const move = (e: PointerEvent) => { const d = drag.current; if (d) update(snapLine(d.start, cellAt(e))) }
  const up = () => { drag.current = null }

  const cells = []
  for (let y = N; y >= 1; y--) for (let x = 1; x <= N; x++) {   // (1,1) abajo, igual que el radar
    const k = key({ x, y })
    let cls = 'c'
    const ks = knownShipAt(known, { x, y })
    const st = map.get(k)
    if (ks) cls += ' kship'
    if (st === 'miss') cls += ' miss'
    else if (st === 'hit') cls += ' hit'
    else if (st === 'sunk') cls += ' sunk'
    if (x === hit.x && y === hit.y) cls += ' hitnow'
    if (preview.has(k)) cls += check.ok ? ' pv ok' : ' pv bad'
    cells.push(<div class={cls} />)
  }

  const ready = () => {
    const r = app.locate(sel)
    if (!r.ok) say(r.errors[0] ?? 'Revisa el trazo.')
    else setSel([])
  }
  const lens = (n: number, p: string) => `${n} ${p}`
  const left = { e: 3 - known.filter(s => s.len === 2).length, s: 2 - known.filter(s => s.len === 4).length }

  return (
    <div class="loc" role="dialog" aria-label="Ubica el barco">
      <header class="lochead">
        <div>
          <small>UBICA EL BARCO</small>
          <b id="locCoord">Impacto en ({hit.x}, {hit.y})</b>
        </div>
        <button type="button" id="bStop3" class="stop vstop" onClick={() => { void app.stop() }} aria-label="STOP">STOP</button>
      </header>
      <p class="locask">Arrastra el dedo sobre las casillas del barco, como lo ves en tu tablero físico.</p>
      <div class="field locfield">
        <div class="stage">
          <div class="band slim"><div class="xlab" aria-hidden="true">{NUMS.map(n => <i class={n % 5 === 0 || n === 1 ? 'm' : ''}>{n % 5 === 0 || n === 1 ? n : ''}</i>)}</div></div>
          <div class="bw" id="locBoard" style={{ cursor: 'crosshair' }} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}
            aria-label="Tablero 20 por 20. Arrastra para trazar el barco.">
            <div class="ylab" aria-hidden="true">{[...NUMS].reverse().map(n => <i class={n % 5 === 0 ? 'm' : ''}>{n % 5 === 0 || n === 1 ? n : ''}</i>)}</div>
            <div class="board" aria-hidden="true">{cells}</div>
          </div>
        </div>
      </div>
      <div id="locLabel" class={`loclabel ${showCheck ? (check.ok ? 'ok' : 'bad') : ''}`} role="status" aria-live="polite">
        {showCheck ? (<><b>{check.label}</b><span>{check.ok ? 'Listo para registrar' : check.errors[0]}</span></>) : (<span>Faltan por ubicar: {lens(left.e, 'embarcaciones')} · {lens(left.s, 'submarinos')}</span>)}
      </div>
      <div class="locbtns">
        <button type="button" id="locDone" class="btn pri big" disabled={!check.ok} onClick={ready}>LISTO</button>
        <button type="button" id="locClear" class="btn" disabled={sel.length === 0} onClick={() => setSel([])}>Borrar</button>
        <button type="button" id="locSkip" class="btn" onClick={() => { setSel([]); app.skipLocate() }}>No sé / después</button>
      </div>
    </div>
  )
}
