/**
 * Efectos del ciclo de disparo sobre un <canvas> 2D que cubre el escenario del radar (estación arriba + tablero 20×20).
 * Pensado para un celular de gama baja: solo trazos, círculos y degradados radiales; sin blur ni filtros;
 * máximo ~40 partículas; el bucle rAF corre únicamente mientras hay algo animándose.
 * Con `prefers-reduced-motion` se usa una versión simple (un anillo / un destello) con la misma lógica de fases.
 */
import type { Coord } from '../../core/types'

export type FxPhase = 'idle' | 'flying' | 'verdict' | 'splash' | 'explosion' | 'cancel'

const HIT = '255,93,77'
const WARM = '255,176,74'
const ECHO = '90,214,255'
const INK = '2,8,12'
/** Fracción del trayecto a la que se congela el proyectil: «justo antes» de tocar la casilla. */
export const FREEZE_AT = 0.93

interface Spark { x: number; y: number; vx: number; vy: number; life: number; col: string }
interface Drop { x: number; y: number; vx: number; vy: number; life: number }
interface Puff { x: number; y: number; vx: number; vy: number; life: number; r0: number }

const clamp01 = (v: number) => Math.max(0, Math.min(1, v))
const easeOut = (v: number) => 1 - (1 - clamp01(v)) ** 3
const easeInOut = (v: number) => { const k = clamp01(v); return k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2 }
const smooth = (v: number) => { const k = clamp01(v); return k * k * (3 - 2 * k) }

export class Fx {
  private ctx: CanvasRenderingContext2D | null
  private w = 0
  private h = 0
  private raf = 0
  private phase: FxPhase = 'idle'
  private t0 = 0
  private at: Coord = { x: 10, y: 10 }
  private flightMs = 1100
  private spawned = false
  private sparks: Spark[] = []
  private drops: Drop[] = []
  private puffs: Puff[] = []

  constructor(private canvas: HTMLCanvasElement, private reduced: boolean) { this.ctx = canvas.getContext('2d') }

