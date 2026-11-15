import { useState } from 'preact/hooks'

export type Axis = 'x' | 'y'
/** Entrada rápida «x» «y»: dos casillas grandes con ±1 y teclado numérico. Avanza sola de x a y. */
export function CoordPad(p: { x: number | null; y: number | null; onAxis: (a: Axis, v: number | null) => void; onNudge: (a: Axis, d: number) => void }) {
  const [active, setActive] = useState<Axis>('x')
  const [typing, setTyping] = useState(false)
  const [buf, setBuf] = useState('')

  const press = (d: string) => {
    let nb = typing ? buf + d : d
    if (Number(nb) > 20) nb = d
    const v = Number(nb)
    setBuf(nb); setTyping(true)
    p.onAxis(active, v >= 1 && v <= 20 ? v : null)
    if (active === 'x' && v >= 1 && (nb.length === 2 || v > 2)) { setActive('y'); setTyping(false); setBuf('') }
  }
  const back = () => {
    if (typing && buf.length > 1) { const nb = buf.slice(0, -1); setBuf(nb); p.onAxis(active, Number(nb) || null) } else { setBuf(''); setTyping(false); p.onAxis(active, null) }
  }
  const pick = (a: Axis) => { setActive(a); setTyping(false); setBuf('') }
  const field = (a: Axis, v: number | null) => (
    <div class="axis">
      <button type="button" class="step" aria-label={`${a} menos uno`} onClick={() => { p.onNudge(a, -1); pick(a) }}>−</button>
      <div class={`val ${active === a ? 'on' : ''} ${v === null ? 'none' : ''}`} id={`val-${a}`} role="button" tabIndex={0} aria-label={`Coordenada ${a}: ${v ?? 'sin valor'}. Tocar para editar con el teclado.`} onClick={() => pick(a)}>
        <small>{a.toUpperCase()}</small><b>{v ?? '—'}</b>
      </div>
      <button type="button" class="step" aria-label={`${a} más uno`} onClick={() => { p.onNudge(a, 1); pick(a) }}>+</button>
    </div>
  )
  return (
    <div>
      <div class="aim">{field('x', p.x)}{field('y', p.y)}</div>
      <div class="keypad" role="group" aria-label="Teclado numérico">
        {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map(d => <button type="button" onClick={() => press(d)}>{d}</button>)}
        <button type="button" class="aux" aria-label="Borrar" onClick={back}>⌫</button>
        <button type="button" onClick={() => press('0')}>0</button>
        <button type="button" class="aux" aria-label="Cambiar entre x e y" onClick={() => pick(active === 'x' ? 'y' : 'x')}>{active === 'x' ? 'x → y' : 'y → x'}</button>
      </div>
    </div>
  )
}
