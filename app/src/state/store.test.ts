import { afterEach, describe, expect, it, vi } from 'vitest'
import { shipCells, seededRng } from '../core/fleet'
import { PLANTILLAS } from '../core/plantillas'
import { SimTransport, SIM_ID, type SimOptions } from '../transport/sim'
import { createApp, type App } from './store'
import { memoryKV } from './storage'

const apps: App[] = []
function mk(sim: SimOptions = {}, kv = memoryKV()) {
  const tr = new SimTransport({ rng: seededRng(7), ...sim })
  const fx: string[] = []
  const app = createApp({ makeTransport: async () => tr, storage: kv, feedback: e => fx.push(e), heartbeatMs: 3_600_000, reconnectDelaysMs: [5, 5, 5], defaultKind: 'sim' })
  apps.push(app)
  return { app, tr, kv, fx }
}
async function ready(sim: SimOptions = {}) {
  const r = mk(sim)
  await r.app.init()
  expect(await r.app.connect(SIM_ID)).toBe(true)
  return r
}
afterEach(async () => { await Promise.all(apps.splice(0).map(a => a.dispose())) })

describe('enlace', () => {
  it('lista, conecta y lee HELLO', async () => {
    const { app } = await ready()
    expect(app.peers.value.map(p => p.id)).toEqual([SIM_ID])
    expect(app.link.value).toBe('on')
    expect(app.hello.value?.name).toBe('SONAR-SIM')
    expect(app.linkMsg.value).toContain('SONAR-SIM')
  })
  it('PING actualiza el latido', async () => {
    const { app } = await ready()
    expect(await app.ping()).toBe(true)
    expect(app.hb.value.ok).toBe(true)
  })
  it('si el enlace cae, reconecta solo (transporte no Bluetooth)', async () => {
    const { app, tr } = await ready()
    await tr.disconnect()
    expect(app.link.value).toBe('error')
    await new Promise(r => setTimeout(r, 60))
    expect(app.link.value).toBe('on')
  })
  it('desconexión manual no reconecta', async () => {
    const { app } = await ready()
    await app.disconnect()
    await new Promise(r => setTimeout(r, 40))
    expect(app.link.value).toBe('off')
  })
})

