/** Acto 2 · recorrido de la interfaz con pantallas SIMULADAS (no usan el DOM real de la app: otro equipo
 *  las está reescribiendo). Cada pantalla vive en un marco de celular de 220×452 que se escala con `--k`. */
import type { ComponentChildren } from 'preact'
import { UbicarBoard } from './act1'
import { Board, FLEET, Ship, t } from './util'

type TabId = 'batalla' | 'flota' | 'enlace' | 'partida'
const TABS: [TabId, string][] = [['batalla', 'Batalla'], ['flota', 'Mi flota'], ['enlace', 'Enlace'], ['partida', 'Partida']]

/** Anillo pulsante que resalta el elemento padre (que debe tener `.rel`). */
const Ring = ({ o, l = 0.22 }: { o: number; l?: number }) => <i class="ring2 an ringa" style={t(o, l)} />

function Phone({ tab, pill, children }: { tab: TabId; pill?: ComponentChildren; children: ComponentChildren }) {
  return (
    <div class="phbox">
      <div class="ph">
        <div class="pscr">
          <div class="ptop">
            <svg class="pmark" viewBox="0 0 32 32"><circle cx={16} cy={16} r={12} /><circle cx={16} cy={16} r={6.5} /><path d="M16 16V4" /></svg>
            <b>SONAR</b>
            <span class="ppill">{pill ?? <span class="pl off">Sin enlace</span>}</span>
          </div>
          <div class="pbody">{children}</div>
          <div class="ptabs">
            {TABS.map(([id, label]) => <span key={id} class={id === tab ? 'act' : ''}><i />{label}</span>)}
          </div>
        </div>
      </div>
    </div>
  )
}

/** Radar simulado: cuadrícula 20×20, barrido y retícula en (10,15). */
function Radar({ dim = false, shot = false }: { dim?: boolean; shot?: boolean }) {
  return (
    <Board cls={`radar ${dim ? 'dim' : ''}`}>
      <g class="lp sweepg"><path class="sweepw" d="M100 100L100 -10A110 110 0 0 1 178 22Z" /></g>
      <path class="reticle" d="M105 0V200M0 155H200" />
      <rect class="cellx" x={100} y={150} width={10} height={10} />
      <circle class="dotx" cx={105} cy={155} r={2.6} />
      {shot && <circle class="ripx an ripple" style={t(0.62, 0.22)} cx={105} cy={155} r={7} />}
    </Board>
  )
}

/** 1 · Enlace: elegir SONAR-A y conectar. */
export function UiEnlace() {
  const pill = (
    <>
      <span class="pl off an fadeout" style={t(0.58, 0.04)}>Sin enlace</span>
      <span class="pl on an fade" style={t(0.6, 0.05)}><u />SONAR-A · 42 ms</span>
    </>
  )
  return (
    <div class="sc"><Phone tab="enlace" pill={pill}>
      <div class="pcard">
        <h4>Módulos SONAR</h4>
        <div class="peer rel">SONAR-A<small>emparejado</small><i class="selbg an fade" style={t(0.28, 0.05)} /><Ring o={0.04} l={0.3} /></div>
        <div class="peer">SONAR-B<small>emparejado</small></div>
        <div class="peer">HC-05<small>otro equipo</small></div>
      </div>
      <div class="pbtn pri rel">CONECTAR<i class="kpo an kpress" style={t(0.5, 0.1)} /><Ring o={0.4} l={0.22} /></div>
      <div class="pcard an rise" style={t(0.62, 0.1)}><h4>Estado</h4><div class="live"><u />Conectado · latido 42 ms</div></div>
      <div class="pcard"><h4>Guía de emparejado</h4><p class="hint">1. Empareja SONAR-A en Ajustes → Bluetooth.<br />2. Vuelve aquí y toca CONECTAR.<br />3. Haz el TEST antes de jugar.</p></div>
    </Phone></div>
  )
}

const STEPS = [[2, 2], [17, 2], [10, 10], [2, 17], [17, 17]]
/** 2 · Enlace: TEST de 5 posiciones. */
export function UiEnlaceTest() {
  return (
    <div class="sc"><Phone tab="enlace" pill={<span class="pl on"><u />SONAR-A · 41 ms</span>}>
      <div class="pbtn pri rel">TEST · 5 posiciones<i class="kpo an kpress" style={t(0.24, 0.1)} /><Ring o={0.04} l={0.22} /></div>
      <div class="pcard rel">
        <h4>Posiciones</h4>
        {STEPS.map(([x, y], i) => (
          <div class="step" key={i}>
            <span class="sti"><i class="so" /><i class="sk an pop" style={t(0.34 + i * 0.1, 0.06)}>✓</i></span>
            Posición {i + 1}<small>({x},{y})</small>
          </div>
        ))}
        <div class="pbar"><i class="an grow" style={t(0.3, 0.55)} /></div>
        <Ring o={0.38} l={0.45} />
      </div>
      <div class="result an pop rel" style={t(0.86, 0.1)}>TEST APROBADO<Ring o={0.88} l={0.1} /></div>
    </Phone></div>
  )
}

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '←', '0', 'OK']
/** 3 · Batalla: radar, teclado, DISPARAR y STOP. */
export function UiBatalla() {
  return (
    <div class="sc"><Phone tab="batalla" pill={<span class="pl on"><u />SONAR-A · 40 ms</span>}>
      <div class="rel"><Radar shot /><Ring o={0.03} l={0.24} /></div>
      <div class="xy"><span>x <b class="an fade" style={t(0.33, 0.04)}>10</b></span><span>y <b class="an fade" style={t(0.45, 0.04)}>15</b></span></div>
      <div class="mkp rel">
        {KEYS.map(k => <b key={k}>{k}{(k === '1' || k === '0' || k === '5') && <i class="kpo an kpress" style={t(k === '1' ? 0.33 : k === '0' ? 0.4 : 0.47, 0.06)} />}</b>)}
        <Ring o={0.3} l={0.24} />
      </div>
      <div class="prow">
        <div class="pbtn pri rel grow2">DISPARAR (10,15)<i class="kpo an kpress" style={t(0.62, 0.08)} /><Ring o={0.56} l={0.2} /></div>
        <div class="pbtn stop rel">STOP<Ring o={0.78} l={0.18} /></div>
      </div>
    </Phone></div>
  )
}

