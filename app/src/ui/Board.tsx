import { useRef } from 'preact/hooks'
import { cellMap } from '../core/board'
import { knownShipAt, unshotKnownCells } from '../core/known'
import { shipAt, shipCells } from '../core/fleet'
import { bestShot, heatMap } from '../core/heat'
import { key, N, type Coord } from '../core/types'
import { app } from '../state'
import { CycleFx } from './cycle/Stage'

const NUMS = Array.from({ length: N }, (_, i) => i + 1)
/** Etiquetas del eje Y de arriba abajo: (1,1) queda ABAJO, junto a la estación, como en el tablero físico. */
const NUMS_Y = [...NUMS].reverse()
const clampCell = (n: number) => Math.max(1, Math.min(N, n))
export function cellFromPointer(e: PointerEvent): Coord {
  const r = (e.currentTarget as HTMLElement).getBoundingClientRect()
  return { x: clampCell(Math.floor(((e.clientX - r.left) / r.width) * N) + 1), y: clampCell(N - Math.floor(((e.clientY - r.top) / r.height) * N)) }
}
const capture = (e: PointerEvent) => { try { (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId) } catch { /* sin captura */ } }

export const YLab = (p: { y?: number | undefined }) => (
  <div class="ylab" aria-hidden="true">{NUMS_Y.map(n => <i class={`${n % 5 === 0 ? 'm' : ''} ${p.y === n ? 'on' : ''}`}>{n % 5 === 0 || n === 1 || p.y === n ? n : ''}</i>)}</div>
)
export const XLab = (p: { x?: number | undefined }) => (
  <div class="xlab" aria-hidden="true">{NUMS.map(n => <i class={`${n % 5 === 0 ? 'm' : ''} ${p.x === n ? 'on' : ''}`}>{n % 5 === 0 || n === 1 || p.x === n ? n : ''}</i>)}</div>
)

/** Radar 20×20 del tablero rival: barrido animado, retícula con cotas, marcas y (opcional) mapa de calor. */
export function Radar() {
  const g = app.game.value
  const map = cellMap(g)
  const t = app.target.value
  const last = app.lastSent.value
  const aiming = app.cycle.value.phase === 'aim'
  const phase = app.cycle.value.phase
  const flash = app.flash.value
  const known = app.known.value
  const heatOn = app.settings.value.assistant && aiming
  const heat = heatOn ? heatMap(g) : null
  // el asistente prioriza rematar los barcos ya ubicados; si no hay, la mejor celda del mapa de calor
  const best = heatOn ? (unshotKnownCells(g, known)[0] ?? bestShot(g)) : null
  const pendLoc = new Set(app.pendingHits.value.map(key))
  const max = heat ? Math.max(1, ...heat) : 1
  const down = useRef(false)
  const beam = app.beam.value
  const bt = beam ?? t ?? { x: 10, y: 10 }

  const cells = []
  for (let y = N; y >= 1; y--) for (let x = 1; x <= N; x++) {   // fila de arriba = y 20; la de abajo (y 1) queda junto a la estación
    const st = map.get(key({ x, y }))
    let cls = 'c'
    if (st === 'hit') cls += ' hit'
    else if (st === 'sunk') cls += ' sunk'
    else if (st === 'miss') cls += ' miss'
    else if (st === 'pending') cls += ' pend shot'
    if (pendLoc.has(key({ x, y }))) cls += ' ploc'
    else if (!st && knownShipAt(known, { x, y })) cls += ' kship'
    if (flash && flash.at.x === x && flash.at.y === y) cls += ' dup'
    const isSel = !!t && t.x === x && t.y === y
    if (isSel) cls += ' sel'
    if (last && last.x === x && last.y === y && !isSel) cls += ' last'
    let style: Record<string, string> | undefined
    if (heat && !st) {
      const v = heat[(y - 1) * N + (x - 1)]!
      if (v > 0) { cls += ' heat'; style = { '--hp': `${Math.round((v / max) * 62)}%` } }
    }
    if (best && best.x === x && best.y === y) cls += ' best'
    cells.push(<div class={cls} style={style} />)
  }

  const set = (e: PointerEvent) => { if (aiming) app.setTarget(cellFromPointer(e)) }
  const arrow = (e: KeyboardEvent) => {
    const d: Record<string, [number, number]> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] }
    const v = d[e.key]
    if (!v) return
    e.preventDefault()
    const c = app.target.value ?? { x: 10, y: 10 }
    app.setTarget({ x: c.x + v[0], y: c.y + v[1] })
  }
  return (
    <div class={`field ${phase === 'explosion' ? 'shake' : ''}`}>
      <div class="stage">
        <div class={`bw ${t ? 'has' : ''}`} style={t ? { '--tx': t.x - 1, '--ty': N - t.y } : undefined} tabIndex={0} role="application" id="radar"
          aria-label="Radar de 20 por 20. Toca o arrastra para apuntar; las flechas del teclado ajustan la celda."
          onPointerDown={e => { if (!aiming) return; down.current = true; capture(e); set(e) }}
          onPointerMove={e => { if (down.current) set(e) }}
          onPointerUp={() => { down.current = false }} onPointerCancel={() => { down.current = false }} onKeyDown={arrow}>
          <YLab y={t?.y} />
          <div class="board" aria-hidden="true">{cells}</div>
          <div class="fx" aria-hidden="true">
            <i class="cv" /><i class="ch" />
            {app.rings.value.map(r => <i key={r.id} class={`ring ${r.kind}`} style={{ left: `${(r.at.x - 0.5) * 5}%`, top: `${(N - r.at.y + 0.5) * 5}%` }} />)}
          </div>
        </div>
        <div class="band low"><XLab x={t?.x} /></div>
        <svg class="svg" viewBox="0 0 20 22.4" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="gs" gradientUnits="userSpaceOnUse" x1="10.5" y1="21.5" x2="10.5" y2="-2"><stop offset="0" style="stop-color:var(--sonar)" stop-opacity=".5" /><stop offset="1" style="stop-color:var(--sonar)" stop-opacity="0" /></linearGradient>
            <clipPath id="cp"><rect x="0" y="0" width="20" height="22.4" /></clipPath>
          </defs>
          <g clip-path="url(#cp)"><g class="sweep"><path d="M10.5 21.5 8.1 -4 12.9 -4Z" fill="url(#gs)" /><path d="M10.5 21.5 10.5 -4" stroke="var(--sonar)" stroke-width=".05" opacity=".6" /></g></g>
          <line class={`beam ${beam ? 'on' : ''}`} x1="10.5" y1="21.5" x2={bt.x - 0.5} y2={N - bt.y + 0.5} />
          <circle class="stn" cx="10.5" cy="21.5" r=".5" /><circle cx="10.5" cy="21.5" r=".16" fill="var(--sonar)" />
        </svg>
        <CycleFx />
      </div>
    </div>
  )
}

