/**
 * Transporte de LÍNEAS (el protocolo es texto, una línea por mensaje; ver PROTOCOLO.md).
 * Tres implementaciones: Bluetooth SPP (Capacitor), Wi-Fi HTTP de mantenimiento y Simulado.
 */
export interface PeerInfo { id: string; name: string; rssi?: number }

export interface LineTransport {
  readonly kind: 'bluetooth' | 'wifi' | 'sim'
  /** módulos disponibles (emparejados o conocidos) cuyo nombre empieza por el prefijo */
  list(prefix?: string): Promise<PeerInfo[]>
  connect(id: string): Promise<void>
  disconnect(): Promise<void>
  isConnected(): boolean
  /** Envía UNA línea y devuelve las líneas de respuesta hasta la terminal. Rechaza por timeout. */
  request(line: string, timeoutMs: number): Promise<string[]>
  /** líneas no solicitadas (p. ej. EVT …) y cambios de estado */
  onUnsolicited(cb: (line: string) => void): () => void
  onStateChange(cb: (connected: boolean, reason?: string) => void): () => void
}

/** Línea terminal de cada orden (para saber cuándo acabó de responder). */
export const isTerminal = (line: string): boolean =>
  /^(OK|ERR|PONG|HELLO|CAL|MODE|ARM|PT|LASER|CORNERS|MAP|TEST DONE|TEST ABORT)\b/i.test(line)
