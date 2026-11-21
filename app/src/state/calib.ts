/**
 * Calibración de apuntado por esquinas (protocolo v3). Estado y acciones que usa la pestaña Enlace.
 *
 * Flujo: LÁSER on → mover con la cruceta (JOG) hasta la esquina física → «Esta es la esquina n» (CORNER n) ×4
 * → CALCULAR (CAL FIT) → verificar tocando celdas (AIM) → GUARDAR (CAL SAVE).
 *
 * Respeta la cola de peticiones del transporte (una orden en vuelo): los JOG repetidos se UNEN en uno solo mientras hay
 * uno en vuelo (nunca se acumulan ráfagas), y el STOP urgente sigue pasando por `store.stop()`.
 */
import { batch, computed, signal } from '@preact/signals'
import { CORNER_CELLS, formatAim, formatCorner, formatGoto, formatJog, formatLaser, friendlyError, JOG_MAX, parseReply, type ErrCode } from '../core/protocol'
import type { Coord } from '../core/types'
import { loadJSON, saveJSON, type KV } from './storage'

export const CALIB_STEPS = [5, 1, 0.2, 0.05] as const
/** El módulo apaga el láser solo a los 120 s: la app lleva la misma cuenta atrás. */
export const LASER_AUTO_S = 120
export type JogDir = 'left' | 'right' | 'up' | 'down'
export interface CalibPrefs { step: number; invertH: boolean; invertV: boolean }
export interface CornerInfo { n: number; cell: Coord; label: string; short: string; optional: boolean }

/** Orden y descripción de los puntos, vistos con la estación abajo (como el radar). */
export const CORNERS_INFO: CornerInfo[] = [
  { n: 1, cell: CORNER_CELLS[0]!, label: 'Esta es la esquina (1,1) · abajo-izquierda', short: '(1,1) abajo-izquierda', optional: false },
  { n: 2, cell: CORNER_CELLS[1]!, label: 'Esta es la esquina (20,1) · abajo-derecha', short: '(20,1) abajo-derecha', optional: false },
  { n: 3, cell: CORNER_CELLS[2]!, label: 'Esta es la esquina (20,20) · arriba-derecha', short: '(20,20) arriba-derecha', optional: false },
  { n: 4, cell: CORNER_CELLS[3]!, label: 'Esta es la esquina (1,20) · arriba-izquierda', short: '(1,20) arriba-izquierda', optional: false },
  { n: 5, cell: CORNER_CELLS[4]!, label: 'Punto de control (11,11) · centro (opcional)', short: '(11,11) centro', optional: true },
]

export const DEFAULT_CALIB_PREFS: CalibPrefs = { step: 1, invertH: false, invertV: false }

export interface CalibCtx {
  kv: KV
  send: (line: string, timeoutMs: number) => Promise<string[]>
  connected: { readonly value: boolean }
  /** disparo o TEST en curso: el módulo no atiende apuntado mientras tanto */
  busy: { readonly value: boolean }
  caps: { readonly value: string[] }
}

const errText = (e: unknown): string => (e instanceof Error ? e.message : String(e))
const clampJog = (v: number): number => Math.max(-JOG_MAX, Math.min(JOG_MAX, v))

