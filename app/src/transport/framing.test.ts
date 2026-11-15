import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LineFramer, RequestQueue, TransportTimeout, terminalFor } from './framing'

describe('LineFramer', () => {
  it('parte por \\n y deja el resto pendiente', () => {
    const f = new LineFramer()
    expect(f.push('OK (3,4)\nPON')).toEqual(['OK (3,4)'])
    expect(f.push('G\n')).toEqual(['PONG'])
  })
  it('maneja CRLF y descarta líneas vacías', () => {
    const f = new LineFramer()
    expect(f.push('HELLO SONAR-A\r\n\r\nPONG\r\n')).toEqual(['HELLO SONAR-A', 'PONG'])
  })
  it('línea partida en 3 lecturas, incluso partiendo el CRLF', () => {
    const f = new LineFramer()
    expect(f.push('TEST ST')).toEqual([])
    expect(f.push('ART\r')).toEqual(['TEST START'])
    expect(f.push('\nOK')).toEqual([])
    expect(f.push(' (1,1)\n')).toEqual(['OK (1,1)'])
  })
  it('ruido de arranque: quita controles y reset() descarta lo pendiente', () => {
    const f = new LineFramer()
    expect(f.push('\u0000\u0007rst:0x1 (POWERON)\nOK')).toEqual(['rst:0x1 (POWERON)'])
    f.reset()
    expect(f.push(' (2,2)\n')).toEqual(['(2,2)'])
  })
  it('no crece sin fin si nunca hay salto de línea', () => {
    const f = new LineFramer(32)
    f.push('x'.repeat(500))
    expect(f.pending.length).toBeLessThanOrEqual(32)
  })
})

describe('terminalFor', () => {
  it('TEST: OK intermedio no termina; DONE/ABORT/ERR sí', () => {
    const t = terminalFor('TEST')
    expect(t('TEST START')).toBe(false)
    expect(t('OK (1,1)')).toBe(false)
    expect(t('TEST DONE')).toBe(true)
    expect(t('TEST ABORT')).toBe(true)
    expect(t('ERR busy')).toBe(true)
  })
  it('resto de órdenes usa isTerminal', () => {
    expect(terminalFor('(3,4)')('OK (3,4)')).toBe(true)
    expect(terminalFor('PING')('PONG')).toBe(true)
  })
})

