/** Splash de arranque: el HTML/CSS vive en index.html (se pinta en el primer fotograma); aquí solo se
 *  decide cuándo retirarlo: ~1,6 s, un toque lo salta, y un tope de seguridad por si algo falla. */
export function runSplash(speed = 1, reduced = false): Promise<void> {
  const el = typeof document === 'undefined' ? null : document.getElementById('splash')
  if (!el) return Promise.resolve()
  return new Promise<void>(resolve => {
    let done = false
    const end = () => {
      if (done) return
      done = true
      el.classList.add('out')
      setTimeout(() => { el.remove(); resolve() }, 300 / Math.min(speed, 4))
    }
    el.addEventListener('pointerdown', end, { once: true })
    setTimeout(end, (reduced ? 900 : 1600) / speed)
    setTimeout(end, 4000)
  })
}