  private resize(): void {
    const r = this.canvas.getBoundingClientRect()
    const dpr = Math.min(globalThis.devicePixelRatio || 1, 2)
    this.w = r.width; this.h = r.height
    const bw = Math.max(1, Math.round(r.width * dpr)), bh = Math.max(1, Math.round(r.height * dpr))
    if (this.canvas.width !== bw || this.canvas.height !== bh) { this.canvas.width = bw; this.canvas.height = bh }
    this.ctx?.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  /** unidades del tablero (x: 0..20, y: -2.2..20) → píxeles del canvas */
  private P(xu: number, yu: number): [number, number] { const u = this.w / 20; return [xu * u, (yu + 2.2) * u] }
  private get u(): number { return this.w / 20 }

  setPhase(phase: FxPhase, at: Coord, flightMs = 1100): void {
    if (!this.ctx) return
    this.resize()
    const prev = this.phase
    this.phase = phase
    this.at = at
    this.flightMs = flightMs
    this.t0 = performance.now()
    this.spawned = false
    // el veredicto continúa donde se congeló el vuelo: sin saltos
    if (phase === 'idle') { this.stopLoop(); this.ctx.clearRect(0, 0, this.w, this.h); this.sparks = []; this.drops = []; this.puffs = []; return }
    if (prev === 'flying' && phase === 'verdict') this.t0 = performance.now()
    if (!this.raf) this.raf = requestAnimationFrame(this.frame)
  }
  private stopLoop(): void { if (this.raf) cancelAnimationFrame(this.raf); this.raf = 0 }
  destroy(): void { this.stopLoop(); this.phase = 'idle' }

  private frame = (now: number): void => {
    this.raf = 0
    const ctx = this.ctx
    if (!ctx || this.phase === 'idle') return
    ctx.clearRect(0, 0, this.w, this.h)
    const t = now - this.t0
    switch (this.phase) {
      case 'flying': this.drawFlight(ctx, t); break
      case 'verdict': this.drawFrozen(ctx, t); break
      case 'splash': this.drawSplash(ctx, t); break
      case 'explosion': this.drawExplosion(ctx, t); break
      case 'cancel': this.drawCancel(ctx, t); break
    }
    this.raf = requestAnimationFrame(this.frame)
  }

  // ---- piezas ----
  private target(): [number, number] { return this.P(this.at.x - 0.5, this.at.y - 0.5) }
  private station(): [number, number] { return this.P(10.5, -1.4) }
  private at_(p: number): [number, number] {
    const [sx, sy] = this.station(), [tx, ty] = this.target()
    return [sx + (tx - sx) * p, sy + (ty - sy) * p]
  }
  private dim(ctx: CanvasRenderingContext2D, a: number): void {
    if (a <= 0.01) return
    const [tx, ty] = this.target(), u = this.u
    ctx.fillStyle = `rgba(${INK},${0.58 * a})`
    ctx.fillRect(0, 0, this.w, this.h)
    ctx.globalCompositeOperation = 'destination-out'
    const g = ctx.createRadialGradient(tx, ty, u * 1.1, tx, ty, u * 5.2)
    g.addColorStop(0, `rgba(0,0,0,${a})`); g.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, this.w, this.h)
    ctx.globalCompositeOperation = 'source-over'
  }
  private beam(ctx: CanvasRenderingContext2D, p: number, a = 1): void {
    const [sx, sy] = this.station(), [hx, hy] = this.at_(p)
    ctx.lineCap = 'round'
    ctx.strokeStyle = `rgba(${HIT},${0.22 * a})`; ctx.lineWidth = 1.2
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(hx, hy); ctx.stroke()
  }
  private trail(ctx: CanvasRenderingContext2D, p: number, a = 1): void {
    if (this.reduced) return
    const u = this.u
    ctx.lineCap = 'round'
    for (let i = 0; i < 12; i++) {
      const p1 = Math.max(0, p - i * 0.024), p2 = Math.max(0, p - (i + 1) * 0.024)
      const [x1, y1] = this.at_(p1), [x2, y2] = this.at_(p2)
      const k = 1 - i / 12
      ctx.strokeStyle = `rgba(${i < 3 ? WARM : HIT},${0.85 * k * a})`
      ctx.lineWidth = Math.max(1, u * 0.36 * k)
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke()
    }
  }
  private head(ctx: CanvasRenderingContext2D, p: number, pulse = 0, a = 1): void {
    const [x, y] = this.at_(p), u = this.u
    const r = u * (0.85 + 0.22 * pulse)
    const g = ctx.createRadialGradient(x, y, 0, x, y, r)
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(0.28, `rgba(${WARM},${0.9 * a})`); g.addColorStop(1, `rgba(${HIT},0)`)
    ctx.fillStyle = g
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill()
  }
  private reticle(ctx: CanvasRenderingContext2D, t: number, a: number): void {
    const [tx, ty] = this.target(), u = this.u
    // cruz tenue que cruza todo el tablero: se lee la coordenada de un vistazo
    ctx.strokeStyle = `rgba(217,243,238,${0.22 * a})`; ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(tx, this.P(0, -1.2)[1]); ctx.lineTo(tx, this.h); ctx.moveTo(0, ty); ctx.lineTo(this.w, ty); ctx.stroke()
    const k = (t % 900) / 900
    const R = u * (1.7 - 1.0 * easeOut(k))
    ctx.strokeStyle = `rgba(217,243,238,${(0.95 - 0.6 * k) * a})`; ctx.lineWidth = 2
    ctx.beginPath(); ctx.arc(tx, ty, R, 0, Math.PI * 2); ctx.stroke()
    // marco fijo con 4 esquinas
    const c = u * 0.62, l = u * 0.32
    ctx.strokeStyle = `rgba(70,240,181,${a})`; ctx.lineWidth = 2.4; ctx.lineCap = 'square'
    ctx.beginPath()
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]] as const) {
      ctx.moveTo(tx + sx * c, ty + sy * (c - l)); ctx.lineTo(tx + sx * c, ty + sy * c); ctx.lineTo(tx + sx * (c - l), ty + sy * c)
    }
    ctx.stroke()
  }

  // ---- fases ----
  private drawFlight(ctx: CanvasRenderingContext2D, t: number): void {
    const f = clamp01(t / this.flightMs)
    const p = FREEZE_AT * (this.reduced ? 1 : easeInOut(f))
    if (this.reduced) {
      const [tx, ty] = this.target()
      ctx.fillStyle = `rgba(${HIT},${0.2 + 0.5 * f})`; ctx.beginPath(); ctx.arc(tx, ty, this.u * (0.4 + 0.5 * f), 0, Math.PI * 2); ctx.fill()
      this.dim(ctx, smooth((f - 0.5) / 0.5)); return
    }
    this.dim(ctx, smooth((f - 0.55) / 0.45))
    this.beam(ctx, p, 0.4 + 0.6 * f)
    this.trail(ctx, p)
    this.head(ctx, p)
    this.reticle(ctx, t, smooth((f - 0.5) / 0.5))
  }
  private drawFrozen(ctx: CanvasRenderingContext2D, t: number): void {
    this.dim(ctx, 1)
    if (this.reduced) { this.reticle(ctx, 0, 1); return }
    this.beam(ctx, FREEZE_AT)
    this.trail(ctx, FREEZE_AT)
    this.head(ctx, FREEZE_AT, 0.5 + 0.5 * Math.sin(t / 130))
    this.reticle(ctx, t, 1)
  }
  /** Tramo final (150 ms): el proyectil termina de llegar. Devuelve el tiempo restante tras la llegada. */
  private approach(ctx: CanvasRenderingContext2D, t: number, lead: number, dimFade = 500): number {
    const k = clamp01(t / lead)
    this.dim(ctx, 1 - smooth(t / dimFade))
    if (k < 1 && !this.reduced) {
      const p = FREEZE_AT + (1 - FREEZE_AT) * easeOut(k)
      this.beam(ctx, p); this.trail(ctx, p); this.head(ctx, p)
    }
    return t - lead
  }
  private drawSplash(ctx: CanvasRenderingContext2D, t: number): void {
    const lead = this.reduced ? 0 : 150
    const s = this.approach(ctx, t, lead)
    if (s < 0) return
    const [tx, ty] = this.target(), u = this.u
    if (!this.spawned) {
      this.spawned = true
      this.drops = this.reduced ? [] : Array.from({ length: 9 }, () => ({ x: 0, y: 0, vx: (Math.random() - 0.5) * 2.8 * u, vy: -(3 + Math.random() * 2.6) * u, life: 520 + Math.random() * 260 }))
    }
    const rings = this.reduced ? 1 : 3
    for (let i = 0; i < rings; i++) {
      const k = clamp01((s - i * 140) / 950)
      if (k <= 0 || k >= 1) continue
      ctx.strokeStyle = `rgba(${ECHO},${(1 - k) * 0.95})`
      ctx.lineWidth = Math.max(0.8, 3 - 2.4 * k)
      ctx.beginPath(); ctx.arc(tx, ty, u * (0.25 + 2.7 * easeOut(k)), 0, Math.PI * 2); ctx.stroke()
    }
    const k0 = clamp01(s / 420)
    if (k0 < 1) { ctx.fillStyle = `rgba(${ECHO},${0.55 * (1 - k0)})`; ctx.beginPath(); ctx.arc(tx, ty, u * (0.3 + 0.5 * k0), 0, Math.PI * 2); ctx.fill() }
    ctx.fillStyle = `rgb(${ECHO})`
    for (const d of this.drops) {
      const ts = s / 1000
      if (s > d.life) continue
      const x = tx + d.vx * ts, y = ty + d.vy * ts + 0.5 * 14 * u * ts * ts
      ctx.globalAlpha = 1 - s / d.life
      ctx.beginPath(); ctx.arc(x, y, u * 0.13, 0, Math.PI * 2); ctx.fill()
    }
    ctx.globalAlpha = 1
  }
  private drawExplosion(ctx: CanvasRenderingContext2D, t: number): void {
    const lead = this.reduced ? 0 : 150
    const s = this.approach(ctx, t, lead, 600)
    if (s < 0) return
    const [tx, ty] = this.target(), u = this.u
    if (!this.spawned) {
      this.spawned = true
      if (!this.reduced) {
        this.sparks = Array.from({ length: 26 }, () => {
          const a = Math.random() * Math.PI * 2, v = (6 + Math.random() * 10) * u
          return { x: 0, y: 0, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 2 * u, life: 450 + Math.random() * 450, col: ['255,210,122', WARM, HIT][Math.floor(Math.random() * 3)]! }
        })
        this.puffs = Array.from({ length: 6 }, () => ({ x: (Math.random() - 0.5) * u * 0.9, y: (Math.random() - 0.5) * u * 0.6, vx: (Math.random() - 0.5) * 0.8 * u, vy: -(0.8 + Math.random() * 1.2) * u, life: 900 + Math.random() * 400, r0: u * (0.5 + Math.random() * 0.4) }))
      }
    }
    // destello
    const kf = clamp01(s / 340)
    if (kf < 1) {
      const R = u * (this.reduced ? 2.4 : 3.6) * (0.4 + 0.6 * easeOut(kf))
      const g = ctx.createRadialGradient(tx, ty, 0, tx, ty, R)
      g.addColorStop(0, `rgba(255,255,255,${1 - kf})`); g.addColorStop(0.35, `rgba(${WARM},${0.85 * (1 - kf)})`); g.addColorStop(1, `rgba(${HIT},0)`)
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(tx, ty, R, 0, Math.PI * 2); ctx.fill()
    }
    // onda de choque
    const kw = clamp01(s / 650)
    if (kw < 1) {
      ctx.strokeStyle = `rgba(${kw < 0.4 ? WARM : HIT},${(1 - kw) * 0.95})`
      ctx.lineWidth = Math.max(1, 5 * (1 - kw))
      ctx.beginPath(); ctx.arc(tx, ty, u * (0.5 + 4.6 * easeOut(kw)), 0, Math.PI * 2); ctx.stroke()
    }
    // humo
    for (const p of this.puffs) {
      if (s > p.life) continue
      const k = s / p.life, ts = s / 1000
      ctx.fillStyle = `rgba(120,132,134,${0.34 * (1 - k)})`
      ctx.beginPath(); ctx.arc(tx + p.x + p.vx * ts, ty + p.y + p.vy * ts, p.r0 * (1 + 2.2 * k), 0, Math.PI * 2); ctx.fill()
    }
    // chispas (rayitas siguiendo la velocidad)
    ctx.lineCap = 'round'; ctx.lineWidth = Math.max(1.6, u * 0.17)
    for (const p of this.sparks) {
      if (s > p.life) continue
      const ts = s / 1000, drag = 1 - 0.55 * Math.min(1, ts)
      const x = tx + p.vx * ts * drag, y = ty + p.vy * ts * drag + 0.5 * 9 * u * ts * ts
      ctx.strokeStyle = `rgba(${p.col},${1 - s / p.life})`
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - p.vx * 0.028 * drag, y - p.vy * 0.028 * drag); ctx.stroke()
    }
  }
  private drawCancel(ctx: CanvasRenderingContext2D, t: number): void {
    const k = clamp01(t / 520)
    if (k >= 1) return
    this.dim(ctx, 1 - k)
    if (this.reduced) return
    this.beam(ctx, FREEZE_AT, 1 - k); this.trail(ctx, FREEZE_AT, 1 - k); this.head(ctx, FREEZE_AT, 0, 1 - k)
  }
}

export const prefersReducedMotion = (): boolean => {
  try { return !!globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches } catch { return false }
}
