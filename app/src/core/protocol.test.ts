import { describe, expect, it } from 'vitest'
import { ERROR_CODES, fire, friendlyError, isValidCoord, parseCommand, parseReply } from './protocol'

describe('fire / isValidCoord', () => {
  it('formatea con paréntesis y x primero', () => expect(fire({ x: 12, y: 7 })).toBe('(12,7)'))
  it('valida límites 1..20', () => {
    expect(isValidCoord({ x: 1, y: 20 })).toBe(true)
    expect(isValidCoord({ x: 0, y: 5 })).toBe(false)
    expect(isValidCoord({ x: 21, y: 5 })).toBe(false)
    expect(isValidCoord({ x: 3.5, y: 5 })).toBe(false)
  })
})

describe('parseReply', () => {
  it('OK (x,y) con espacios tolerados', () => {
    expect(parseReply('OK (5,6)')).toEqual({ t: 'ok-shot', at: { x: 5, y: 6 } })
    expect(parseReply('ok ( 12 , 7 )\r\n')).toEqual({ t: 'ok-shot', at: { x: 12, y: 7 } })
  })
  it('OK de acuse', () => {
    expect(parseReply('OK STOP')).toEqual({ t: 'ok', what: 'STOP' })
    expect(parseReply('OK MARK')).toEqual({ t: 'ok', what: 'MARK' })
    expect(parseReply('OK CAL')).toEqual({ t: 'ok', what: 'CAL' })
    expect(parseReply('OK SAVE')).toEqual({ t: 'ok', what: 'SAVE' })
    expect(parseReply('OK RESET')).toEqual({ t: 'ok', what: 'RESET' })
    expect(parseReply('OK MODE wifi')).toEqual({ t: 'ok', what: 'MODE', mode: 'WIFI' })
  })
  it.each(ERROR_CODES)('ERR %s', code => {
    expect(parseReply(`ERR ${code}`)).toEqual({ t: 'err', code })
    expect(parseReply(`err ${code.toLowerCase()}`)).toEqual({ t: 'err', code })
  })
  it('ERR con código desconocido -> unknown', () => expect(parseReply('ERR WAT').t).toBe('unknown'))
  it('PONG', () => expect(parseReply('PONG DUELO-A 0.1.0')).toEqual({ t: 'pong', name: 'DUELO-A', version: '0.1.0' }))
  it('HELLO con caps y con "-"', () => {
    expect(parseReply('HELLO SONAR 2 0.3.0 SONAR-A BT ws,stream')).toEqual({ t: 'hello', fw: '0.3.0', name: 'SONAR-A', mode: 'BT', caps: ['ws', 'stream'] })
    expect(parseReply('HELLO SONAR 2 0.3.0 SONAR-B WIFI -')).toEqual({ t: 'hello', fw: '0.3.0', name: 'SONAR-B', mode: 'WIFI', caps: [] })
  })
  it('HELLO mal formado -> unknown', () => expect(parseReply('HELLO SONAR 2 x').t).toBe('unknown'))
  it('TEST START/DONE/ABORT', () => {
    expect(parseReply('TEST START').t).toBe('test-start')
    expect(parseReply('TEST DONE').t).toBe('test-done')
    expect(parseReply('TEST ABORT').t).toBe('test-abort')
  })
  it('CAL con 2 decimales y negativos', () => {
    expect(parseReply('CAL 12.50 -3.00 150.00 0.25 -1.75')).toEqual({ t: 'cal', cal: { x: 12.5, y: -3, h: 150, panTrim: 0.25, tiltTrim: -1.75 } })
    expect(parseReply('CAL 1 2 3').t).toBe('unknown')
  })
  it('MODE y ARM', () => {
    expect(parseReply('MODE BT')).toEqual({ t: 'mode', mode: 'BT' })
    expect(parseReply('ARM NOTREQ')).toEqual({ t: 'arm', state: 'NOTREQ' })
    expect(parseReply('ARM OFF')).toEqual({ t: 'arm', state: 'OFF' })
    expect(parseReply('ARM ON 25')).toEqual({ t: 'arm', state: 'ON', seconds: 25 })
    expect(parseReply('ARM ON x').t).toBe('unknown')
  })
  it('basura y vacío -> unknown con la línea', () => {
    expect(parseReply('')).toEqual({ t: 'unknown', line: '' })
    expect(parseReply('EVT hola')).toEqual({ t: 'unknown', line: 'EVT hola' })
  })
})

describe('friendlyError', () => {
  it.each(ERROR_CODES)('mensaje en español para %s', code => {
    const m = friendlyError(code)
    expect(m.length).toBeGreaterThan(10)
  })
  it('código desconocido conserva el texto', () => expect(friendlyError('XYZ')).toContain('XYZ'))
  it('RANGE menciona 1 y 20', () => expect(friendlyError('RANGE')).toMatch(/1.*20/))
})

