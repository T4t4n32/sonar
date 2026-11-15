import { effect, signal } from '@preact/signals'
import { FLEET_SPEC } from '../../core/types'
import { app } from '../../state'
import { FleetBoard } from '../Board'
import { copyText, say, shareText, tab } from '../nav'
import { HoldButton } from '../parts'

const editing = signal(false)
const revealFleet = signal(false)

// La flota nunca queda a la vista sola (el celular lo usa el profesor): al salir de la pestaña o minimizar, todo se oculta.
effect(() => { if (tab.value !== 'flota') { editing.value = false; revealFleet.value = false } })
if (typeof document !== 'undefined') document.addEventListener('visibilitychange', () => { if (document.hidden) { editing.value = false; revealFleet.value = false } })

function Fleet() {
  const ed = editing.value
  const show = ed || revealFleet.value
  const v = app.validation.value
  const ships = app.fleet.value
  const sel = app.selected.value
  const text = app.fleetText()
  return (
    <section class="card" aria-label="Mi flota">
      <div class="cardhead"><h2>Mi flota · 20×20</h2><span class="sub">{ships.length}/5 colocados</span></div>
      <FleetBoard edit={ed} reveal={revealFleet.value} />
      {!ed && (
        <div style={{ display: 'grid', gap: '8px', marginTop: '12px' }}>
          <HoldButton id="bSeeFleet" class="warn" label="Mantén pulsado: Ver flota" onHold={on => { revealFleet.value = on }} />
          <HoldButton id="bEdit" completeMs={800} label="Mantén 0,8 s para editar la flota" onComplete={() => { editing.value = true }} />
        </div>
      )}
      {ed && (
        <div style={{ display: 'grid', gap: '10px', marginTop: '12px' }}>
          <div class="shiplist" role="group" aria-label="Barcos">
            {FLEET_SPEC.map(f => {
              const placed = ships.some(s => s.id === f.id)
              return <button type="button" class={sel === f.id ? 'se' : placed ? 'pl' : ''} onClick={() => { if (placed) app.selected.value = sel === f.id ? null : f.id; else say('Toca una casilla libre para colocarlo.') }}>{f.id} · {f.len}</button>
            })}
          </div>
          <p class="sub">Toca una casilla para colocar el siguiente barco · arrastra un barco para moverlo · {sel ? `seleccionado: ${sel}` : `orientación: ${app.orientPref.value === 'H' ? 'horizontal' : 'vertical'}`}</p>
          <div class="grid2">
            <button type="button" class="btn sm" id="bRotate" onClick={() => app.rotateSelected()}>Rotar</button>
            <button type="button" class="btn sm warn" id="bRemove" disabled={!sel} onClick={() => app.removeSelected()}>Quitar</button>
            <button type="button" class="btn sm" id="bRandom" onClick={() => app.randomizeFleet()}>Aleatoria</button>
            <button type="button" class="btn sm" id="bClear" onClick={() => app.clearFleet()}>Vaciar</button>
          </div>
          <button type="button" class="btn pri" id="bDone" onClick={() => { editing.value = false; app.selected.value = null }}>Listo, ocultar flota</button>
        </div>
      )}
      <div style={{ marginTop: '12px' }} id="validation">
        {ships.length === 0 ? <div class="empty"><b>Sin flota todavía</b>Mantén pulsado «editar» y usa Aleatoria o toca el tablero.</div>
          : v.ok ? <div class="okbox">Flota válida: 3 embarcaciones de 2 + 2 submarinos de 4 (14 casillas).</div>
          : <ul class="issues">{v.issues.map(i => <li>{i.message}</li>)}</ul>}
      </div>
      {show && ships.length > 0 && (
        <div style={{ marginTop: '12px', display: 'grid', gap: '8px' }}>
          <div class="cardhead" style={{ marginBottom: 0 }}><h2>Para colocar las piezas físicas</h2></div>
          <pre class="pre" id="coords">{text}</pre>
          {ed && (
            <div class="grid2">
              <button type="button" class="btn sm" onClick={async () => say((await copyText(text)) ? 'Coordenadas copiadas.' : 'No se pudo copiar.')}>Copiar</button>
              <button type="button" class="btn sm" onClick={async () => say((await shareText('Mi flota SONAR', text)) ? 'Listo.' : 'No se pudo compartir.')}>Compartir</button>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export function MiFlota() {
  return <Fleet />
}
