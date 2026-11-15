/**
 * Transporte Bluetooth clásico (SPP) sobre @e-is/capacitor-bluetooth-serial.
 * Los permisos, la lista de emparejados y el encendido del BT los resuelve el plugin local
 * `SonarBt` (android/.../SonarBtPlugin.java), porque el plugin serial no los pide en Android 13+.
 * El framing y la cola de peticiones viven en framing.ts (puro, con pruebas).
 */
import { Capacitor, registerPlugin } from '@capacitor/core'
import type { PluginListenerHandle } from '@capacitor/core'
import { BluetoothSerial } from '@e-is/capacitor-bluetooth-serial'
import { LineFramer, RequestQueue } from './framing'
import type { LineTransport, PeerInfo } from './transport'

interface SonarBtPlugin {
  ensurePermissions(): Promise<{ granted: boolean }>
  enableBluetooth(): Promise<{ enabled: boolean }>
  bonded(): Promise<{ devices: { name: string; address: string }[] }>
}
const SonarBt = registerPlugin<SonarBtPlugin>('SonarBt')

export interface BluetoothTransportOptions {
  /** Reconectar solo si el enlace se cae sin que el usuario lo pida. Por defecto true. */
  autoReconnect?: boolean
  /** Esperas (ms) entre intentos de reconexión; su longitud = nº de intentos. */
  reconnectDelaysMs?: number[]
  /** Cada cuánto verificar que el enlace sigue vivo (el plugin no avisa de caídas). Por defecto 2500 ms. */
  pollMs?: number
  /** Largo máximo de línea (el firmware limita a 64). Por defecto 64. */
  maxLine?: number
}

const DEFAULT_BACKOFF = [0, 800, 1600, 3200, 6400]
const sleep = (ms: number) => new Promise<void>(r => setTimeout(r, ms))
const msg = (e: unknown): string => (e instanceof Error ? e.message : typeof e === 'string' ? e : JSON.stringify(e))

export class BluetoothTransport implements LineTransport {
  readonly kind = 'bluetooth' as const

  private address: string | null = null
  private connected = false
  private manualClose = false
  private reconnecting = false
  private cancelReco = false
  private poll: ReturnType<typeof setInterval> | null = null
  private readHandle: PluginListenerHandle | null = null
  private readonly framer = new LineFramer()
  private readonly queue: RequestQueue
  private readonly stateCbs = new Set<(connected: boolean, reason?: string) => void>()
  private readonly opt: Required<BluetoothTransportOptions>
  private readonly onVisible = () => {
    if (!document.hidden && this.connected) void this.check()
  }

  constructor(opts: BluetoothTransportOptions = {}) {
    this.opt = {
      autoReconnect: opts.autoReconnect ?? true,
      reconnectDelaysMs: opts.reconnectDelaysMs ?? DEFAULT_BACKOFF,
      pollMs: opts.pollMs ?? 2500,
      maxLine: opts.maxLine ?? 64,
    }
    this.queue = new RequestQueue(line => this.write(line))
  }

  // ───────────── permisos / Bluetooth encendido ─────────────

  /**
   * Pide en tiempo de ejecución BLUETOOTH_CONNECT + BLUETOOTH_SCAN (Android 12+) o ubicación (≤ 11)
   * y, si el Bluetooth está apagado, muestra el diálogo del sistema para encenderlo.
   * `list()` y `connect()` ya lo llaman solos; la UI puede llamarlo antes para dar contexto.
   */
  async ensureReady(): Promise<void> {
    this.requireNative()
    const { granted } = await SonarBt.ensurePermissions()
    if (!granted) throw new Error('Permiso de Bluetooth denegado. Actívalo en Ajustes › Aplicaciones › SONAR › Permisos.')
    const { enabled } = await SonarBt.enableBluetooth()
    if (!enabled) throw new Error('El Bluetooth está apagado.')
  }

  private requireNative(): void {
    if (!Capacitor.isNativePlatform()) throw new Error('El Bluetooth solo funciona en la app Android (usa el modo simulado en el navegador).')
  }

  // ───────────── LineTransport ─────────────

  /**
   * Módulos cuyo nombre empieza por `prefix` (sin distinguir mayúsculas).
   * Devuelve los emparejados; si no hay ninguno (o `scan === true`) añade una búsqueda de ~5 s.
   */
  async list(prefix = 'SONAR', scan?: boolean): Promise<PeerInfo[]> {
    await this.ensureReady()
    const p = prefix.toLowerCase()
    const found = new Map<string, PeerInfo>()
    const add = (name: string, address: string, rssi?: number) => {
      if (name && address && name.toLowerCase().startsWith(p)) found.set(address, { id: address, name, rssi })
    }
    const { devices } = await SonarBt.bonded()
    for (const d of devices) add(d.name, d.address)
    if (scan === true || (scan === undefined && found.size === 0)) {
      try {
        const r = await BluetoothSerial.scan()
        for (const d of r.devices) add(d.name, d.address, d.rssi)
      } catch { /* la búsqueda es opcional: los emparejados ya están */ }
    }
    return [...found.values()].sort((a, b) => a.name.localeCompare(b.name))
  }

  /** `id` = dirección MAC devuelta por `list()`. */
  async connect(id: string): Promise<void> {
    await this.ensureReady()
    if (this.connected && this.address === id) return
    if (this.address) await this.teardown('cambio de módulo')
    this.manualClose = false
    this.cancelReco = true // un connect explícito corta cualquier reconexión en curso
    await this.open(id)
    this.address = id
    this.setConnected(true)
  }

