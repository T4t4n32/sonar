/**
 * Lógica PURA de framing y cola de peticiones (no importa Capacitor).
 * La usan BluetoothTransport (y sirve para probar el protocolo sin hardware).
 */
import { isTerminal } from './transport'

/** Error de timeout de una petición (distinguible con `instanceof`). */
export class TransportTimeout extends Error {
  constructor(public readonly line: string, public readonly ms: number) {
    super(`Sin respuesta a «${line}» en ${ms} ms`)
    this.name = 'TransportTimeout'
  }
}

/** Parte un flujo de texto en líneas: tolera \r\n, \n, \r y líneas partidas entre lecturas. */
export class LineFramer {
  private buf = ''
  /** Tope de una línea incompleta; evita crecer sin fin con ruido sin saltos de línea. */
  constructor(private readonly maxPending = 512) {}

  /** Añade un trozo y devuelve las líneas completas (sin vacías, sin caracteres de control). */
  push(chunk: string): string[] {
    this.buf += chunk
    const out: string[] = []
    let i: number
    // \r o \n delimitan; "\r\n" produce una línea vacía que se descarta
    while ((i = this.buf.search(/[\r\n]/)) >= 0) {
      const line = clean(this.buf.slice(0, i))
      this.buf = this.buf.slice(i + 1)
      if (line) out.push(line)
    }
    if (this.buf.length > this.maxPending) this.buf = this.buf.slice(-this.maxPending)
    return out
  }

  /** Descarta lo pendiente (p. ej. ruido de arranque al conectar). */
  reset(): void { this.buf = '' }
  get pending(): string { return this.buf }
}

// quita controles (ruido serial) y recorta
const clean = (s: string): string => s.replace(/[\u0000-\u001f\u007f]/g, '').trim()

/** ¿La línea es un evento asíncrono del módulo? Nunca forma parte de una respuesta. */
export const isEvent = (line: string): boolean => /^EVT\b/i.test(line)

/**
 * Terminal según la orden enviada:
 *  - TEST: emite `TEST START`, varios `OK (x,y)` y termina en `TEST DONE` / `TEST ABORT`
 *    (o `ERR …` si la rechaza). Un `OK` intermedio NO termina.
 *  - resto: `isTerminal` de transport.ts.
 */
export function terminalFor(request: string): (line: string) => boolean {
  if (/^\s*TEST\b/i.test(request)) {
    return l => /^(TEST (DONE|ABORT)|ERR)\b/i.test(l)
  }
  return isTerminal
}

interface Pending {
  line: string
  timeoutMs: number
  isDone: (l: string) => boolean
  lines: string[]
  resolve: (l: string[]) => void
  reject: (e: Error) => void
  timer?: ReturnType<typeof setTimeout>
  grace?: ReturnType<typeof setTimeout>
  sent: boolean
}

export interface QueueOptions {
  /** Tras `OK STOP` espera este tiempo por un `ERR STOP` tardío para incluirlo. Por defecto 150 ms. */
  stopGraceMs?: number
}

/**
 * Cola FIFO de peticiones: una sola en vuelo. Acumula líneas hasta la terminal;
 * lo que llega sin petición pendiente (o es EVT) va a `onUnsolicited`.
 */
export class RequestQueue {
  private queue: Pending[] = []
  private current: Pending | null = null
  /** STOP enviado mientras otra orden está en vuelo (no espera turno: seguridad del láser). */
  private urgent: Pending[] = []
  private unsolicited = new Set<(line: string) => void>()
  private stopGraceMs: number

  /** `send` escribe la línea cruda (sin `\n`; el transporte la añade). Debe rechazar si falla la escritura. */
  constructor(private readonly send: (line: string) => Promise<void>, opts: QueueOptions = {}) {
    this.stopGraceMs = opts.stopGraceMs ?? 150
  }

  onUnsolicited(cb: (line: string) => void): () => void {
    this.unsolicited.add(cb)
    return () => { this.unsolicited.delete(cb) }
  }

  get inFlight(): boolean { return this.current !== null }
  get waiting(): number { return this.queue.length }

