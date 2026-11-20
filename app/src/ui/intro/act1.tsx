/** Acto 1 · la dinámica del juego. Cada escena es un componente; el movimiento es CSS (transform/opacity)
 *  coreografiado con fracciones de la duración de la escena (ver `t(o, l)` y `.an` en intro.css). */
import { Board, cc, FLEET, Ship, t, type ShipDef } from './util'

const TX = 10; const TY = 15 // coordenada del ejemplo: (10, 15)

/** 1 · La flota cae y se acomoda. */
export function EscFlota() {
  return (
    <div class="sc">
      <div class="tag an rise" style={t(0, 0.08)}>TABLERO 20 × 20</div>
      <Board>
        {FLEET.map((s, i) => (
          <g class="an fall" style={t(0.1 + i * 0.1, 0.2)}><Ship s={s} /></g>
        ))}
      </Board>
      <div class="legend">
        <span class="an rise" style={t(0.52, 0.1)}><i class="sw bote" />× 3 · 2 casillas</span>
        <span class="an rise" style={t(0.62, 0.1)}><i class="sw sub" />× 2 · 4 casillas</span>
      </div>
    </div>
  )
}

const Wave = ({ o }: { o: number }) => (
  <path class="wave lp" style={`--dl:${-o}s`} d="M112 62Q130 95 112 128" />
)
const WaveL = ({ o }: { o: number }) => (
  <path class="wave lp rev" style={`--dl:${-o}s`} d="M188 62Q170 95 188 128" />
)

/** 2 · Cada equipo tiene su tablero; el rival lo maneja por Bluetooth. */
export function EscBluetooth() {
  return (
    <div class="sc">
      <svg class="bd wide" viewBox="8 12 284 168" aria-hidden="true">
        <g class="an pop" style={t(0.02, 0.12)}>
          <rect class="phn" x={18} y={38} width={62} height={112} rx={11} />
          <rect class="phs" x={23} y={46} width={52} height={92} rx={6} />
          <circle class="phd" cx={49} cy={92} r={14} />
          <path class="phx" d="M49 74V110M31 92H67" />
        </g>
        <text class="lbl" x={49} y={168}>CELULAR RIVAL</text>
        <g class="an pop" style={t(0.12, 0.12)}>
          <rect class="mod" x={206} y={38} width={80} height={112} rx={7} />
          <path class="bdgrid" d="M214 54H278M214 70H278M214 86H278M214 102H278M214 118H278M214 134H278M222 46V142M238 46V142M254 46V142M270 46V142" />
          <g class="an fall" style={t(0.3, 0.2)}><rect class="shp sub" x={223} y={103} width={32} height={14} rx={3.5} /></g>
          <circle class="led" cx={276} cy={44} r={2.6} />
        </g>
        <text class="lbl" x={246} y={168}>TU TABLERO</text>
        <g class="an fade" style={t(0.3, 0.1)}>
          <Wave o={0} /><Wave o={0.5} /><Wave o={1} />
          <WaveL o={0.25} /><WaveL o={0.75} />
        </g>
        <g class="an pop" style={t(0.4, 0.1)}>
          <rect class="chip" x={113} y={20} width={74} height={20} rx={10} />
          <text class="lbl mono" x={150} y={33.5}>SONAR-A</text>
        </g>
        <path class="dash an draw" pathLength={1} style={t(0.34, 0.25)} d="M82 150H204" />
        <text class="lbl dim an fade" style={t(0.6, 0.1)} x={150} y={170}>Bluetooth</text>
      </svg>
    </div>
  )
}

