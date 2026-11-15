import { signal } from '@preact/signals'

export type Tab = 'batalla' | 'flota' | 'enlace' | 'partida'
export const tab = signal<Tab>('batalla')
export const toast = signal('')
let timer: ReturnType<typeof setTimeout> | undefined
export function say(text: string, ms = 2200): void {
  toast.value = text
  clearTimeout(timer)
  timer = setTimeout(() => { toast.value = '' }, ms)
}

/** Copia texto al portapapeles; si no hay API, usa un textarea temporal. */
export async function copyText(text: string): Promise<boolean> {
  try { await navigator.clipboard.writeText(text); return true } catch { /* sigue */ }
  try {
    const ta = document.createElement('textarea')
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    return ok
  } catch { return false }
}

export async function shareText(title: string, text: string): Promise<boolean> {
  try {
    if (navigator.share) { await navigator.share({ title, text }); return true }
  } catch { return false }
  return copyText(text)
}

export function download(name: string, mime: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mime }))
  const a = document.createElement('a')
  a.href = url; a.download = name
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}
