import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { seededRng, shipCells } from '../core/fleet'
import { parseReply } from '../core/protocol'
import { isTerminal } from './transport'
import { REALISTIC_LATENCY, SIM_ID, SimTransport } from './sim'

const mk = async (opts: ConstructorParameters<typeof SimTransport>[0] = {}) => {
  const t = new SimTransport({ rng: seededRng(5), ...opts })
  await t.connect(SIM_ID)
  return t
}

beforeEach(() => { vi.useFakeTimers() })
afterEach(() => { vi.useRealTimers() })

describe('SimTransport: conexión', () => {
  it('list devuelve el módulo y respeta el prefijo', async () => {
    const t = new SimTransport()
    expect(await t.list('SONAR-')).toEqual([{ id: SIM_ID, name: 'SONAR-SIM', rssi: -42 }])
    expect(await t.list('DUELO-')).toEqual([])
    expect(t.kind).toBe('sim')
  })
  it('request sin conectar rechaza; connect/disconnect notifican', async () => {
    const t = new SimTransport()
    await expect(t.request('PING', 100)).rejects.toThrow('no conectado')
    const events: boolean[] = []
    t.onStateChange(c => events.push(c))
    await t.connect(SIM_ID)
    expect(t.isConnected()).toBe(true)
    await t.disconnect()
    expect(events).toEqual([true, false])
    expect(t.isConnected()).toBe(false)
  })
  it('connect con id desconocido falla', async () => {
    await expect(new SimTransport().connect('otro')).rejects.toThrow()
  })
})

