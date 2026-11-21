/**
 * Transporte SIMULADO: se comporta como el módulo real (PROTOCOLO.md v1+v2) y sirve de rival/testigo automático.
 * Los temporizadores usan setTimeout global en cada llamada, así que vi.useFakeTimers() los controla.
 */
import { fmtAngle, formatCal, parseCommand, SERVO_MAX, SERVO_MIN, type CalValues, type Command, type ModuleMode } from '../core/protocol'
import { randomFleet, resolveShot, shipAt, type Rng } from '../core/fleet'
import type { Coord, PlacedShip, ShotResult } from '../core/types'
import { applyHomography, DEFAULT_MOUNT, fitHomography, GEO_BIAS, pointedCell, truthAngles, type Angles, type Homography, type Mount } from './gimbal'
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
  /** duración de un movimiento de apuntado (JOG / GOTO / AIM); 0 = instantáneo */
  moveMs: number
}
export const FAST_LATENCY: SimLatency = { shotMs: 20, testStepMs: 10, markMs: 20, cmdMs: 0, moveMs: 0 }
/** ≈ módulo real: disparo ≈ 2 s, TEST ≈ 12 s */
export const REALISTIC_LATENCY: SimLatency = { shotMs: 2000, testStepMs: 2400, markMs: 2000, cmdMs: 40, moveMs: 400 }

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
  /** montaje «verdadero» del gimbal virtual (pared, distancia, desplazamiento y giro) */
  mount?: Partial<Mount>
  /** el láser de calibración se apaga solo tras este tiempo (el módulo real: 120 s) */
  laserAutoOffMs?: number
}

export const SIM_ID = 'sim-0'
export const TEST_POSITIONS: Coord[] = [{ x: 1, y: 1 }, { x: 20, y: 1 }, { x: 20, y: 20 }, { x: 1, y: 20 }, { x: 11, y: 11 }]
const DEFAULT_CAL: CalValues = { x: 0, y: 0, h: 150, panTrim: 0, tiltTrim: 0 }

