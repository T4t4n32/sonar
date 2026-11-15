/** Estado del tutorial: `introSeen` y preferencias, con persistencia tolerante a fallos (no toca store.ts). */
import { signal } from '@preact/signals'
import type { IntroMode } from '../ui/intro/guion'
import { loadJSON, localKV, saveJSON, type KV } from './storage'

export type { IntroMode }
/** Tutorial abierto (null = cerrado). */
export const introOpen = signal<IntroMode | null>(null)
/** El splash ya terminó: el tutorial puede mostrarse. */
export const introReady = signal(false)

const MODES: IntroMode[] = ['ambos', 'acto1', 'acto2']
export const isMode = (v: unknown): v is IntroMode => typeof v === 'string' && (MODES as string[]).includes(v)

export function isIntroSeen(kv: KV = localKV()): boolean { return kv.get('introSeen') === '1' }
export function markIntroSeen(kv: KV = localKV()): void { try { kv.set('introSeen', '1') } catch { /* nada */ } }

/** Modo elegido la última vez en «Ver tutorial». */
export const replayMode = signal<IntroMode>(((): IntroMode => {
  const v = loadJSON<{ mode?: unknown }>(localKV(), 'introPrefs', {}).mode
  return isMode(v) ? v : 'ambos'
})())
export function setReplayMode(m: IntroMode, kv: KV = localKV()): void { replayMode.value = m; saveJSON(kv, 'introPrefs', { mode: m }) }

/** Primera vez: abre el tutorial completo. */
export function initIntro(kv: KV = localKV()): boolean {
  if (isIntroSeen(kv)) return false
  introOpen.value = 'ambos'
  return true
}
export function openIntro(mode: IntroMode = 'ambos'): void { introOpen.value = mode }
export function closeIntro(kv: KV = localKV()): void { markIntroSeen(kv); introOpen.value = null }

/** `?introSpeed=20` acelera el tiempo (pruebas e2e). 1 por defecto; acotado a 0,25..60. */
export function introSpeed(search: string = typeof location === 'undefined' ? '' : location.search): number {
  const n = Number(new URLSearchParams(search).get('introSpeed'))
  return Number.isFinite(n) && n > 0 ? Math.min(60, Math.max(0.25, n)) : 1
}
export function prefersReducedMotion(): boolean {
  try { return !!globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches } catch { return false }
}
/** El sonido del tutorial respeta el ajuste global y se apaga con movimiento reducido. */
export function introSound(kv: KV = localKV()): boolean {
  return !prefersReducedMotion() && loadJSON<{ sound?: boolean }>(kv, 'settings', {}).sound !== false
}