describe('disparar', () => {
  it('ejecuta, arranca el vuelo y deja el disparo pendiente de veredicto', async () => {
    const { app, tr } = await ready()
    const r = await app.fireAt({ x: 3, y: 4 })
    expect(r).toEqual({ ok: true, at: { x: 3, y: 4 } })
    expect(tr.fired).toEqual([{ x: 3, y: 4 }])
    expect(app.status.value.text).toContain('(3,4)')
    expect(['flying', 'verdict']).toContain(app.cycle.value.phase)
    expect(app.game.value.shots).toHaveLength(1)
    expect(app.game.value.shots[0]!.result).toBeUndefined()
    expect(app.lastSent.value).toEqual({ x: 3, y: 4 })
    expect(app.sent.value).toBe(1)
    expect(app.busy.value).toBe(false)
    expect(app.link.value).toBe('on')
  })
  it('valida coordenada y enlace', async () => {
    const { app } = await ready()
    expect(await app.fireAt({ x: 0, y: 5 })).toMatchObject({ ok: false, reason: 'range' })
    expect(await app.fireAt({ x: 21, y: 5 })).toMatchObject({ ok: false, reason: 'range' })
    await app.disconnect()
    expect(await app.fireAt({ x: 1, y: 1 })).toMatchObject({ ok: false, reason: 'offline' })
  })
  it('no permite doble disparo mientras está ocupado', async () => {
    const { app, tr } = await ready({ latency: { shotMs: 60 } })
    const a = app.fireAt({ x: 1, y: 1 })
    expect(app.busy.value).toBe(true)
    expect(app.link.value).toBe('busy')
    const b = await app.fireAt({ x: 2, y: 2 })
    expect(b).toMatchObject({ ok: false, reason: 'pending' })
    expect((await a).ok).toBe(true)
    expect(tr.fired).toEqual([{ x: 1, y: 1 }])
  })
  it('traduce ERR del módulo a español (LIMIT, DISARMED)', async () => {
    const { app, tr } = await ready({ limit: c => c.x === 20 })
    const r = await app.fireAt({ x: 20, y: 1 })
    expect(r).toMatchObject({ ok: false, reason: 'module', code: 'LIMIT' })
    expect(app.status.value.kind).toBe('err')
    expect(app.status.value.text).toContain('límite mecánico')
    expect(app.game.value.shots).toHaveLength(0)
    tr.setArm('OFF')
    expect(await app.fireAt({ x: 1, y: 1 })).toMatchObject({ ok: false, code: 'DISARMED' })
  })
  it('STOP interrumpe el disparo en curso', async () => {
    const { app } = await ready({ latency: { shotMs: 400 } })
    const p = app.fireAt({ x: 5, y: 5 })
    await new Promise(r => setTimeout(r, 20))
    await app.stop()
    const r = await p
    expect(r).toMatchObject({ ok: false, reason: 'stopped', code: 'STOP' })
    expect(app.game.value.shots).toHaveLength(0)
    expect(app.busy.value).toBe(false)
  })
  it('timeout del módulo: mensaje claro y libera el estado', async () => {
    const tr = new SimTransport({ latency: { shotMs: 300 } })
    const mini = createApp({ makeTransport: async () => tr, storage: memoryKV(), feedback: () => {}, shotTimeoutMs: 30, defaultKind: 'sim' })
    apps.push(mini)
    await mini.init()
    await mini.connect(SIM_ID)
    const r = await mini.fireAt({ x: 2, y: 2 })
    expect(r).toMatchObject({ ok: false, reason: 'timeout' })
    expect(mini.busy.value).toBe(false)
  })
  it('registra la bitácora tx/rx', async () => {
    const { app } = await ready()
    await app.fireAt({ x: 7, y: 8 })
    const texts = app.log.value.map(l => `${l.dir}:${l.text}`)
    expect(texts).toContain('tx:(7,8)')
    expect(texts).toContain('rx:OK (7,8)')
  })
})

describe('TEST de 5 posiciones', () => {
  it('aprueba con 5 posiciones y TEST DONE', async () => {
    const { app } = await ready()
    expect(await app.runTest()).toBe(true)
    expect(app.test.value.state).toBe('ok')
    expect(app.test.value.done).toBe(5)
    expect(app.test.value.msg).toContain('APROBADO')
    expect(app.busy.value).toBe(false)
  })
  it('falla con ERR (desarmado)', async () => {
    const { app, tr } = await ready()
    tr.setArm('OFF')
    expect(await app.runTest()).toBe(false)
    expect(app.test.value.state).toBe('fail')
    expect(app.test.value.msg).toContain('FALLÓ')
  })
  it('STOP durante el TEST lo aborta', async () => {
    const { app } = await ready({ latency: { testStepMs: 80 } })
    const p = app.runTest()
    await new Promise(r => setTimeout(r, 30))
    await app.stop()
    expect(await p).toBe(false)
    expect(app.test.value.state).toBe('fail')
    expect(app.test.value.msg).toContain('interrumpida')
  })
  it('sin enlace falla con mensaje', async () => {
    const { app } = mk()
    expect(await app.runTest()).toBe(false)
    expect(app.test.value.msg).toContain('Conecta')
  })
})

describe('calibración', () => {
  it('valida rangos antes de enviar y lee CAL SHOW', async () => {
    const { app, tr } = await ready()
    expect(await app.calSet({ x: 0, y: 0, h: 20, panTrim: 0, tiltTrim: 0 })).toBe(false)
    expect(app.calMsg.value).toContain('Altura h')
    expect(await app.calSet({ x: 100, y: -65, h: 180, panTrim: 1, tiltTrim: -1 })).toBe(true)
    expect(tr.cal.x).toBe(100)
    expect(await app.calShow()).toBe(true)
    expect(app.cal.value?.h).toBe(180)
    expect(await app.calSave()).toBe(true)
    expect(await app.calReset()).toBe(true)
    expect(app.cal.value?.h).toBe(150)
  })
})

