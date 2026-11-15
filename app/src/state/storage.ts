/** Persistencia tolerante a fallos: si localStorage no existe o lanza, la app sigue funcionando en memoria. */
export interface KV { get(key: string): string | null; set(key: string, value: string): void; remove(key: string): void }

export const PREFIX = 'sonar.v1.'

export function localKV(): KV {
  return {
    get(key) { try { return globalThis.localStorage?.getItem(PREFIX + key) ?? null } catch { return null } },
    set(key, value) { try { globalThis.localStorage?.setItem(PREFIX + key, value) } catch { /* sin espacio o bloqueado */ } },
    remove(key) { try { globalThis.localStorage?.removeItem(PREFIX + key) } catch { /* nada */ } },
  }
}

/** KV en memoria (pruebas o cuando no hay almacenamiento). */
export function memoryKV(init: Record<string, string> = {}): KV & { data: Map<string, string> } {
  const data = new Map(Object.entries(init))
  return { data, get: k => data.get(k) ?? null, set: (k, v) => { data.set(k, v) }, remove: k => { data.delete(k) } }
}

export function loadJSON<T>(kv: KV, key: string, fallback: T): T {
  try {
    const raw = kv.get(key)
    const v = raw === null ? null : (JSON.parse(raw) as T | null)
    return v === null || v === undefined ? fallback : v
  } catch { return fallback }
}
export const saveJSON = (kv: KV, key: string, value: unknown): void => {
  try { kv.set(key, JSON.stringify(value)) } catch { /* nada */ }
}