/** 4 · La pausa antes del impacto con SÍ LE DIO / NO LE DIO. */
export function UiVeredicto() {
  return (
    <div class="sc"><Phone tab="batalla" pill={<span class="pl on"><u />SONAR-A · 40 ms</span>}>
      <Radar dim />
      <div class="pause an rise" style={t(0.04, 0.1)}>
        <h4>PAUSA · antes del impacto</h4>
        <p>¿Le dio a la coordenada (10,15)?</p>
        <div class="prow">
          <div class="pbtn hitb rel">SÍ LE DIO<i class="kpo an kpress" style={t(0.4, 0.08)} /><Ring o={0.18} l={0.3} /></div>
          <div class="pbtn missb rel">NO LE DIO<i class="kpo an kpress" style={t(0.74, 0.08)} /><Ring o={0.53} l={0.3} /></div>
        </div>
      </div>
    </Phone></div>
  )
}

/** 5 · Ubica el barco arrastrando el dedo. */
export function UiUbicar() {
  return (
    <div class="sc"><Phone tab="batalla" pill={<span class="pl on"><u />SONAR-A · 40 ms</span>}>
      <div class="pcard"><h4>Ubica el barco</h4><p class="hint">Arrastra sobre sus casillas · largo 4</p></div>
      <div class="rel"><UbicarBoard /><Ring o={0.06} l={0.62} /></div>
      <div class="prow">
        <div class="pbtn pri rel an pop" style={t(0.72, 0.08)}>LISTO<Ring o={0.72} l={0.26} /></div>
        <div class="pbtn">No sé / después</div>
      </div>
    </Phone></div>
  )
}

const LISTA = [['Submarino 1', '(2,3)→(5,3)'], ['Submarino 2', '(14,11)→(14,14)'], ['Bote 1', '(13,4)→(14,4)'], ['Bote 2', '(5,8)→(5,9)'], ['Bote 3', '(9,14)→(10,14)']]
/** 6 · Mi flota: colocar y lista de coordenadas. */
export function UiFlota() {
  return (
    <div class="sc"><Phone tab="flota" pill={<span class="pl on"><u />SONAR-A · 40 ms</span>}>
      <div class="rel">
        <Board cls="mini">{FLEET.map((s, i) => <g class="an fall" style={t(0.04 + i * 0.05, 0.14)} key={i}><Ship s={s} /></g>)}</Board>
        <Ring o={0.03} l={0.32} />
      </div>
      <div class="pbtn">Aleatoria</div>
      <div class="pcard rel">
        <h4>Coordenadas para armar el tablero</h4>
        {LISTA.map(([n, c], i) => <div class="lrow an rise" style={t(0.46 + i * 0.07, 0.08)} key={n}>{n}<small>{c}</small></div>)}
        <Ring o={0.44} l={0.5} />
      </div>
    </Phone></div>
  )
}

const BIT = [['17:02:11', '→', '(10,15)'], ['17:02:14', '←', 'SÍ LE DIO'], ['17:03:40', '→', '(6,10)'], ['17:03:43', '←', 'NO LE DIO']]
/** 7 · Partida: estadísticas, bitácora y «Ver tutorial». */
export function UiPartida() {
  return (
    <div class="sc"><Phone tab="partida" pill={<span class="pl on"><u />SONAR-A · 40 ms</span>}>
      <div class="pcard rel">
        <h4>Estadísticas</h4>
        <div class="stg"><div><b>12</b>Disparos</div><div><b>5</b>Aciertos</div><div><b>7</b>Agua</div><div><b>42%</b>Precisión</div><div><b>3</b>Racha</div><div><b>4,1s</b>Veredicto</div></div>
        <Ring o={0.06} l={0.26} />
      </div>
      <div class="pcard rel">
        <h4>Bitácora</h4>
        {BIT.map(([h, d, x], i) => <div class="brow an rise" style={t(0.36 + i * 0.06, 0.08)} key={i}><time>{h}</time>{d} {x}</div>)}
        <Ring o={0.34} l={0.32} />
      </div>
      <div class="pbtn rel">Ver tutorial<Ring o={0.7} l={0.28} /></div>
    </Phone></div>
  )
}
