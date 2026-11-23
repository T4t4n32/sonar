import { signal } from '@preact/signals'
import { exportCsv, stats } from '../../core/board'
import { app, APP_VERSION } from '../../state'
import { openIntro, replayMode, setReplayMode } from '../../state/intro'
import { MODOS } from '../intro/guion'
import { wakeSupported } from '../../state/feedback'
import { copyText, download, say, shareText } from '../nav'
import { Toggle } from '../parts'

const confirmNew = signal(false)
let prevKind: 'bluetooth' | 'wifi' = 'bluetooth'
const hhmmss = (t: number) => new Date(t).toLocaleTimeString('es-CO', { hour12: false })
const stamp = () => new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '')
const DIR_TXT = { tx: '→', rx: '←', sys: '·', err: '!' } as const

export function Partida() {
  const g = app.game.value
  const st = stats(g)
  const s = app.settings.value
  const log = app.log.value
  const sim = app.kind.value === 'sim'
  const k = app.kind.value
  if (k !== 'sim') prevKind = k
  return (
    <>
      <section class="card" aria-label="Estadísticas">
        <div class="cardhead"><h2>Estadísticas</h2><span class="sub">{app.submode.value === 'duelo' ? 'Duelo' : 'Profesor'}</span></div>
        <div class="statgrid">
          <div><b>{app.sent.value}</b><span>Disparos</span></div>
          <div><b>{st.hits}</b><span>Aciertos</span></div>
          <div><b>{st.misses}</b><span>Agua</span></div>
          <div><b>{st.decided ? `${st.precision}%` : '—'}</b><span>Precisión</span></div>
          <div><b>{st.maxStreak}</b><span>Mejor racha</span></div>
          <div><b>{st.avgDecisionMs ? `${(st.avgDecisionMs / 1000).toFixed(1)}s` : '—'}</b><span>Veredicto medio</span></div>
        </div>
        {st.decided === 0 && g.shots.length > 0 && <p class="sub" style={{ marginTop: '8px' }}>En modo Profesor no hay veredicto en la app: el defensor lo dice en voz alta.</p>}
      </section>

      <section class="card" aria-label="Exportar">
        <div class="cardhead"><h2>Exportar partida</h2></div>
        <div class="grid2">
          <button type="button" class="btn sm" id="bJson" onClick={() => download(`sonar-${stamp()}.json`, 'application/json', app.exportJSON())}>Descargar JSON</button>
          <button type="button" class="btn sm" id="bCsv" onClick={() => download(`sonar-${stamp()}.csv`, 'text/csv', exportCsv(g))}>Descargar CSV</button>
          <button type="button" class="btn sm" onClick={async () => say((await shareText('Partida SONAR', exportCsv(g))) ? 'Listo.' : 'No se pudo compartir.')}>Compartir CSV</button>
          <button type="button" class="btn sm" onClick={async () => say((await copyText(app.logText())) ? 'Bitácora copiada.' : 'No se pudo copiar.')}>Copiar bitácora</button>
        </div>
      </section>

      <section class="card" aria-label="Ajustes">
        <div class="cardhead"><h2>Ajustes</h2></div>
        <div class="seg" role="group" aria-label="Tema" style={{ marginBottom: '6px' }}>
          <button type="button" aria-pressed={s.theme === 'dark'} onClick={() => app.updateSettings({ theme: 'dark' })}>Oscuro</button>
          <button type="button" aria-pressed={s.theme === 'light'} onClick={() => app.updateSettings({ theme: 'light' })}>Claro</button>
        </div>
        <div class="sw-row"><span>Sonido<small>Pings sintetizados por evento</small></span><Toggle label="Sonido" checked={s.sound} onChange={v => { app.updateSettings({ sound: v }) }} /></div>
        <div class="sw-row"><span>Vibración<small>Disparo, acierto, error…</small></span><Toggle label="Vibración" checked={s.vibrate} onChange={v => { app.updateSettings({ vibrate: v }); if (v) navigator.vibrate?.(40) }} /></div>
        {wakeSupported() && <div class="sw-row"><span>Mantener pantalla encendida<small>Durante la evaluación</small></span><Toggle label="Pantalla encendida" checked={s.wake} onChange={v => app.updateSettings({ wake: v })} /></div>}
        <div class="sw-row"><span>Plantillas de fábrica<small>Partida 1 = plantilla 1, luego la 2… Al tocar un barco se hunde y la app dice dónde está</small></span><Toggle label="Plantillas de fábrica" checked={s.plantillas} onChange={v => app.updateSettings({ plantillas: v })} /></div>
        <div class="sw-row"><span>Modo simulado<small>Rival virtual, sin hardware</small></span><Toggle label="Modo simulado" checked={sim} onChange={v => { void app.setKind(v ? 'sim' : prevKind) }} /></div>
      </section>

      <section class="card" aria-label="Partida">
        <div class="cardhead"><h2>Partida</h2></div>
        <button type="button" class={`btn ${confirmNew.value ? 'hit' : ''}`} id="bNew" style={{ width: '100%' }} onClick={() => {
          if (!confirmNew.value) { confirmNew.value = true; setTimeout(() => { confirmNew.value = false }, 3500); return }
          confirmNew.value = false; app.newMatch(); say('Partida nueva.')
        }}>{confirmNew.value ? '¿Seguro? Toca otra vez para borrar' : 'Nueva partida'}</button>
        <p class="sub" style={{ marginTop: '8px' }}>Borra disparos y recibidos; la flota se conserva.</p>
      </section>

      <section class="card" aria-label="Tutorial">
        <div class="cardhead"><h2>Tutorial</h2></div>
        <div class="seg" role="group" aria-label="Qué ver" style={{ marginBottom: '8px' }}>
          {MODOS.map(m => <button type="button" aria-pressed={replayMode.value === m.id} onClick={() => setReplayMode(m.id)}>{m.label}</button>)}
        </div>
        <button type="button" class="btn" id="bTutorial" style={{ width: '100%' }} onClick={() => openIntro(replayMode.value)}>Ver tutorial</button>
        <p class="sub" style={{ marginTop: '8px' }}>La dinámica del juego (Acto 1) y el recorrido de la app (Acto 2), animados.</p>
      </section>

      <section class="card" aria-label="Bitácora">
        <div class="cardhead"><h2>Bitácora</h2><button type="button" class="ghost" onClick={() => app.clearLog()}>Vaciar</button></div>
        {log.length === 0 ? <div class="empty"><b>Sin eventos</b>Aquí verás cada línea enviada (→) y recibida (←).</div> : (
          <ol class="log" id="log">{log.slice(0, 120).map(e => <li class={e.dir}><time>{hhmmss(e.t)}</time><span>{DIR_TXT[e.dir]} {e.text}</span></li>)}</ol>
        )}
      </section>
      <footer>SONAR · v{APP_VERSION} · Fundamentos de Ingeniería Mecatrónica · UAO</footer>
    </>
  )
}