const TEST_PTS: [number, number][] = [[2, 2], [17, 2], [10, 10], [2, 17], [17, 17]]
/** 3 · El TEST de 5 posiciones. */
export function EscTest() {
  return (
    <div class="sc">
      <Board vb="0 0 200 232">
        {TEST_PTS.map(([cx, cy], i) => {
          const o = 0.12 + i * 0.145
          return (
            <g key={i} transform={`translate(${cc(cx)} ${cc(cy)})`}>
              <circle class="an ripple ringe tr" style={t(o, 0.2)} r={8} />
              <circle class="an pop dotl" style={t(o, 0.08)} r={4} />
              <path class="an draw chk" pathLength={1} style={t(o + 0.05, 0.08)} d="M-2.6 .2L-.6 2.4L3 -2.4" />
            </g>
          )
        })}
        <g transform="translate(0 0)">
          {TEST_PTS.map((_, i) => (
            <g key={i}>
              <circle class="slot" cx={60 + i * 20} cy={214} r={6} />
              <circle class="an pop okd" style={t(0.17 + i * 0.145, 0.08)} cx={60 + i * 20} cy={214} r={6} />
              <path class="an draw chk2" pathLength={1} style={t(0.2 + i * 0.145, 0.07)} d={`M${57.2 + i * 20} 214.2L${59 + i * 20} 216.2L${62.6 + i * 20} 211.8`} />
            </g>
          ))}
          <text class="lbl ok an pop" style={t(0.84, 0.1)} x={100} y={230}>TEST APROBADO</text>
        </g>
      </Board>
    </div>
  )
}

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '←', '0', 'OK']
const PRESS: Record<string, number[]> = { '1': [0.22, 0.57], '0': [0.32], '5': [0.67], OK: [0.78] }
/** 4 · El profesor escribe X y luego Y. */
export function EscCoordenada() {
  return (
    <div class="sc">
      <div class="who an rise" style={t(0, 0.08)}>PROFESOR · ATACANTE</div>
      <div class="coord">
        <div class="fld"><small>X</small>
          <b><span class="an fade" style={t(0.22, 0.03)}>1</span><span class="an fade" style={t(0.32, 0.03)}>0</span><em class="cur" /></b>
          <i class="fa an ring" style={t(0.08, 0.4)} />
        </div>
        <div class="fld"><small>Y</small>
          <b><span class="an fade" style={t(0.57, 0.03)}>1</span><span class="an fade" style={t(0.67, 0.03)}>5</span><em class="cur" /></b>
          <i class="fa an ring" style={t(0.44, 0.4)} />
        </div>
      </div>
      <div class="kp">
        {KEYS.map(k => (
          <b key={k} class={`key ${k === 'OK' ? 'okk' : ''}`}>{k}
            {(PRESS[k] ?? []).map(o => <i class="kpo an kpress" style={t(o, 0.09)} />)}
          </b>
        ))}
      </div>
      <div class="big an pop" style={t(0.82, 0.1)}>({TX}, {TY})</div>
    </div>
  )
}

/** 5 · El láser cae en la coordenada del tablero real. */
export function EscLaser() {
  return (
    <div class="sc">
      <Board vb="0 0 200 230">
        <g class="an fallup" style={t(0, 0.12)}>
          <rect class="tur" x={88} y={212} width={24} height={14} rx={4} />
          <circle class="turl" cx={100} cy={212} r={3.4} />
        </g>
        <line class="beamg an draw" pathLength={1} style={t(0.25, 0.2)} x1={100} y1={212} x2={cc(TX)} y2={cc(TY)} />
        <line class="beam an draw" pathLength={1} style={t(0.25, 0.2)} x1={100} y1={212} x2={cc(TX)} y2={cc(TY)} />
        <rect class="cellx an pop" style={t(0.45, 0.1)} x={TX * 10} y={TY * 10} width={10} height={10} />
        <circle class="dotx an pop" style={t(0.45, 0.08)} cx={cc(TX)} cy={cc(TY)} r={2.6} />
        <circle class="ripx an ripple lp" style={`--w:1.6s`} cx={cc(TX)} cy={cc(TY)} r={6} />
        <g class="an pop" style={t(0.55, 0.12)}>
          <rect class="tagbg" x={118} y={141} width={44} height={15} rx={7.5} />
          <text class="lbl mono" x={140} y={151.4}>({TX}, {TY})</text>
        </g>
      </Board>
    </div>
  )
}

const PARTS = Array.from({ length: 14 }, (_, i) => {
  const a = (i / 14) * Math.PI * 2 + 0.2
  const r = i % 2 ? 34 : 22
  return { dx: Math.round(Math.cos(a) * r), dy: Math.round(Math.sin(a) * r), hot: i % 3 === 0 }
})

function Students({ text, cls }: { text: string; cls: string }) {
  return (
    <g>
      <g class="an pop" style={t(0, 0.12)}>
        <circle class="stu" cx={70} cy={241} r={6} /><path class="stu" d="M60 258Q70 244 80 258Z" />
        <circle class="stu" cx={130} cy={241} r={6} /><path class="stu" d="M120 258Q130 244 140 258Z" />
      </g>
      <g class="an pop" style={t(0.14, 0.14)}>
        <path class={`bub ${cls}`} d="M30 204H170Q176 204 176 210V226Q176 232 170 232H110L100 238L96 232H30Q24 232 24 226V210Q24 204 30 204Z" />
        <text class={`lbl big2 ${cls}`} x={100} y={223}>{text}</text>
      </g>
    </g>
  )
}

