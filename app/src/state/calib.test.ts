import { afterEach, describe, expect, it, vi } from 'vitest'
import { seededRng } from '../core/fleet'
import { SimTransport, SIM_ID, type SimOptions } from '../transport/sim'
import { createApp, type App } from './store'
import { memoryKV } from './storage'

const apps: App[] = []
function mk(sim: SimOptions = {}, kv = memoryKV()) {
  const tr = new SimTransport({ rng: seededRng(7), caps: ['grid'], ...sim })
  const app = createApp({ makeTransport: async () => tr, storage: kv, feedback: () => undefined, heartbeatMs: 3_600_000, reconnectDelaysMs: [5, 5, 5], defaultKind: 'sim' })
  apps.push(app)
  return { app, tr, kv }
}
async function ready(sim: SimOptions = {}, kv = memoryKV()) {
  const r = mk(sim, kv)
  await r.app.init()
  expect(await r.app.connect(SIM_ID)).toBe(true)
  return r
}
afterEach(async () => { vi.useRealTimers(); await Promise.all(apps.splice(0).map(a => a.dispose())) })

const CORNERS = [{ x: 1, y: 1 }, { x: 20, y: 1 }, { x: 20, y: 20 }, { x: 1, y: 20 }]
/** El operario «perfecto»: pone el gimbal virtual exactamente en la celda y registra el punto n. */
async function place(r: Awaited<ReturnType<typeof ready>>, n: number, c: { x: number; y: number }) {
  const a = r.tr.truth(c)
  r.tr.pan = a.pan; r.tr.tilt = a.tilt
  return r.app.calib.recordCorner(n)
}

describe('calibración: requisitos', () => {
  it('sin «grid» en HELLO avisa y no envía nada', async () => {
    const { app, tr } = await ready({ caps: [] })
    const lines: string[] = []
    tr.onTraffic((d, l) => { if (d === 'tx') lines.push(l) })
    expect(app.calib.supported.value).toBe(false)
    app.calib.jog('right')
    await app.calib.laser(true)
    expect(app.calib.msg.value).toMatch(/grid/)
    expect(lines).toEqual([])
  })
  it('sin enlace pide conectar', async () => {
    const { app } = mk()
    await app.init()
    expect(await app.calib.laser(true)).toBe(false)
    expect(app.calib.msg.value).toMatch(/Conecta/)
  })
  it('refresh lee ángulos, láser, puntos y modo del mapa', async () => {
    const { app, tr } = await ready()
    tr.pan = 101.5; tr.tilt = 77
    await app.calib.refresh()
    expect(app.calib.pan.value).toBe(101.5)
    expect(app.calib.tilt.value).toBe(77)
    expect(app.calib.laserOn.value).toBe(false)
    expect(app.calib.corners.value).toEqual([false, false, false, false, false])
    expect(app.calib.mapMode.value).toBe('GEO')
  })
})