interface Job { abort: () => void }
type CornerSlot = Angles | null
const NO_CORNERS = (): CornerSlot[] => [null, null, null, null, null]
const CORNER_PLANE = [{ x: 1, y: 1 }, { x: 20, y: 1 }, { x: 20, y: 20 }, { x: 1, y: 20 }]
const CHECK_CELL = { x: 11, y: 11 }

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

  // ---- gimbal virtual (calibración de apuntado) ----
  readonly mount: Mount
  /** ángulos de servo actuales (90/90 al arrancar) */
  pan = 90
  tilt = 90
  laserOn = false
  /** esquinas registradas (1..4) y punto de control (5) */
  corners: CornerSlot[] = NO_CORNERS()
  /** homografía calculada (modo GRID); null = geometría de fábrica (GEO) */
  fit: Homography | null = null
  /** lo guardado en NVS por CAL SAVE */
  saved: { corners: CornerSlot[]; fit: Homography | null } = { corners: NO_CORNERS(), fit: null }

  private readonly fw: string
  private readonly caps: string[]
  private readonly limit: ((c: Coord) => boolean) | undefined
  private readonly laserAutoOffMs: number
  private laserTimer: ReturnType<typeof setTimeout> | undefined
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
    this.mount = { ...DEFAULT_MOUNT, ...opts.mount }
    this.laserAutoOffMs = opts.laserAutoOffMs ?? 120_000
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
    this.setLaser(false) // sin enlace el láser de calibración no debe quedar encendido
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

  /** Celda (fraccionaria) a la que apunta AHORA el rayo, según el montaje verdadero. */
  pointing(): { x: number; y: number } { return pointedCell(this.mount, { pan: this.pan, tilt: this.tilt }) }

  /** Ángulos exactos para la celda (lo que un operario perfecto lograría al apuntar a mano). */
  truth(c: Coord): Angles { return truthAngles(this.mount, c.x, c.y) }

  /** Reinicio de energía: vuelve a 90/90, láser apagado y se recarga lo guardado en NVS. */
  powerCycle(): void {
    this.setLaser(false)
    this.pan = 90; this.tilt = 90
    this.corners = this.saved.corners.map(c => (c ? { ...c } : null))
    this.fit = this.saved.fit
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
      this.setLaser(false)
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
        this.saved = { corners: this.corners.map(c => (c ? { ...c } : null)), fit: this.fit }
        return reply(['OK SAVE'])
      case 'cal-reset':
        if (this.failStore) return reply(['ERR STORE'])
        this.cal = { ...DEFAULT_CAL }
        this.savedCal = { ...DEFAULT_CAL }
        this.corners = NO_CORNERS(); this.fit = null
        this.saved = { corners: NO_CORNERS(), fit: null }
        return reply(['OK RESET'])
      // ---- protocolo v3: calibración de apuntado ----
      case 'pt': return reply([`PT ${fmtAngle(this.pan)} ${fmtAngle(this.tilt)}`])
      case 'laser-query': return reply([`LASER ${this.laserOn ? 'ON' : 'OFF'}`])
      case 'laser-set':
        if (cmd.on && this.armState === 'OFF') return reply(['ERR DISARMED'])
        this.setLaser(cmd.on)
        return reply([`OK LASER ${cmd.on ? 'ON' : 'OFF'}`])
      case 'jog': return this.moveTo(this.pan + cmd.dp, this.tilt + cmd.dt, 'JOG', done)
      case 'goto': return this.moveTo(cmd.pan, cmd.tilt, 'JOG', done)
      case 'aim': {
        const a = this.aimAngles(cmd.at)
        if (!a) return reply(['ERR LIMIT'])
        return this.moveTo(a.pan, a.tilt, `AIM ${cmd.at.x} ${cmd.at.y}`, done)
      }
      case 'corner':
        this.corners[cmd.n - 1] = { pan: this.pan, tilt: this.tilt }
        this.fit = null // un punto nuevo invalida el mapa hasta el siguiente CAL FIT
        return reply([`OK CORNER ${cmd.n} ${fmtAngle(this.pan)} ${fmtAngle(this.tilt)}`])
      case 'corners': return reply([`CORNERS ${this.corners.map(c => (c ? '1' : '0')).join('')} ${this.fit ? 1 : 0}`])
      case 'cal-map': return reply([`MAP ${this.fit ? 'GRID' : 'GEO'}`])
      case 'cal-fit': {
        if (!this.corners.slice(0, 4).every(Boolean)) return reply(['ERR NODATA'])
        const H = fitHomography(CORNER_PLANE, this.corners.slice(0, 4) as Angles[])
        if (!H) return reply(['ERR FIT'])
        this.fit = H
        const ctl = this.corners[4]
        const pred = applyHomography(H, CHECK_CELL.x, CHECK_CELL.y)
        const err = ctl && pred ? Math.max(Math.abs(pred.pan - ctl.pan), Math.abs(pred.tilt - ctl.tilt)) : null
        return reply([`OK FIT ${err === null ? '-' : err.toFixed(2)}`])
      }
      case 'mark': {
        if (!cmd.hit) return reply(['OK MARK'])
        this.startJob(this.latency.markMs, () => done(['OK MARK']), () => done(['ERR STOP']))
        return
      }
      case 'fire': {
        if (this.armState === 'OFF') return reply(['ERR DISARMED'])
        if (this.limit?.(cmd.at)) return reply(['ERR LIMIT'])
        const at = cmd.at
        this.setLaser(false) // como el módulo real: el disparo apaga el láser de calibración
        this.startJob(this.latency.shotMs, () => { this.fired.push(at); this.pointAt(at); done([`OK (${at.x},${at.y})`]) }, () => done(['ERR STOP']))
        return
      }
      case 'test': {
        if (this.armState === 'OFF') return reply(['ERR DISARMED'])
        this.runTest(done)
        return
      }
    }
  }

  private setLaser(on: boolean): void {
    this.laserOn = on
    if (this.laserTimer !== undefined) { clearTimeout(this.laserTimer); this.laserTimer = undefined }
    if (on) this.laserTimer = setTimeout(() => { this.laserTimer = undefined; this.laserOn = false }, this.laserAutoOffMs)
  }

  /** Ángulos con los que el módulo apunta a la celda: homografía si hay mapa (GRID); si no, la geometría de fábrica (GEO, desviada). */
  private aimAngles(c: Coord): Angles | null {
    const a = this.fit
      ? applyHomography(this.fit, c.x, c.y)
      : (() => { const t = truthAngles(this.mount, c.x, c.y); return { pan: t.pan + GEO_BIAS.pan, tilt: t.tilt + GEO_BIAS.tilt } })()
    if (!a || a.pan < SERVO_MIN || a.pan > SERVO_MAX || a.tilt < SERVO_MIN || a.tilt > SERVO_MAX) return null
    return a
  }
  private pointAt(c: Coord): void {
    const a = this.aimAngles(c)
    if (a) { this.pan = a.pan; this.tilt = a.tilt }
  }

  /** JOG / GOTO / AIM: valida el límite 15..165, mueve (moveMs) y responde con los ángulos absolutos nuevos. */
  private moveTo(pan: number, tilt: number, tag: string, done: (lines: string[]) => void): void {
    if (this.armState === 'OFF') return done(['ERR DISARMED'])
    if (pan < SERVO_MIN || pan > SERVO_MAX || tilt < SERVO_MIN || tilt > SERVO_MAX) return done(['ERR LIMIT'])
    const ok = () => {
      this.pan = pan; this.tilt = tilt
      done([tag.startsWith('AIM') ? `OK ${tag}` : `OK JOG ${fmtAngle(pan)} ${fmtAngle(tilt)}`])
    }
    if (this.latency.moveMs <= 0) return this.later(this.latency.cmdMs, ok)
    this.startJob(this.latency.moveMs, ok, () => done(['ERR STOP']))
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
