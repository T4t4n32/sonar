import { useEffect } from 'preact/hooks'
import { app } from '../state'
import { introOpen, introReady } from '../state/intro'
import { tab, toast, type Tab } from './nav'
import { IntroHost } from './intro/host'
import { Icons, Mark } from './parts'
import { Batalla } from './views/Batalla'
import { Enlace } from './views/Enlace'
import { MiFlota } from './views/MiFlota'
import { Partida } from './views/Partida'

const TABS: { id: Tab; label: string; icon: keyof typeof Icons }[] = [
  { id: 'batalla', label: 'Batalla', icon: 'batalla' },
  { id: 'flota', label: 'Mi flota', icon: 'flota' },
  { id: 'enlace', label: 'Enlace', icon: 'enlace' },
  { id: 'partida', label: 'Partida', icon: 'partida' },
]

function Header() {
  const link = app.link.value
  const def = app.mode.value === 'defensor'
  const hb = app.hb.value
  const txt = link === 'busy' ? 'Módulo ocupado' : app.linkMsg.value
  return (
    <header class="top">
      <div class="brand"><Mark /><div><h1>SONAR</h1><p>Batalla Naval</p></div></div>
      <button type="button" id="modeChip" class={`modechip ${def ? 'def' : ''}`} aria-label={def ? 'Modo defensor. Tocar para entregar al profesor.' : 'Modo atacante. Tocar para ir a Mi flota.'}
        onClick={() => { if (def) { app.setMode('atacante'); tab.value = 'batalla' } else tab.value = 'flota' }}>
        <i />{def ? 'DEFENSOR' : 'ATACANTE'}
      </button>
      <div class="statusrow">
        <div id="pill" class={`pill ${link}`} role="status" aria-live="polite">
          <span class="dot" /><span class="ptxt">{txt}</span>
          {link === 'on' && hb.ok && <span class="pk">{hb.rttMs} ms</span>}
        </div>
      </div>
    </header>
  )
}

export function App() {
  useEffect(() => { void app.init() }, [])
  const t = tab.value
  const intro = introOpen.value
  const pend = app.submode.value === 'duelo' && app.pendingShot.value !== null
  return (
    <div class={`shell ${t === 'batalla' ? '' : 'nodock'}`}>
      <Header />
      <main class="view" key={t} id={`view-${t}`}>
        {t === 'batalla' && <Batalla />}
        {t === 'flota' && <MiFlota />}
        {t === 'enlace' && <Enlace />}
        {t === 'partida' && <Partida />}
      </main>
      <nav class="tabs" aria-label="Secciones">
        {TABS.map(x => (
          <button type="button" id={`tab-${x.id}`} aria-current={t === x.id ? 'page' : undefined} onClick={() => { tab.value = x.id }}>
            {Icons[x.icon]}{x.label}
            {x.id === 'batalla' && pend && t !== 'batalla' && <span class="bdg">1</span>}
          </button>
        ))}
      </nav>
      {toast.value && <div class="toast" role="status">{toast.value}</div>}
      {intro && introReady.value && <IntroHost mode={intro} />}
    </div>
  )
}