  async disconnect(): Promise<void> {
    this.manualClose = true
    this.cancelReco = true
    await this.teardown('desconectado')
  }

  isConnected(): boolean { return this.connected }

  request(line: string, timeoutMs: number): Promise<string[]> {
    const l = line.replace(/[\r\n]+/g, ' ').trim()
    if (!this.connected) return Promise.reject(new Error('Sin enlace Bluetooth'))
    if (l.length > this.opt.maxLine) return Promise.reject(new Error(`Línea de ${l.length} caracteres (máx. ${this.opt.maxLine})`))
    return this.queue.request(l, timeoutMs)
  }

  onUnsolicited(cb: (line: string) => void): () => void { return this.queue.onUnsolicited(cb) }

  onStateChange(cb: (connected: boolean, reason?: string) => void): () => void {
    this.stateCbs.add(cb)
    return () => { this.stateCbs.delete(cb) }
  }

  // ───────────── extras ─────────────

  /** Dirección del módulo actual (o el último conectado). */
  get peerId(): string | null { return this.address }

  /**
   * Reintenta con espera creciente hasta `delaysMs.length` veces. Resuelve true si recuperó el enlace.
   * Emite `onStateChange(false, 'reconectando n/N')` en cada intento y `(true, 'reconectado')` al lograrlo.
   */
  async reconnect(delaysMs: number[] = this.opt.reconnectDelaysMs): Promise<boolean> {
    const id = this.address
    if (!id || this.reconnecting) return this.connected
    this.reconnecting = true
    this.cancelReco = false
    this.manualClose = false
    try {
      for (let i = 0; i < delaysMs.length; i++) {
        await sleep(delaysMs[i] ?? 0)
        if (this.cancelReco) return false
        this.emit(false, `reconectando ${i + 1}/${delaysMs.length}`)
        try {
          await this.open(id)
          this.setConnected(true, 'reconectado')
          return true
        } catch { /* siguiente intento */ }
      }
      this.emit(false, 'no se pudo reconectar')
      return false
    } finally {
      this.reconnecting = false
    }
  }

  /** Cancela una reconexión en curso. */
  cancelReconnect(): void { this.cancelReco = true }

  /** Libera listeners y timers (al cerrar la app). */
  async dispose(): Promise<void> {
    await this.disconnect()
    await this.readHandle?.remove()
    this.readHandle = null
  }

  // ───────────── internos ─────────────

  /** Abre el socket (seguro, y si falla, inseguro), activa las notificaciones por línea. */
  private async open(address: string): Promise<void> {
    try { await BluetoothSerial.disconnect({ address }) } catch { /* no había sesión */ }
    try {
      await BluetoothSerial.connect({ address })
    } catch (e1) {
      try { await BluetoothSerial.connectInsecure({ address }) }
      catch (e2) { throw new Error(`No se pudo conectar: ${msg(e2) || msg(e1)}`) }
    }
    if (!this.readHandle) {
      this.readHandle = await BluetoothSerial.addListener('onRead', r => this.onRead(r.value))
    }
    this.framer.reset()
    await BluetoothSerial.startNotifications({ address, delimiter: '\n' })
    this.address = address
    this.startPoll()
  }

  private onRead(value: string): void {
    for (const line of this.framer.push(value)) this.queue.feed(line)
  }

  private async write(line: string): Promise<void> {
    const address = this.address
    if (!address) throw new Error('Sin enlace Bluetooth')
    try {
      await BluetoothSerial.write({ address, value: line + '\n' })
    } catch (e) {
      this.dropped(`error de escritura: ${msg(e)}`)
      throw e
    }
  }

  private startPoll(): void {
    this.stopPoll()
    this.poll = setInterval(() => void this.check(), this.opt.pollMs)
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange', this.onVisible)
  }

  private stopPoll(): void {
    if (this.poll) clearInterval(this.poll)
    this.poll = null
    if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', this.onVisible)
  }

  /** Verifica el socket (Android lo cierra al pasar la app a segundo plano). */
  private async check(): Promise<void> {
    const address = this.address
    if (!address || !this.connected) return
    try {
      const { connected } = await BluetoothSerial.isConnected({ address })
      if (!connected) this.dropped('enlace perdido')
    } catch {
      this.dropped('enlace perdido')
    }
  }

  /** Caída inesperada: falla lo pendiente, avisa y (si aplica) reconecta. */
  private dropped(reason: string): void {
    if (!this.connected) return
    this.stopPoll()
    this.setConnected(false, reason)
    this.queue.failAll(new Error(reason))
    if (this.opt.autoReconnect && !this.manualClose) void this.reconnect()
  }

  private async teardown(reason: string): Promise<void> {
    const address = this.address
    this.stopPoll()
    this.queue.failAll(new Error(reason))
    if (address) {
      try { await BluetoothSerial.stopNotifications({ address }) } catch { /* ya cerrado */ }
      try { await BluetoothSerial.disconnect({ address }) } catch { /* ya cerrado */ }
    }
    if (reason !== 'cambio de módulo') this.address = null
    this.setConnected(false, reason)
  }

  private setConnected(c: boolean, reason?: string): void {
    const changed = this.connected !== c
    this.connected = c
    if (changed || reason) this.emit(c, reason)
  }

  private emit(c: boolean, reason?: string): void {
    for (const cb of [...this.stateCbs]) {
      try { cb(c, reason) } catch { /* oyente roto */ }
    }
  }
}
