/** Reproductor del tutorial animado (sin interacción necesaria): escenas encadenadas, subtítulos, progreso,
 *  pausa (toque largo o botón), Atrás/Siguiente (botones o deslizar), «Saltar» y «Empezar». */
import type { ComponentType } from 'preact'
import { useEffect, useMemo, useRef, useState } from 'preact/hooks'
import { introSound, introSpeed, prefersReducedMotion } from '../../state/intro'
import { playTones } from '../../state/feedback'
import '../../styles/intro.css'
import { EscBluetooth, EscCoordenada, EscDuelo, EscFlota, EscLaser, EscTest, EscUbicar, EscVictoria } from './act1'
import { UiBatalla, UiEnlace, UiEnlaceTest, UiFlota, UiPartida, UiUbicar, UiVeredicto } from './act2'
import { ACTOS, escenasDe, TXT, type IntroMode } from './guion'
import { Timeline } from './timeline'

const ESC: Record<string, ComponentType> = {
  flota: EscFlota, bluetooth: EscBluetooth, test: EscTest, coordenada: EscCoordenada, laser: EscLaser,
  ledio: () => <EscDuelo hit />, noledio: () => <EscDuelo hit={false} />, ubicar: EscUbicar, victoria: EscVictoria,
  enlace: UiEnlace, 'enlace-test': UiEnlaceTest, batalla: UiBatalla, veredicto: UiVeredicto,
  'ubicar-ui': UiUbicar, 'flota-ui': UiFlota, partida: UiPartida,
}

export function Tutorial({ mode, onDone }: { mode: IntroMode; onDone: () => void }) {
  const scenes = useMemo(() => escenasDe(mode), [mode])
  const speed = useMemo(() => introSpeed(), [])
  const rm = useMemo(() => prefersReducedMotion(), [])
  const sound = useMemo(() => introSound(), [])
  const tl = useMemo(() => new Timeline(scenes.map(s => ({ id: s.id, dur: s.dur })), { speed }), [scenes, speed])
  const root = useRef<HTMLDivElement>(null)
  const stage = useRef<HTMLDivElement>(null)
  const fired = useRef(new Set<string>())
  const [idx, setIdx] = useState(0)
  const [cap, setCap] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [ended, setEnded] = useState(false)
  const [seq, setSeq] = useState(0)

  useEffect(() => {
    const off = tl.on((s, why) => {
      const r = root.current
      if (r) { r.style.setProperty('--sp', s.progress.toFixed(4)); r.style.setProperty('--tp', tl.total.toFixed(4)) }
      const sc = scenes[s.index]!
      if (why === 'scene') { fired.current.clear(); setSeq(n => n + 1) }
      let c = 0
      sc.caps.forEach((x, i) => { if (s.progress >= x.at) c = i })
      setIdx(s.index); setCap(c); setPlaying(s.playing); setEnded(s.ended)
      if (sound && s.playing) {
        for (const [i, f] of (sc.sfx ?? []).entries()) {
          const k = `${s.index}:${i}`
          if (s.progress >= f.at && s.progress < f.at + 0.2 && !fired.current.has(k)) { fired.current.add(k); playTones(f.ev) }
        }
      }
    })
    tl.play()
    return () => { off(); tl.dispose() }
  }, [tl, scenes, sound])

  // Escala del marco de celular según el espacio disponible.
  useEffect(() => {
    const el = stage.current
    if (!el) return
    const fit = () => {
      const k = Math.max(0.5, Math.min((el.clientWidth - 8) / 220, (el.clientHeight - 6) / 452, 1.3))
      root.current?.style.setProperty('--k', k.toFixed(3))
    }
    fit()
    if (typeof ResizeObserver === 'undefined') { window.addEventListener('resize', fit); return () => window.removeEventListener('resize', fit) }
    const ro = new ResizeObserver(fit); ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') tl.next()
      else if (e.key === 'ArrowLeft') tl.prev()
      else if (e.key === ' ') { e.preventDefault(); tl.toggle() }
      else if (e.key === 'Escape') onDone()
    }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [tl, onDone])

  // Gestos: toque largo = pausa/continuar; deslizar = escena anterior/siguiente.
  const g = useRef({ x: 0, y: 0, timer: 0, long: false })
  const down = (e: PointerEvent) => {
    g.current.x = e.clientX; g.current.y = e.clientY; g.current.long = false
    window.clearTimeout(g.current.timer)
    g.current.timer = window.setTimeout(() => { g.current.long = true; tl.toggle() }, 480)
  }
  const up = (e: PointerEvent) => {
    window.clearTimeout(g.current.timer)
    if (g.current.long) return
    const dx = e.clientX - g.current.x; const dy = e.clientY - g.current.y
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.4) { if (dx < 0) tl.next(); else tl.prev() }
  }
  const cancel = () => window.clearTimeout(g.current.timer)

  const sc = scenes[idx]!
  const Esc = ESC[sc.id]
  const last = idx === scenes.length - 1
  const actScenes = scenes.filter(s => s.act === sc.act)
  const posAct = actScenes.indexOf(sc) + 1
  const frozen = !playing && !ended

  return (
    <div ref={root} class={`intro ${rm ? 'rm' : ''} ${frozen ? 'paused' : ''}`} id="intro" role="dialog" aria-label="Tutorial de SONAR" data-scene={sc.id} data-seq={seq}>
      <div class="tbar"><i /></div>
      <header class="ihead">
        <div class="ibrand"><b>{ACTOS[sc.act]}</b><span>{sc.title} · {posAct}/{actScenes.length}</span></div>
        {frozen && <span class="pbadge" aria-hidden="true">{TXT.pausado}</span>}
        <button type="button" class="iskip" id="introSkip" onClick={onDone}>{TXT.saltar}</button>
      </header>
      <div ref={stage} class="stagei" aria-label={sc.title} style={`--sd:${(sc.dur / speed).toFixed(0)}ms`}
        onPointerDown={down} onPointerUp={up} onPointerCancel={cancel} onPointerLeave={cancel}>
        <div class="scene" key={seq}>{Esc ? <Esc /> : null}</div>
      </div>
      <p class="cap" aria-live="polite" key={`${seq}:${cap}`}>{sc.caps[cap]?.text}</p>
      <div class="dots" role="presentation">
        {scenes.map((s, i) => (
          <i key={s.id} class={`${i < idx ? 'done' : ''} ${i === idx ? 'cur' : ''} ${i > 0 && s.act !== scenes[i - 1]!.act ? 'gap' : ''}`}><b /></i>
        ))}
      </div>
      <nav class="ictl" aria-label="Controles del tutorial">
        <button type="button" class="ibtn" id="introPrev" onClick={() => tl.prev()}>{TXT.atras}</button>
        <button type="button" class="ibtn mid" id="introPause" aria-pressed={frozen} onClick={() => tl.toggle()}>{ended ? '↺' : frozen ? TXT.seguir : TXT.pausa}</button>
        {last || ended
          ? <button type="button" class="ibtn pri" id="introGo" onClick={onDone}>{TXT.empezar}</button>
          : <button type="button" class="ibtn" id="introNext" onClick={() => tl.next()}>{TXT.siguiente}</button>}
      </nav>
    </div>
  )
}
