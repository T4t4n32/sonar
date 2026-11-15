/**
 * Contratos compartidos de SONAR (app). Fuente: docs/03-firmware-y-app/APP_SONAR.md
 * Coordenadas: 1..20, SIEMPRE (x,y) con x primero. (1,1) = esquina posterior-izquierda.
 */
export const N = 20
export type Coord = { x: number; y: number }
export type Orient = 'H' | 'V'

/** Flota reglamentaria: 3 embarcaciones de 2 y 2 submarinos de 4 (14 casillas). */
export type ShipKind = 'embarcacion' | 'submarino'
export interface ShipSpec { id: string; kind: ShipKind; len: number }
export const FLEET_SPEC: ShipSpec[] = [
  { id: 'E1', kind: 'embarcacion', len: 2 },
  { id: 'E2', kind: 'embarcacion', len: 2 },
  { id: 'E3', kind: 'embarcacion', len: 2 },
  { id: 'S1', kind: 'submarino', len: 4 },
  { id: 'S2', kind: 'submarino', len: 4 },
]
export const FLEET_CELLS = 14

export interface PlacedShip { id: string; kind: ShipKind; len: number; x: number; y: number; orient: Orient }

/** Resultado de un disparo sobre un tablero. */
export type ShotResult = 'hit' | 'miss' | 'sunk'

/** Un disparo propio al tablero rival, tal como lo vive la partida. */
export interface Shot {
  n: number              // consecutivo desde 1
  at: Coord
  firedAt: number        // epoch ms
  /** undefined mientras espera el veredicto del testigo */
  result?: ShotResult
  /** si se hundió, qué barco (largo) */
  sunkLen?: number
  /** casillas del barco hundido (las fija board.setVerdict) */
  sunkCells?: Coord[]
  /** milisegundos entre disparo y veredicto */
  decidedMs?: number
}

/** Estado de enlace con un módulo. */
export type LinkState = 'off' | 'connecting' | 'on' | 'busy' | 'error'

/** Mapa de probabilidad (para el asistente de tiro): peso por celda, 0 si ya disparada. */
export type Heat = number[] // longitud N*N, índice (y-1)*N + (x-1)

export const idx = (c: Coord) => (c.y - 1) * N + (c.x - 1)
export const inBoard = (c: Coord) => c.x >= 1 && c.x <= N && c.y >= 1 && c.y <= N
export const key = (c: Coord) => `${c.x},${c.y}`
