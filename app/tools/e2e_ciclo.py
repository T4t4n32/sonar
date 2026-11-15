# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Prueba e2e del CICLO DE DISPARO (apuntar → vuelo → veredicto → gota / explosión → ubicar el barco → hundido).

Transporte SIMULADO, 375×812. Requiere `npx vite preview --port 4173` (o --url).
Capturas en registro/2026-11-15-app/ciclo-*.png.
    uv run --script tools/e2e_ciclo.py
"""
from __future__ import annotations

import argparse
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
RES: list[tuple[str, bool, str]] = []
ERRORS: list[str] = []


def check(nombre: str, ok: bool, detalle: str = "") -> None:
    RES.append((nombre, bool(ok), detalle))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""), flush=True)


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        import glob, os
        cands = sorted(glob.glob(os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), "chromium_headless_shell-*", "*", "chrome-headless-shell.exe")))
        if not cands:
            raise
        return p.chromium.launch(executable_path=cands[-1])


def aim(pg, x: int, y: int) -> None:
    """Escribe (x,y) con el teclado numérico de la vista Batalla."""
    pg.click("#val-x")
    for d in str(x):
        pg.get_by_role("button", name=d, exact=True).click()
    pg.click("#val-y")
    for d in str(y):
        pg.get_by_role("button", name=d, exact=True).click()


def drag_cells(pg, a: tuple[int, int], b: tuple[int, int], steps: int = 12) -> None:
    """Arrastra el dedo sobre #locBoard desde el centro de la casilla a hasta la b (con un poco de deriva lateral)."""
    bb = pg.locator("#locBoard").bounding_box()
    cw = bb["width"] / 20

    def pt(c, dx=0.0, dy=0.0):
        return bb["x"] + (c[0] - 0.5) * cw + dx, bb["y"] + (c[1] - 0.5) * cw + dy
    x0, y0 = pt(a)
    pg.mouse.move(x0, y0)
    pg.mouse.down()
    for i in range(1, steps + 1):
        k = i / steps
        x1, y1 = pt(b, dx=cw * 0.3)  # deriva lateral: el trazo debe «ajustarse» al eje
        pg.mouse.move(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
        pg.wait_for_timeout(18)
    pg.mouse.up()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:4173/")
    ap.add_argument("--out", default=str(REPO / "registro" / "2026-11-15-app"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = launch(p)
        ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, color_scheme="dark")
        ctx.add_init_script("try{localStorage.setItem('sonar.v1.introSeen','1')}catch(e){}")
        pg = ctx.new_page()
        pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type == "error" else None)
        pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
        pg.goto(a.url); pg.wait_for_selector("#tab-batalla")

        # ---- conectar
        pg.click("#tab-enlace"); pg.wait_for_selector("[data-peer]")
        pg.click("[data-peer]"); pg.wait_for_selector("#pill.on", timeout=5000)
        pg.click("#tab-batalla"); pg.wait_for_selector("#bFire")
        check("conectado y en Batalla", pg.locator("#pill.on").count() == 1)
        check("sin selector Atacante/Defensor ni Profesor/Duelo", pg.locator("#smProf, #smDuelo").count() == 0)
        check("marcador de flota: 3 embarcaciones · 2 submarinos", "3" in pg.inner_text("#fleetLeft") and "2" in pg.inner_text("#fleetLeft"), pg.inner_text("#fleetLeft").replace("\n", " "))

        # ---- apuntar (10,15) y disparar
        aim(pg, 10, 15)
        check("objetivo (10,15)", pg.inner_text("#bFire").startswith("DISPARAR (10,15)"), pg.inner_text("#bFire"))
        pg.click("#bFire")
        pg.wait_for_timeout(650)
        pg.screenshot(path=out / "ciclo-01-vuelo.png")
        check("vuelo: DISPARAR inhabilitado", pg.is_disabled("#bFire"))
        pg.wait_for_selector("#vYes", timeout=4000)
        pg.wait_for_timeout(250)
        pg.screenshot(path=out / "ciclo-02-pausa-botones.png")
        check("pausa: aparecen SÍ LE DIO y NO LE DIO", pg.is_visible("#vYes") and pg.is_visible("#vNo"))
        check("pausa: STOP visible", pg.is_visible("#bStop2"))
        bb = pg.locator("#vYes").bounding_box()
        check("botones enormes (≥ 120 px de alto)", bb["height"] >= 120, f"{bb['height']:.0f}px")

        # ---- NO LE DIO → gota
        pg.click("#vNo"); pg.wait_for_timeout(430)
        pg.screenshot(path=out / "ciclo-03-gota.png")
        pg.wait_for_function("document.querySelector('#bFire')?.textContent.startsWith('DISPARAR')", timeout=6000)
        check("NO LE DIO: marca de agua y vuelve a apuntar", pg.locator(".c.miss").count() == 1 and pg.locator("#vYes").count() == 0)

        # ---- repetir (10,15): casilla resuelta
        pg.click("#bFire"); pg.wait_for_timeout(300)
        check("repetir casilla: avisa", "Ya disparaste" in pg.inner_text("#status") or pg.locator(".toast").count() > 0, pg.inner_text("#status"))
        check("repetir casilla: la resalta y no abre vuelo", pg.locator(".c.dup").count() == 1 and pg.locator("#vYes").count() == 0)
        pg.screenshot(path=out / "ciclo-04-casilla-repetida.png")
        pg.wait_for_timeout(1800)

        # ---- (7,3) SÍ LE DIO → explosión → ubicar
        aim(pg, 7, 3)
        pg.click("#bFire"); pg.wait_for_selector("#vYes", timeout=4000)
        pg.click("#vYes"); pg.wait_for_timeout(300)
        pg.screenshot(path=out / "ciclo-05-explosion.png")
        pg.wait_for_selector("#locBoard", timeout=5000)
        pg.wait_for_timeout(300)
        check("pantalla «Ubica el barco» con el impacto (7, 3)", "(7, 3)" in pg.inner_text("#locCoord"), pg.inner_text("#locCoord"))
        bw = pg.locator("#locBoard").bounding_box()
        check("tablero a pantalla grande (≥ 300 px)", bw["width"] >= 300, f"{bw['width']:.0f}px")
        check("LISTO deshabilitado sin trazo", pg.is_disabled("#locDone"))
        # trazo inválido: 3 casillas
        drag_cells(pg, (7, 3), (7, 5))
        pg.wait_for_timeout(150)
        check("trazo de 3 casillas es inválido (rojo)", pg.locator(".c.pv.bad").count() == 3 and pg.is_disabled("#locDone"), pg.inner_text("#locLabel").replace("\n", " "))
        pg.screenshot(path=out / "ciclo-06-ubicar-invalido.png")
        # trazo válido de 4 casillas, verticales, con deriva lateral (se ajusta al eje)
        drag_cells(pg, (7, 3), (7, 6))
        pg.wait_for_timeout(150)
        lab = pg.inner_text("#locLabel").replace("\n", " ")
        check("trazo de 4 casillas: «Submarino · 4 casillas» en verde", pg.locator(".c.pv.ok").count() == 4 and "Submarino" in lab and pg.is_enabled("#locDone"), lab)
        pg.screenshot(path=out / "ciclo-07-ubicar-valido.png")
        pg.click("#locDone"); pg.wait_for_function("document.querySelector('#bFire')?.textContent.startsWith('DISPARAR') || document.querySelector('#bFire')?.textContent.includes('ELIGE')", timeout=6000)
        check("LISTO registra el barco y vuelve a apuntar", pg.locator("#locBoard").count() == 0 and pg.locator(".c.kship").count() == 3, f"kship={pg.locator('.c.kship').count()}")

        # ---- impactos directos hasta hundir
        saw_question = False
        for (x, y) in [(7, 4), (7, 5), (7, 6)]:
            aim(pg, x, y)
            pg.click("#bFire")
            pg.wait_for_timeout(1500)
            if pg.locator("#vYes").count():
                saw_question = True
            if (x, y) == (7, 6):
                pg.wait_for_selector(".sunk-in", timeout=4000)
                pg.wait_for_timeout(1100)
                pg.screenshot(path=out / "ciclo-08-hundido.png")
            else:
                pg.wait_for_function("document.querySelector('#bFire')?.textContent.startsWith('DISPARAR') || document.querySelector('#bFire')?.textContent.includes('ELIGE')", timeout=6000)
        check("impacto directo: nunca pregunta SÍ/NO", not saw_question)
        pg.wait_for_selector(".sunk-in", state="detached", timeout=6000)
        left = pg.inner_text("#fleetLeft").replace("\n", " ")
        check("¡HUNDIDO!: quedan 3 embarcaciones y 1 submarino", pg.locator("#fleetLeft .pip.s.dead").count() == 1 and pg.locator("#fleetLeft .pip.e.dead").count() == 0, left)
        check("hundido: 4 casillas marcadas en el radar", pg.locator(".c.sunk").count() == 4, str(pg.locator(".c.sunk").count()))
        pg.evaluate("window.scrollTo(0,0)")
        pg.wait_for_timeout(200)
        pg.screenshot(path=out / "ciclo-09-radar-tras-hundir.png")

        # ---- persistencia: cerrar a mitad de veredicto
        aim(pg, 1, 1)
        pg.click("#bFire"); pg.wait_for_selector("#vYes", timeout=4000)
        pg.reload(); pg.wait_for_selector("#vYes", timeout=5000)
        check("recargar con veredicto pendiente lo reabre", pg.is_visible("#vNo") and pg.locator(".c.sunk, .c.miss").count() >= 5)
        pg.click("#vNo"); pg.wait_for_timeout(1800)
        check("tras responder vuelve a apuntar", pg.locator("#vYes").count() == 0)

        check("sin errores de consola", not ERRORS, "; ".join(ERRORS)[:300])
        br.close()
    bad = [r for r in RES if not r[1]]
    print(f"\n{len(RES) - len(bad)}/{len(RES)} comprobaciones OK")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
