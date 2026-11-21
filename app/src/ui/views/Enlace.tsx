import { effect, signal } from '@preact/signals'
import { useEffect } from 'preact/hooks'
import { CAL_RANGES, app } from '../../state'
import { KIND_LABEL, type TransportKind } from '../../state/transports'
import { TEST_POSITIONS } from '../../transport/sim'
import { Calibrar } from './Calibrar'

const KINDS: TransportKind[] = ['bluetooth', 'wifi', 'sim']
const calDraft = signal<string[]>(['100', '-65', '180', '0', '0'])
const showAll = signal(false)
effect(() => {
  const c = app.cal.value
  if (c) calDraft.value = [c.x, c.y, c.h, c.panTrim, c.tiltTrim].map(v => String(v))
})

function Modules() {
  const link = app.link.value
  const on = link === 'on' || link === 'busy'
  const h = app.hello.value
  const hb = app.hb.value
  const peers = app.peers.value
  return (
    <section class="card" aria-label="Módulo">
      <div class="cardhead"><h2>Módulo SONAR</h2>
        {!on && <button type="button" class="ghost" id="bScan" onClick={() => void app.refreshPeers(showAll.value)}>Buscar</button>}
      </div>
      {on || link === 'connecting' ? (
        <div style={{ display: 'grid', gap: '10px' }}>
          <dl class="kv">
            <dt>Estado</dt><dd>{app.linkMsg.value}</dd>
            {h && <><dt>Nombre</dt><dd id="helloName">{h.name}</dd><dt>Firmware</dt><dd>{h.fw}</dd><dt>Modo</dt><dd>{h.mode}</dd><dt>Capacidades</dt><dd>{h.caps.length ? h.caps.join(', ') : '—'}</dd></>}
            <dt>Latido (PING)</dt>
            <dd id="hb">{hb.ok === null ? 'esperando…' : hb.ok ? `ok · ${hb.rttMs} ms` : `sin respuesta (${hb.fails})`}</dd>
          </dl>
          <div class="row">
            <button type="button" class="btn sm" onClick={() => void app.ping()} disabled={link === 'busy'}>PING ahora</button>
            <button type="button" class="btn sm warn" id="bDisc" onClick={() => void app.disconnect()}>Desconectar</button>
          </div>
        </div>
      ) : peers.length === 0 ? (
        <div class="empty"><b>{app.peersMsg.value.startsWith('Buscando') ? 'Buscando…' : 'No hay módulos a la vista'}</b>{app.peersMsg.value || 'Pulsa Buscar para listar los módulos SONAR.'}</div>
      ) : (
        <ul class="peers">{peers.map(pr => (
          <li><div style={{ flex: 1, minWidth: 0 }}><b>{pr.name}</b><br /><small>{pr.id}{pr.rssi !== undefined ? ` · ${pr.rssi} dBm` : ''}</small></div>
            <button type="button" class="btn pri" data-peer={pr.id} onClick={() => void app.connect(pr.id)}>Conectar</button></li>
        ))}</ul>
      )}
      {link === 'error' && <p class="msg err" style={{ marginTop: '10px' }}>{app.linkMsg.value}</p>}
      {!on && app.kind.value === 'bluetooth' && (
        <label class="sub" style={{ display: 'flex', gap: '8px', alignItems: 'center', minHeight: '48px' }}>
          <input type="checkbox" checked={showAll.value} onChange={e => { showAll.value = (e.currentTarget as HTMLInputElement).checked; void app.refreshPeers(showAll.value) }} style={{ width: '20px', height: '20px' }} /> Mostrar todos los dispositivos emparejados
        </label>
      )}
    </section>
  )
}

