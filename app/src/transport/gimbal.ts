/**
 * Gimbal pan-tilt VIRTUAL y matemática de la calibración por esquinas (la usa el módulo simulado).
 *
 * Modelo: pan (eje vertical) + tilt (eje horizontal) con los ejes cortándose en el pivote. Con los ángulos de servo
 * relativos al centro (90°), la dirección del rayo tiene coordenadas gnomónicas
 *     u = tan(pan),  v = tan(tilt) / cos(pan)
 * y la proyección central del pivote sobre CUALQUIER plano (pared vertical, tablero horizontal, inclinado…) es una
 * homografía entre las coordenadas del plano (x, y de la celda) y (u, v). Cuatro puntos la determinan por completo.
 */
export interface Angles { pan: number; tilt: number }          // grados de servo (90 = centro)
export interface Homography { h: number[] }                    // 8 coeficientes, h9 = 1

const D2R = Math.PI / 180
const CENTER = 90

export const toUV = (a: Angles): { u: number; v: number } => {
  const th = (a.pan - CENTER) * D2R
  const ph = (a.tilt - CENTER) * D2R
  return { u: Math.tan(th), v: Math.tan(ph) / Math.cos(th) }
}
export const fromUV = (u: number, v: number): Angles => {
  const th = Math.atan(u)
  const ph = Math.atan(v * Math.cos(th))
  return { pan: CENTER + th / D2R, tilt: CENTER + ph / D2R }
}

/** Coordenadas del plano normalizadas (buen condicionamiento): centro del tablero (10.5, 10.5) → (0, 0). */
const norm = (x: number, y: number): [number, number] => [(x - 10.5) / 9.5, (y - 10.5) / 9.5]

/** Resuelve A·s = b (n×n) por eliminación con pivote parcial; null si es singular. */
function solve(A: number[][], b: number[]): number[] | null {
  const n = b.length
  const M = A.map((row, i) => [...row, b[i]!])
  for (let c = 0; c < n; c++) {
    let p = c
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r]![c]!) > Math.abs(M[p]![c]!)) p = r
    if (Math.abs(M[p]![c]!) < 1e-10) return null
    ;[M[c], M[p]] = [M[p]!, M[c]!]
    for (let r = c + 1; r < n; r++) {
      const f = M[r]![c]! / M[c]![c]!
      for (let k = c; k <= n; k++) M[r]![k]! -= f * M[c]![k]!
    }
  }
  const s = new Array<number>(n).fill(0)
  for (let r = n - 1; r >= 0; r--) {
    let v = M[r]![n]!
    for (let k = r + 1; k < n; k++) v -= M[r]![k]! * s[k]!
    s[r] = v / M[r]![r]!
  }
  return s.every(Number.isFinite) ? s : null
}

/** Homografía (x, y) → (u, v) a partir de 4 correspondencias. null si es degenerada (puntos alineados o repetidos). */
export function fitHomography(plane: { x: number; y: number }[], angles: Angles[]): Homography | null {
  if (plane.length !== 4 || angles.length !== 4) return null
  const A: number[][] = []
  const b: number[] = []
  for (let i = 0; i < 4; i++) {
    const [x, y] = norm(plane[i]!.x, plane[i]!.y)
    const { u, v } = toUV(angles[i]!)
    if (!Number.isFinite(u) || !Number.isFinite(v)) return null
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u)
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v)
  }
  const h = solve(A, b)
  return h ? { h } : null
}

/** Ángulos de servo que apuntan a la celda (x, y) según la homografía; null si cae detrás del pivote. */
export function applyHomography(H: Homography, x: number, y: number): Angles | null {
  const [xn, yn] = norm(x, y)
  const h = H.h
  const w = h[6]! * xn + h[7]! * yn + 1
  if (!(Math.abs(w) > 1e-9)) return null
  const u = (h[0]! * xn + h[1]! * yn + h[2]!) / w
  const v = (h[3]! * xn + h[4]! * yn + h[5]!) / w
  return Number.isFinite(u) && Number.isFinite(v) ? fromUV(u, v) : null
}

// ---------- montaje «verdadero» del simulador (lo que el módulo físico no sabe) ----------
/** Pared plana a D mm del pivote, centrada con un desplazamiento y un giro: la calibración debe absorberlos. */
export interface Mount { dMm: number; offX: number; offZ: number; rollDeg: number; cellMm: number }
export const DEFAULT_MOUNT: Mount = { dMm: 300, offX: 12, offZ: -20, rollDeg: 2, cellMm: 10 }
/** Error de la geometría «de fábrica» (modo GEO, sin calibrar): el apuntado sale desviado. */
export const GEO_BIAS: Angles = { pan: 3, tilt: -2 }

/** Ángulos exactos que apuntan al centro de la celda (x, y) con ese montaje. */
export function truthAngles(m: Mount, x: number, y: number): Angles {
  const px = (x - 10.5) * m.cellMm
  const pz = (y - 10.5) * m.cellMm
  const r = m.rollDeg * D2R
  const X = px * Math.cos(r) - pz * Math.sin(r) + m.offX
  const Z = px * Math.sin(r) + pz * Math.cos(r) + m.offZ
  return fromUV(X / m.dMm, Z / m.dMm)
}

/** Celda (fraccionaria, 1 = centro de la primera) donde cae el rayo con esos ángulos; inversa de truthAngles. */
export function pointedCell(m: Mount, a: Angles): { x: number; y: number } {
  const { u, v } = toUV(a)
  const X = u * m.dMm - m.offX
  const Z = v * m.dMm - m.offZ
  const r = m.rollDeg * D2R
  const px = X * Math.cos(r) + Z * Math.sin(r)
  const pz = -X * Math.sin(r) + Z * Math.cos(r)
  return { x: px / m.cellMm + 10.5, y: pz / m.cellMm + 10.5 }
}
