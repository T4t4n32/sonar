import type { ComponentChildren } from 'preact'
import { useEffect, useRef, useState } from 'preact/hooks'

/**
 * Botón de MANTENER PULSADO. Solo responde a puntero (dedo/ratón): una tecla o un gesto accidental no lo activa.
 * - sin `completeMs`: revela mientras se mantiene (onHold(true) al bajar, onHold(false) al soltar).
 * - con `completeMs`: llama onComplete al cumplirse el tiempo y vuelve a soltar.
 */
export function HoldButton(p: { label: ComponentChildren; completeMs?: number; onHold?: (on: boolean) => void; onComplete?: () => void; class?: string; label2?: string; id?: string }) {
  const [on, setOn] = useState(false)
  const live = useRef(false)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const end = () => {
    clearTimeout(timer.current)
    if (!live.current) return
    live.current = false
    setOn(false)
    p.onHold?.(false)
  }
  const start = (e: PointerEvent) => {
    if (e.button !== undefined && e.button > 0) return
    e.preventDefault()
    try { (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId) } catch { /* sin captura */ }
    live.current = true
    setOn(true)
    p.onHold?.(true)
    if (p.completeMs) timer.current = setTimeout(() => { const done = live.current; end(); if (done) p.onComplete?.() }, p.completeMs)
  }
  useEffect(() => {
    const off = () => end()
    window.addEventListener('blur', off)
    document.addEventListener('visibilitychange', off)
    return () => { window.removeEventListener('blur', off); document.removeEventListener('visibilitychange', off); end() }
  }, [])
  return (
    <button id={p.id} type="button" class={`hold ${p.completeMs ? '' : 'rev'} ${on ? 'on' : ''} ${p.class ?? ''}`} style={p.completeMs ? { '--ms': `${p.completeMs}ms` } : undefined}
      onPointerDown={start} onPointerUp={end} onPointerCancel={end} onLostPointerCapture={end} onContextMenu={e => e.preventDefault()}
      aria-label={typeof p.label === 'string' ? p.label : p.label2}>
      <span>{p.label}</span>
    </button>
  )
}

export function Toggle(p: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return <button type="button" role="switch" class="toggle" aria-checked={p.checked} aria-label={p.label} onClick={() => p.onChange(!p.checked)} />
}

export const Mark = () => (
  <svg class="mark" viewBox="0 0 32 32" aria-hidden="true">
    <circle class="arc" cx="16" cy="16" r="13" opacity=".35" /><circle class="arc" cx="16" cy="16" r="8.5" opacity=".6" />
    <g class="sw"><path d="M16 16 16 3A13 13 0 0 1 27.3 9.5Z" fill="var(--sonar)" opacity=".28" /><path class="arc" d="M16 16 16 3" /></g>
    <circle cx="16" cy="16" r="2.2" fill="var(--sonar)" />
  </svg>
)

const I = (d: string) => <svg viewBox="0 0 24 24" aria-hidden="true"><path d={d} /></svg>
export const Icons = {
  batalla: <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4.5" /><path d="M12 12 19 7" /></svg>,
  flota: <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 15h18l-2.5 4h-13z" /><path d="M7 15V9h6v6M13 11h4l1 4" /></svg>,
  enlace: <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 7 10 10-5 5V2l5 5L7 17" /></svg>,
  partida: I('M4 5h16M4 12h16M4 19h10'),
}
