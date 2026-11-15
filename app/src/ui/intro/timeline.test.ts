import { describe, expect, it, vi } from 'vitest'
import { Timeline, type TLReason } from './timeline'
import { ESCENAS, escenasDe } from './guion'
import { initIntro, introOpen, introSpeed, isIntroSeen, markIntroSeen, closeIntro, setReplayMode, replayMode } from '../../state/intro'
import { memoryKV } from '../../state/storage'

const S = [{ id: 'a', dur: 1000 }, { id: 'b', dur: 2000 }, { id: 'c', dur: 500 }]
const mk = (speed = 1) => new Timeline(S, { speed, raf: () => 1, caf: () => {}, now: () => 0 })

describe('Timeline', () => {
  it('progreso dentro de la escena y global', () => {
    const t = mk(); t.play(); t.tick(500)
    expect(t.state.index).toBe(0); expect(t.state.progress).toBeCloseTo(0.5)
    expect(t.total).toBeCloseTo(500 / 3500)
  })
  it('encadena escenas con el sobrante', () => {
    const t = mk(); t.play(); t.tick(1500)
    expect(t.state.index).toBe(1); expect(t.state.elapsed).toBeCloseTo(500)
  })
  it('termina en la última escena y se detiene', () => {
    const t = mk(); const ev: TLReason[] = []; t.on((_, w) => ev.push(w))
    t.play(); t.tick(99999)
    expect(t.state.ended).toBe(true); expect(t.state.playing).toBe(false)
    expect(t.state.index).toBe(2); expect(t.state.progress).toBe(1)
    expect(ev).toContain('end')
    t.play(); expect(t.state.playing).toBe(false)
  })
  it('pausa congela el tiempo', () => {
    const t = mk(); t.play(); t.tick(300); t.pause(); t.tick(300)
    expect(t.state.elapsed).toBe(300)
    t.play(); t.tick(100); expect(t.state.elapsed).toBe(400)
  })
  it('speed multiplica el tiempo', () => {
    const t = mk(20); t.play(); t.tick(50) // 50 ms * 20 = 1000 ms -> escena siguiente
    expect(t.state.index).toBe(1); expect(t.state.elapsed).toBe(0)
  })
  it('seek, next y prev', () => {
    const t = mk(); t.seek(1, 0.5)
    expect(t.state.index).toBe(1); expect(t.state.elapsed).toBe(1000)
    t.next(); expect(t.state.index).toBe(2)
    t.prev(); t.prev(); t.prev(); expect(t.state.index).toBe(0)
    t.seek(99); expect(t.state.index).toBe(2)
  })
  it('next en la última escena la da por terminada; seek reabre', () => {
    const t = mk(); t.seek(2); t.next()
    expect(t.state.ended).toBe(true)
    t.seek(1); expect(t.state.ended).toBe(false)
  })
  it('el bucle raf avanza con dt acotado y se puede cancelar', () => {
    let cb: ((t: number) => void) | null = null
    const t = new Timeline(S, { raf: f => { cb = f; return 7 }, caf: vi.fn(), now: () => 0 })
    t.play(); cb!(5000) // salto enorme: se recorta a 100 ms
    expect(t.state.elapsed).toBe(100)
    t.dispose(); expect(t.state.playing).toBe(false)
  })
  it('sin escenas lanza error', () => { expect(() => new Timeline([])).toThrow() })
})

describe('guion', () => {
  it('ids únicos, Acto 1 de 45-60 s y subtítulos ordenados', () => {
    const ids = ESCENAS.map(s => s.id); expect(new Set(ids).size).toBe(ids.length)
    const a1 = escenasDe('acto1'); const a2 = escenasDe('acto2')
    const d1 = a1.reduce((a, s) => a + s.dur, 0)
    expect(d1).toBeGreaterThanOrEqual(45000); expect(d1).toBeLessThanOrEqual(60000)
    expect(escenasDe('ambos').length).toBe(a1.length + a2.length)
    for (const s of ESCENAS) {
      expect(s.caps[0]!.at).toBe(0)
      for (let i = 1; i < s.caps.length; i++) expect(s.caps[i]!.at).toBeGreaterThan(s.caps[i - 1]!.at)
      for (const c of s.caps) expect(c.at).toBeLessThan(1)
    }
  })
})

describe('estado del tutorial', () => {
  it('primera vez abre; tras cerrar no vuelve', () => {
    const kv = memoryKV(); introOpen.value = null
    expect(isIntroSeen(kv)).toBe(false); expect(initIntro(kv)).toBe(true); expect(introOpen.value).toBe('ambos')
    closeIntro(kv); expect(introOpen.value).toBeNull(); expect(isIntroSeen(kv)).toBe(true)
    expect(initIntro(kv)).toBe(false)
    markIntroSeen(kv); expect(isIntroSeen(kv)).toBe(true)
  })
  it('introSpeed acota y valida', () => {
    expect(introSpeed('?introSpeed=20')).toBe(20); expect(introSpeed('?introSpeed=999')).toBe(60)
    expect(introSpeed('?introSpeed=x')).toBe(1); expect(introSpeed('')).toBe(1)
  })
  it('recuerda el modo de repetición', () => {
    const kv = memoryKV(); setReplayMode('acto2', kv); expect(replayMode.value).toBe('acto2'); expect(kv.get('introPrefs')).toContain('acto2')
    setReplayMode('ambos', kv)
  })
})