describe('ciclo de disparo', () => {
  const FAST = { flight: 15, splash: 15, explosion: 15, sunk: 15, cancel: 15 }
  async function cyc(sim: SimOptions = {}, kv = memoryKV()) {
    const tr = new SimTransport({ rng: seededRng(7), ...sim })
    const fx: string[] = []
    const app = createApp({ makeTransport: async () => tr, storage: kv, feedback: e => fx.push(e), heartbeatMs: 3_600_000, reconnectDelaysMs: [5, 5, 5], defaultKind: 'sim', cycleMs: FAST })
    apps.push(app)
    await app.init()
    await app.connect(SIM_ID)
    return { app, tr, kv, fx }
  }
  const phase = (app: App) => app.cycle.value.phase
  const until = (app: App, p: string) => vi.waitFor(() => expect(phase(app)).toBe(p), { timeout: 1500, interval: 5 })
  const col = (x: number, y0: number, n: number) => Array.from({ length: n }, (_, i) => ({ x, y: y0 + i }))

  it('agua: vuelo → veredicto → gota → aim; se envía UNA sola vez (x,y)', async () => {
    const { app, tr, fx } = await cyc()
    const p = app.fireAt({ x: 10, y: 15 })
    expect(phase(app)).toBe('flying')
    expect(app.cycle.value).toMatchObject({ at: { x: 10, y: 15 }, n: 1, direct: false })
    await until(app, 'verdict')
    expect((await p).ok).toBe(true)
    expect(tr.fired).toEqual([{ x: 10, y: 15 }])
    await expect(app.fireAt({ x: 1, y: 1 })).resolves.toMatchObject({ ok: false, reason: 'pending' })
    expect(app.answer(false)).toBe('ok')
    expect(phase(app)).toBe('splash')
    await until(app, 'aim')
    expect(app.game.value.shots[0]).toMatchObject({ result: 'miss' })
    expect(tr.fired).toHaveLength(1)
    expect(fx).toEqual(expect.arrayContaining(['disparo', 'pausa', 'agua']))
  })

  it('casilla ya resuelta: avisa, resalta y no dispara de nuevo', async () => {
    const { app, tr } = await cyc()
    await app.fireAt({ x: 10, y: 15 }); await until(app, 'verdict'); app.answer(false); await until(app, 'aim')
    const r = await app.fireAt({ x: 10, y: 15 })
    expect(r).toMatchObject({ ok: false, reason: 'repeat' })
    expect(r.ok ? '' : r.message).toContain('resuelta')
    expect(app.flash.value?.at).toEqual({ x: 10, y: 15 })
    expect(tr.fired).toHaveLength(1)
    expect(phase(app)).toBe('aim')
  })

  it('el ejemplo del profe: impacto en (10,15), se ubica el submarino y los siguientes son impactos directos hasta ¡HUNDIDO!', async () => {
    const { app, tr, fx } = await cyc()
    await app.fireAt({ x: 10, y: 15 }); await until(app, 'verdict')
    expect(app.answer(true)).toBe('ok')
    expect(phase(app)).toBe('explosion')
    await until(app, 'locate')
    // inválido: no incluye el impacto
    expect(app.locate(col(10, 1, 4))).toMatchObject({ ok: false })
    expect(app.checkLocation(col(10, 12, 3)).ok).toBe(false)
    expect(app.checkLocation(col(10, 12, 4))).toMatchObject({ ok: true, label: 'Submarino · 4 casillas' })
    const r = app.locate(col(10, 12, 4))
    expect(r).toMatchObject({ ok: true, ship: { id: 'S1', len: 4 } })
    await until(app, 'aim')
    expect(app.known.value).toHaveLength(1)
    expect(app.left.value).toEqual({ embarcaciones: 3, submarinos: 2 })
    // impacto directo: sin veredicto, vuelo → explosión → aim
    await app.fireAt({ x: 10, y: 14 })
    await until(app, 'explosion')
    expect(app.game.value.shots[1]!.result).toBe('hit')
    await until(app, 'aim')
    await app.fireAt({ x: 10, y: 13 }); await until(app, 'aim')
    await app.fireAt({ x: 10, y: 12 })
    await until(app, 'sunk')
    expect(app.lastSunk.value?.id).toBe('S1')
    expect(app.game.value.shots.filter(s => s.result === 'sunk')).toHaveLength(1)
    expect(app.left.value).toEqual({ embarcaciones: 3, submarinos: 1 })
    await until(app, 'aim')
    expect(tr.fired).toHaveLength(4)
    expect(fx).toEqual(expect.arrayContaining(['acierto', 'hundido']))
  })

  it('hundir la flota completa llega a «won»', async () => {
    const { app } = await cyc()
    const layout = [col(1, 1, 2), col(3, 1, 2), col(5, 1, 2), col(7, 1, 4), col(9, 1, 4)]
    for (const cells of layout) {
      await app.fireAt(cells[0]!); await until(app, 'verdict'); app.answer(true); await until(app, 'locate')
      expect(app.locate(cells).ok).toBe(true)
      await until(app, 'aim').catch(() => undefined)
      for (const c of cells.slice(1)) { await vi.waitFor(() => expect(['aim']).toContain(phase(app)), { timeout: 1500, interval: 5 }); await app.fireAt(c); await vi.waitFor(() => expect(['aim', 'won']).toContain(phase(app)), { timeout: 1500, interval: 5 }) }
    }
    await until(app, 'won')
    expect(app.victory.value).toBe(true)
    expect(await app.fireAt({ x: 20, y: 20 })).toMatchObject({ ok: false, reason: 'pending' })
    app.newMatch()
    expect(phase(app)).toBe('aim')
    expect(app.victory.value).toBe(false)
  })

  it('«No sé»: el impacto queda pendiente y se puede ubicar después', async () => {
    const { app } = await cyc()
    await app.fireAt({ x: 4, y: 4 }); await until(app, 'verdict'); app.answer(true); await until(app, 'locate')
    app.skipLocate()
    expect(phase(app)).toBe('aim')
    expect(app.pendingHits.value).toEqual([{ x: 4, y: 4 }])
    expect(app.relocate({ x: 4, y: 4 })).toBe(true)
    expect(phase(app)).toBe('locate')
    expect(app.locate([{ x: 4, y: 4 }, { x: 5, y: 4 }]).ok).toBe(true)
    expect(app.pendingHits.value).toEqual([])
  })

  it('NO LE DIO sobre un barco ubicado pide confirmar', async () => {
    const { app } = await cyc()
    await app.fireAt({ x: 4, y: 4 }); await until(app, 'verdict'); app.answer(true); await until(app, 'locate')
    app.locate([{ x: 4, y: 4 }, { x: 5, y: 4 }]); await until(app, 'aim')
    // fuerza un veredicto sobre una casilla ubicada (p. ej. tras un error de ubicación)
    app.cycle.value = { phase: 'verdict', at: { x: 5, y: 4 }, n: 2, direct: false }
    expect(app.answer(false)).toBe('conflict')
    expect(app.conflict.value).toBe(true)
    expect(phase(app)).toBe('verdict')
    expect(app.answer(false, true)).toBe('ok')
    expect(app.conflict.value).toBe(false)
  })

  it('deshacer: acierto → ubicar → deshacer vuelve a «ubicar», y otra vez al veredicto', async () => {
    const { app } = await cyc()
    await app.fireAt({ x: 4, y: 4 }); await until(app, 'verdict'); app.answer(true); await until(app, 'locate')
    app.locate([{ x: 4, y: 4 }, { x: 4, y: 5 }]); await until(app, 'aim')
    expect(app.undo()).toBe(true)
    expect(phase(app)).toBe('locate')
    expect(app.known.value).toHaveLength(0)
    expect(app.undo()).toBe(true)
    expect(phase(app)).toBe('verdict')
    expect(app.game.value.shots[0]!.result).toBeUndefined()
    expect(app.answer(false)).toBe('ok')
    await until(app, 'aim')
    expect(app.undo()).toBe(true)
    expect(phase(app)).toBe('verdict')
  })

  it('si el módulo responde ERR, el ciclo se cancela con mensaje claro y el disparo no cuenta', async () => {
    const { app, tr } = await cyc({ limit: c => c.x === 20 })
    const r = await app.fireAt({ x: 20, y: 3 })
    expect(r).toMatchObject({ ok: false, code: 'LIMIT' })
    expect(phase(app)).toBe('aim')
    expect(app.game.value.shots).toHaveLength(0)
    expect(app.sent.value).toBe(0)
    expect(app.cancelFx.value?.text).toContain('límite mecánico')
    expect(tr.fired).toHaveLength(0)
    tr.setArm('OFF')
    await app.fireAt({ x: 1, y: 1 })
    expect(app.status.value.text).toContain('desarmado')
    expect(phase(app)).toBe('aim')
  })

  it('STOP durante el vuelo cancela el ciclo; si el enlace cae también', async () => {
    const { app, tr } = await cyc({ latency: { shotMs: 400 } })
    const p = app.fireAt({ x: 5, y: 5 })
    expect(phase(app)).toBe('flying')
    await app.stop()
    expect(phase(app)).toBe('aim')
    expect(app.cancelFx.value?.text).toContain('STOP')
    expect((await p).ok).toBe(false)
    expect(app.game.value.shots).toHaveLength(0)
    const q = app.fireAt({ x: 6, y: 6 })
    await tr.disconnect()
    await q
    expect(phase(app)).toBe('aim')
    expect(app.game.value.shots).toHaveLength(0)
  })

  it('si la app se cierra a mitad de ciclo no se pierde el tablero: el veredicto pendiente se reabre', async () => {
    const kv = memoryKV()
    const a = (await cyc({}, kv)).app
    await a.fireAt({ x: 9, y: 9 }); await until(a, 'verdict')
    const b = createApp({ makeTransport: async () => new SimTransport(), storage: kv, feedback: () => {}, defaultKind: 'sim' })
    apps.push(b)
    expect(b.game.value.shots).toHaveLength(1)
    expect(b.cycle.value).toMatchObject({ phase: 'verdict', at: { x: 9, y: 9 }, n: 1 })
    // a mitad de «ubicar»
    expect(b.answer(true)).toBe('ok')
    await vi.waitFor(() => expect(b.cycle.value.phase).toBe('locate'), { timeout: 3000 })
    const c = createApp({ makeTransport: async () => new SimTransport(), storage: kv, feedback: () => {}, defaultKind: 'sim' })
    apps.push(c)
    expect(c.cycle.value).toMatchObject({ phase: 'locate', at: { x: 9, y: 9 } })
    // a mitad de la animación (vuelo) vuelve a aim sin perder nada
    const kv2 = memoryKV()
    const d = (await cyc({}, kv2)).app
    d.setTarget({ x: 2, y: 2 })
    d.cycle.value = { phase: 'splash', at: { x: 1, y: 1 }, n: 1, direct: false }
    const e = createApp({ makeTransport: async () => new SimTransport(), storage: kv2, feedback: () => {}, defaultKind: 'sim' })
    apps.push(e)
    expect(e.cycle.value.phase).toBe('aim')
  })
})