describe('parseCommand (reglas del módulo)', () => {
  it('disparo válido con espacios y signo +', () => {
    expect(parseCommand('(5,6)')).toEqual({ t: 'fire', at: { x: 5, y: 6 } })
    expect(parseCommand('( 12 , 7 )')).toEqual({ t: 'fire', at: { x: 12, y: 7 } })
    expect(parseCommand('(+5,6)')).toEqual({ t: 'fire', at: { x: 5, y: 6 } })
  })
  it('paréntesis obligatorios', () => {
    expect(parseCommand('5,6')).toEqual({ t: 'error', code: 'UNKNOWN' })
    expect(parseCommand('(5,6')).toEqual({ t: 'error', code: 'FORMAT' })
  })
  it('RANGE vs FORMAT: la sintaxis gana', () => {
    expect(parseCommand('(0,a)')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('(-1,5)')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('(21,1)')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('(0,1)')).toEqual({ t: 'error', code: 'RANGE' })
  })
  it('EMPTY, TOOLONG, UNKNOWN', () => {
    expect(parseCommand('')).toEqual({ t: 'error', code: 'EMPTY' })
    expect(parseCommand('   ')).toEqual({ t: 'error', code: 'EMPTY' })
    expect(parseCommand('X'.repeat(65))).toEqual({ t: 'error', code: 'TOOLONG' })
    expect(parseCommand('X'.repeat(64))).toEqual({ t: 'error', code: 'UNKNOWN' })
    expect(parseCommand('FOO')).toEqual({ t: 'error', code: 'UNKNOWN' })
  })
  it('palabra conocida con argumentos de más/menos -> FORMAT; subcomando desconocido -> UNKNOWN', () => {
    expect(parseCommand('PING x')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('MARK')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('MARK FOO')).toEqual({ t: 'error', code: 'UNKNOWN' })
    expect(parseCommand('CAL FOO')).toEqual({ t: 'error', code: 'UNKNOWN' })
    expect(parseCommand('MODE X')).toEqual({ t: 'error', code: 'UNKNOWN' })
    expect(parseCommand('MODE BT WIFI')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('HELLO x')).toEqual({ t: 'error', code: 'FORMAT' })
  })
  it('no distingue mayúsculas', () => {
    expect(parseCommand('ping').t).toBe('ping')
    expect(parseCommand('mark hit')).toEqual({ t: 'mark', hit: true })
    expect(parseCommand('Cal Show').t).toBe('cal-show')
  })
  it('CAL SET: rangos y formato', () => {
    expect(parseCommand('CAL SET 0 0 150 0 0').t).toBe('cal-set')
    expect(parseCommand('CAL SET 0 0 150 11 0')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('CAL SET 0 0 40 0 0')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('CAL SET 0 0 150 0')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('CAL SET a 0 150 0 0')).toEqual({ t: 'error', code: 'FORMAT' })
  })
})

describe('protocolo v3: calibración de apuntado (respuestas)', () => {
  it('PT, OK JOG y OK AIM', () => {
    expect(parseReply('PT 90.00 90.00')).toEqual({ t: 'pt', pan: 90, tilt: 90 })
    expect(parseReply('PT 73.25 -4')).toEqual({ t: 'pt', pan: 73.25, tilt: -4 })
    expect(parseReply('OK JOG 91.50 88.25')).toEqual({ t: 'ok-jog', pan: 91.5, tilt: 88.25 })
    expect(parseReply('OK AIM 20 1')).toEqual({ t: 'ok-aim', at: { x: 20, y: 1 } })
  })
  it('LASER: consulta y acuse', () => {
    expect(parseReply('LASER ON')).toEqual({ t: 'laser', on: true })
    expect(parseReply('laser off')).toEqual({ t: 'laser', on: false })
    expect(parseReply('OK LASER ON')).toEqual({ t: 'ok-laser', on: true })
    expect(parseReply('OK LASER OFF')).toEqual({ t: 'ok-laser', on: false })
    expect(parseReply('OK LASER MAYBE').t).toBe('unknown')
  })
  it('CORNER, CORNERS, FIT y MAP', () => {
    expect(parseReply('OK CORNER 3 112.40 71.05')).toEqual({ t: 'ok-corner', n: 3, pan: 112.4, tilt: 71.05 })
    expect(parseReply('OK CORNER 6 1 1').t).toBe('unknown')
    expect(parseReply('CORNERS 11110 0')).toEqual({ t: 'corners', mask: [true, true, true, true, false], fit: false })
    expect(parseReply('CORNERS 11111 1')).toEqual({ t: 'corners', mask: [true, true, true, true, true], fit: true })
    expect(parseReply('CORNERS 1111 0').t).toBe('unknown')
    expect(parseReply('OK FIT 0.42')).toEqual({ t: 'ok-fit', err: 0.42 })
    expect(parseReply('OK FIT -')).toEqual({ t: 'ok-fit', err: null })
    expect(parseReply('MAP GRID')).toEqual({ t: 'map', mode: 'GRID' })
    expect(parseReply('MAP geo')).toEqual({ t: 'map', mode: 'GEO' })
    expect(parseReply('MAP X').t).toBe('unknown')
  })
  it('rechaza números raros', () => {
    expect(parseReply('PT nan 90').t).toBe('unknown')
    expect(parseReply('OK JOG 1e2 3').t).toBe('unknown')
    expect(parseReply('PT 90').t).toBe('unknown')
  })
  it('NODATA y FIT son errores con mensaje propio', () => {
    expect(friendlyError('NODATA')).toMatch(/esquinas/i)
    expect(friendlyError('FIT')).toMatch(/esquinas/i)
  })
  it('las respuestas v3 son terminales (la cola no las deja colgadas)', async () => {
    const { isTerminal } = await import('../transport/transport')
    for (const l of ['PT 90.00 90.00', 'LASER ON', 'CORNERS 11110 0', 'MAP GRID', 'OK JOG 90.00 90.00', 'ERR NODATA']) expect(isTerminal(l)).toBe(true)
  })
})