  request(line: string, timeoutMs: number): Promise<string[]> {
    // STOP no hace cola: el módulo lo atiende siempre y de inmediato, aun con un disparo en curso.
    if (/^\s*STOP\s*$/i.test(line) && this.current && this.current.sent && !/^\s*STOP\b/i.test(this.current.line)) {
      return new Promise<string[]>((resolve, reject) => {
        const p: Pending = { line, timeoutMs, isDone: isTerminal, lines: [], resolve, reject, sent: true }
        p.timer = setTimeout(() => {
          this.urgent = this.urgent.filter(u => u !== p)
          this.settle(p, () => p.reject(new TransportTimeout(line, timeoutMs)))
        }, timeoutMs)
        this.urgent.push(p)
        this.send(line).then(undefined, (e: unknown) => {
          this.urgent = this.urgent.filter(u => u !== p)
          this.settle(p, () => p.reject(e instanceof Error ? e : new Error(String(e))))
        })
      })
    }
    return new Promise<string[]>((resolve, reject) => {
      this.queue.push({
        line, timeoutMs, isDone: terminalFor(line), lines: [], resolve, reject, sent: false,
      })
      this.pump()
    })
  }

  /** Una línea ya enmarcada llegó del módulo. */
  feed(line: string): void {
    const cur = this.current
    if (!cur || !cur.sent || isEvent(line)) { this.emit(line); return }

    // `OK STOP` es de un STOP urgente; el `ERR STOP` posterior pertenece a la orden interrumpida.
    if (this.urgent.length && /^OK STOP\b/i.test(line)) {
      const u = this.urgent.shift()!
      u.lines.push(line)
      this.settle(u, () => u.resolve(u.lines))
      return
    }

    // Ventana de gracia tras `OK STOP`: solo un `ERR STOP` se anexa; lo demás es no solicitado.
    if (cur.grace) {
      if (/^ERR\b/i.test(line)) cur.lines.push(line)
      else this.emit(line)
      return
    }

    cur.lines.push(line)
    if (!cur.isDone(line)) return

    if (/^\s*STOP\b/i.test(cur.line) && /^OK\b/i.test(line) && this.stopGraceMs > 0) {
      if (cur.timer) clearTimeout(cur.timer) // ya hay respuesta: el timeout deja de aplicar
      cur.grace = setTimeout(() => this.finish(cur), this.stopGraceMs)
      return
    }
    this.finish(cur)
  }

  /** Falla lo en vuelo y lo encolado (p. ej. al desconectar). */
  failAll(reason: Error): void {
    const all = [...(this.current ? [this.current] : []), ...this.urgent, ...this.queue]
    this.queue = []
    this.urgent = []
    for (const p of all) this.settle(p, () => p.reject(reason))
    this.current = null
  }

  private emit(line: string): void {
    for (const cb of [...this.unsolicited]) {
      try { cb(line) } catch { /* un oyente roto no debe tumbar el flujo */ }
    }
  }

  private pump(): void {
    if (this.current || this.queue.length === 0) return
    const p = this.queue.shift()!
    this.current = p
    p.timer = setTimeout(() => {
      if (this.current === p) {
        this.current = null
        this.settle(p, () => p.reject(new TransportTimeout(p.line, p.timeoutMs)))
        this.pump()
      }
    }, p.timeoutMs)
    p.sent = true // desde aquí cualquier línea entrante cuenta como respuesta
    this.send(p.line).then(
      undefined,
      (e: unknown) => {
        if (this.current !== p) return
        this.current = null
        this.settle(p, () => p.reject(e instanceof Error ? e : new Error(String(e))))
        this.pump()
      },
    )
  }

  private finish(p: Pending): void {
    if (this.current !== p) return
    this.current = null
    this.settle(p, () => p.resolve(p.lines))
    this.pump()
  }

  private settle(p: Pending, fn: () => void): void {
    if (p.timer) clearTimeout(p.timer)
    if (p.grace) clearTimeout(p.grace)
    fn()
  }
}