function TestCard() {
  const t = app.test.value
  const on = app.connected.value
  return (
    <section class="card" aria-label="Prueba de 5 posiciones">
      <div class="cardhead"><h2>TEST · 5 posiciones</h2></div>
      <div class="steps" id="steps">
        {TEST_POSITIONS.map((p, i) => {
          const cls = i < t.done ? 'ok' : t.state === 'run' ? 'run' : t.state === 'fail' && i === t.done ? 'bad' : ''
          return <div class={`step ${cls}`}><b>{i + 1}</b><span>{p.x},{p.y}</span><span>{cls === 'ok' ? '✓' : cls === 'bad' ? '✕' : cls === 'run' ? '…' : '·'}</span></div>
        })}
      </div>
      {t.state === 'ok' && <div class="result ok" id="testResult">APROBADO<small>{t.msg} ({(t.durationMs / 1000).toFixed(1)} s)</small></div>}
      {t.state === 'fail' && <div class="result fail" id="testResult">FALLÓ<small>{t.msg.replace(/^FALLÓ:\s*/, '')}</small></div>}
      {t.state === 'run' && <p class="msg wait" role="status">Probando esquinas y centro… espera el resultado del módulo.</p>}
      {t.state === 'idle' && <p class="sub" style={{ textAlign: 'center' }}>Esquinas y centro, ~12 s en el módulo real. Es lo primero que revisa el profesor.</p>}
      <div class="grid2" style={{ marginTop: '10px' }}>
        <button type="button" class="btn pri" id="bTest" disabled={!on || app.busy.value} onClick={() => void app.runTest()}>{t.state === 'run' ? 'PROBANDO…' : 'INICIAR TEST'}</button>
        <button type="button" class="btn" style={{ background: 'var(--stop)', color: '#fff', borderColor: 'var(--stop)' }} onClick={() => void app.stop()}>STOP</button>
      </div>
      {!on && <p class="sub" style={{ marginTop: '8px', textAlign: 'center' }}>Conecta el módulo para poder probarlo.</p>}
    </section>
  )
}

function Calibration() {
  const d = calDraft.value
  const set = (i: number, v: string) => { const n = [...calDraft.value]; n[i] = v; calDraft.value = n }
  const vals = () => ({ x: Number(d[0]), y: Number(d[1]), h: Number(d[2]), panTrim: Number(d[3]), tiltTrim: Number(d[4]) })
  const on = app.connected.value
  return (
    <details class="card" id="cal">
      <summary>Avanzado · calibración</summary>
      <div class="calgrid">
        {CAL_RANGES.map((r, i) => {
          const n = Number(d[i])
          const bad = d[i] === '' || !Number.isFinite(n) || n < r.min || n > r.max
          return (
            <label>{r.label} ({r.unit})
              <input type="number" step="any" inputMode="decimal" value={d[i]} class={bad ? 'bad' : ''} aria-invalid={bad} onInput={e => set(i, (e.currentTarget as HTMLInputElement).value)} />
              <small>{r.min} … {r.max}</small>
            </label>
          )
        })}
      </div>
      <div class="grid2">
        <button type="button" class="btn sm" disabled={!on} onClick={() => void app.calShow()}>LEER (CAL SHOW)</button>
        <button type="button" class="btn sm" disabled={!on} onClick={() => void app.calSet(vals())}>APLICAR (SET)</button>
        <button type="button" class="btn sm" disabled={!on} onClick={() => void app.calSave()}>GUARDAR (SAVE)</button>
        <button type="button" class="btn sm warn" disabled={!on} onClick={() => void app.calReset()}>RESTABLECER</button>
      </div>
      <p class="sub" style={{ marginTop: '10px' }} role="status" aria-live="polite">{app.calMsg.value}</p>
    </details>
  )
}

export function Enlace() {
  useEffect(() => { if (!app.connected.value) void app.refreshPeers(showAll.value) }, [app.kind.value])
  const k = app.kind.value
  return (
    <>
      <div class="seg" role="group" aria-label="Tipo de enlace">
        {KINDS.map(x => <button type="button" id={`k-${x}`} aria-pressed={k === x} onClick={() => { void app.setKind(x).then(() => app.refreshPeers(showAll.value)) }}>{KIND_LABEL[x]}</button>)}
      </div>
      {k === 'wifi' && <div class="notice"><span>Wi-Fi de mantenimiento: conecta el celular a la red <b>DUELO-A-MANT</b> y vuelve aquí. El STOP espera a que termine el disparo.</span></div>}
      {k === 'sim' && <div class="notice"><span>Módulo simulado: practica sin hardware (responde como el real).</span></div>}
      <Modules />
      <TestCard />
      <Calibrar />
      <details class="card">
        <summary>Guía · emparejar y renombrar</summary>
        <ol>
          <li>Enciende el módulo (el nombre aparece como <b>SONAR-A</b> o <b>SONAR-B</b>).</li>
          <li>Ajustes del celular → Bluetooth → empareja con el módulo (sin PIN o 1234).</li>
          <li>Vuelve aquí, pulsa <b>Buscar</b> y <b>Conectar</b>. El Bluetooth clásico atiende a <b>un solo</b> celular a la vez.</li>
          <li>Para renombrarlo (regla 7 del profesor) cambia <code>DEVICE_NAME</code> en el firmware, vuelve a cargarlo y en el celular «olvida» el dispositivo antes de emparejar otra vez.</li>
        </ol>
      </details>
      <Calibration />
    </>
  )
}
