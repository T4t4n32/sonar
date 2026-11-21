import { render } from 'preact'
import './styles/app.css'
import { app } from './state'
import { initIntro, introReady, introSpeed, prefersReducedMotion } from './state/intro'
import { App } from './ui/App'
import { preloadTutorial } from './ui/intro/host'
import { runSplash } from './ui/intro/splash'

render(<App />, document.getElementById('app')!)

// Gancho para las pruebas e2e (app/tools/e2e_*.py): solo existe con «?e2e» en la URL.
try { if (new URLSearchParams(location.search).has('e2e')) (globalThis as { __sonar?: unknown }).__sonar = app } catch { /* nada */ }

// Arranque: splash (HTML/CSS ya pintado en index.html) y, la primera vez, tutorial. Nada de esto debe bloquear la app.
try {
  const speed = introSpeed()
  if (speed !== 1) document.documentElement.style.setProperty('--ispd', String(speed))
  if (initIntro()) void preloadTutorial().catch(() => { /* el anfitrión lo reintenta y, si falla, cierra */ })
  void runSplash(speed, prefersReducedMotion()).catch(() => { /* nada */ }).finally(() => { introReady.value = true })
} catch {
  document.getElementById('splash')?.remove()
  introReady.value = true
}
