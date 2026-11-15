/** Protocolo de líneas v1+v2 (ver docs/03-firmware-y-app/PROTOCOLO.md). Funciones puras. */
import { N, type Coord } from './types'

export const MAX_LINE = 64
export const ERROR_CODES = ['RANGE', 'FORMAT', 'LIMIT', 'BUSY', 'STOP', 'DISARMED', 'UNKNOWN', 'EMPTY', 'TOOLONG', 'STORE'] as const
export type ErrCode = (typeof ERROR_CODES)[number]
export type ModuleMode = 'BT' | 'WIFI'
export interface CalValues { x: number; y: number; h: number; panTrim: number; tiltTrim: number }

export const isValidCoord = (c: Coord): boolean =>
  Number.isInteger(c.x) && Number.isInteger(c.y) && c.x >= 1 && c.x <= N && c.y >= 1 && c.y <= N

/** Línea de disparo: "(x,y)". */
export const fire = (c: Coord): string => `(${c.x},${c.y})`

// ---------- respuestas módulo -> app ----------
export type Reply =
  | { t: 'ok-shot'; at: Coord }
  | { t: 'ok'; what: 'STOP' | 'MARK' | 'CAL' | 'SAVE' | 'RESET' | 'MODE'; mode?: ModuleMode }
  | { t: 'err'; code: ErrCode }
  | { t: 'pong'; name: string; version: string }
  | { t: 'hello'; fw: string; name: string; mode: ModuleMode; caps: string[] }
  | { t: 'test-start' }
  | { t: 'test-done' }
  | { t: 'test-abort' }
  | { t: 'cal'; cal: CalValues }
  | { t: 'mode'; mode: ModuleMode }
  | { t: 'arm'; state: 'NOTREQ' | 'OFF' | 'ON'; seconds?: number }
  | { t: 'unknown'; line: string }

const COORD_RE = /^\(\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\)$/
const toMode = (s: string | undefined): ModuleMode | null => {
  const u = (s ?? '').toUpperCase()
  return u === 'BT' || u === 'WIFI' ? u : null
}

export function parseReply(raw: string): Reply {
  const line = raw.replace(/[\r\n]+$/g, '').trim()
  const unknown: Reply = { t: 'unknown', line }
  if (!line) return unknown
  const p = line.split(/\s+/)
  const w = p[0]!.toUpperCase()
  const w2 = (p[1] ?? '').toUpperCase()
  switch (w) {
    case 'OK': {
      const m = COORD_RE.exec(line.slice(2).trim())
      if (m) return { t: 'ok-shot', at: { x: Number(m[1]), y: Number(m[2]) } }
      if (p.length === 2 && (w2 === 'STOP' || w2 === 'MARK' || w2 === 'CAL' || w2 === 'SAVE' || w2 === 'RESET')) return { t: 'ok', what: w2 }
      if (p.length === 3 && w2 === 'MODE') { const mo = toMode(p[2]); if (mo) return { t: 'ok', what: 'MODE', mode: mo } }
      return unknown
    }
    case 'ERR': {
      const code = w2 as ErrCode
      return p.length === 2 && (ERROR_CODES as readonly string[]).includes(code) ? { t: 'err', code } : unknown
    }
    case 'PONG':
      return p.length >= 2 ? { t: 'pong', name: p[1]!, version: p[2] ?? '' } : unknown
    case 'HELLO': {
      // HELLO SONAR 2 <fw> <nombre> <modo> <caps>
      if (p.length < 7 || p[1]!.toUpperCase() !== 'SONAR') return unknown
      const mode = toMode(p[5])
      if (!mode) return unknown
      const caps = p[6] === '-' ? [] : p[6]!.split(',').filter(Boolean)
      return { t: 'hello', fw: p[3]!, name: p[4]!, mode, caps }
    }
    case 'TEST':
      if (w2 === 'START') return { t: 'test-start' }
      if (w2 === 'DONE') return { t: 'test-done' }
      if (w2 === 'ABORT') return { t: 'test-abort' }
      return unknown
    case 'CAL': {
      if (p.length !== 6) return unknown
      const n = p.slice(1).map(Number)
      if (n.some(v => !Number.isFinite(v))) return unknown
      return { t: 'cal', cal: { x: n[0]!, y: n[1]!, h: n[2]!, panTrim: n[3]!, tiltTrim: n[4]! } }
    }
    case 'MODE': {
      const mo = toMode(p[1])
      return p.length === 2 && mo ? { t: 'mode', mode: mo } : unknown
    }
    case 'ARM': {
      if (p.length === 2 && (w2 === 'NOTREQ' || w2 === 'OFF')) return { t: 'arm', state: w2 }
      if (p.length === 3 && w2 === 'ON' && /^\d+$/.test(p[2]!)) return { t: 'arm', state: 'ON', seconds: Number(p[2]) }
      return unknown
    }
    default:
      return unknown
  }
}