describe('SimTransport: órdenes instantáneas', () => {
  it('PING y HELLO', async () => {
    const t = await mk()
    expect(await t.request('PING', 100)).toEqual(['PONG SONAR-SIM 0.2.0-sim'])
    expect(parseReply((await t.request('HELLO', 100))[0]!)).toEqual({ t: 'hello', fw: '0.2.0-sim', name: 'SONAR-SIM', mode: 'BT', caps: [] })
    const t2 = await mk({ caps: ['fleet', 'ws'], mode: 'WIFI' })
    expect((await t2.request('hello', 100))[0]).toBe('HELLO SONAR 2 0.2.0-sim SONAR-SIM WIFI fleet,ws')
  })
  it('errores de sintaxis y rango', async () => {
    const t = await mk()
    expect(await t.request('', 100)).toEqual(['ERR EMPTY'])
    expect(await t.request('X'.repeat(70), 100)).toEqual(['ERR TOOLONG'])
    expect(await t.request('FOO', 100)).toEqual(['ERR UNKNOWN'])
    expect(await t.request('PING x', 100)).toEqual(['ERR FORMAT'])
    expect(await t.request('(0,a)', 100)).toEqual(['ERR FORMAT'])
    expect(await t.request('(21,3)', 100)).toEqual(['ERR RANGE'])
    expect(await t.request('(-1,5)', 100)).toEqual(['ERR RANGE'])
    expect(await t.request('5,6', 100)).toEqual(['ERR UNKNOWN'])
  })
  it('MODE: consulta, cambio, STORE', async () => {
    const t = await mk()
    expect(await t.request('MODE', 100)).toEqual(['MODE BT'])
    expect(await t.request('MODE WIFI', 100)).toEqual(['OK MODE WIFI'])
    expect(t.reboots).toBe(1)
    expect(await t.request('MODE', 100)).toEqual(['MODE WIFI'])
    expect(await t.request('MODE X', 100)).toEqual(['ERR UNKNOWN'])
    t.failStore = true
    expect(await t.request('MODE BT', 100)).toEqual(['ERR STORE'])
  })
  it('ARM: NOTREQ en BT; DISARMED bloquea disparo y TEST pero no PING/STOP', async () => {
    const t = await mk()
    expect(await t.request('ARM', 100)).toEqual(['ARM NOTREQ'])
    await t.request('MODE WIFI', 100)
    expect(await t.request('ARM', 100)).toEqual(['ARM OFF'])
    expect(await t.request('(5,5)', 100)).toEqual(['ERR DISARMED'])
    expect(await t.request('TEST', 100)).toEqual(['ERR DISARMED'])
    expect((await t.request('PING', 100))[0]).toMatch(/^PONG/)
    expect(await t.request('STOP', 100)).toEqual(['OK STOP'])
    t.setArm('ON', 25)
    expect(await t.request('ARM', 100)).toEqual(['ARM ON 25'])
    const p = t.request('(5,5)', 1000)
    await vi.advanceTimersByTimeAsync(50)
    expect(await p).toEqual(['OK (5,5)'])
  })
  it('CAL SHOW/SET/SAVE/RESET', async () => {
    const t = await mk()
    expect(await t.request('CAL SHOW', 100)).toEqual(['CAL 0.00 0.00 150.00 0.00 0.00'])
    expect(await t.request('CAL SET 10.5 -20 120 1.25 -0.5', 100)).toEqual(['OK CAL'])
    expect(await t.request('cal show', 100)).toEqual(['CAL 10.50 -20.00 120.00 1.25 -0.50'])
    expect(t.savedCal.x).toBe(0)
    expect(await t.request('CAL SAVE', 100)).toEqual(['OK SAVE'])
    expect(t.savedCal).toMatchObject({ x: 10.5, panTrim: 1.25 })
    expect(await t.request('CAL SET 0 0 150 11 0', 100)).toEqual(['ERR RANGE'])
    expect(await t.request('CAL SET 0 0 150', 100)).toEqual(['ERR FORMAT'])
    expect(await t.request('CAL FOO', 100)).toEqual(['ERR UNKNOWN'])
    expect(await t.request('CAL RESET', 100)).toEqual(['OK RESET'])
    expect((await t.request('CAL SHOW', 100))[0]).toBe('CAL 0.00 0.00 150.00 0.00 0.00')
    t.failStore = true
    expect(await t.request('CAL SAVE', 100)).toEqual(['ERR STORE'])
    expect(await t.request('CAL RESET', 100)).toEqual(['ERR STORE'])
  })
  it('las respuestas terminales son reconocidas por isTerminal', async () => {
    const t = await mk()
    for (const l of ['PING', 'HELLO', 'MODE', 'ARM', 'CAL SHOW', 'FOO']) {
      const r = await t.request(l, 100)
      expect(isTerminal(r[r.length - 1]!), l).toBe(true)
    }
  })
  it('latencia configurable: con cmdMs la respuesta espera', async () => {
    const t = await mk({ latency: { cmdMs: 40 } })
    let got: string[] | null = null
    void t.request('PING', 1000).then(r => { got = r })
    await vi.advanceTimersByTimeAsync(39)
    expect(got).toBeNull()
    await vi.advanceTimersByTimeAsync(2)
    expect(got).toEqual(['PONG SONAR-SIM 0.2.0-sim'])
  })
  it('perfil realista: disparo ≈2 s y TEST ≈12 s', () => {
    expect(REALISTIC_LATENCY.shotMs).toBe(2000)
    expect(REALISTIC_LATENCY.testStepMs * 5).toBe(12000)
  })
})