describe('calibración: JOG', () => {
  it('→ sube el pan, ↑ baja el ángulo de tilt; los ajustes invierten el sentido', async () => {
    const { app, tr } = await ready()
    app.calib.setPrefs({ step: 5 })
    app.calib.jog('right'); await vi.waitFor(() => expect(tr.pan).toBe(95))
    app.calib.jog('up'); await vi.waitFor(() => expect(tr.tilt).toBe(85))
    app.calib.setPrefs({ invertH: true, invertV: true, step: 1 })
    app.calib.jog('right'); await vi.waitFor(() => expect(tr.pan).toBe(94))
    app.calib.jog('up'); await vi.waitFor(() => expect(tr.tilt).toBe(86))
    expect(app.calib.pan.value).toBe(94)
  })
  it('las repeticiones se unen: nunca más de una orden en vuelo ni una ráfaga acumulada', async () => {
    const { app, tr } = await ready({ latency: { moveMs: 40 } })
    app.calib.setPrefs({ step: 0.2 })
    const jogs: string[] = []
    let inflight = 0, maxInflight = 0
    tr.onTraffic((d, l) => {
      if (!l.startsWith('JOG') && !l.startsWith('OK JOG')) return
      if (d === 'tx') { jogs.push(l); inflight++; maxInflight = Math.max(maxInflight, inflight) } else inflight--
    })
    for (let i = 0; i < 12; i++) app.calib.jog('right') // 12 pulsaciones seguidas
    await vi.waitFor(() => expect(app.calib.working.value).toBe(0))
    expect(maxInflight).toBe(1)
    expect(jogs.length).toBeLessThanOrEqual(3) // la primera, y el resto unido
    expect(tr.pan).toBeCloseTo(90 + 12 * 0.2, 5) // no se pierde ningún paso
  })
  it('el tope mecánico se explica y no deja JOG pendientes', async () => {
    const { app, tr } = await ready()
    tr.pan = 164
    app.calib.setPrefs({ step: 5 })
    app.calib.jog('right')
    await vi.waitFor(() => expect(app.calib.msg.value).toMatch(/Tope mecánico/))
    expect(tr.pan).toBe(164)
  })
  it('no apunta mientras hay un disparo en curso', async () => {
    const { app, tr } = await ready({ latency: { shotMs: 200 } })
    const lines: string[] = []
    tr.onTraffic((d, l) => { if (d === 'tx') lines.push(l) })
    const p = app.fireAt({ x: 5, y: 5 })
    app.calib.jog('left')
    expect(app.calib.msg.value).toMatch(/disparando/i)
    await p
    expect(lines.some(l => l.startsWith('JOG'))).toBe(false)
  })
  it('center manda GOTO 90 90', async () => {
    const { app, tr } = await ready()
    tr.pan = 120; tr.tilt = 60
    expect(await app.calib.center()).toBe(true)
    expect([tr.pan, tr.tilt]).toEqual([90, 90])
  })
})

describe('calibración: láser', () => {
  it('toggle, cuenta atrás de 120 s y apagado automático', async () => {
    vi.useFakeTimers()
    const { app, tr } = await ready()
    expect(await app.calib.toggleLaser()).toBe(true)
    expect(app.calib.laserOn.value).toBe(true)
    expect(tr.laserOn).toBe(true)
    expect(app.calib.laserLeft.value).toBe(120)
    await vi.advanceTimersByTimeAsync(30_000)
    expect(app.calib.laserLeft.value).toBe(90)
    await vi.advanceTimersByTimeAsync(90_500)
    expect(app.calib.laserOn.value).toBe(false)
    expect(app.calib.msg.value).toMatch(/apagó solo/)
    expect(await app.calib.toggleLaser()).toBe(true)
    expect(app.calib.laserOn.value).toBe(true)
    expect(await app.calib.toggleLaser()).toBe(true)
    expect(app.calib.laserOn.value).toBe(false)
    expect(app.calib.laserLeft.value).toBe(0)
  })
  it('STOP y DISPARAR apagan el láser de calibración', async () => {
    const { app, tr } = await ready()
    await app.calib.laser(true)
    await app.stop()
    expect(app.calib.laserOn.value).toBe(false)
    expect(tr.laserOn).toBe(false)
    await app.calib.laser(true)
    await app.fireAt({ x: 4, y: 4 })
    expect(app.calib.laserOn.value).toBe(false)
    expect(tr.laserOn).toBe(false)
  })
  it('perder el enlace lo olvida todo', async () => {
    const { app, tr } = await ready()
    await app.calib.laser(true)
    await app.calib.refresh()
    expect(app.calib.pan.value).toBe(90)
    await app.disconnect()
    expect(app.calib.laserOn.value).toBe(false)
    expect(app.calib.pan.value).toBeNull()
    expect(tr.laserOn).toBe(false)
  })
})