describe('protocolo v3: órdenes (parseCommand y formateadores)', () => {
  it('formateadores', async () => {
    const m = await import('./protocol')
    expect(m.formatJog(0.05, -5)).toBe('JOG 0.05 -5.00')
    expect(m.formatJog(-0.001, 0)).toBe('JOG 0.00 0.00')
    expect(m.formatGoto(90, 90)).toBe('GOTO 90.00 90.00')
    expect(m.formatAim({ x: 7, y: 20 })).toBe('AIM 7 20')
    expect(m.formatLaser(true)).toBe('LASER ON')
    expect(m.formatCorner(4)).toBe('CORNER 4')
    for (const l of [m.formatJog(-20, 20), m.formatGoto(165, 165), m.formatAim({ x: 20, y: 20 })]) expect(l.length).toBeLessThanOrEqual(m.MAX_LINE)
  })
  it('JOG', () => {
    expect(parseCommand('JOG 1.5 -0.25')).toEqual({ t: 'jog', dp: 1.5, dt: -0.25 })
    expect(parseCommand('JOG 20 -20')).toEqual({ t: 'jog', dp: 20, dt: -20 })
    expect(parseCommand('JOG 21 0')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('JOG 1')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('JOG a b')).toEqual({ t: 'error', code: 'FORMAT' })
  })
  it('GOTO, PT, CORNERS', () => {
    expect(parseCommand('GOTO 90 90')).toEqual({ t: 'goto', pan: 90, tilt: 90 })
    expect(parseCommand('GOTO 14 90')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('GOTO 90 166')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('PT')).toEqual({ t: 'pt' })
    expect(parseCommand('PT 1')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('CORNERS')).toEqual({ t: 'corners' })
  })
  it('LASER', () => {
    expect(parseCommand('LASER')).toEqual({ t: 'laser-query' })
    expect(parseCommand('laser on')).toEqual({ t: 'laser-set', on: true })
    expect(parseCommand('LASER OFF')).toEqual({ t: 'laser-set', on: false })
    expect(parseCommand('LASER X')).toEqual({ t: 'error', code: 'FORMAT' })
  })
  it('CORNER n', () => {
    expect(parseCommand('CORNER 1')).toEqual({ t: 'corner', n: 1 })
    expect(parseCommand('CORNER 5')).toEqual({ t: 'corner', n: 5 })
    expect(parseCommand('CORNER 0')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('CORNER 6')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('CORNER 1.5')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('CORNER')).toEqual({ t: 'error', code: 'FORMAT' })
  })
  it('AIM x y (sin paréntesis) y CAL FIT / CAL MAP', () => {
    expect(parseCommand('AIM 3 18')).toEqual({ t: 'aim', at: { x: 3, y: 18 } })
    expect(parseCommand('AIM 21 1')).toEqual({ t: 'error', code: 'RANGE' })
    expect(parseCommand('AIM (3,4)')).toEqual({ t: 'error', code: 'FORMAT' })
    expect(parseCommand('CAL FIT')).toEqual({ t: 'cal-fit' })
    expect(parseCommand('CAL MAP')).toEqual({ t: 'cal-map' })
    expect(parseCommand('CAL FIT 1')).toEqual({ t: 'error', code: 'FORMAT' })
  })
})