describe('SimTransport: disparo, BUSY y STOP', () => {
  it('el disparo responde OK (x,y) tras shotMs', async () => {
    const t = await mk({ latency: { shotMs: 2000 } })
    let got: string[] | null = null
    void t.request('( 12 , 7 )', 5000).then(r => { got = r })
    await vi.advanceTimersByTimeAsync(1999)
    expect(got).toBeNull()
    expect(t.busy).toBe(true)
    await vi.advanceTimersByTimeAsync(2)
    expect(got).toEqual(['OK (12,7)'])
    expect(t.busy).toBe(false)
    expect(t.fired).toEqual([{ x: 12, y: 7 }])
  })
  it('ERR BUSY para cualquier orden (incluido PING) mientras dispara', async () => {
    const t = await mk()
    const shot = t.request('(3,3)', 1000)
    expect(await t.request('PING', 100)).toEqual(['ERR BUSY'])
    expect(await t.request('(4,4)', 100)).toEqual(['ERR BUSY'])
    expect(await t.request('TEST', 100)).toEqual(['ERR BUSY'])
    expect(await t.request('MARK HIT', 100)).toEqual(['ERR BUSY'])
    await vi.advanceTimersByTimeAsync(50)
    expect(await shot).toEqual(['OK (3,3)'])
    expect(await t.request('PING', 100)).toEqual(['PONG SONAR-SIM 0.2.0-sim'])
    expect(t.fired).toHaveLength(1) // los disparos rechazados no cuentan
  })
  it('STOP siempre se atiende: OK STOP y luego el disparo responde ERR STOP', async () => {
    const t = await mk({ latency: { shotMs: 2000 } })
    const shot = t.request('(3,3)', 5000)
    await vi.advanceTimersByTimeAsync(500)
    expect(await t.request('STOP', 100)).toEqual(['OK STOP'])
    expect(await shot).toEqual(['ERR STOP'])
    expect(t.busy).toBe(false)
    expect(t.fired).toEqual([])
    await vi.advanceTimersByTimeAsync(5000) // el temporizador cancelado no dispara nada
    expect(t.fired).toEqual([])
  })
  it('STOP sin nada en curso también responde OK STOP', async () => {
    const t = await mk()
    expect(await t.request('STOP', 100)).toEqual(['OK STOP'])
  })
  it('timeout del cliente rechaza, pero el módulo sigue ocupado hasta terminar', async () => {
    const t = await mk({ latency: { shotMs: 2000 } })
    const p = t.request('(1,1)', 500)
    const assertion = expect(p).rejects.toThrow('timeout')
    await vi.advanceTimersByTimeAsync(600)
    await assertion
    expect(t.busy).toBe(true)
    await vi.advanceTimersByTimeAsync(2000)
    expect(t.busy).toBe(false)
  })
  it('ERR LIMIT con calibración desplazada', async () => {
    const t = await mk({ limit: c => c.x === 20 })
    expect(await t.request('(20,5)', 100)).toEqual(['ERR LIMIT'])
    expect(t.busy).toBe(false)
  })
  it('MARK HIT dura markMs y responde OK MARK; MARK MISS es instantáneo', async () => {
    const t = await mk({ latency: { markMs: 2000 } })
    expect(await t.request('MARK MISS', 100)).toEqual(['OK MARK'])
    let got: string[] | null = null
    void t.request('MARK HIT', 5000).then(r => { got = r })
    await vi.advanceTimersByTimeAsync(1000)
    expect(got).toBeNull()
    expect(await t.request('PING', 100)).toEqual(['ERR BUSY'])
    await vi.advanceTimersByTimeAsync(1001)
    expect(got).toEqual(['OK MARK'])
  })
  it('disconnect aborta lo pendiente', async () => {
    const t = await mk({ latency: { shotMs: 2000 } })
    const p = t.request('(2,2)', 5000)
    const assertion = expect(p).rejects.toThrow('desconectado')
    await t.disconnect()
    await assertion
    expect(t.busy).toBe(false)
  })
  it('onTraffic ve las líneas enviadas y recibidas', async () => {
    const t = await mk()
    const log: string[] = []
    t.onTraffic((d, l) => log.push(`${d}:${l}`))
    await t.request('PING', 100)
    expect(log).toEqual(['tx:PING', 'rx:PONG SONAR-SIM 0.2.0-sim'])
  })
})

