/**
 * Transporte SIMULADO: se comporta como el módulo real (PROTOCOLO.md v1+v2) y sirve de rival/testigo automático.
 * Los temporizadores usan setTimeout global en cada llamada, así que vi.useFakeTimers() los controla.
 */
import { formatCal, parseCommand, type CalValues, type Command, type ModuleMode } from '../core/protocol'
import { randomFleet, resolveShot, shipAt, type Rng } from '../core/fleet'
import type { Coord, PlacedShip, ShotResult } from '../core/types'
import type { LineTransport, PeerInfo } from './transport'

export interface SimLatency {
  /** duración de un disparo (láser encendido + movimiento) */
  shotMs: number
  /** duración de cada una de las 5 posiciones del TEST */
  testStepMs: number
  /** MARK HIT (LED 2 s) */
  markMs: number
  /** retardo de las órdenes instantáneas (PING, CAL, …) */
  cmdMs: number
}
export const FAST_LATENCY: SimLatency = { shotMs: 20, testStepMs: 10, markMs: 20, cmdMs: 0 }
/** ≈ módulo real: disparo ≈ 2 s, TEST ≈ 12 s */
export const REALISTIC_LATENCY: SimLatency = { shotMs: 2000, testStepMs: 2400, markMs: 2000, cmdMs: 40 }

export interface SimOptions {
  latency?: Partial<SimLatency>
  rng?: Rng
  rivalFleet?: PlacedShip[]
  name?: string
  fw?: string
  mode?: ModuleMode
  caps?: string[]
  /** celdas inalcanzables -> ERR LIMIT */
  limit?: (c: Coord) => boolean
}

export const SIM_ID = 'sim-0'
export const TEST_POSITIONS: Coord[] = [{ x: 1, y: 1 }, { x: 20, y: 1 }, { x: 20, y: 20 }, { x: 1, y: 20 }, { x: 11, y: 11 }]
const DEFAULT_CAL: CalValues = { x: 0, y: 0, h: 150, panTrim: 0, tiltTrim: 0 }

interface Job { abort: () => void }

export class SimTransport implements LineTransport {
  readonly kind = 'sim' as const
  readonly name: string
  readonly latency: SimLatency
  /** flota del rival simulado (la que el módulo "tiene" en su tablero) */
  rivalFleet: PlacedShip[]
  /** disparos completados (OK) por el módulo, en orden */
  readonly fired: Coord[] = []
  /** simula fallo de NVS: CAL SAVE / CAL RESET / MODE X responden ERR STORE */
  failStore = false
  mode: ModuleMode
  armState: 'NOTREQ' | 'OFF' | 'ON'
  armSeconds = 30
  cal: CalValues = { ...DEFAULT_CAL }
  savedCal: CalValues = { ...DEFAULT_CAL }
  /** nº de reinicios simulados por cambio de modo */
  reboots = 0

  private readonly fw: string
  private readonly caps: string[]
  private readonly limit: ((c: Coord) => boolean) | undefined
  private connected = false
  private job: Job | null = null
  private unsolicited = new Set<(line: string) => void>()
  private stateCbs = new Set<(connected: boolean, reason?: string) => void>()
  private traffic = new Set<(dir: 'tx' | 'rx', line: string) => void>()
  private pending = new Set<(e: Error) => void>()

  constructor(opts: SimOptions = {}) {
    this.name = opts.name ?? 'SONAR-SIM'
    this.fw = opts.fw ?? '0.2.0-sim'
    this.mode = opts.mode ?? 'BT'
    this.caps = opts.caps ?? []
    this.limit = opts.limit
    this.latency = { ...FAST_LATENCY, ...opts.latency }
    this.rivalFleet = opts.rivalFleet ?? randomFleet(opts.rng ?? Math.random)
    this.armState = this.mode === 'WIFI' ? 'OFF' : 'NOTREQ'
  }

  // ---- LineTransport ----
  async list(prefix?: string): Promise<PeerInfo[]> {
    if (prefix && !this.name.toUpperCase().startsWith(prefix.toUpperCase())) return []
    return [{ id: SIM_ID, name: this.name, rssi: -42 }]
  }

  async connect(id: string): Promise<void> {
    if (id !== SIM_ID) throw new Error(`Módulo simulado desconocido: ${id}`)
    this.connected = true
    this.stateCbs.forEach(cb => cb(true))
  }

  async disconnect(): Promise<void> {
    if (!this.connected) return
    this.connected = false
    this.pending.forEach(rej => rej(new Error('desconectado')))
    this.pending.clear()
    this.job?.abort()
    this.job = null
    this.stateCbs.forEach(cb => cb(false, 'disconnect'))
  }

  isConnected(): boolean { return this.connected }
  get busy(): boolean { return this.job !== null }

  request(line: string, timeoutMs: number): Promise<string[]> {
    if (!this.connected) return Promise.reject(new Error('no conectado'))
    this.traffic.forEach(cb => cb('tx', line))
    return new Promise<string[]>((resolve, reject) => {
      let settled = false
      const fail = (e: Error) => { if (!settled) { settled = true; clearTimeout(timer); this.pending.delete(fail); reject(e) } }
      const timer = setTimeout(() => fail(new Error('timeout')), timeoutMs)
      this.pending.add(fail)
      const done = (lines: string[]) => {
        if (settled) return
        settled = true
        clearTimeout(timer)
        this.pending.delete(fail)
        lines.forEach(l => this.traffic.forEach(cb => cb('rx', l)))
        resolve(lines)
      }
      this.handle(line, done)
    })
  }