/** Mensaje claro en español para un código de error del módulo. */
export function friendlyError(code: ErrCode | string): string {
  switch (code.toUpperCase()) {
    case 'RANGE': return 'Coordenada fuera del tablero: x e y deben estar entre 1 y 20.'
    case 'FORMAT': return 'Orden mal escrita. El disparo debe ser (x,y) con paréntesis.'
    case 'LIMIT': return 'El láser no alcanza esa celda con la calibración actual (límite mecánico).'
    case 'BUSY': return 'El módulo está ocupado terminando otra orden. Espera un momento o pulsa STOP.'
    case 'STOP': return 'Disparo detenido por STOP.'
    case 'DISARMED': return 'El láser está desarmado: pulsa el botón de armado en el módulo.'
    case 'UNKNOWN': return 'El módulo no reconoce esa orden.'
    case 'EMPTY': return 'Se envió una línea vacía.'
    case 'TOOLONG': return 'La orden supera los 64 caracteres.'
    case 'STORE': return 'El módulo no pudo guardar en su memoria (NVS).'
    default: return `Error del módulo: ${code}`
  }
}

// ---------- órdenes app -> módulo (usado por el simulado y pruebas) ----------
export type Command =
  | { t: 'fire'; at: Coord }
  | { t: 'test' } | { t: 'stop' } | { t: 'ping' } | { t: 'hello' } | { t: 'arm' }
  | { t: 'mark'; hit: boolean }
  | { t: 'cal-show' } | { t: 'cal-save' } | { t: 'cal-reset' }
  | { t: 'cal-set'; cal: CalValues }
  | { t: 'mode-query' }
  | { t: 'mode-set'; mode: ModuleMode }
  | { t: 'error'; code: ErrCode }

const CAL_RANGES: [number, number][] = [[-200, 400], [-300, 400], [50, 400], [-10, 10], [-10, 10]]

export function parseCommand(raw: string): Command {
  const line = raw.replace(/[\r\n]+$/g, '')
  if (line.length > MAX_LINE) return { t: 'error', code: 'TOOLONG' }
  const s = line.trim()
  if (!s) return { t: 'error', code: 'EMPTY' }
  const err = (code: ErrCode): Command => ({ t: 'error', code })
  if (s.startsWith('(')) {
    const m = COORD_RE.exec(s)
    if (!m) return err('FORMAT')
    const at = { x: Number(m[1]), y: Number(m[2]) }
    return isValidCoord(at) ? { t: 'fire', at } : err('RANGE')
  }
  const p = s.split(/\s+/)
  const w = p[0]!.toUpperCase()
  const a = p.slice(1).map(x => x.toUpperCase())
  switch (w) {
    case 'PING': return a.length ? err('FORMAT') : { t: 'ping' }
    case 'TEST': return a.length ? err('FORMAT') : { t: 'test' }
    case 'STOP': return a.length ? err('FORMAT') : { t: 'stop' }
    case 'HELLO': return a.length ? err('FORMAT') : { t: 'hello' }
    case 'ARM': return a.length ? err('FORMAT') : { t: 'arm' }
    case 'MARK':
      if (a.length !== 1) return err('FORMAT')
      return a[0] === 'HIT' || a[0] === 'MISS' ? { t: 'mark', hit: a[0] === 'HIT' } : err('UNKNOWN')
    case 'MODE':
      if (a.length === 0) return { t: 'mode-query' }
      if (a.length > 1) return err('FORMAT')
      return a[0] === 'BT' || a[0] === 'WIFI' ? { t: 'mode-set', mode: a[0] } : err('UNKNOWN')
    case 'CAL': {
      if (a.length === 0) return err('FORMAT')
      const sub = a[0]
      if (sub === 'SHOW') return a.length === 1 ? { t: 'cal-show' } : err('FORMAT')
      if (sub === 'SAVE') return a.length === 1 ? { t: 'cal-save' } : err('FORMAT')
      if (sub === 'RESET') return a.length === 1 ? { t: 'cal-reset' } : err('FORMAT')
      if (sub === 'SET') {
        if (a.length !== 6) return err('FORMAT')
        const n = p.slice(2).map(Number)
        if (n.some(v => !Number.isFinite(v))) return err('FORMAT')
        if (n.some((v, i) => v < CAL_RANGES[i]![0] || v > CAL_RANGES[i]![1])) return err('RANGE')
        return { t: 'cal-set', cal: { x: n[0]!, y: n[1]!, h: n[2]!, panTrim: n[3]!, tiltTrim: n[4]! } }
      }
      return err('UNKNOWN')
    }
    default: return err('UNKNOWN')
  }
}

const f2 = (v: number) => v.toFixed(2)
export const formatCal = (c: CalValues): string => `CAL ${f2(c.x)} ${f2(c.y)} ${f2(c.h)} ${f2(c.panTrim)} ${f2(c.tiltTrim)}`
