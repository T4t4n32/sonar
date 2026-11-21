/**
 * Estado de la app: orquesta transporte + partida + flota + ajustes.
 * Store con @preact/signals; `createApp()` es una fábrica (cada prueba crea el suyo con su KV y su transporte).
 */
import { batch, computed, effect, signal } from '@preact/signals'
import { addShot, fromJSON, hasShot, isVictory, newGame, remainingShips, setVerdict, toJSON, type GameState } from '../core/board'
import { ensureInside, fleetCoordinatesList, placeShip, randomFleet, removeShip, rotateShip, shipAt, shipCells, validateFleet } from '../core/fleet'
import { fleetLeft, isKnownShip, knownShipAt, locateShip, pendingLocate, reconcileSunk, validateLocation, type KnownShip, type LocationCheck } from '../core/known'
import { fire, friendlyError, isValidCoord, parseReply, type CalValues, type ErrCode, type ModuleMode } from '../core/protocol'
import { FLEET_SPEC, type Coord, type LinkState, type Orient, type PlacedShip } from '../core/types'
import { SimTransport } from '../transport/sim'
import type { LineTransport, PeerInfo } from '../transport/transport'
import { createCalib } from './calib'
import { IDLE, isCancellable, next as cycleNext, type Cycle, type CycleEvent } from './cycle'
import { makeFeedback, setWake, type FxEvent } from './feedback'
import { loadJSON, localKV, saveJSON, type KV } from './storage'
import { createTransport, isNative, type TransportKind } from './transports'

export const APP_VERSION: string = typeof __APP_VERSION__ === 'string' ? __APP_VERSION__ : '0.0.0'

export type Mode = 'atacante' | 'defensor'
export type Submode = 'profesor' | 'duelo'
export interface Settings { theme: 'dark' | 'light'; sound: boolean; vibrate: boolean; wake: boolean; assistant: boolean }
export interface LogEntry { id: number; t: number; dir: 'tx' | 'rx' | 'sys' | 'err'; text: string }
export interface Status { kind: 'idle' | 'wait' | 'ok' | 'err'; text: string }
export interface Hello { fw: string; name: string; mode: ModuleMode; caps: string[] }
export interface Heartbeat { ok: boolean | null; rttMs: number; at: number; fails: number }
export interface TestState { state: 'idle' | 'run' | 'ok' | 'fail'; done: number; at: Coord[]; msg: string; startedAt: number; durationMs: number }
export interface Ring { id: number; kind: 'eco' | 'hit' | 'sunk'; at: Coord }

export type FireFail = 'range' | 'offline' | 'busy' | 'pending' | 'repeat' | 'module' | 'timeout' | 'stopped'
/** Duración (ms) de cada animación del ciclo. */
export interface CycleTiming { flight: number; splash: number; explosion: number; sunk: number; cancel: number }
export const DEFAULT_TIMING: CycleTiming = { flight: 1100, splash: 1500, explosion: 1500, sunk: 2600, cancel: 1300 }
/** Instantánea para «Deshacer». */
interface Snap { game: GameState; known: KnownShip[]; sent: number; lastSent: Coord | null; cycle: Cycle }
export type FireResult = { ok: true; at: Coord } | { ok: false; reason: FireFail; message: string; code?: string }

export interface AppDeps {
  makeTransport?: (kind: TransportKind) => Promise<LineTransport>
  storage?: KV
  now?: () => number
  /** efectos (sonido/vibración); por defecto sintetizados según los ajustes */
  feedback?: (ev: FxEvent) => void
  shotTimeoutMs?: number
  /** duraciones de las animaciones del ciclo (pruebas: valores pequeños) */
  cycleMs?: Partial<CycleTiming>
  testTimeoutMs?: number
  heartbeatMs?: number
  reconnectDelaysMs?: number[]
  /** transporte inicial si no hay uno guardado */
  defaultKind?: TransportKind
}

export const DEFAULT_SETTINGS: Settings = { theme: 'dark', sound: true, vibrate: true, wake: false, assistant: false }
export const CAL_RANGES: { key: keyof CalValues; label: string; min: number; max: number; unit: string }[] = [
  { key: 'x', label: 'Estación x', min: -200, max: 400, unit: 'mm' },
  { key: 'y', label: 'Estación y', min: -300, max: 400, unit: 'mm' },
  { key: 'h', label: 'Altura h', min: 50, max: 400, unit: 'mm' },
  { key: 'panTrim', label: 'Ajuste pan', min: -10, max: 10, unit: '°' },
  { key: 'tiltTrim', label: 'Ajuste tilt', min: -10, max: 10, unit: '°' },
]

const SHIP_NAME: Record<string, string> = { embarcacion: 'Embarcación', submarino: 'Submarino' }
export const shipLabel = (s: Pick<PlacedShip, 'id' | 'kind'>): string => `${SHIP_NAME[s.kind] ?? s.kind} ${s.id.replace(/\D/g, '')}`

const errMsg = (e: unknown): string => (e instanceof Error ? e.message : String(e))
const isShip = (o: unknown): o is PlacedShip => {
  const s = o as PlacedShip
  return !!s && typeof s.id === 'string' && typeof s.len === 'number' && Number.isInteger(s.x) && Number.isInteger(s.y) && (s.orient === 'H' || s.orient === 'V') && FLEET_SPEC.some(f => f.id === s.id)
}