describe('calibración: esquinas, cálculo y guardado', () => {
  it('flujo completo: 4 esquinas + control → CALCULAR → verificar → GUARDAR', async () => {
    const r = await ready()
    const { app, tr } = r
    await app.calib.refresh()
    // calcular sin esquinas: avisa
    expect(await app.calib.compute()).toBeUndefined()
    expect(app.calib.msg.value).toMatch(/Faltan esquinas/)

    for (const [i, c] of CORNERS.entries()) expect(await place(r, i + 1, c)).toBe(true)
    expect(app.calib.corners.value).toEqual([true, true, true, true, false])
    expect(app.calib.cornersDone.value).toBe(true)
    expect(app.calib.stale.value).toBe(true)
    expect(app.calib.canSave.value).toBe(false)
    expect(await app.calib.save()).toBe(false) // no se guarda sin calcular

    expect(await place(r, 5, { x: 11, y: 11 })).toBe(true)
    const err = await app.calib.compute()
    expect(err).not.toBeUndefined()
    expect(err!).toBeLessThan(0.01)
    expect(app.calib.mapMode.value).toBe('GRID')
    expect(app.calib.fitOk.value).toBe(true)
    expect(app.calib.stale.value).toBe(false)
    expect(app.calib.msg.value).toMatch(/Error del control: 0\.0\d°/)

    expect(await app.calib.laser(true)).toBe(true)
    expect(await app.calib.verify({ x: 14, y: 6 })).toBe(true)
    expect(app.calib.verified.value).toEqual({ x: 14, y: 6 })
    const at = tr.pointing()
    expect(Math.hypot(at.x - 14, at.y - 6)).toBeLessThan(0.05)

    expect(await app.calib.save()).toBe(true)
    expect(app.calib.msg.value).toMatch(/guardado/)
    tr.powerCycle()
    await app.calib.refresh()
    expect(app.calib.mapMode.value).toBe('GRID')
    expect(app.calib.corners.value).toEqual([true, true, true, true, true])
  })

  it('verify enciende el láser si estaba apagado', async () => {
    const r = await ready()
    for (const [i, c] of CORNERS.entries()) await place(r, i + 1, c)
    await r.app.calib.compute()
    expect(r.app.calib.laserOn.value).toBe(false)
    expect(await r.app.calib.verify({ x: 3, y: 3 })).toBe(true)
    expect(r.app.calib.laserOn.value).toBe(true)
  })

  it('registrar otra esquina deja el mapa «por recalcular»', async () => {
    const r = await ready()
    for (const [i, c] of CORNERS.entries()) await place(r, i + 1, c)
    await r.app.calib.compute()
    expect(r.app.calib.stale.value).toBe(false)
    await place(r, 2, { x: 20, y: 1 })
    expect(r.app.calib.stale.value).toBe(true)
    expect(r.app.calib.canSave.value).toBe(false)
  })

  it('esquinas degeneradas: ERR FIT con mensaje', async () => {
    const r = await ready()
    for (let n = 1; n <= 4; n++) await r.app.calib.recordCorner(n) // las 4 en 90/90
    expect(await r.app.calib.compute()).toBeUndefined()
    expect(r.app.calib.msg.value).toMatch(/no sirven para calcular/)
    expect(r.app.calib.mapMode.value).not.toBe('GRID')
  })

  it('reiniciar el mapa limpia esquinas, vuelve a GEO y relee la calibración', async () => {
    const r = await ready()
    for (const [i, c] of CORNERS.entries()) await place(r, i + 1, c)
    await r.app.calib.compute()
    expect(await r.app.calibResetMap()).toBe(true)
    expect(r.app.calib.corners.value).toEqual([false, false, false, false, false])
    expect(r.app.calib.mapMode.value).toBe('GEO')
    expect(r.app.calib.fitOk.value).toBe(false)
    expect(r.app.cal.value).not.toBeNull()
  })

  it('error del módulo al guardar (NVS) se muestra', async () => {
    const r = await ready()
    for (const [i, c] of CORNERS.entries()) await place(r, i + 1, c)
    await r.app.calib.compute()
    r.tr.failStore = true
    expect(await r.app.calib.save()).toBe(false)
    expect(r.app.calib.msg.value).toMatch(/NVS/)
  })
})

describe('calibración: ajustes persistentes', () => {
  it('paso e inversiones sobreviven al reinicio de la app', async () => {
    const kv = memoryKV()
    const a = mk({}, kv).app
    a.calib.setPrefs({ step: 0.05, invertH: true })
    const b = mk({}, kv).app
    expect(b.calib.prefs.value).toEqual({ step: 0.05, invertH: true, invertV: false })
  })
  it('un valor guardado inválido cae al paso por defecto', () => {
    const kv = memoryKV({ calib: JSON.stringify({ step: 7, invertV: 'sí' }) })
    expect(mk({}, kv).app.calib.prefs.value).toEqual({ step: 1, invertH: false, invertV: false })
  })
})