describe('flota (editor)', () => {
  it('tapCell coloca el siguiente barco, selecciona, mueve, rota y quita', () => {
    const { app } = mk()
    app.clearFleet()
    app.tapCell({ x: 3, y: 3 })
    expect(app.fleet.value).toHaveLength(1)
    expect(app.selected.value).toBe('E1')
    app.tapCell({ x: 10, y: 10 })
    expect(app.fleet.value[0]).toMatchObject({ x: 10, y: 10 })
    app.rotateSelected()
    expect(app.fleet.value[0]!.orient).toBe('V')
    app.removeSelected()
    expect(app.fleet.value).toHaveLength(0)
    for (let i = 0; i < 5; i++) { app.tapCell({ x: 1 + i * 3, y: 1 }); app.tapCell({ x: 1 + i * 3, y: 1 }) }
    expect(app.fleet.value).toHaveLength(5)
    expect(app.unplaced.value).toHaveLength(0)
    expect(app.fleetText()).toContain('Submarino 1')
  })
  it('un barco que se saldría del tablero se desplaza hacia dentro', () => {
    const { app } = mk()
    app.tapCell({ x: 20, y: 20 })
    const s = app.fleet.value[0]!
    expect(shipCells(s).every(c => c.x <= 20 && c.y <= 20)).toBe(true)
  })
})

