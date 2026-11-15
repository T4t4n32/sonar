/**
 * Transporte Wi-Fi de mantenimiento: GET <base>/cmd?l=<línea> → texto plano, una línea por respuesta.
 * El celular debe estar unido al AP del módulo (SONAR-A/B). En Android se usa CapacitorHttp (nativo)
 * para esquivar el bloqueo de contenido mixto del WebView; el HTTP «en claro» solo se permite a
 * 192.168.4.1 (android/.../res/xml/network_security_config.xml).
 */
import { Capacitor, CapacitorHttp, registerPlugin } from '@capacitor/core'
import type { LineTransport, PeerInfo } from './transport'

export const WIFI_DEFAULT_BASE = 'http://192.168.4.1'
export const WIFI_PEER_ID = 'wifi-mantenimiento'

/** Inyectable para pruebas: hace un GET y devuelve estado + cuerpo de texto. */
export type HttpGet = (url: string, timeoutMs: number) => Promise<{ status: number; text: string }>

interface SonarBtWifi { bindWifi(): Promise<{ bound: boolean }> }

/** GET real: CapacitorHttp en Android/iOS; fetch con AbortController en el navegador. */
export const defaultHttpGet: HttpGet = async (url, timeoutMs) => {
  if (Capacitor.isNativePlatform()) {
    const r = await CapacitorHttp.get({
      url, responseType: 'text', connectTimeout: timeoutMs, readTimeout: timeoutMs,
    })
    return { status: r.status, text: typeof r.data === 'string' ? r.data : String(r.data ?? '') }
  }
  const ctl = new AbortController()
  const t = setTimeout(() => ctl.abort(), timeoutMs)
  try {
    const r = await fetch(url, { signal: ctl.signal })
    return { status: r.status, text: await r.text() }
  } finally {
    clearTimeout(t)
  }
}

/** Tope duro por si el GET inyectado/nativo ignora su propio timeout. */
const withTimeout = <T>(p: Promise<T>, ms: number): Promise<T> =>
  new Promise<T>((resolve, reject) => {
    const t = setTimeout(() => reject(new Error(`timeout de ${ms} ms`)), ms + 250)
    p.then(v => { clearTimeout(t); resolve(v) }, e => { clearTimeout(t); reject(e) })
  })

export interface WifiTransportOptions {
  /** URL base del módulo. Por defecto http://192.168.4.1 */
  baseUrl?: string
  /** GET inyectable (pruebas). */
  httpGet?: HttpGet
  /** Atar el proceso a la red Wi-Fi (Android la desvía por datos móviles si no tiene internet). Por defecto true. */
  bindWifi?: boolean
}

export class WifiTransport implements LineTransport {
  readonly kind = 'wifi' as const

  private connected = false
  private chain: Promise<unknown> = Promise.resolve()
  private readonly base: string
  private readonly get: HttpGet
  private readonly bind: boolean
  private readonly stateCbs = new Set<(connected: boolean, reason?: string) => void>()
  private readonly unsolCbs = new Set<(line: string) => void>()

  constructor(opts: WifiTransportOptions = {}) {
    this.base = (opts.baseUrl ?? WIFI_DEFAULT_BASE).replace(/\/+$/, '')
    this.get = opts.httpGet ?? defaultHttpGet
    this.bind = opts.bindWifi ?? true
  }

  /** Un único par: el AP de mantenimiento (no hay descubrimiento por HTTP). */
  async list(): Promise<PeerInfo[]> {
    return [{ id: WIFI_PEER_ID, name: 'Wi-Fi mantenimiento' }]
  }

  /** Comprueba que el módulo responde (PING) antes de dar el enlace por bueno. */
  async connect(_id: string = WIFI_PEER_ID): Promise<void> {
    if (this.bind && Capacitor.isNativePlatform()) {
      try { await registerPlugin<SonarBtWifi>('SonarBt').bindWifi() } catch { /* sigue por la red por defecto */ }
    }
    this.connected = true // permite que request() corra el PING
    try {
      await this.request('PING', 3000)
    } catch (e) {
      this.connected = false
      throw new Error(`El módulo no responde en ${this.base}. ¿Estás unido a su Wi-Fi? (${e instanceof Error ? e.message : e})`)
    }
    this.emit(true)
  }

  async disconnect(): Promise<void> {
    if (!this.connected) return
    this.connected = false
    this.emit(false, 'desconectado')
  }

  isConnected(): boolean { return this.connected }

  /** Una petición a la vez (cadena de promesas). Una línea de cuerpo = una línea de respuesta. */
  request(line: string, timeoutMs: number): Promise<string[]> {
    const run = async (): Promise<string[]> => {
      if (!this.connected) throw new Error('Sin enlace Wi-Fi')
      const l = line.replace(/[\r\n]+/g, ' ').trim()
      const url = `${this.base}/cmd?l=${encodeURIComponent(l)}`
      let res: { status: number; text: string }
      try {
        res = await withTimeout(this.get(url, timeoutMs), timeoutMs)
      } catch (e) {
        const m = e instanceof Error ? e.message : String(e)
        if (this.connected) { this.connected = false; this.emit(false, `sin respuesta: ${m}`) }
        throw new Error(`Sin respuesta a «${l}»: ${m}`)
      }
      if (res.status < 200 || res.status >= 300) throw new Error(`HTTP ${res.status} a «${l}»`)
      return res.text.split(/\r?\n/).map(s => s.trim()).filter(Boolean)
    }
    const p = this.chain.then(run, run)
    this.chain = p.catch(() => undefined) // un fallo no atasca la cadena
    return p
  }

  /** HTTP no puede empujar eventos: el oyente existe por contrato pero no recibirá nada. */
  onUnsolicited(cb: (line: string) => void): () => void {
    this.unsolCbs.add(cb)
    return () => { this.unsolCbs.delete(cb) }
  }

  onStateChange(cb: (connected: boolean, reason?: string) => void): () => void {
    this.stateCbs.add(cb)
    return () => { this.stateCbs.delete(cb) }
  }

  private emit(c: boolean, reason?: string): void {
    for (const cb of [...this.stateCbs]) {
      try { cb(c, reason) } catch { /* oyente roto */ }
    }
  }
}