  onUnsolicited(cb: (line: string) => void): () => void {
    this.unsolicited.add(cb)
    return () => { this.unsolicited.delete(cb) }
  }

  onStateChange(cb: (connected: boolean, reason?: string) => void): () => void {
    this.stateCbs.add(cb)
    return () => { this.stateCbs.delete(cb) }
  }

  // ---- extras del simulado ----
  /** observa el tráfico crudo (para bitácora / depuración) */
  onTraffic(cb: (dir: 'tx' | 'rx', line: string) => void): () => void {
    this.traffic.add(cb)
    return () => { this.traffic.delete(cb) }
  }

  /** emite una línea no solicitada (p. ej. "EVT …") */
  emit(line: string): void { this.unsolicited.forEach(cb => cb(line)) }

  /** Testigo automático: resultado del disparo a `c` contra la flota rival (considera los disparos ya hechos). */
  verdictFor(c: Coord): ShotResult { return resolveShot(this.rivalFleet, c, this.fired) }

  /** Igual que verdictFor, con el largo del barco hundido. */
  verdictDetail(c: Coord): { result: ShotResult; sunkLen?: number } {
    const result = this.verdictFor(c)
    const ship = shipAt(this.rivalFleet, c)
    return result === 'sunk' && ship ? { result, sunkLen: ship.len } : { result }
  }

  /** Nueva flota rival y borrón de disparos. */
  newRival(rng: Rng = Math.random): void {
    this.rivalFleet = randomFleet(rng)
    this.fired.length = 0
  }

  setArm(state: 'NOTREQ' | 'OFF' | 'ON', seconds?: number): void {
    this.armState = state
    if (seconds !== undefined) this.armSeconds = seconds
  }

  // ---- lógica del módulo ----
  private later(ms: number, fn: () => void): void {
    if (ms > 0) setTimeout(fn, ms)
    else fn()
  }

  private handle(line: string, done: (lines: string[]) => void): void {
    const cmd: Command = parseCommand(line)
    const reply = (lines: string[]) => this.later(this.latency.cmdMs, () => done(lines))

    if (cmd.t === 'stop') {
      const job = this.job
      done(['OK STOP']) // STOP siempre se atiende; el disparo interrumpido responde ERR STOP después
      job?.abort()
      return
    }
    if (this.job) return reply(['ERR BUSY'])
    switch (cmd.t) {
      case 'error': return reply([`ERR ${cmd.code}`])
      case 'ping': return reply([`PONG ${this.name} ${this.fw}`])
      case 'hello': return reply([`HELLO SONAR 2 ${this.fw} ${this.name} ${this.mode} ${this.caps.length ? this.caps.join(',') : '-'}`])
      case 'mode-query': return reply([`MODE ${this.mode}`])
      case 'mode-set':
        if (this.failStore) return reply(['ERR STORE'])
        this.mode = cmd.mode
        this.armState = cmd.mode === 'WIFI' ? 'OFF' : 'NOTREQ'
        this.reboots++
        return reply([`OK MODE ${cmd.mode}`])
      case 'arm': return reply([this.armState === 'ON' ? `ARM ON ${this.armSeconds}` : `ARM ${this.armState}`])
      case 'cal-show': return reply([formatCal(this.cal)])
      case 'cal-set': this.cal = { ...cmd.cal }; return reply(['OK CAL'])
      case 'cal-save':
        if (this.failStore) return reply(['ERR STORE'])
        this.savedCal = { ...this.cal }
        return reply(['OK SAVE'])
      case 'cal-reset':
        if (this.failStore) return reply(['ERR STORE'])
        this.cal = { ...DEFAULT_CAL }
        this.savedCal = { ...DEFAULT_CAL }
        return reply(['OK RESET'])
      case 'mark': {
        if (!cmd.hit) return reply(['OK MARK'])
        this.startJob(this.latency.markMs, () => done(['OK MARK']), () => done(['ERR STOP']))
        return
      }
      case 'fire': {
        if (this.armState === 'OFF') return reply(['ERR DISARMED'])
        if (this.limit?.(cmd.at)) return reply(['ERR LIMIT'])
        const at = cmd.at
        this.startJob(this.latency.shotMs, () => { this.fired.push(at); done([`OK (${at.x},${at.y})`]) }, () => done(['ERR STOP']))
        return
      }
      case 'test': {
        if (this.armState === 'OFF') return reply(['ERR DISARMED'])
        this.runTest(done)
        return
      }
    }
  }

  private startJob(ms: number, onDone: () => void, onAbort: () => void): void {
    let timer: ReturnType<typeof setTimeout> | undefined
    const job: Job = {
      abort: () => {
        if (timer !== undefined) clearTimeout(timer)
        if (this.job === job) this.job = null
        onAbort()
      },
    }
    this.job = job
    timer = setTimeout(() => {
      if (this.job === job) this.job = null
      onDone()
    }, ms)
  }

  private runTest(done: (lines: string[]) => void): void {
    const lines: string[] = ['TEST START']
    let step = 0
    let timer: ReturnType<typeof setTimeout> | undefined
    const job: Job = {
      abort: () => {
        if (timer !== undefined) clearTimeout(timer)
        if (this.job === job) this.job = null
        done([...lines, 'TEST ABORT', 'ERR STOP'])
      },
    }
    this.job = job
    const next = () => {
      timer = setTimeout(() => {
        const p = TEST_POSITIONS[step]!
        lines.push(`OK (${p.x},${p.y})`)
        step++
        if (step < TEST_POSITIONS.length) next()
        else {
          if (this.job === job) this.job = null
          done([...lines, 'TEST DONE'])
        }
      }, this.latency.testStepMs)
    }
    next()
  }
}