export function createCalib(ctx: CalibCtx) {
  const loaded = loadJSON<Partial<CalibPrefs>>(ctx.kv, 'calib', {})
  const prefs = signal<CalibPrefs>({
    step: (CALIB_STEPS as readonly number[]).includes(Number(loaded.step)) ? Number(loaded.step) : DEFAULT_CALIB_PREFS.step,
    invertH: loaded.invertH === true,
    invertV: loaded.invertV === true,
  })
  /** ángulos de servo conocidos (los devuelve el módulo en cada orden) */
  const pan = signal<number | null>(null)
  const tilt = signal<number | null>(null)
  const laserOn = signal(false)
  const laserLeft = signal(0)
  /** puntos registrados 1..5 y sus ángulos */
  const corners = signal<boolean[]>([false, false, false, false, false])
  const cornerAngles = signal<({ pan: number; tilt: number } | null)[]>([null, null, null, null, null])
  /** el módulo tiene un mapa calculado (modo GRID) */
  const fitOk = signal(false)
  /** se registró un punto después del último cálculo: hay que volver a calcular */
  const stale = signal(false)
  /** error (°) del punto de control en el último cálculo; null = sin punto de control; undefined = aún no calculado */
  const fitErr = signal<number | null | undefined>(undefined)
  const mapMode = signal<'GRID' | 'GEO' | null>(null)
  const verified = signal<Coord | null>(null)
  const msg = signal('')
  const working = signal(0)

  const supported = computed(() => ctx.caps.value.includes('grid'))
  const ready = computed(() => ctx.connected.value && supported.value)
  const cornersDone = computed(() => corners.value.slice(0, 4).every(Boolean))
  const canSave = computed(() => fitOk.value && !stale.value)

  let countdown: ReturnType<typeof setInterval> | null = null
  const stopCountdown = () => { if (countdown) clearInterval(countdown); countdown = null; laserLeft.value = 0 }
  const startCountdown = () => {
    if (countdown) clearInterval(countdown)
    laserLeft.value = LASER_AUTO_S
    countdown = setInterval(() => {
      const left = laserLeft.value - 1
      if (left <= 0) { stopCountdown(); laserOn.value = false; msg.value = 'El láser se apagó solo (120 s). Vuelve a encenderlo.'; return }
      laserLeft.value = left
    }, 1000)
  }
  const setLaserLocal = (on: boolean) => {
    laserOn.value = on
    if (on) startCountdown(); else stopCountdown()
  }

  /** Envía una orden y vuelca las respuestas en el estado. Devuelve las respuestas, o null si falló. */
  async function cmd(line: string, timeoutMs = 4000): Promise<ReturnType<typeof parseReply>[] | null> {
    if (!ctx.connected.value) { msg.value = 'Conecta el módulo primero.'; return null }
    working.value++
    try {
      const reps = (await ctx.send(line, timeoutMs)).map(parseReply)
      const err = reps.find(r => r.t === 'err')
      if (err && err.t === 'err') {
        msg.value = err.code === 'LIMIT' && /^(JOG|GOTO)/.test(line) ? 'Tope mecánico: el servo no puede ir más allá (15°–165°).' : friendlyError(err.code as ErrCode)
        return null
      }
      batch(() => { for (const r of reps) apply(r) })
      return reps
    } catch (e) {
      msg.value = `Sin respuesta: ${errText(e)}`
      return null
    } finally { working.value-- }
  }

  function apply(r: ReturnType<typeof parseReply>): void {
    switch (r.t) {
      case 'pt': case 'ok-jog': pan.value = r.pan; tilt.value = r.tilt; break
      case 'laser': case 'ok-laser': if (r.on !== laserOn.value || (r.on && !countdown)) setLaserLocal(r.on); break
      case 'ok-corner': {
        corners.value = corners.value.map((v, i) => (i === r.n - 1 ? true : v))
        cornerAngles.value = cornerAngles.value.map((v, i) => (i === r.n - 1 ? { pan: r.pan, tilt: r.tilt } : v))
        pan.value = r.pan; tilt.value = r.tilt
        stale.value = true; fitErr.value = undefined
        break
      }
      case 'corners': corners.value = r.mask; fitOk.value = r.fit; if (!r.fit) fitErr.value = undefined; break
      case 'ok-fit': fitOk.value = true; stale.value = false; fitErr.value = r.err; mapMode.value = 'GRID'; break
      case 'map': mapMode.value = r.mode; if (r.mode === 'GEO') fitOk.value = false; break
      case 'ok-aim': verified.value = r.at; break
      default: break
    }
  }

  const guard = (): boolean => {
    if (!ctx.connected.value) { msg.value = 'Conecta el módulo primero.'; return false }
    if (!supported.value) { msg.value = 'Este firmware no trae la calibración de apuntado (falta «grid» en HELLO).'; return false }
    if (ctx.busy.value) { msg.value = 'El módulo está disparando o en el TEST. Espera o pulsa STOP.'; return false }
    return true
  }

  // ---- acciones ----
  /** Lee el estado del módulo: ángulos, láser, puntos y modo del mapa. */
  async function refresh(): Promise<void> {
    if (!ready.value || ctx.busy.value) return
    for (const l of ['PT', 'LASER', 'CORNERS', 'CAL MAP']) { if (!(await cmd(l))) return }
    if (!msg.value) msg.value = ''
  }

  // JOG: los repetidos se unen mientras uno está en vuelo
  let jogging = false
  let acc = { dp: 0, dt: 0 }
  async function pumpJog(): Promise<void> {
    if (jogging) return
    jogging = true
    try {
      while (acc.dp !== 0 || acc.dt !== 0) {
        const dp = clampJog(acc.dp), dt = clampJog(acc.dt)
        acc = { dp: 0, dt: 0 }
        if (!(await cmd(formatJog(dp, dt)))) { acc = { dp: 0, dt: 0 }; break }
      }
    } finally { jogging = false }
  }
  /** Un paso en la dirección dada (← → pan, ↑ ↓ tilt). El sentido físico se invierte desde los ajustes. */
  function jog(dir: JogDir): void {
    if (!guard()) return
    const p = prefs.value
    const s = p.step
    const h = p.invertH ? -1 : 1
    const v = p.invertV ? -1 : 1
    // por defecto: → sube el pan (gira a la derecha) y ↑ BAJA el ángulo de tilt (TILT_SIGN = +1: más ángulo = rayo más abajo)
    if (dir === 'right') acc.dp += s * h
    else if (dir === 'left') acc.dp -= s * h
    else if (dir === 'up') acc.dt -= s * v
    else acc.dt += s * v
    acc = { dp: clampJog(acc.dp), dt: clampJog(acc.dt) }
    void pumpJog()
  }

  async function laser(on: boolean): Promise<boolean> {
    if (!guard()) return false
    return (await cmd(formatLaser(on))) !== null
  }
  const toggleLaser = () => laser(!laserOn.value)

  async function center(): Promise<boolean> {
    if (!guard()) return false
    const r = await cmd(formatGoto(90, 90))
    if (r) msg.value = 'Servos centrados (90° / 90°).'
    return r !== null
  }

  async function recordCorner(n: number): Promise<boolean> {
    if (!guard()) return false
    const info = CORNERS_INFO[n - 1]
    const r = await cmd(formatCorner(n))
    if (r && info) msg.value = `Registrada la esquina ${info.short}.`
    return r !== null
  }

  /** CAL FIT. Devuelve el error del punto de control (°), null si no hay control, o undefined si falló. */
  async function compute(): Promise<number | null | undefined> {
    if (!guard()) return undefined
    if (!cornersDone.value) { msg.value = friendlyError('NODATA'); return undefined }
    const r = await cmd('CAL FIT')
    if (!r) return undefined
    await cmd('CAL MAP')
    const e = fitErr.value
    msg.value = e === null || e === undefined ? 'Mapa calculado. Sin punto de control: verifica tocando celdas.' : `Mapa calculado. Error del control: ${e.toFixed(2)}°.`
    return e
  }

  /** Apunta a una celda con el mapa actual; enciende el láser si hace falta. */
  async function verify(c: Coord): Promise<boolean> {
    if (!guard()) return false
    if (!laserOn.value && !(await laser(true))) return false
    const r = await cmd(formatAim(c))
    if (r) msg.value = `Apuntando a (${c.x},${c.y}): comprueba que el láser cae en esa casilla.`
    return r !== null
  }

  async function save(): Promise<boolean> {
    if (!guard()) return false
    if (!canSave.value) { msg.value = 'Calcula el mapa antes de guardarlo.'; return false }
    const r = await cmd('CAL SAVE')
    if (r) msg.value = 'Mapa guardado en el módulo: sobrevive al apagado.'
    return r !== null
  }

  /** CAL RESET: borra el mapa (y la calibración geométrica) y vuelve a la geometría de fábrica. */
  async function resetMap(): Promise<boolean> {
    if (!guard()) return false
    const r = await cmd('CAL RESET')
    if (!r) return false
    batch(() => {
      corners.value = [false, false, false, false, false]; cornerAngles.value = [null, null, null, null, null]
      fitOk.value = false; stale.value = false; fitErr.value = undefined; mapMode.value = 'GEO'; verified.value = null
    })
    await cmd('CORNERS'); await cmd('CAL MAP')
    msg.value = 'Mapa borrado: el módulo vuelve a la geometría de fábrica.'
    return true
  }

  function setPrefs(p: Partial<CalibPrefs>): void {
    prefs.value = { ...prefs.value, ...p }
    saveJSON(ctx.kv, 'calib', prefs.value)
  }

  /** El STOP (o un disparo/TEST) apaga el láser del módulo: la app lo refleja y suelta los JOG pendientes. */
  function laserKilled(): void { acc = { dp: 0, dt: 0 }; if (laserOn.value) setLaserLocal(false) }
  /** Enlace caído: se olvida todo lo que el módulo ya no puede confirmar. */
  function linkLost(): void {
    acc = { dp: 0, dt: 0 }
    batch(() => { stopCountdown(); laserOn.value = false; pan.value = null; tilt.value = null; mapMode.value = null; verified.value = null })
  }
  function dispose(): void { stopCountdown() }

  return {
    prefs, pan, tilt, laserOn, laserLeft, corners, cornerAngles, fitOk, stale, fitErr, mapMode, verified, msg, working,
    supported, ready, cornersDone, canSave,
    refresh, jog, laser, toggleLaser, center, recordCorner, compute, verify, save, resetMap, setPrefs, laserKilled, linkLost, dispose,
  }
}

export type Calib = ReturnType<typeof createCalib>