/** 6a / 6b · Veredicto de los estudiantes: explosión o gota de agua. */
export function EscDuelo({ hit }: { hit: boolean }) {
  const ships: ShipDef[] = hit ? [{ k: 'sub', x: TX, y: TY - 3, w: 1, h: 4 }, FLEET[0]!] : [FLEET[0]!, FLEET[3]!, FLEET[4]!]
  return (
    <div class="sc">
      <Board vb="0 0 200 262">
        {ships.map((s, i) => <g class="an fade" style={t(0, 0.1)} key={i}><Ship s={s} cls="ghost" /></g>)}
        <rect class="cellx" x={TX * 10} y={TY * 10} width={10} height={10} />
        <circle class="dotx" cx={cc(TX)} cy={cc(TY)} r={2.2} />
        <Students text={hit ? '¡Le dio!' : 'No le dio'} cls={hit ? 'hit' : 'miss'} />
        {hit ? (
          <g transform={`translate(${cc(TX)} ${cc(TY)})`}>
            <rect class="an pop hitc" style={t(0.58, 0.1)} x={-5} y={-5} width={10} height={10} />
            <circle class="an flash tr" style={t(0.55, 0.18)} r={5} />
            <circle class="an ripple ringh tr" style={t(0.55, 0.3)} r={6} />
            {PARTS.map((p, i) => (
              <circle key={i} class={`an burst tr ${p.hot ? 'w' : 'h'}`} style={`--o:.55;--l:.3;--dx:${p.dx}px;--dy:${p.dy}px`} r={1.7} />
            ))}
          </g>
        ) : (
          <g transform={`translate(${cc(TX)} ${cc(TY)})`}>
            <g class="an drop tr" style={t(0.5, 0.14)}><path class="drp" d="M0 -5C3 -1 4 1.5 0 3.5C-4 1.5 -3 -1 0 -5Z" /></g>
            <circle class="an ripple ringw tr" style={t(0.62, 0.22)} r={6} />
            <circle class="an ripple ringw tr" style={t(0.7, 0.22)} r={6} />
            <circle class="an ripple ringw tr" style={t(0.78, 0.22)} r={6} />
            <circle class="an pop waterm" style={t(0.7, 0.1)} r={3.2} />
          </g>
        )}
      </Board>
    </div>
  )
}

/** Tablero ampliado con el dedo trazando el barco de (10,15) a (10,12). Compartido con el Acto 2. */
export function UbicarBoard() {
  const rows = [15, 14, 13, 12]
  return (
    <Board vb="50 90 100 100" cls="zoom">
      <rect class="cellx" x={TX * 10} y={TY * 10} width={10} height={10} />
      <rect class="hitc" x={TX * 10 + 1.5} y={TY * 10 + 1.5} width={7} height={7} rx={2} />
      {rows.map((r, i) => (
        <rect key={r} class="an pop selc" style={t(0.27 + i * 0.12, 0.08)} x={TX * 10 + 0.6} y={r * 10 + 0.6} width={8.8} height={8.8} rx={2} />
      ))}
      <rect class="an fade shapeo" style={t(0.7, 0.1)} x={TX * 10 - 1} y={12 * 10 - 1} width={12} height={42} rx={4} />
      <g transform={`translate(${cc(TX)} ${cc(TY)})`}>
        <g class="an fade" style={t(0.08, 0.12)}>
          <g class="an drag" style={t(0.26, 0.44)}>
            <circle class="halo" r={9} /><circle class="tip" r={3.6} />
          </g>
        </g>
      </g>
      <text class="lbl mono start an fade" style={t(0.1, 0.1)} x={cc(TX) + 8} y={cc(TY) + 3}>(10,15)</text>
      <text class="lbl mono start an fade" style={t(0.66, 0.1)} x={cc(TX) + 8} y={12 * 10 + 8}>(10,12)</text>
    </Board>
  )
}

/** 7 · Ubicar el barco arrastrando el dedo. */
export function EscUbicar() {
  return (
    <div class="sc">
      <UbicarBoard />
      <div class="btnrow">
        <span class="btnx pri an pop" style={t(0.78, 0.1)}>LISTO</span>
      </div>
    </div>
  )
}

const CONF = Array.from({ length: 24 }, (_, i) => ({
  x: 8 + ((i * 53) % 184), dx: ((i * 37) % 41) - 20, c: i % 4, o: 0.6 + (i % 6) * 0.02,
}))
/** 8 · Victoria: la flota entera hundida. */
export function EscVictoria() {
  return (
    <div class="sc">
      <Board>
        {FLEET.map((s, i) => <g class="an pop" style={t(0.06 + i * 0.1, 0.1)} key={i}><Ship s={s} cls="sunk" /></g>)}
        <g class="an pop" style={t(0.58, 0.14)}>
          <rect class="banner" x={14} y={78} width={172} height={50} rx={10} />
          <text class="victory" x={100} y={104}>¡VICTORIA!</text>
          <text class="lbl mono" x={100} y={120}>14 / 14 casillas</text>
        </g>
        {CONF.map((c, i) => (
          <circle key={i} class={`an conf tr c${c.c}`} style={`--o:${c.o};--l:.38;--dx:${c.dx}px`} cx={c.x} cy={-6} r={2} />
        ))}
      </Board>
    </div>
  )
}
