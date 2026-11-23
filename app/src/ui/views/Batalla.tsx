import { useEffect } from 'preact/hooks'
import { bestShot } from '../../core/heat'
import { unshotKnownCells } from '../../core/known'
import { app } from '../../state'
import '../../styles/cycle.css'
import { Radar } from '../Board'
import { CoordPad } from '../CoordPad'
import { CancelNotice, FleetMarker, SunkOverlay, VerdictSheet, WonOverlay } from '../cycle/Stage'
import { LocateScreen } from '../cycle/Locate'
import { say, tab } from '../nav'
import { Toggle } from '../parts'

const RES_TXT = { hit: 'ACIERTO', sunk: 'HUNDIDO', miss: 'AGUA' } as const

function Dock() {
  const t = app.target.value
  const link = app.link.value
  const busy = app.busy.value
  const ph = app.cycle.value.phase
  const online = link === 'on' || link === 'busy'
  const idle = ph === 'aim'
  const label = ph === 'won' ? 'PARTIDA TERMINADA'
    : !idle ? (ph === 'verdict' ? 'DA EL VEREDICTO' : ph === 'locate' ? 'UBICA EL BARCO' : ph === 'sunk' ? '¡HUNDIDO!' : 'DISPARO EN CURSO…')
    : busy ? 'DISPARANDO…' : !online ? 'SIN ENLACE' : t ? `DISPARAR (${t.x},${t.y})` : 'ELIGE UNA CELDA'
  const fire = async () => {
    if (!t) return
    const r = await app.fireAt(t)
    if (!r.ok) say(r.message, 3200)
  }
  return (
    <div class="dock"><div class="dockin">
      <button type="button" id="bStop" class="stop" onClick={() => void app.stop()} aria-label="Detener el láser (STOP)">STOP</button>
      <button type="button" id="bFire" class={`fire ${busy || !idle ? 'go' : ''}`} disabled={!t || !online || !idle || busy} onClick={() => void fire()}>{label}</button>
    </div></div>
  )
}

/** Mientras el ciclo corre: el radar a la vista y sin que el scroll lo desplace. */
function useCycleLock(): void {
  const ph = app.cycle.value.phase
  useEffect(() => {
    const root = document.documentElement
    if (ph === 'aim') { root.classList.remove('cyc-lock'); return }
    if (ph === 'flying') {
      const card = document.getElementById('radarCard')
      if (card) window.scrollTo({ top: Math.max(0, card.getBoundingClientRect().top + window.scrollY - 64), behavior: 'auto' })
    }
    root.classList.add('cyc-lock')
  }, [ph])
  useEffect(() => () => document.documentElement.classList.remove('cyc-lock'), [])
}

export function Batalla() {
  useCycleLock()
  const s = app.status.value
  const g = app.game.value
  const link = app.link.value
  const online = link === 'on' || link === 'busy'
  const recent = [...g.shots].reverse().slice(0, 6)
  const t = app.target.value
  const ph = app.cycle.value.phase
  const hits = g.shots.filter(x => x.result === 'hit' || x.result === 'sunk').length
  const pend = app.pendingHits.value
  const assist = app.settings.value.assistant
  const known = app.known.value
  return (
    <>
      {!online && (
        <div class="notice" role="status">
          <span>{link === 'connecting' ? 'Conectando con el módulo…' : 'Sin enlace con el módulo.'}</span>
          <button type="button" class="btn warn" onClick={() => { tab.value = 'enlace' }}>Conectar</button>
        </div>
      )}
      <FleetMarker />
      <section class="card" id="radarCard" aria-label="Radar">
        <div class="cardhead"><h2>Radar · tablero 20×20</h2>
          <span class="sub" id="aimLabel">{app.settings.value.plantillas ? `Plantilla ${app.plantilla.value.n} · ` : ''}{t ? `(${t.x}, ${t.y})` : 'sin elegir'}</span>
        </div>
        <Radar />
        <CancelNotice />
        <p class="hint">Toca o arrastra para apuntar · (1,1) = esquina junto a la estación</p>
        <div class="counters">
          <div><b>{app.sent.value}</b><span>Disparos</span></div>
          <div><b>{app.lastSent.value ? `${app.lastSent.value.x},${app.lastSent.value.y}` : '—'}</b><span>Último</span></div>
          <div><b>{hits}/14</b><span>Impactos</span></div>
        </div>
      </section>
      {pend.length > 0 && ph === 'aim' && (
        <section class="card pendbox" aria-label="Impactos sin ubicar">
          <div class="cardhead"><h2>Impactos sin ubicar</h2><span class="sub">{pend.length}</span></div>
          <div class="row">{pend.slice(0, 4).map(c => <button type="button" class="btn warn sm" onClick={() => app.relocate(c)}>Ubicar ({c.x},{c.y})</button>)}</div>
        </section>
      )}
      <section class="card" aria-label="Objetivo">
        <div class="cardhead"><h2>Objetivo</h2><span class="sub">{t ? `(${t.x}, ${t.y})` : 'sin elegir'}</span></div>
        <CoordPad x={app.draft.value.x} y={app.draft.value.y} onAxis={(a, v) => app.setAxis(a, v)} onNudge={(a, d) => app.nudgeAxis(a, d)} />
        <div id="status" class={`msg ${s.kind}`} style={{ marginTop: '12px' }} role="status" aria-live="polite">{s.text}</div>
        <button type="button" class="ghost" id="bUndo" style={{ width: '100%', marginTop: '8px' }} disabled={app.undoCount.value === 0 || (ph !== 'aim' && ph !== 'locate')} onClick={() => app.undo()}>
          Deshacer última marca{app.undoCount.value ? ` (${app.undoCount.value})` : ''}
        </button>
      </section>
      <section class="card" aria-label="Asistente de tiro">
        <div class="sw-row"><span>Asistente de tiro<small>Mapa de calor sobre casillas sin disparar</small></span>
          <Toggle label="Asistente de tiro" checked={assist} onChange={v => app.updateSettings({ assistant: v })} /></div>
        {assist && (
          <button type="button" class="btn warn sm" style={{ width: '100%', marginTop: '10px' }} id="bBest" disabled={ph !== 'aim'}
            onClick={() => { const b = unshotKnownCells(g, known)[0] ?? bestShot(g); if (b) app.setTarget(b) }}>Usar la mejor celda sugerida</button>
        )}
      </section>
      <section class="card" aria-label="Historial">
        <div class="cardhead"><h2>Últimos disparos</h2></div>
        {recent.length === 0 ? (
          <div class="empty"><b>Aún no hay disparos</b>Elige una celda, comprueba el enlace y pulsa DISPARAR.</div>
        ) : (
          <ul class="hist">{recent.map(x => (
            <li><span class="n">#{x.n}</span><span>({x.at.x},{x.at.y})</span>
              <span class={`r ${x.result ?? 'pend'}`}>{x.result ? RES_TXT[x.result] : 'ESPERANDO VEREDICTO'}</span></li>
          ))}</ul>
        )}
      </section>
      <Dock />
      <VerdictSheet />
      {ph === 'locate' && <LocateScreen key={app.cycle.value.n ?? 0} />}
      <SunkOverlay />
      <WonOverlay />
    </>
  )
}
