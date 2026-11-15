import { describe, expect, it, vi } from 'vitest'
import { WifiTransport } from './wifi'
import type { HttpGet } from './wifi'

const mk = (fn: HttpGet) => new WifiTransport({ httpGet: fn, bindWifi: false })

describe('WifiTransport', () => {
  it('list devuelve un único par «Wi-Fi mantenimiento»', async () => {
    const peers = await mk(async () => ({ status: 200, text: '' })).list()
    expect(peers).toHaveLength(1)
    expect(peers[0]?.name).toBe('Wi-Fi mantenimiento')
  })

  it('connect hace PING, codifica la línea y emite estado', async () => {
    const urls: string[] = []
    const t = mk(async u => { urls.push(u); return { status: 200, text: 'PONG\r\n' } })
    const states: boolean[] = []
    t.onStateChange(c => states.push(c))
    await t.connect()
    expect(urls).toEqual(['http://192.168.4.1/cmd?l=PING'])
    expect(t.isConnected()).toBe(true)
    expect(states).toEqual([true])
  })

  it('request: codifica (x,y) y devuelve una línea por respuesta', async () => {
    const urls: string[] = []
    const t = mk(async u => { urls.push(u); return { status: 200, text: u.endsWith('PING') ? 'PONG' : 'TEST START\nOK (1,1)\nTEST DONE\n' } })
    await t.connect()
    expect(await t.request('(3,4)', 1000)).toEqual(['TEST START', 'OK (1,1)', 'TEST DONE'])
    expect(urls[1]).toBe('http://192.168.4.1/cmd?l=(3%2C4)')
  })

  it('baseUrl configurable (sin barra final)', async () => {
    const urls: string[] = []
    const t = new WifiTransport({ baseUrl: 'http://10.0.0.5:8080/', httpGet: async u => { urls.push(u); return { status: 200, text: 'PONG' } }, bindWifi: false })
    await t.connect()
    expect(urls[0]).toBe('http://10.0.0.5:8080/cmd?l=PING')
  })

  it('serializa: una petición a la vez, en orden', async () => {
    let live = 0, maxLive = 0
    const order: string[] = []
    const t = mk(async u => {
      live++; maxLive = Math.max(maxLive, live)
      await new Promise(r => setTimeout(r, 5))
      order.push(decodeURIComponent(u.split('l=')[1]!))
      live--
      return { status: 200, text: 'OK' }
    })
    await t.connect()
    await Promise.all([t.request('A', 1000), t.request('B', 1000), t.request('C', 1000)])
    expect(maxLive).toBe(1)
    expect(order).toEqual(['PING', 'A', 'B', 'C'])
  })

  it('connect falla con mensaje claro si no responde', async () => {
    const t = mk(async () => { throw new Error('red inalcanzable') })
    await expect(t.connect()).rejects.toThrow(/no responde/)
    expect(t.isConnected()).toBe(false)
  })

  it('HTTP no-2xx rechaza sin tumbar el enlace ni atascar la cola', async () => {
    let n = 0
    const t = mk(async () => (++n === 2 ? { status: 500, text: '' } : { status: 200, text: 'PONG' }))
    await t.connect()
    await expect(t.request('X', 1000)).rejects.toThrow('HTTP 500')
    expect(t.isConnected()).toBe(true)
    expect(await t.request('PING', 1000)).toEqual(['PONG'])
  })

  it('error de red marca desconectado y avisa; timeout duro si el GET se cuelga', async () => {
    vi.useFakeTimers()
    try {
      let hang = false
      const t = mk(() => (hang ? new Promise(() => {}) : Promise.resolve({ status: 200, text: 'PONG' })))
      await t.connect()
      const states: [boolean, string | undefined][] = []
      t.onStateChange((c, r) => states.push([c, r]))
      hang = true
      const p = expect(t.request('PING', 500)).rejects.toThrow(/Sin respuesta/)
      await vi.advanceTimersByTimeAsync(800)
      await p
      expect(t.isConnected()).toBe(false)
      expect(states[0]?.[0]).toBe(false)
    } finally { vi.useRealTimers() }
  })
})
