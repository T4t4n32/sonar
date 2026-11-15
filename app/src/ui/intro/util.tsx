/** Piezas compartidas por las escenas del tutorial: tablero SVG, flota de ejemplo y el helper de tiempos. */
import type { ComponentChildren } from 'preact'

/** Estilo de una animación: empieza en la fracción `o` de la escena y dura la fracción `l`. */
export const t = (o: number, l = 0.1): string => `--o:${o};--l:${l}`

const gridPath = (n: number, s: number): string => {
  let d = ''
  for (let i = 0; i <= n; i++) d += `M0 ${i * s}H${n * s}M${i * s} 0V${n * s}`
  return d
}
export const GRID = gridPath(20, 10)

export interface ShipDef { k: 'sub' | 'bote'; x: number; y: number; w: number; h: number }
/** Flota de ejemplo: 2 submarinos de 4 y 3 embarcaciones de 2 (14 casillas), sin solaparse. */
export const FLEET: ShipDef[] = [
  { k: 'sub', x: 2, y: 3, w: 4, h: 1 },
  { k: 'sub', x: 14, y: 11, w: 1, h: 4 },
  { k: 'bote', x: 9, y: 14, w: 2, h: 1 },
  { k: 'bote', x: 5, y: 8, w: 1, h: 2 },
  { k: 'bote', x: 13, y: 4, w: 2, h: 1 },
]

export function shipSep(s: ShipDef): string {
  let d = ''
  const n = Math.max(s.w, s.h)
  for (let i = 1; i < n; i++) d += s.w > s.h ? `M${(s.x + i) * 10} ${s.y * 10 + 2}V${(s.y + 1) * 10 - 2}` : `M${s.x * 10 + 2} ${(s.y + i) * 10}H${(s.x + 1) * 10 - 2}`
  return d
}

export function Ship({ s, cls = '' }: { s: ShipDef; cls?: string }) {
  return (
    <>
      <rect class={`shp ${s.k} ${cls}`} x={s.x * 10 + 1} y={s.y * 10 + 1} width={s.w * 10 - 2} height={s.h * 10 - 2} rx={3.5} />
      <path class={`shpc ${s.k} ${cls}`} d={shipSep(s)} />
    </>
  )
}

/** Tablero 20×20 (200×200 unidades; 10 por casilla). Los hijos se dibujan encima. */
export function Board({ children, vb = '0 0 200 200', cls = '' }: { children?: ComponentChildren; vb?: string; cls?: string }) {
  return (
    <svg class={`bd ${cls}`} viewBox={vb} aria-hidden="true">
      <rect class="bdbg" width={200} height={200} rx={3} />
      <path class="bdgrid" d={GRID} />
      <rect class="bdframe" width={200} height={200} rx={3} />
      {children}
    </svg>
  )
}

/** Centro de la casilla (cx, cy) en unidades del tablero. */
export const cc = (c: number): number => c * 10 + 5
