# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Prueba e2e de la app SONAR contra el transporte SIMULADO (sin hardware).

Requiere `npx vite preview --port 4173` (o --url). Capturas en registro/2026-11-15-app/.
    uv run --script tools/e2e_app.py
"""
from __future__ import annotations

import argparse
import re
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


def press(pg, sel: str) -> None:
    """Baja el ratón en el centro del elemento (centrado en pantalla, lejos de la barra de pestañas)."""
    pg.evaluate("s => document.querySelector(s).scrollIntoView({block: 'center'})", sel)
    pg.wait_for_timeout(120)
    b = pg.locator(sel).bounding_box()
    pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.mouse.down()


def hold(pg, sel: str, ms: int) -> None:
    press(pg, sel)
    pg.wait_for_timeout(ms)
    pg.mouse.up()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:4173/")
    ap.add_argument("--out", default=str(REPO / "registro" / "2026-11-15-app"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        # Si la versión de Playwright no coincide con el Chromium instalado, usa cualquier headless-shell ya descargado.
        try:
            br = p.chromium.launch()
        except Exception:
            import glob, os
            cands = sorted(glob.glob(os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), "chromium_headless_shell-*", "*", "chrome-headless-shell.exe")))
            if not cands:
                raise
            br = p.chromium.launch(executable_path=cands[-1])
        ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, color_scheme="dark")
        ctx.add_init_script("try{localStorage.setItem('sonar.v1.introSeen','1')}catch(e){}")
        pg = ctx.new_page()
        pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type in ("error",) else None)
        pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
        pg.goto(a.url); pg.wait_for_selector("#tab-batalla")
        check("DISPARAR deshabilitado sin enlace", pg.is_disabled("#bFire"))
        pg.screenshot(path=out / "01-batalla-sin-enlace.png")

        # ---- enlace + TEST
        pg.click("#tab-enlace"); pg.wait_for_selector("[data-peer]")
        pg.click("[data-peer]"); pg.wait_for_selector("#pill.on", timeout=5000)
        pg.wait_for_selector("#helloName")
        check("HELLO muestra el nombre del módulo", "SONAR" in pg.inner_text("#helloName"), pg.inner_text("#helloName"))
        pg.click("#bTest"); pg.wait_for_timeout(500)
        check("TEST en curso muestra pasos animados", pg.locator(".step.run").count() > 0)
        pg.wait_for_selector(".result.ok", timeout=15000)
        check("TEST APROBADO con 5 pasos ✓", pg.locator(".step.ok").count() == 5)
        pg.screenshot(path=out / "02-enlace-test-aprobado.png")

        # ---- disparar (3,4): arranca el ciclo (el detalle del ciclo lo cubre tools/e2e_ciclo.py)
        pg.click("#tab-batalla")
        pg.get_by_role("button", name="3", exact=True).click()   # x -> avanza a y
        pg.get_by_role("button", name="4", exact=True).click()
        check("teclado: objetivo (3,4)", pg.inner_text("#val-x").endswith("3") and pg.inner_text("#val-y").endswith("4"), pg.inner_text("#val-x") + "|" + pg.inner_text("#val-y"))
        check("botón dice DISPARAR (3,4)", "DISPARAR (3,4)" in pg.inner_text("#bFire"))
        fb = pg.locator("#bFire").bounding_box()
        check("DISPARAR visible sin desplazar", fb["y"] + fb["height"] <= 812, f"y={fb['y']:.0f}")
        pg.click("#bFire"); pg.wait_for_timeout(300)
        check("no permite doble disparo (botón deshabilitado)", pg.is_disabled("#bFire"))
        pg.screenshot(path=out / "03-batalla-disparando.png")
        pg.wait_for_selector("#vYes", timeout=5000)
        check("el ciclo pide el veredicto (SÍ / NO)", pg.is_visible("#vYes") and pg.is_visible("#vNo"))
        pg.click("#vNo"); pg.wait_for_function("document.querySelector('#bFire')?.textContent.startsWith('DISPARAR')", timeout=6000)
        check("el radar marca la celda (agua)", pg.locator(".c.miss").count() == 1)
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
        pg.screenshot(path=out / "04-batalla-disparo-resuelto.png")

        # ---- Mi flota: ocultar por defecto, editar con pulsación larga, coordenadas
        pg.click("#tab-flota")
        check("flota oculta por defecto", pg.locator(".c.ship, .c.shipsel").count() == 0 and "FLOTA OCULTA" in pg.inner_text("body"))
        hold(pg, "#bEdit", 1000)
        pg.wait_for_selector("#bRandom")
        pg.click("#bRandom")
        check("aleatoria: flota válida", "Flota válida" in pg.inner_text("#validation"), pg.inner_text("#validation")[:60])
        check("editor muestra 14 casillas de barco", pg.locator(".c.ship, .c.shipsel").count() == 14, str(pg.locator(".c.ship, .c.shipsel").count()))
        check("lista de coordenadas con Submarino 1", "Submarino 1" in pg.inner_text("#coords"))
        pg.click("#bDone")
        check("al terminar, la flota vuelve a ocultarse", pg.locator(".c.ship, .c.shipsel").count() == 0)
        press(pg, "#bSeeFleet"); pg.wait_for_timeout(250)
        check("mantener «Ver flota» revela 14 casillas", pg.locator(".c.ship, .c.shipsel").count() == 14)
        pg.screenshot(path=out / "06-flota-ver.png")
        pg.mouse.up(); pg.wait_for_timeout(200)
        check("al soltar, la flota se oculta", pg.locator(".c.ship, .c.shipsel").count() == 0)
        pg.click("#tab-batalla"); pg.wait_for_timeout(200)
        check("de vuelta en Batalla", pg.locator("#bFire").count() == 1)

        # ---- layout
        for w in (360, 375, 412):
            pg.set_viewport_size({"width": w, "height": 812})
            for t in ("batalla", "flota", "enlace", "partida"):
                pg.click(f"#tab-{t}"); pg.wait_for_timeout(150)
                sw = pg.evaluate("document.documentElement.scrollWidth")
                check(f"sin scroll horizontal {w}px · {t}", sw <= w, f"scrollWidth={sw}")
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.click("#tab-partida"); pg.wait_for_timeout(200)
        pg.screenshot(path=out / "07-partida.png", full_page=False)
        pg.click("#tab-batalla")
        # objetivos táctiles >= 48 px
        small = pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => { const r=b.getBoundingClientRect(); return r.width>0 && (r.height<44) }).map(b => (b.id||b.textContent).slice(0,20)+':'+Math.round(b.getBoundingClientRect().height))""")
        check("botones de Batalla ≥ 44 px de alto", len(small) == 0, ",".join(small))
        check("sin errores de consola", not ERRORS, "; ".join(ERRORS[:3]))
        br.close()
    bad = [r for r in RES if not r[1]]
    print(f"\n{len(RES) - len(bad)}/{len(RES)} comprobaciones OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