describe('SimTransport: TEST', () => {
  it('rutina de 5 posiciones con TEST START ... TEST DONE', async () => {
    const t = await mk({ latency: { testStepMs: 2400 } })
    const p = t.request('TEST', 20000)
    await vi.advanceTimersByTimeAsync(12000)
    expect(await p).toEqual(['TEST START', 'OK (1,1)', 'OK (20,1)', 'OK (20,20)', 'OK (1,20)', 'OK (11,11)', 'TEST DONE'])
    expect(t.busy).toBe(false)
  })
  it('ocupado durante el TEST', async () => {
    const t = await mk({ latency: { testStepMs: 100 } })
    const p = t.request('TEST', 5000)
    await vi.advanceTimersByTimeAsync(150)
    expect(await t.request('(5,5)', 100)).toEqual(['ERR BUSY'])
    await vi.advanceTimersByTimeAsync(400)
    const r = await p
    expect(r[r.length - 1]).toBe('TEST DONE')
  })
  it('STOP durante el TEST -> TEST ABORT + ERR STOP con las posiciones ya hechas', async () => {
    const t = await mk({ latency: { testStepMs: 100 } })
    const p = t.request('TEST', 5000)
    await vi.advanceTimersByTimeAsync(250) // 2 posiciones completas
    expect(await t.request('STOP', 100)).toEqual(['OK STOP'])
    expect(await p).toEqual(['TEST START', 'OK (1,1)', 'OK (20,1)', 'TEST ABORT', 'ERR STOP'])
    expect(t.busy).toBe(false)
  })
  it('el TEST no cuenta como disparos de la partida', async () => {
    const t = await mk()
    const p = t.request('TEST', 5000)
    await vi.advanceTimersByTimeAsync(100)
    await p
    expect(t.fired).toEqual([])
  })
})

describe('SimTransport: rival y testigo automático', () => {
  it('rivalFleet es una flota de 14 casillas y reproducible por semilla', async () => {
    const a = new SimTransport({ rng: seededRng(11) })
    const b = new SimTransport({ rng: seededRng(11) })
    expect(a.rivalFleet).toEqual(b.rivalFleet)
    expect(a.rivalFleet.flatMap(shipCells)).toHaveLength(14)
  })
  it('verdictFor: agua, acierto y hundido tras disparar de verdad', async () => {
    const t = await mk()
    const ship = t.rivalFleet.find(s => s.id === 'E1')!
    const [c1, c2] = shipCells(ship) as [{ x: number; y: number }, { x: number; y: number }]
    // casilla de agua: la primera que no pertenezca a ningún barco
    const occupied = new Set(t.rivalFleet.flatMap(shipCells).map(c => `${c.x},${c.y}`))
    const water = { x: 1, y: 1 }
    while (occupied.has(`${water.x},${water.y}`)) water.x++
    const fireAt = async (c: { x: number; y: number }) => {
      const p = t.request(`(${c.x},${c.y})`, 1000)
      await vi.advanceTimersByTimeAsync(50)
      expect(await p).toEqual([`OK (${c.x},${c.y})`])
    }
    await fireAt(water)
    expect(t.verdictFor(water)).toBe('miss')
    await fireAt(c1)
    expect(t.verdictFor(c1)).toBe('hit')
    await fireAt(c2)
    expect(t.verdictFor(c2)).toBe('sunk')
    expect(t.verdictDetail(c2)).toEqual({ result: 'sunk', sunkLen: 2 })
    expect(t.verdictDetail(water)).toEqual({ result: 'miss' })
  })
  it('newRival cambia la flota y borra los disparos', async () => {
    const t = await mk()
    const old = t.rivalFleet
    t.fired.push({ x: 1, y: 1 })
    t.newRival(seededRng(99))
    expect(t.rivalFleet).not.toEqual(old)
    expect(t.fired).toEqual([])
  })
  it('emit entrega líneas no solicitadas', async () => {
    const t = await mk()
    const got: string[] = []
    const off = t.onUnsolicited(l => got.push(l))
    t.emit('EVT hola')
    off()
    t.emit('EVT chao')
    expect(got).toEqual(['EVT hola'])
  })
})