describe('RequestQueue', () => {
  let sent: string[]
  let q: RequestQueue
  beforeEach(() => {
    vi.useFakeTimers()
    sent = []
    q = new RequestQueue(async l => { sent.push(l) }, { stopGraceMs: 100 })
  })
  afterEach(() => vi.useRealTimers())

  it('resuelve con las líneas hasta la terminal', async () => {
    const p = q.request('PING', 1000)
    q.feed('PONG')
    await expect(p).resolves.toEqual(['PONG'])
  })

  it('FIFO: una sola en vuelo; la segunda se envía al terminar la primera', async () => {
    const a = q.request('PING', 1000)
    const b = q.request('HELLO', 1000)
    await Promise.resolve()
    expect(sent).toEqual(['PING'])
    expect(q.waiting).toBe(1)
    q.feed('PONG')
    await expect(a).resolves.toEqual(['PONG'])
    expect(sent).toEqual(['PING', 'HELLO'])
    q.feed('HELLO SONAR-A v2')
    await expect(b).resolves.toEqual(['HELLO SONAR-A v2'])
  })

  it('timeout rechaza y NO atasca la cola', async () => {
    const a = q.request('(3,4)', 500)
    const b = q.request('PING', 500)
    const aa = expect(a).rejects.toBeInstanceOf(TransportTimeout)
    await vi.advanceTimersByTimeAsync(501)
    await aa
    expect(sent).toEqual(['(3,4)', 'PING'])
    q.feed('PONG')
    await expect(b).resolves.toEqual(['PONG'])
  })

  it('EVT no solicitado (con y sin petición pendiente) va a onUnsolicited', async () => {
    const got: string[] = []
    q.onUnsolicited(l => got.push(l))
    q.feed('EVT BOOT')
    const p = q.request('PING', 1000)
    await Promise.resolve()
    q.feed('EVT HIT')
    q.feed('PONG')
    await expect(p).resolves.toEqual(['PONG'])
    expect(got).toEqual(['EVT BOOT', 'EVT HIT'])
  })

  it('línea suelta sin petición pendiente es no solicitada', () => {
    const got: string[] = []
    const off = q.onUnsolicited(l => got.push(l))
    q.feed('OK (1,1)')
    off()
    q.feed('OK (2,2)')
    expect(got).toEqual(['OK (1,1)'])
  })

  it('TEST multilínea: START, varios OK (x,y) y DONE', async () => {
    const p = q.request('TEST', 10_000)
    await Promise.resolve()
    for (const l of ['TEST START', 'OK (1,1)', 'OK (1,20)', 'OK (20,20)', 'TEST DONE']) q.feed(l)
    await expect(p).resolves.toEqual(['TEST START', 'OK (1,1)', 'OK (1,20)', 'OK (20,20)', 'TEST DONE'])
  })

  it('TEST abortado por STOP: TEST ABORT termina', async () => {
    const p = q.request('TEST', 10_000)
    await Promise.resolve()
    q.feed('TEST START'); q.feed('OK (1,1)'); q.feed('TEST ABORT')
    await expect(p).resolves.toEqual(['TEST START', 'OK (1,1)', 'TEST ABORT'])
  })

  it('OK STOP seguido de ERR STOP tardío: se incluye dentro de la gracia', async () => {
    const p = q.request('STOP', 1000)
    await Promise.resolve()
    q.feed('OK STOP')
    q.feed('ERR STOP')
    await vi.advanceTimersByTimeAsync(101)
    await expect(p).resolves.toEqual(['OK STOP', 'ERR STOP'])
  })

  it('OK STOP sin ERR: resuelve al vencer la gracia, y el timeout no lo rompe', async () => {
    const p = q.request('STOP', 120)
    await Promise.resolve()
    q.feed('OK STOP')
    await vi.advanceTimersByTimeAsync(101)
    await expect(p).resolves.toEqual(['OK STOP'])
  })

  it('failAll rechaza la petición en vuelo y las encoladas', async () => {
    const a = q.request('PING', 1000)
    const b = q.request('HELLO', 1000)
    const ra = expect(a).rejects.toThrow('cae')
    const rb = expect(b).rejects.toThrow('cae')
    q.failAll(new Error('cae'))
    await ra; await rb
    expect(q.inFlight).toBe(false)
  })

  it('si la escritura falla, rechaza y sigue con la siguiente', async () => {
    let n = 0
    const q2 = new RequestQueue(async l => { if (n++ === 0) throw new Error('write falló'); sent.push(l) })
    const a = q2.request('PING', 1000)
    const b = q2.request('HELLO', 1000)
    const ra = expect(a).rejects.toThrow('write falló')
    await ra
    await Promise.resolve()
    q2.feed('HELLO SONAR-B')
    await expect(b).resolves.toEqual(['HELLO SONAR-B'])
  })

  it('STOP urgente: se escribe de inmediato con un disparo en vuelo y no espera turno', async () => {
    const shot = q.request('(3,4)', 5000)
    await Promise.resolve()
    const stop = q.request('STOP', 1000)
    await Promise.resolve()
    expect(sent).toEqual(['(3,4)', 'STOP'])
    q.feed('OK STOP')
    q.feed('ERR STOP')
    await expect(stop).resolves.toEqual(['OK STOP'])
    await expect(shot).resolves.toEqual(['ERR STOP'])
  })

  it('STOP urgente durante TEST: TEST ABORT + ERR STOP van al TEST', async () => {
    const test = q.request('TEST', 5000)
    await Promise.resolve()
    const stop = q.request('STOP', 1000)
    q.feed('OK STOP')
    q.feed('TEST ABORT')
    q.feed('ERR STOP')
    await expect(stop).resolves.toEqual(['OK STOP'])
    await expect(test).resolves.toEqual(['TEST ABORT'])
  })
})