describe('persistencia', () => {
  it('guarda y restaura modo, flota, partida y ajustes', async () => {
    const kv = memoryKV()
    const a = mk({}, kv).app
    await a.init(); await a.connect(SIM_ID)
    a.randomizeFleet(seededRng(1))
    a.setMode('defensor')
    a.updateSettings({ theme: 'light', sound: false })
    await a.fireAt({ x: 9, y: 9 })
    const fleet = a.fleet.value
    const b = createApp({ makeTransport: async () => new SimTransport(), storage: kv, feedback: () => {}, defaultKind: 'sim' })
    apps.push(b)
    expect(b.mode.value).toBe('defensor')
    expect(b.fleet.value).toEqual(fleet)
    expect(b.settings.value).toMatchObject({ theme: 'light', sound: false })
    expect(b.game.value.shots).toHaveLength(1)
    expect(b.lastSent.value).toEqual({ x: 9, y: 9 })
  })
  it('datos corruptos no rompen; el ciclo arranca en aim', () => {
    const kv = memoryKV()
    kv.set('fleet', '{no es json'); kv.set('game', 'zzz'); kv.set('settings', '[1'); kv.set('prefs', 'null')
    const b = createApp({ makeTransport: async () => new SimTransport(), storage: kv, feedback: () => {}, defaultKind: 'sim' })
    apps.push(b)
    expect(b.mode.value).toBe('atacante')
    expect(b.cycle.value.phase).toBe('aim')
    expect(b.fleet.value).toEqual(PLANTILLAS[0]!.barcos)   // sin flota guardada arranca con la plantilla 1
    expect(b.game.value.shots).toEqual([])
  })
  it('si el almacenamiento lanza, la app funciona', async () => {
    const bad = { get() { throw new Error('x') }, set() { throw new Error('x') }, remove() { throw new Error('x') } }
    const b = createApp({ makeTransport: async () => new SimTransport({ latency: { shotMs: 5 } }), storage: bad, feedback: () => {}, defaultKind: 'sim' })
    apps.push(b)
    await b.init(); await b.connect(SIM_ID)
    expect((await b.fireAt({ x: 1, y: 2 })).ok).toBe(true)
  })
  it('nueva partida limpia disparos y barcos ubicados pero conserva la flota', async () => {
    const { app } = await ready()
    app.randomizeFleet(seededRng(2))
    await app.fireAt({ x: 1, y: 1 })
    app.newMatch()
    expect(app.game.value.shots).toHaveLength(0)
    expect(app.known.value).toHaveLength(0)
    expect(app.cycle.value.phase).toBe('aim')
    expect(app.sent.value).toBe(0)
    expect(app.fleet.value).toHaveLength(5)
  })
  it('exportJSON es JSON válido con versión', async () => {
    const { app } = await ready()
    const o = JSON.parse(app.exportJSON())
    expect(o.app).toBe('SONAR')
    expect(typeof o.version).toBe('string')
  })
})

