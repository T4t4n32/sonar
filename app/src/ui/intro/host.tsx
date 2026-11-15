/** Anfitrión ligero del tutorial: carga diferida del chunk pesado y red de seguridad (si algo falla, cae a la app). */
import { Component, type ComponentChildren, type ComponentType } from 'preact'
import { useEffect, useState } from 'preact/hooks'
import { closeIntro, type IntroMode } from '../../state/intro'

type TutorialC = ComponentType<{ mode: IntroMode; onDone: () => void }>
let pending: Promise<TutorialC> | null = null
/** Empieza a descargar el tutorial (se llama al arrancar para que esté listo al terminar el splash). */
export function preloadTutorial(): Promise<TutorialC> {
  pending ??= import('./Tutorial').then(m => m.Tutorial)
  return pending
}

class Guard extends Component<{ children: ComponentChildren }, { bad: boolean }> {
  state = { bad: false }
  componentDidCatch(): void { this.setState({ bad: true }); closeIntro() }
  render() { return this.state.bad ? null : this.props.children }
}

export function IntroHost({ mode }: { mode: IntroMode }) {
  const [C, setC] = useState<TutorialC | null>(null)
  useEffect(() => {
    let alive = true
    preloadTutorial().then(c => { if (alive) setC(() => c) }).catch(() => { pending = null; closeIntro() })
    return () => { alive = false }
  }, [])
  // Mientras carga, un fondo liso evita ver la app por un instante.
  if (!C) return <div style="position:fixed;inset:0;z-index:200;background:#040a0f" aria-hidden="true" />
  return <Guard><C mode={mode} onDone={() => closeIntro()} /></Guard>
}
