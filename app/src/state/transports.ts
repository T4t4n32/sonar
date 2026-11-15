/** Fábrica de transportes. Bluetooth y Wi-Fi se cargan bajo demanda (el simulado va siempre). */
import { SimTransport, type SimOptions } from '../transport/sim'
import type { LineTransport } from '../transport/transport'

export type TransportKind = LineTransport['kind']
export const KIND_LABEL: Record<TransportKind, string> = { bluetooth: 'Bluetooth', wifi: 'Wi-Fi mantenimiento', sim: 'Simulado' }

/** Latencias del simulado en la app: se nota el disparo, el TEST dura ~3 s. */
export const APP_SIM: SimOptions = { latency: { shotMs: 900, testStepMs: 600, markMs: 600, cmdMs: 30 } }

export async function createTransport(kind: TransportKind): Promise<LineTransport> {
  switch (kind) {
    case 'sim': return new SimTransport(APP_SIM)
    case 'wifi': { const m = await import('../transport/wifi'); return new m.WifiTransport() }
    case 'bluetooth': { const m = await import('../transport/bluetooth'); return new m.BluetoothTransport() }
  }
}

export const isNative = (): boolean => {
  try { return Boolean((globalThis as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor?.isNativePlatform?.()) } catch { return false }
}