describe('plantillas de fábrica', () => {
  it('son 5, numeradas, válidas y sin barcos pegados', async () => {
    const { PLANTILLAS } = await import('../core/plantillas')
    const { validateFleet } = await import('../core/fleet')
    expect(PLANTILLAS.map(t => t.n)).toEqual([1, 2, 3, 4, 5])
    for (const t of PLANTILLAS) {
      expect(validateFleet(t.barcos, { allowTouching: false }).ok, t.nombre).toBe(true)
      expect(t.barcos).toHaveLength(5)
    }
    expect(new Set(PLANTILLAS.map(t => JSON.stringify(t.barcos))).size).toBe(5)   // todas distintas
  })
  it('loadTemplate coloca la plantilla n y la flota queda válida', () => {
    const app = createApp({ storage: memoryKV(), feedback: () => {}, defaultKind: 'sim' })
    app.loadTemplate(3)
    expect(app.fleet.value).toHaveLength(5)
    expect(app.validation.value.ok).toBe(true)
    expect(app.fleet.value.find(b => b.id === 'S1')).toMatchObject({ x: 18, y: 13, orient: 'V' })
    app.loadTemplate(99)   // inexistente: no cambia nada
    expect(app.fleet.value.find(b => b.id === 'S1')).toMatchObject({ x: 18, y: 13 })
  })
})