export function createApp(deps: AppDeps = {}) {
  const kv = deps.storage ?? localKV()
  const now = deps.now ?? (() => Date.now())
  const makeTransport = deps.makeTransport ?? createTransport
  const shotTimeout = deps.shotTimeoutMs ?? 12000
  const testTimeout = deps.testTimeoutMs ?? 45000
  const hbMs = deps.heartbeatMs ?? 5000
  const reconnectDelays = deps.reconnectDelaysMs ?? [1000, 2000, 4000]

  // ---------- carga ----------
  const timing: CycleTiming = { ...DEFAULT_TIMING, ...deps.cycleMs }
  const prefs = loadJSON<{ mode?: Mode; kind?: TransportKind; peer?: string | null; lastSent?: Coord | null; sent?: number }>(kv, 'prefs', {})
  const loadedFleet = loadJSON<unknown[]>(kv, 'fleet', []).filter(isShip)
  let loadedGame: GameState = newGame(now())
  try { const g = kv.get('game'); if (g) loadedGame = fromJSON(g) } catch { /* partida corrupta: empieza limpia */ }
  const loadedKnown = loadJSON<unknown[]>(kv, 'known', []).filter(isKnownShip)
  // Un disparo pendiente sobre un barco ya ubicado es impacto directo: se resuelve sin preguntar.
  for (const sh of loadedGame.shots) {
    if (sh.result === undefined && knownShipAt(loadedKnown, sh.at)) loadedGame = reconcileSunk(setVerdict(loadedGame, sh.n, 'hit', undefined, now()), loadedKnown, now()).state
  }
  const savedCycle = loadJSON<Partial<Cycle>>(kv, 'cycle', {})
  /** Si la app se cerró a mitad de ciclo: el veredicto o la ubicación pendientes se reabren; lo demás vuelve a apuntar. */
  const restoreCycle = (): Cycle => {
    const pend = loadedGame.shots.find(x => x.result === undefined)
    if (pend) return { phase: 'verdict', at: pend.at, n: pend.n, direct: false }
    const c = savedCycle.at
    if ((savedCycle.phase === 'locate' || savedCycle.phase === 'explosion') && c && isValidCoord(c)) {
      const sh = loadedGame.shots.find(x => x.result === 'hit' && x.at.x === c.x && x.at.y === c.y)
      if (sh && !knownShipAt(loadedKnown, sh.at)) return { phase: 'locate', at: sh.at, n: sh.n, direct: false }
    }
    if (savedCycle.phase === 'won' && loadedGame.shots.length > 0 && isVictory(loadedGame)) return { phase: 'won', at: null, n: null, direct: false }
    return IDLE
  }

  // ---------- señales ----------
  /** @deprecated ya no hay modos: solo queda por compatibilidad con App/Partida. */
  const mode = signal<Mode>(prefs.mode === 'defensor' ? 'defensor' : 'atacante')
  /** @deprecated un solo flujo (equivale al antiguo «duelo»). */
  const submode = signal<Submode>('duelo')
  const kind = signal<TransportKind>(prefs.kind ?? deps.defaultKind ?? (isNative() ? 'bluetooth' : 'sim'))
  const settings = signal<Settings>({ ...DEFAULT_SETTINGS, ...loadJSON<Partial<Settings>>(kv, 'settings', {}) })
  const link = signal<LinkState>('off')
  const linkMsg = signal('Sin enlace')
  const hello = signal<Hello | null>(null)
  const peers = signal<PeerInfo[]>([])
  const peersMsg = signal('')
  const peerId = signal<string | null>(prefs.peer ?? null)
  const hb = signal<Heartbeat>({ ok: null, rttMs: 0, at: 0, fails: 0 })
  const game = signal<GameState>(loadedGame)
  const fleet = signal<PlacedShip[]>(loadedFleet)
  const known = signal<KnownShip[]>(loadedKnown)
  const cycle = signal<Cycle>(restoreCycle())
  /** cancelación sobria del ciclo (error del módulo, STOP, enlace caído) */
  const cancelFx = signal<{ id: number; text: string } | null>(null)
  /** casilla ya resuelta que se intentó repetir: la interfaz la resalta */
  const flash = signal<{ id: number; at: Coord } | null>(null)
  /** el estudiante dijo «NO LE DIO» sobre un barco ubicado: pide confirmar */
  const conflict = signal(false)
  /** último barco hundido (para la animación) */
  const lastSunk = signal<KnownShip | null>(null)
  const undoCount = signal(0)
  const selected = signal<string | null>(null)
  const orientPref = signal<Orient>('H')
  const draft = signal<{ x: number | null; y: number | null }>({ x: null, y: null })
  const target = computed<Coord | null>(() => (draft.value.x !== null && draft.value.y !== null ? { x: draft.value.x, y: draft.value.y } : null))
  const lastSent = signal<Coord | null>(prefs.lastSent && isValidCoord(prefs.lastSent) ? prefs.lastSent : null)
  const sent = signal<number>(prefs.sent ?? 0)
  const busy = signal(false)
  const status = signal<Status>({ kind: 'idle', text: '' })
  const beam = signal<Coord | null>(null)
  const rings = signal<Ring[]>([])
  const test = signal<TestState>({ state: 'idle', done: 0, at: [], msg: '', startedAt: 0, durationMs: 0 })
  const cal = signal<CalValues | null>(null)
  const calMsg = signal('')
  const log = signal<LogEntry[]>([])
  const calib = createCalib({ kv, send, connected: computed(() => link.value === 'on' || link.value === 'busy'), busy, caps: computed(() => hello.value?.caps ?? []) })
  const victory = signal(cycle.value.phase === 'won')

  const validation = computed(() => validateFleet(fleet.value))
  const pendingShot = computed(() => game.value.shots.find(s => s.result === undefined) ?? null)
  const connected = computed(() => link.value === 'on' || link.value === 'busy')
  const unplaced = computed(() => FLEET_SPEC.filter(f => !fleet.value.some(s => s.id === f.id)))
  const pendingHits = computed(() => pendingLocate(game.value, known.value))
  const left = computed(() => fleetLeft(game.value))

  // ---------- internos ----------
  let transport: LineTransport | null = null
  let subs: (() => void)[] = []
  let manualClose = false
  let hbTimer: ReturnType<typeof setInterval> | null = null
  let reconnecting = false
  let logId = 0
  let ringId = 0
  let transportReady: Promise<void> | null = null
  const feedback = deps.feedback ?? makeFeedback(() => settings.value)

  const addLog = (dir: LogEntry['dir'], text: string) => {
    const e: LogEntry = { id: ++logId, t: now(), dir, text }
    log.value = [e, ...log.value].slice(0, 400)
  }
  const setStatus = (k: Status['kind'], text: string) => { status.value = { kind: k, text } }
  const pulse = (k: Ring['kind'], at: Coord) => {
    const r: Ring = { id: ++ringId, kind: k, at }
    rings.value = [...rings.value, r]
    setTimeout(() => { rings.value = rings.value.filter(x => x.id !== r.id) }, 1500)
  }

  /** Envía UNA línea, la anota en la bitácora y devuelve las respuestas. */
  async function send(line: string, timeoutMs: number): Promise<string[]> {
    const tr = transport
    if (!tr) throw new Error('sin transporte')
    addLog('tx', line)
    try {
      const lines = await tr.request(line, timeoutMs)
      for (const l of lines) addLog(/^ERR\b/i.test(l) ? 'err' : 'rx', l)
      return lines
    } catch (e) {
      addLog('err', `${line} → ${errMsg(e)}`)
      throw e
    }
  }

  // ---------- transporte y enlace ----------
  function detach() { subs.forEach(u => u()); subs = []; stopHeartbeat() }

  async function attach(): Promise<void> {
    detach()
    const tr = await makeTransport(kind.value)
    transport = tr
    subs.push(tr.onStateChange((on, reason) => void onLinkChange(on, reason)))
    subs.push(tr.onUnsolicited(line => addLog('rx', line)))
  }

  /** Garantiza que haya un transporte creado para `kind`. */
  function ensureTransport(): Promise<void> {
    if (!transportReady) transportReady = attach().catch(e => { transportReady = null; throw e })
    return transportReady
  }

  async function setKind(k: TransportKind): Promise<void> {
    if (k === kind.value && transport) return
    manualClose = true
    try { await transport?.disconnect() } catch { /* ya caído */ }
    batch(() => {
      kind.value = k; link.value = 'off'; linkMsg.value = 'Sin enlace'; hello.value = null; peers.value = []; peerId.value = null; busy.value = false
    })
    transport = null; transportReady = null
    addLog('sys', `Transporte: ${k}`)
    await ensureTransport()
  }

  async function refreshPeers(all = false): Promise<void> {
    try {
      await ensureTransport()
      peersMsg.value = 'Buscando módulos…'
      const list = await transport!.list(all ? undefined : 'SONAR')
      peers.value = list
      peersMsg.value = list.length ? '' : kind.value === 'bluetooth'
        ? (all ? 'No hay dispositivos Bluetooth emparejados.' : 'No hay módulos SONAR emparejados. Empareja SONAR-A en Ajustes de Bluetooth del celular y vuelve a buscar (o prueba «Mostrar todos»).')
        : 'No se encontró ningún módulo SONAR.'
    } catch (e) {
      peers.value = []
      peersMsg.value = `No se pudo buscar módulos: ${errMsg(e)}`
    }
  }

  async function doHello(): Promise<void> {
    try {
      const lines = await send('HELLO', 3000)
      for (const l of lines) { const r = parseReply(l); if (r.t === 'hello') { hello.value = { fw: r.fw, name: r.name, mode: r.mode, caps: r.caps }; return } }
      hello.value = null
    } catch { hello.value = null }
  }

  async function connect(id?: string): Promise<boolean> {
    const pid = id ?? peerId.value
    if (!pid) { linkMsg.value = 'Elige un módulo de la lista.'; return false }
    try {
      await ensureTransport()
      manualClose = false
      batch(() => { link.value = 'connecting'; linkMsg.value = 'Conectando…'; peerId.value = pid })
      await transport!.connect(pid)
      await onConnected()
      return true
    } catch (e) {
      batch(() => { link.value = 'error'; linkMsg.value = kind.value === 'bluetooth' ? 'No se pudo conectar. ¿Está encendido y emparejado el módulo SONAR?' : `No se pudo conectar: ${errMsg(e)}` })
      addLog('err', `conexión: ${errMsg(e)}`)
      feedback('error')
      return false
    }
  }

  async function onConnected(): Promise<void> {
    batch(() => { link.value = 'on'; linkMsg.value = 'Conectado'; hb.value = { ok: null, rttMs: 0, at: 0, fails: 0 } })
    addLog('sys', 'Enlace establecido')
    await doHello()
    if (hello.value) linkMsg.value = `Conectado a ${hello.value.name}`
    startHeartbeat()
    feedback('ok')
  }

  async function disconnect(): Promise<void> {
    manualClose = true
    stopHeartbeat()
    try { await transport?.disconnect() } catch { /* nada */ }
    batch(() => { link.value = 'off'; linkMsg.value = 'Desconectado'; hello.value = null; busy.value = false })
    calib.linkLost()
    addLog('sys', 'Desconectado')
  }

  async function onLinkChange(on: boolean, reason?: string): Promise<void> {
    if (on) {
      if (link.value === 'connecting' || reconnecting) return // lo gestiona connect()/reconexión
      if (link.value === 'error' || link.value === 'off') await onConnected() // reconexión propia del transporte
      return
    }
    stopHeartbeat()
    batch(() => { busy.value = false; hello.value = null })
    calib.linkLost()
    if (isCancellable(cycle.value.phase)) cancelCycle('Se perdió el enlace con el módulo.')
    if (test.value.state === 'run') test.value = { ...test.value, state: 'fail', msg: 'Se perdió el enlace durante la prueba.' }
    if (manualClose) { link.value = 'off'; linkMsg.value = 'Desconectado'; return }
    batch(() => { link.value = 'error'; linkMsg.value = 'Enlace perdido' + (reason ? ` (${reason})` : '') })
    addLog('err', `enlace perdido${reason ? `: ${reason}` : ''}`)
    feedback('error')
    if (kind.value !== 'bluetooth') void reconnectLoop() // el transporte Bluetooth ya reintenta por su cuenta
  }

  async function reconnectLoop(): Promise<void> {
    if (reconnecting || !peerId.value) return
    reconnecting = true
    try {
      for (const d of reconnectDelays) {
        await new Promise(r => setTimeout(r, d))
        if (manualClose || !transport) return
        link.value = 'connecting'; linkMsg.value = 'Reconectando…'
        try { await transport.connect(peerId.value); reconnecting = false; await onConnected(); return } catch { /* siguiente intento */ }
      }
      batch(() => { link.value = 'error'; linkMsg.value = 'No se pudo reconectar. Revisa el módulo y vuelve a conectar.' })
    } finally { reconnecting = false }
  }

  // ---------- latido ----------
  async function ping(): Promise<boolean> {
    if (!transport?.isConnected() || busy.value || test.value.state === 'run' || calib.working.value > 0) return true
    const t0 = now()
    try {
      const lines = await send('PING', 3000)
      const ok = lines.some(l => parseReply(l).t === 'pong')
      hb.value = ok ? { ok: true, rttMs: Math.max(0, now() - t0), at: now(), fails: 0 } : { ...hb.value, ok: false, fails: hb.value.fails + 1 }
      return ok
    } catch {
      const fails = hb.value.fails + 1
      hb.value = { ...hb.value, ok: false, fails }
      if (fails >= 2 && link.value === 'on') {
        batch(() => { link.value = 'error'; linkMsg.value = 'El módulo no responde' })
        if (kind.value !== 'bluetooth' && !manualClose) void reconnectLoop()
      }
      return false
    }
  }
  function startHeartbeat() { stopHeartbeat(); hbTimer = setInterval(() => void ping(), hbMs) }
  function stopHeartbeat() { if (hbTimer) clearInterval(hbTimer); hbTimer = null }

  // ---------- ciclo de disparo ----------
  let token = 0
  const timers = new Set<ReturnType<typeof setTimeout>>()
  let fxId = 0
  const undoStack: Snap[] = []
  const clearTimers = () => { timers.forEach(clearTimeout); timers.clear() }
  /** Programa `fn` para dentro de `ms`; se descarta si el ciclo cambió de fase mientras tanto. */
  const after = (ms: number, fn: () => void) => {
    const mine = token
    const h = setTimeout(() => { timers.delete(h); if (mine === token) fn() }, ms)
    timers.add(h)
  }
  /** Aplica un evento a la máquina de estados; invalida los temporizadores de la fase anterior. */
  const go = (ev: CycleEvent): boolean => {
    const nx = cycleNext(cycle.value, ev)
    if (nx === cycle.value) return false
    token++; clearTimers()
    batch(() => { cycle.value = nx; if (nx.phase === 'won') victory.value = true; else if (victory.value) victory.value = false })
    return true
  }
  const snap = (cy?: Cycle): Snap => ({ game: game.value, known: known.value, sent: sent.value, lastSent: lastSent.value, cycle: cy ?? cycle.value })
  const pushUndo = (cy?: Cycle) => { undoStack.push(snap(cy)); if (undoStack.length > 30) undoStack.shift(); undoCount.value = undoStack.length }
  const flashCell = (at: Coord) => { flash.value = { id: ++fxId, at }; const id = fxId; setTimeout(() => { if (flash.value?.id === id) flash.value = null }, 1800) }

  const fail = (reason: FireFail, message: string, code?: string): FireResult => {
    setStatus('err', message)
    return code ? { ok: false, reason, message, code } : { ok: false, reason, message }
  }

  /** Cancela el ciclo (flying / verdict) y deshace el disparo que aún no tenía veredicto. */
  function cancelCycle(message: string, n?: number): void {
    const cy = cycle.value
    if (!isCancellable(cy.phase) || (n !== undefined && cy.n !== n)) { setStatus('err', message); return }
    const sh = game.value.shots.find(x => x.n === cy.n)
    batch(() => {
      if (sh && sh.result === undefined) {
        const rest = game.value.shots.filter(x => x.n !== sh.n)
        game.value = { ...game.value, shots: rest }
        sent.value = Math.max(0, sent.value - 1)
        lastSent.value = rest.length ? rest[rest.length - 1]!.at : null
        if (cy.direct) { undoStack.pop(); undoCount.value = undoStack.length }
      }
      beam.value = null
      cancelFx.value = { id: ++fxId, text: message }
    })
    const id = fxId
    setTimeout(() => { if (cancelFx.value?.id === id) cancelFx.value = null }, timing.cancel)
    go({ t: 'cancel' })
    setStatus('err', message)
    feedback('error')
  }

  function startExplosion(at: Coord): void {
    pulse('hit', at)
    feedback('acierto')
    after(timing.explosion, onExplosionDone)
  }
  function startSunk(ship: KnownShip, at: Coord): void {
    lastSunk.value = ship
    pulse('sunk', at)
    feedback('hundido')
    after(timing.sunk, onSunkDone)
  }
  function onSunkDone(): void {
    const won = isVictory(game.value)
    if (go({ t: 'done', won })) { if (won) feedback('victoria'); else setStatus('ok', 'Hundido. Sigue apuntando.') }
  }
  function onExplosionDone(): void {
    const cy = cycle.value
    if (cy.phase !== 'explosion' || !cy.at) return
    const r = reconcileSunk(game.value, known.value, now())
    if (r.sunk.length) {
      game.value = r.state
      go({ t: 'done', sunk: true })
      startSunk(r.sunk[r.sunk.length - 1]!, cy.at)
    } else go({ t: 'done' })
  }
  /** Fin del vuelo: justo antes de tocar la casilla el tiempo se congela (veredicto), o explota si el barco ya está ubicado. */
  function onLanded(): void {
    const cy = cycle.value
    if (cy.phase !== 'flying' || !cy.at || cy.n === null) return
    go({ t: 'landed' })
    if (cy.direct) {
      game.value = setVerdict(game.value, cy.n, 'hit', undefined, now())
      startExplosion(cy.at)
    } else { feedback('pausa'); setStatus('wait', `Espera el veredicto en (${cy.at.x},${cy.at.y}).`) }
  }

  /**
   * DISPARAR. Arranca el ciclo YA (vuelo animado) y envía (x,y) UNA vez al módulo; la pausa del veredicto es solo visual
   * y no espera la respuesta. La promesa devuelta resuelve con la respuesta del módulo (la interfaz no la espera);
   * si el módulo responde ERR o el enlace cae, el ciclo se cancela.
   */
  async function fireAt(c: Coord): Promise<FireResult> {
    if (!isValidCoord(c)) return fail('range', friendlyError('RANGE'), 'RANGE')
    const tr = transport
    if (!tr || !tr.isConnected() || link.value === 'off' || link.value === 'error' || link.value === 'connecting') {
      return fail('offline', 'Sin enlace con el módulo. Conéctalo en la pestaña Enlace.')
    }
    if (cycle.value.phase === 'won') return fail('pending', 'La partida terminó. Empieza una nueva en la pestaña Partida.')
    if (cycle.value.phase !== 'aim') return fail('pending', 'Primero termina el disparo en curso: falta el veredicto o ubicar el barco.')
    if (busy.value || test.value.state === 'run') return fail('busy', 'El módulo sigue con el disparo anterior. Espera o pulsa STOP.')
    if (hasShot(game.value, c)) { flashCell(c); feedback('error'); return fail('repeat', `Ya disparaste a (${c.x},${c.y}): casilla resuelta. Elige otra.`) }
    const direct = !!knownShipAt(known.value, c)
    calib.laserKilled() // el módulo apaga el láser de calibración al disparar
    if (direct) pushUndo(IDLE)
    batch(() => {
      busy.value = true; link.value = 'busy'; beam.value = c
      game.value = addShot(game.value, c, now())
      sent.value += 1; lastSent.value = c
    })
    const n = game.value.shots.length
    go({ t: 'fire', at: c, n, direct })
    setStatus('wait', `Disparando a (${c.x},${c.y})…`)
    feedback('disparo')
    after(timing.flight, onLanded)
    try {
      const lines = await send(fire(c), shotTimeout)
      let okAt: Coord | null = null
      let errCode: string | null = null
      for (const l of lines) {
        const r = parseReply(l)
        if (r.t === 'ok-shot') okAt = r.at
        else if (r.t === 'err') errCode = r.code
      }
      if (errCode) {
        const msg = friendlyError(errCode as ErrCode)
        cancelCycle(msg, n)
        return fail(errCode === 'STOP' ? 'stopped' : 'module', msg, errCode)
      }
      if (!okAt) { const msg = 'Respuesta inesperada del módulo. Revisa la bitácora.'; cancelCycle(msg, n); return fail('module', msg) }
      if (cycle.value.n === n && isCancellable(cycle.value.phase)) setStatus('ok', `Láser en (${c.x},${c.y}) · da el veredicto`)
      return { ok: true, at: c }
    } catch (e) {
      const msg = !tr.isConnected() ? 'Se perdió el enlace con el módulo.' : /timeout/i.test(errMsg(e)) ? 'El módulo no respondió a tiempo. Pulsa STOP y revisa el enlace.' : `Fallo de comunicación: ${errMsg(e)}`
      cancelCycle(msg, n)
      return fail(!tr.isConnected() ? 'offline' : 'timeout', msg)
    } finally {
      beam.value = null
      busy.value = false
      if (link.value === 'busy') link.value = 'on'
    }
  }

  async function stop(): Promise<void> {
    if (isCancellable(cycle.value.phase)) cancelCycle('Disparo detenido por STOP.')
    if (!transport?.isConnected()) { if (!cancelFx.value) setStatus('err', 'Sin enlace: no hay nada que detener.'); return }
    try {
      await send('STOP', 3000)
      calib.laserKilled()
      setStatus('ok', 'STOP enviado')
    } catch (e) { setStatus('err', `STOP no confirmado: ${errMsg(e)}`) }
  }

  /** Veredicto de los estudiantes. NO sobre un barco ubicado pide confirmar (devuelve 'conflict'). */
  function answer(yes: boolean, confirmed = false): 'ok' | 'conflict' | 'ignored' {
    const cy = cycle.value
    if (cy.phase !== 'verdict' || cy.n === null || !cy.at) return 'ignored'
    if (!yes && !confirmed && knownShipAt(known.value, cy.at)) { conflict.value = true; return 'conflict' }
    conflict.value = false
    pushUndo()
    game.value = setVerdict(game.value, cy.n, yes ? 'hit' : 'miss', undefined, now())
    if (yes) { go({ t: 'hit' }); startExplosion(cy.at) }
    else {
      go({ t: 'miss' })
      pulse('eco', cy.at)
      feedback('agua')
      after(timing.splash, () => { if (go({ t: 'done' })) setStatus('ok', 'Agua. Sigue apuntando.') })
    }
    return 'ok'
  }
  const dismissConflict = () => { conflict.value = false }

  // ---------- ubicar el barco ----------
  const checkLocation = (cells: Coord[]): LocationCheck => {
    const at = cycle.value.at ?? { x: 0, y: 0 }
    return validateLocation(game.value, known.value, at, cells)
  }
  function locate(cells: Coord[]): { ok: true; ship: KnownShip } | { ok: false; errors: string[] } {
    const cy = cycle.value
    if (cy.phase !== 'locate' || !cy.at) return { ok: false, errors: ['No hay ningún impacto por ubicar.'] }
    const r = locateShip(game.value, known.value, cy.at, cells)
    if (!r.ok) return r
    pushUndo()
    const rec = reconcileSunk(game.value, r.known, now())
    batch(() => { known.value = r.known; game.value = rec.state })
    go({ t: 'located', sunk: rec.sunk.length > 0 })
    if (rec.sunk.length) startSunk(rec.sunk[rec.sunk.length - 1]!, cy.at)
    else { feedback('ok'); setStatus('ok', `${r.ship.kind === 'submarino' ? 'Submarino' : 'Embarcación'} ubicado. Sigue apuntando.`) }
    return { ok: true, ship: r.ship }
  }
  /** «No sé / después»: el impacto queda sin ubicar (pendiente en el radar). */
  function skipLocate(): void {
    if (cycle.value.phase !== 'locate') return
    pushUndo()
    go({ t: 'skip' })
    setStatus('ok', 'Impacto sin ubicar: queda pendiente en el radar.')
  }
  /** Reabre «Ubica el barco» para un impacto pendiente. */
  function relocate(c: Coord): boolean {
    const sh = game.value.shots.find(x => x.result === 'hit' && x.at.x === c.x && x.at.y === c.y)
    if (!sh || knownShipAt(known.value, c) || cycle.value.phase !== 'aim') return false
    return go({ t: 'relocate', at: sh.at, n: sh.n })
  }

  /** Deshace la última marca (veredicto, ubicación o impacto directo). */
  function undo(): boolean {
    const ph = cycle.value.phase
    if (ph !== 'aim' && ph !== 'locate' && ph !== 'won') return false
    const sn = undoStack.pop()
    undoCount.value = undoStack.length
    if (!sn) return false
    token++; clearTimers()
    batch(() => {
      game.value = sn.game; known.value = sn.known; sent.value = sn.sent; lastSent.value = sn.lastSent
      cycle.value = sn.cycle; victory.value = sn.cycle.phase === 'won'; conflict.value = false; lastSunk.value = null
    })
    setStatus('ok', sn.cycle.phase === 'verdict' ? 'Deshecho: vuelve a dar el veredicto.' : sn.cycle.phase === 'locate' ? 'Deshecho: vuelve a ubicar el barco.' : 'Deshecho.')
    return true
  }

  // ---------- TEST de 5 posiciones ----------
  async function runTest(): Promise<boolean> {
    const tr = transport
    if (!tr?.isConnected() || link.value === 'off' || link.value === 'error') {
      test.value = { state: 'fail', done: 0, at: [], msg: 'Conecta el módulo antes de hacer la prueba.', startedAt: now(), durationMs: 0 }
      return false
    }
    if (busy.value || test.value.state === 'run') return false
    calib.laserKilled()
    const t0 = now()
    batch(() => { busy.value = true; link.value = 'busy'; test.value = { state: 'run', done: 0, at: [], msg: 'Probando 5 posiciones…', startedAt: t0, durationMs: 0 } })
    const live: Coord[] = []
    const onLine = (line: string) => {
      const r = parseReply(line)
      if (r.t === 'ok-shot' && test.value.state === 'run') {
        live.push(r.at)
        test.value = { ...test.value, done: Math.max(test.value.done, live.length), at: [...live] }
      }
    }
    const offs = [tr.onUnsolicited(onLine)]
    if (tr instanceof SimTransport) offs.push(tr.onTraffic((dir, l) => { if (dir === 'rx') onLine(l) }))
    try {
      const lines = await send('TEST', testTimeout)
      const reps = lines.map(parseReply)
      const at = reps.flatMap(r => (r.t === 'ok-shot' ? [r.at] : []))
      const err = reps.find(r => r.t === 'err')
      const done = reps.some(r => r.t === 'test-done')
      const abort = reps.some(r => r.t === 'test-abort')
      const dur = now() - t0
      if (done && at.length >= 5 && !err) {
        test.value = { state: 'ok', done: 5, at, msg: 'APROBADO: el láser pasó por las 5 posiciones.', startedAt: t0, durationMs: dur }
        feedback('victoria')
        return true
      }
      const msg = abort ? 'Prueba interrumpida (STOP).' : err && err.t === 'err' ? friendlyError(err.code) : 'La prueba no terminó correctamente. Revisa la bitácora.'
      test.value = { state: 'fail', done: at.length, at, msg: `FALLÓ: ${msg}`, startedAt: t0, durationMs: dur }
      feedback('error')
      return false
    } catch (e) {
      test.value = { state: 'fail', done: live.length, at: live, msg: `FALLÓ: ${/timeout/i.test(errMsg(e)) ? 'el módulo no respondió a tiempo.' : errMsg(e)}`, startedAt: t0, durationMs: now() - t0 }
      feedback('error')
      return false
    } finally {
      offs.forEach(o => o())
      batch(() => { busy.value = false; if (link.value === 'busy') link.value = 'on' })
    }
  }

  // ---------- calibración ----------
  async function calCmd(line: string, okText: string): Promise<boolean> {
    if (!transport?.isConnected()) { calMsg.value = 'Conecta el módulo primero.'; return false }
    try {
      const reps = (await send(line, 4000)).map(parseReply)
      const err = reps.find(r => r.t === 'err')
      if (err && err.t === 'err') { calMsg.value = friendlyError(err.code); return false }
      const c = reps.find(r => r.t === 'cal')
      if (c && c.t === 'cal') cal.value = c.cal
      calMsg.value = okText
      return true
    } catch (e) { calMsg.value = `Sin respuesta: ${errMsg(e)}`; return false }
  }
  const calShow = () => calCmd('CAL SHOW', 'Calibración leída del módulo.')
  const calSave = () => calCmd('CAL SAVE', 'Calibración guardada en el módulo.')
  const calReset = async () => { const ok = await calCmd('CAL RESET', 'Calibración restablecida.'); if (ok) await calShow(); return ok }
  async function calSet(v: CalValues): Promise<boolean> {
    for (const r of CAL_RANGES) {
      const x = v[r.key]
      if (!Number.isFinite(x) || x < r.min || x > r.max) { calMsg.value = `${r.label} debe estar entre ${r.min} y ${r.max} ${r.unit}.`; return false }
    }
    return calCmd(`CAL SET ${v.x} ${v.y} ${v.h} ${v.panTrim} ${v.tiltTrim}`, 'Calibración aplicada (aún sin guardar).')
  }

  // ---------- calibración de apuntado (protocolo v3) ----------
  const calibResetMap = async (): Promise<boolean> => { const ok = await calib.resetMap(); if (ok) await calShow(); return ok }

  // ---------- apuntar ----------
  const clamp = (n: number) => Math.max(1, Math.min(20, Math.round(n)))
  const setTarget = (c: Coord | null) => { draft.value = c ? { x: clamp(c.x), y: clamp(c.y) } : { x: null, y: null } }
  const setAxis = (axis: 'x' | 'y', v: number | null) => { draft.value = { ...draft.value, [axis]: v === null ? null : clamp(v) } }
  /** ±1 en un eje; sin valor previo, +1 arranca en 1 y −1 en 20. */
  const nudgeAxis = (axis: 'x' | 'y', d: number) => {
    const cur = draft.value[axis]
    setAxis(axis, cur === null ? (d > 0 ? 1 : 20) : cur + d)
  }

  // ---------- flota ----------
  const setFleet = (s: PlacedShip[]) => { fleet.value = s; if (selected.value && !s.some(x => x.id === selected.value)) selected.value = null }
  /** Toca una casilla del editor: selecciona/mueve/coloca según el contexto. */
  function tapCell(c: Coord): void {
    const hit = shipAt(fleet.value, c)
    const sel = fleet.value.find(s => s.id === selected.value)
    if (hit) { selected.value = hit.id === selected.value ? null : hit.id; return }
    if (sel) { setFleet(placeShip(fleet.value, ensureInside({ ...sel, x: c.x, y: c.y }))); return }
    const next = unplaced.value[0]
    if (!next) return
    const ship = ensureInside({ ...next, x: c.x, y: c.y, orient: orientPref.value })
    setFleet(placeShip(fleet.value, ship))
    selected.value = ship.id
  }
  function moveShipTo(id: string, x: number, y: number): void {
    const s = fleet.value.find(q => q.id === id)
    if (s) setFleet(placeShip(fleet.value, ensureInside({ ...s, x, y })))
  }
  function rotateSelected(): void {
    const s = fleet.value.find(q => q.id === selected.value)
    if (s) { const r = rotateShip(s); orientPref.value = r.orient; setFleet(placeShip(fleet.value, r)) } else orientPref.value = orientPref.value === 'H' ? 'V' : 'H'
  }
  function removeSelected(): void { if (selected.value) setFleet(removeShip(fleet.value, selected.value)) }
  const randomizeFleet = (rng?: () => number) => { selected.value = null; setFleet(rng ? randomFleet(rng) : randomFleet()) }
  const clearFleet = () => { selected.value = null; setFleet([]) }
  const fleetText = () => fleetCoordinatesList(fleet.value)

  // ---------- modos ----------
  const setMode = (m: Mode) => { mode.value = m; selected.value = null }
  const setSubmode = (s: Submode) => { submode.value = s }
  function updateSettings(p: Partial<Settings>): void { settings.value = { ...settings.value, ...p } }

  // ---------- partida ----------
  function newMatch(): void {
    batch(() => {
      game.value = newGame(now()); known.value = []; lastSent.value = null; sent.value = 0; draft.value = { x: null, y: null }
      victory.value = false; conflict.value = false; lastSunk.value = null; cancelFx.value = null; flash.value = null
      status.value = { kind: 'idle', text: '' }
    })
    token++; clearTimers(); undoStack.length = 0; undoCount.value = 0
    cycle.value = IDLE
    if (transport instanceof SimTransport) transport.newRival()
    addLog('sys', 'Nueva partida')
  }
  const exportJSON = (): string => JSON.stringify({ app: 'SONAR', version: APP_VERSION, exportedAt: now(), game: JSON.parse(toJSON(game.value)), known: known.value, fleet: fleet.value, sent: sent.value }, null, 1)
  const clearLog = () => { log.value = [] }
  const logText = (): string => [...log.value].reverse().map(e => `${new Date(e.t).toISOString()} ${e.dir.padEnd(3)} ${e.text}`).join('\n')

  // ---------- persistencia y efectos ----------
  const disposers: (() => void)[] = []
  disposers.push(effect(() => saveJSON(kv, 'settings', settings.value)))
  disposers.push(effect(() => saveJSON(kv, 'fleet', fleet.value)))
  disposers.push(effect(() => { try { kv.set('game', toJSON(game.value)) } catch { /* nada */ } }))
  disposers.push(effect(() => saveJSON(kv, 'known', known.value)))
  disposers.push(effect(() => saveJSON(kv, 'cycle', cycle.value)))
  disposers.push(effect(() => saveJSON(kv, 'prefs', { mode: mode.value, kind: kind.value, peer: peerId.value, lastSent: lastSent.value, sent: sent.value })))
  disposers.push(effect(() => { void setWake(settings.value.wake) }))
  disposers.push(effect(() => { try { if (typeof document !== 'undefined') document.documentElement.dataset.theme = settings.value.theme } catch { /* nada */ } }))

  async function init(): Promise<void> { await ensureTransport(); void refreshPeers() }
  async function dispose(): Promise<void> {
    disposers.forEach(d => d())
    calib.dispose()
    token++; clearTimers()
    manualClose = true
    detach()
    try { await transport?.disconnect() } catch { /* nada */ }
  }

  return {
    // señales
    mode, submode, kind, settings, link, linkMsg, hello, peers, peersMsg, peerId, hb, game, fleet, selected, orientPref,
    draft, target, lastSent, sent, busy, status, beam, rings, test, cal, calMsg, log, victory,
    cycle, known, cancelFx, flash, conflict, lastSunk, undoCount,
    // derivadas
    validation, pendingShot, connected, unplaced, pendingHits, left,
    // acciones
    calib, calibResetMap,
    init, dispose, setKind, refreshPeers, connect, disconnect, ping, fireAt, stop, runTest, calShow, calSet, calSave, calReset,
    setTarget, setAxis, nudgeAxis, answer, dismissConflict, checkLocation, locate, skipLocate, relocate, undo,
    tapCell, moveShipTo, rotateSelected, removeSelected, randomizeFleet, clearFleet, setFleet, fleetText,
    setMode, setSubmode, updateSettings, newMatch, exportJSON, clearLog, logText,
    // utilidades
    remaining: () => remainingShips(game.value),
    timing,
    /** sonido + vibración según los ajustes (p. ej. el tick al trazar el barco) */
    fx: feedback,
    shipCells,
    get transport() { return transport },
  }
}

export type App = ReturnType<typeof createApp>
