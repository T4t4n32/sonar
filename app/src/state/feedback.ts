/** Sonido sintetizado (WebAudio), vibración y pantalla encendida. Todo opcional: si falta la API, se omite. */
export type FxEvent = 'disparo' | 'pausa' | 'acierto' | 'agua' | 'hundido' | 'victoria' | 'error' | 'ok' | 'tick'

/** Una voz: oscilador (f → to) o ráfaga de ruido filtrada (noise + lp). */
interface Tone { f: number; d: number; at?: number; type?: OscillatorType; g?: number; to?: number; noise?: boolean; lp?: number; lpTo?: number }
const TONES: Record<FxEvent, Tone[]> = {
  // silbido de lanzamiento: sube de tono durante el vuelo (~1,1 s)
  disparo: [
    { f: 300, to: 1700, d: 1.05, type: 'sine', g: 0.07 },
    { f: 600, to: 2600, d: 1.0, type: 'triangle', g: 0.025 },
    { f: 0, d: 1.0, noise: true, lp: 1200, lpTo: 4200, g: 0.03 },
  ],
  // el tiempo se congela: golpe grave seco
  pausa: [{ f: 140, to: 60, d: 0.22, type: 'sine', g: 0.2 }],
  // explosión grave: ruido que se apaga + retumbo
  acierto: [
    { f: 0, d: 0.9, noise: true, lp: 1800, lpTo: 140, g: 0.42 },
    { f: 120, to: 34, d: 0.75, type: 'sine', g: 0.4 },
    { f: 0, d: 0.08, noise: true, lp: 6000, g: 0.25 },
  ],
  // plop de gota: dos burbujas
  agua: [
    { f: 760, to: 190, d: 0.14, type: 'sine', g: 0.22 },
    { f: 1250, to: 420, d: 0.1, at: 0.09, type: 'sine', g: 0.1 },
    { f: 0, d: 0.3, at: 0.02, noise: true, lp: 900, lpTo: 300, g: 0.05 },
  ],
  // campana de hundido
  hundido: [
    { f: 660, d: 1.5, type: 'sine', g: 0.17 },
    { f: 990, d: 1.1, type: 'sine', g: 0.08 },
    { f: 1650, d: 0.7, type: 'sine', g: 0.05 },
    { f: 440, d: 1.2, at: 0.32, type: 'sine', g: 0.12 },
  ],
  // fanfarria de victoria
  victoria: [
    { f: 523, d: 0.16, type: 'triangle', g: 0.17 }, { f: 659, d: 0.16, at: 0.16, type: 'triangle', g: 0.17 },
    { f: 784, d: 0.16, at: 0.32, type: 'triangle', g: 0.17 }, { f: 1047, d: 0.5, at: 0.48, type: 'triangle', g: 0.2 },
    { f: 784, d: 0.9, at: 0.48, type: 'sine', g: 0.1 }, { f: 1319, d: 0.9, at: 0.7, type: 'triangle', g: 0.14 },
  ],
  error: [{ f: 160, d: 0.28, type: 'sawtooth', g: 0.12 }],
  ok: [{ f: 660, d: 0.08, type: 'sine', g: 0.08 }],
  tick: [{ f: 1900, d: 0.02, type: 'square', g: 0.035 }],
}
const VIBE: Record<FxEvent, number | number[]> = {
  disparo: [30, 60, 20], pausa: 25, acierto: [90, 30, 60, 30, 140], agua: [18, 40, 12], hundido: [80, 40, 80, 40, 220],
  victoria: [100, 60, 100, 60, 100, 60, 320], error: [200], ok: 15, tick: 8,
}

let ctx: AudioContext | null = null
let noiseBuf: AudioBuffer | null = null
function audio(): AudioContext | null {
  try {
    if (ctx) return ctx
    const Ctor = globalThis.AudioContext ?? (globalThis as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctor) return null
    ctx = new Ctor()
    return ctx
  } catch { return null }
}
function noise(a: AudioContext): AudioBuffer {
  if (noiseBuf) return noiseBuf
  const buf = a.createBuffer(1, Math.floor(a.sampleRate * 1.2), a.sampleRate)
  const d = buf.getChannelData(0)
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1
  noiseBuf = buf
  return buf
}

export function playTones(ev: FxEvent): void {
  const a = audio()
  if (!a) return
  try {
    if (a.state === 'suspended') void a.resume()
    const t0 = a.currentTime
    for (const t of TONES[ev]) {
      const gain = a.createGain()
      const start = t0 + (t.at ?? 0)
      let src: AudioScheduledSourceNode
      if (t.noise) {
        const n = a.createBufferSource()
        n.buffer = noise(a)
        const lp = a.createBiquadFilter()
        lp.type = 'lowpass'
        lp.frequency.setValueAtTime(t.lp ?? 2000, start)
        if (t.lpTo) lp.frequency.exponentialRampToValueAtTime(t.lpTo, start + t.d)
        n.connect(lp).connect(gain)
        src = n
      } else {
        const osc = a.createOscillator()
        osc.type = t.type ?? 'sine'
        osc.frequency.setValueAtTime(t.f, start)
        if (t.to) osc.frequency.exponentialRampToValueAtTime(t.to, start + t.d)
        osc.connect(gain)
        src = osc
      }
      gain.gain.setValueAtTime(0.0001, start)
      gain.gain.exponentialRampToValueAtTime(t.g ?? 0.14, start + 0.012)
      gain.gain.exponentialRampToValueAtTime(0.0001, start + t.d)
      gain.connect(a.destination)
      src.start(start)
      src.stop(start + t.d + 0.02)
    }
  } catch { /* nada */ }
}

export function vibrate(ev: FxEvent): void {
  try { globalThis.navigator?.vibrate?.(VIBE[ev] as number | number[]) } catch { /* nada */ }
}

export interface FeedbackPrefs { sound: boolean; vibrate: boolean }
export function makeFeedback(prefs: () => FeedbackPrefs): (ev: FxEvent) => void {
  return ev => {
    const p = prefs()
    if (p.sound) playTones(ev)
    if (p.vibrate) vibrate(ev)
  }
}

// ---- pantalla encendida ----
interface Sentinel { release(): Promise<void> }
let sentinel: Sentinel | null = null
export const wakeSupported = (): boolean => typeof navigator !== 'undefined' && 'wakeLock' in navigator
export async function setWake(on: boolean): Promise<void> {
  try {
    if (!on) { await sentinel?.release(); sentinel = null; return }
    if (!wakeSupported() || sentinel) return
    sentinel = await (navigator as unknown as { wakeLock: { request(t: 'screen'): Promise<Sentinel> } }).wakeLock.request('screen')
  } catch { sentinel = null }
}
