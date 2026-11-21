import { describe, expect, it } from 'vitest'
import { applyHomography, DEFAULT_MOUNT, fitHomography, fromUV, pointedCell, toUV, truthAngles } from './gimbal'

const CORNERS = [{ x: 1, y: 1 }, { x: 20, y: 1 }, { x: 20, y: 20 }, { x: 1, y: 20 }]

describe('gimbal: gnomónicas', () => {
  it('toUV y fromUV son inversas', () => {
    for (const a of [{ pan: 90, tilt: 90 }, { pan: 75, tilt: 101 }, { pan: 110, tilt: 70 }]) {
      const { u, v } = toUV(a)
      const b = fromUV(u, v)
      expect(b.pan).toBeCloseTo(a.pan, 9)
      expect(b.tilt).toBeCloseTo(a.tilt, 9)
    }
  })
})

describe('gimbal: montaje verdadero', () => {
  it('pointedCell invierte truthAngles', () => {
    for (const [x, y] of [[1, 1], [20, 1], [11, 11], [5, 17]]) {
      const p = pointedCell(DEFAULT_MOUNT, truthAngles(DEFAULT_MOUNT, x!, y!))
      expect(p.x).toBeCloseTo(x!, 6)
      expect(p.y).toBeCloseTo(y!, 6)
    }
  })
  it('las esquinas quedan dentro de 15..165 y el montaje exige calibrar', () => {
    for (const c of CORNERS) {
      const a = truthAngles(DEFAULT_MOUNT, c.x, c.y)
      expect(a.pan).toBeGreaterThan(15); expect(a.pan).toBeLessThan(165)
      expect(a.tilt).toBeGreaterThan(15); expect(a.tilt).toBeLessThan(165)
    }
    // sin calibrar (apuntar «al centro» a 90/90) no cae en la celda central
    const p = pointedCell(DEFAULT_MOUNT, { pan: 90, tilt: 90 })
    expect(Math.hypot(p.x - 10.5, p.y - 10.5)).toBeGreaterThan(1)
  })
})

describe('gimbal: homografía por 4 esquinas', () => {
  it('reproduce las 400 celdas con error ≈ 0', () => {
    const H = fitHomography(CORNERS, CORNERS.map(c => truthAngles(DEFAULT_MOUNT, c.x, c.y)))!
    expect(H).not.toBeNull()
    let worst = 0
    for (let x = 1; x <= 20; x++) for (let y = 1; y <= 20; y++) {
      const a = applyHomography(H, x, y)!
      const t = truthAngles(DEFAULT_MOUNT, x, y)
      worst = Math.max(worst, Math.abs(a.pan - t.pan), Math.abs(a.tilt - t.tilt))
    }
    expect(worst).toBeLessThan(1e-6)
  })
  it('esquinas con ruido de 0,05° dan un apuntado dentro de media celda', () => {
    const noisy = CORNERS.map((c, i) => { const a = truthAngles(DEFAULT_MOUNT, c.x, c.y); return { pan: a.pan + (i % 2 ? 0.05 : -0.05), tilt: a.tilt + (i < 2 ? 0.05 : -0.05) } })
    const H = fitHomography(CORNERS, noisy)!
    for (let x = 1; x <= 20; x += 3) for (let y = 1; y <= 20; y += 3) {
      const p = pointedCell(DEFAULT_MOUNT, applyHomography(H, x, y)!)
      expect(Math.hypot(p.x - x, p.y - y)).toBeLessThan(0.5)
    }
  })
  it('puntos alineados o repetidos → null', () => {
    const a = truthAngles(DEFAULT_MOUNT, 1, 1)
    expect(fitHomography(CORNERS, [a, a, a, a])).toBeNull()
    const line = [1, 7, 13, 20].map(x => truthAngles(DEFAULT_MOUNT, x, 5))
    expect(fitHomography(CORNERS, line)).toBeNull()
  })
})