describe('partida con plantillas de fábrica', () => {
  const FAST = { flight: 15, splash: 15, explosion: 15, sunk: 15, cancel: 15 }
  async function cyc(kv = memoryKV()) {
    const tr = new SimTransport({ rng: seededRng(7) })
    const app = createApp({ makeTransport: async () => tr, storage: kv, feedback: () => {}, heartbeatMs: 3_600_000, reconnectDelaysMs: [5, 5, 5], defaultKind: 'sim', cycleMs: FAST })
    apps.push(app)
    await app.init()
    await app.connect(SIM_ID)
    return { app, kv }
  }
  const until = (app: App, p: string) => vi.waitFor(() => expect(app.cycle.value.phase).toBe(p), { timeout: 1500, interval: 5 })

  it('la primera partida usa la plantilla 1; tocar una casilla del barco lo hunde y dice dónde está', async () => {
    const { app } = await cyc()
    expect(app.plantilla.value.n).toBe(1)
    await app.fireAt({ x: 3, y: 13 }); await until(app, 'verdict')   // S1: (3,12) a (3,15)
    expect(app.answer(true)).toBe('ok')
    await until(app, 'sunk')
    expect(app.lastSunk.value).toMatchObject({ id: 'S1', len: 4 })
    expect(app.known.value).toHaveLength(1)
    expect(app.status.value.text).toContain('(3,12) a (3,15)')
    await until(app, 'aim')                                          // sin pantalla de ubicar
    expect(app.game.value.shots[0]).toMatchObject({ result: 'sunk' })
    await app.fireAt({ x: 3, y: 14 })                                // otra casilla del mismo barco: impacto directo
    await until(app, 'aim')
  })

  it('«NO le dio» sobre un barco de la plantilla pide confirmar', async () => {
    const { app } = await cyc()
    await app.fireAt({ x: 16, y: 15 }); await until(app, 'verdict')   // E1
    expect(app.answer(false)).toBe('conflict')
    expect(app.answer(false, true)).toBe('ok')
  })

  it('cada partida nueva con disparos pasa a la siguiente plantilla (1, 2, 3, 4, 5, 1…); sin disparos no gasta', async () => {
    const { app } = await cyc()
    app.newMatch()
    expect(app.plantilla.value.n).toBe(1)                            // partida vacía: se queda
    for (const esperada of [2, 3, 4, 5, 1]) {
      const c = { x: 20, y: 20 }
      await app.fireAt(c); await until(app, 'verdict'); app.answer(false); await until(app, 'aim')
      app.newMatch()
      expect(app.plantilla.value.n).toBe(esperada)
      expect(app.fleet.value).toEqual(PLANTILLAS[esperada - 1]!.barcos)
      expect(app.known.value).toEqual([])
    }
  })

  it('con las plantillas apagadas vuelve a pedir ubicar el barco', async () => {
    const { app } = await cyc()
    app.updateSettings({ plantillas: false })
    await app.fireAt({ x: 3, y: 13 }); await until(app, 'verdict')
    app.answer(true)
    await until(app, 'locate')
  })
})
