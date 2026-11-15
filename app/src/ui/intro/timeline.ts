/** Motor de líneas de tiempo del tutorial: escenas encadenadas con duración, progreso 0..1, pausa y salto.
 *  Sin DOM: el reloj se inyecta (raf/now) y `tick(dt)` es determinista, así se prueba con Vitest. */
export interface TLScene { id: string; dur: number }
export interface TLState { index: number; elapsed: number; progress: number; playing: boolean; ended: boolean }
export type TLReason = 'tick' | 'scene' | 'play' | 'end'
export type TLListener = (s: TLState, why: TLReason) => void

export interface TLOptions {
  speed?: number
  raf?: (cb: (t: number) => void) => number
  caf?: (id: number) => void
  now?: () => number
}

export class Timeline {
  readonly scenes: readonly TLScene[]
  readonly speed: number
  private idx = 0
  private el = 0
  private run = false
  private done = false
  private ls = new Set<TLListener>()
  private rafId = 0
  private last = 0
  private readonly raf: (cb: (t: number) => void) => number
  private readonly caf: (id: number) => void
  private readonly now: () => number

  constructor(scenes: readonly TLScene[], o: TLOptions = {}) {
    if (scenes.length === 0) throw new Error('Timeline sin escenas')
    this.scenes = scenes
    this.speed = o.speed && o.speed > 0 ? o.speed : 1
    this.raf = o.raf ?? (cb => requestAnimationFrame(cb))
    this.caf = o.caf ?? (id => cancelAnimationFrame(id))
    this.now = o.now ?? (() => performance.now())
  }

  get state(): TLState {
    const d = this.scenes[this.idx]!.dur
    return { index: this.idx, elapsed: this.el, progress: Math.min(1, this.el / d), playing: this.run, ended: this.done }
  }
  /** Progreso global 0..1 (todas las escenas). */
  get total(): number {
    const sum = this.scenes.reduce((a, s) => a + s.dur, 0)
    let before = 0
    for (let i = 0; i < this.idx; i++) before += this.scenes[i]!.dur
    return Math.min(1, (before + this.el) / sum)
  }

  on(l: TLListener): () => void { this.ls.add(l); return () => { this.ls.delete(l) } }
  private emit(why: TLReason): void { const s = this.state; for (const l of [...this.ls]) l(s, why) }

  play(): void {
    if (this.run || this.done) return
    this.run = true
    this.last = this.now()
    this.loop()
    this.emit('play')
  }
  pause(): void {
    if (!this.run) return
    this.run = false
    if (this.rafId) this.caf(this.rafId)
    this.rafId = 0
    this.emit('play')
  }
  toggle(): void { if (this.run) this.pause(); else this.play() }

  private loop(): void {
    this.rafId = this.raf(t => {
      this.rafId = 0
      if (!this.run) return
      const dt = Math.min(100, Math.max(0, t - this.last)) // pestaña en segundo plano: no saltar escenas
      this.last = t
      this.tick(dt)
      if (this.run) this.loop()
    })
  }

  /** Avanza `dt` ms de reloj real (se multiplica por `speed`). Encadena escenas; al final se detiene. */
  tick(dt: number): void {
    if (!this.run) return
    let rest = dt * this.speed
    let changed = false
    while (rest > 0) {
      const d = this.scenes[this.idx]!.dur
      const room = d - this.el
      if (rest < room) { this.el += rest; rest = 0; break }
      rest -= room
      if (this.idx >= this.scenes.length - 1) { this.el = d; this.finish(); return }
      this.idx++; this.el = 0; changed = true
    }
    this.emit(changed ? 'scene' : 'tick')
  }

  private finish(): void {
    this.run = false; this.done = true
    if (this.rafId) this.caf(this.rafId)
    this.rafId = 0
    this.emit('end')
  }

  /** Salta a una escena (reinicia su progreso). Conserva el estado reproduciendo/pausado. */
  seek(index: number, progress = 0): void {
    const i = Math.max(0, Math.min(this.scenes.length - 1, Math.floor(index)))
    this.idx = i
    this.el = Math.max(0, Math.min(1, progress)) * this.scenes[i]!.dur
    this.done = false
    this.emit('scene')
  }
  next(): void {
    if (this.idx >= this.scenes.length - 1) { this.el = this.scenes[this.idx]!.dur; this.finish(); return }
    this.seek(this.idx + 1)
  }
  prev(): void { this.seek(this.idx - 1) }

  dispose(): void {
    this.run = false
    if (this.rafId) this.caf(this.rafId)
    this.rafId = 0
    this.ls.clear()
  }
}