/** Mini-tablero de la flota propia. `edit`: tocar para colocar, arrastrar para mover. `reveal`: muestra barcos e impactos. */
export function FleetBoard(p: { edit: boolean; reveal: boolean }) {
  const ships = app.fleet.value
  const sel = app.selected.value
  const show = p.edit || p.reveal
  const drag = useRef<{ id: string; dx: number; dy: number; moved: boolean; wasSel: boolean } | null>(null)
  const owner = new Map<string, string[]>()
  for (const s of ships) for (const c of shipCells(s)) { const k = key(c); owner.set(k, [...(owner.get(k) ?? []), s.id]) }

  const cells = []
  for (let y = N; y >= 1; y--) for (let x = 1; x <= N; x++) {
    const k = key({ x, y })
    const ids = owner.get(k)
    let cls = 'c'
    if (show && ids) cls += ids.length > 1 ? ' bad' : ids[0] === sel ? ' shipsel' : ' ship'
    cells.push(<div class={cls} />)
  }

  const down = (e: PointerEvent) => {
    if (!p.edit) return
    const c = cellFromPointer(e)
    capture(e)
    const s = shipAt(ships, c)
    if (s) {
      drag.current = { id: s.id, dx: c.x - s.x, dy: c.y - s.y, moved: false, wasSel: sel === s.id }
      app.selected.value = s.id
    } else { drag.current = null; app.tapCell(c) }
  }
  const move = (e: PointerEvent) => {
    const d = drag.current
    if (!d || !p.edit) return
    const c = cellFromPointer(e)
    const cur = app.fleet.value.find(s => s.id === d.id)
    if (!cur) return
    const nx = c.x - d.dx, ny = c.y - d.dy
    if (nx !== cur.x || ny !== cur.y) { d.moved = true; app.moveShipTo(d.id, nx, ny) }
  }
  const up = () => {
    const d = drag.current
    drag.current = null
    if (d && !d.moved && d.wasSel) app.selected.value = null
  }
  return (
    <div class="field">
      <div class="stage">
        <div class="band slim"><XLab /></div>
        <div class={`bw ${show ? '' : 'hidden-board'}`} style={{ cursor: p.edit ? 'pointer' : 'default' }} id="fleetboard" aria-label={show ? 'Tablero de mi flota' : 'Tablero oculto'}
          onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}>
          <YLab />
          <div class="board" aria-hidden="true">{cells}</div>
          {!show && <div class="lockveil">FLOTA OCULTA</div>}
        </div>
      </div>
    </div>
  )
}
