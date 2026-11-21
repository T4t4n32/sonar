# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Prueba e2e de CALIBRAR APUNTADO (pestaña Enlace): láser, cruceta, 4 esquinas + control, CALCULAR, verificar, guardar, reiniciar.

Transporte SIMULADO con un gimbal virtual (montaje con desplazamiento y giro: sin calibrar el apuntado sale desviado).
375×812. Requiere `npx vite preview --port 4173` (o --url). La página se abre con ?e2e para exponer `window.__sonar`.
Capturas en registro/2026-11-21-calibracion/.
    uv run --script tools/e2e_calibrar.py --url http://localhost:4173/
"""
from __future__ import annotations

import argparse
import math
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
RES: list[tuple[str, bool, str]] = []
ERRORS: list[str] = []
STEPS = (5, 1, 0.2, 0.05)


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


def angles(pg) -> tuple[float, float]:
    return tuple(pg.evaluate("(()=>{const t=window.__sonar.transport;return [t.pan,t.tilt]})()"))  # type: ignore[return-value]


def truth(pg, x: int, y: int) -> tuple[float, float]:
    return tuple(pg.evaluate("c=>{const a=window.__sonar.transport.truth(c);return [a.pan,a.tilt]}", {"x": x, "y": y}))  # type: ignore[return-value]


def pointing(pg) -> tuple[float, float]:
    return tuple(pg.evaluate("(()=>{const p=window.__sonar.transport.pointing();return [p.x,p.y]})()"))  # type: ignore[return-value]


def idle(pg) -> None:
    pg.wait_for_function("window.__sonar.calib.working.value===0", timeout=8000)
    pg.wait_for_timeout(60)  # hueco entre dos JOG unidos


def drive(pg, target: tuple[float, float], tol: float = 0.12) -> int:
    """Lleva el láser a los ángulos `target` SOLO con la cruceta de la interfaz (paso grande → fino). Devuelve los clics."""
    clicks = 0
    for _ in range(80):
        pan, tilt = angles(pg)
        dp, dt = target[0] - pan, target[1] - tilt
        if abs(dp) < tol and abs(dt) < tol:
            return clicks
        for d, plus, minus in ((dp, "#jog-right", "#jog-left"), (dt, "#jog-down", "#jog-up")):  # ↓ sube el ángulo de tilt
            if abs(d) < tol:
                continue
            step = next(s for s in STEPS if s <= abs(d) + 1e-9)
            pg.click(f"#step-{str(step).replace('.', '_')}")
            pg.click(plus if d > 0 else minus)
            idle(pg)
            clicks += 1
    raise AssertionError(f"no llegó a {target}: está en {angles(pg)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:4173/")
    ap.add_argument("--out", default=str(REPO / "registro" / "2026-11-21-calibracion"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    url = a.url + ("&" if "?" in a.url else "?") + "e2e=1"
    with sync_playwright() as p:
        br = launch(p)
        ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, color_scheme="dark")
        ctx.add_init_script("try{localStorage.setItem('sonar.v1.introSeen','1')}catch(e){}")
        pg = ctx.new_page()
        pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type == "error" else None)
        pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
        pg.goto(url); pg.wait_for_selector("#tab-batalla")

        # ---- sin enlace no se muestra; con enlace aparece
        pg.click("#tab-enlace"); pg.wait_for_selector("[data-peer]")
        check("sin enlace no hay sección de calibración", pg.locator("#calib").count() == 0)
        pg.click("[data-peer]"); pg.wait_for_selector("#pill.on", timeout=5000)
        pg.wait_for_selector("#calib", timeout=4000)
        pg.wait_for_function("document.querySelector('#calAngles')?.textContent.includes('90.00')", timeout=5000)
        check("con enlace aparece «Calibrar apuntado» y lee 90.00 / 90.00", "90.00" in pg.inner_text("#calAngles"), pg.inner_text("#calAngles"))
        pg.wait_for_function("document.querySelector('#calMap')?.textContent.includes('fábrica')", timeout=5000)
        check("mapa de fábrica al inicio", "de fábrica" in pg.inner_text("#calMap"), pg.inner_text("#calMap"))
        check("sin aviso de firmware sin «grid»", pg.locator("#calNoGrid").count() == 0)

        # ---- layout y tamaños táctiles
        check("sin scroll horizontal a 375 px", pg.evaluate("document.documentElement.scrollWidth") <= 375, str(pg.evaluate("document.documentElement.scrollWidth")))
        small = [i for i in ("jog-up", "jog-down", "jog-left", "jog-right") if pg.locator(f"#{i}").bounding_box()["height"] < 56 or pg.locator(f"#{i}").bounding_box()["width"] < 56]
        check("cruceta con botones ≥ 56 px", not small, ", ".join(small))
        pg.locator("#calib").scroll_into_view_if_needed()
        pg.locator("#calib").screenshot(path=out / "cal-01-inicio.png")

        # ---- pasos e inversiones
        pg.click("#step-0_05")
        check("selector de paso (0,05°)", pg.get_attribute("#step-0_05", "aria-pressed") == "true" and pg.get_attribute("#step-1", "aria-pressed") == "false")
        pg.click("#inv-h"); pg.click("#inv-v")
        pan0, tilt0 = angles(pg)
        pg.click("#jog-right"); idle(pg)
        check("invertir ← →: «→» baja el pan", angles(pg)[0] < pan0, f"{pan0:.2f} → {angles(pg)[0]:.2f}")
        pg.click("#jog-up"); idle(pg)
        check("invertir ↑ ↓: «↑» sube el ángulo de tilt", angles(pg)[1] > tilt0, f"{tilt0:.2f} → {angles(pg)[1]:.2f}")
        pg.click("#inv-h"); pg.click("#inv-v")
        pg.click("#calCenter"); idle(pg)
        check("botón 90° centra los servos", angles(pg) == (90.0, 90.0), str(angles(pg)))

        # ---- mantener pulsado repite
        pg.click("#step-0_2")
        pan0 = angles(pg)[0]
        bb = pg.locator("#jog-right").bounding_box()
        pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        pg.mouse.down(); pg.wait_for_timeout(1100); pg.mouse.up(); idle(pg)
        moved = angles(pg)[0] - pan0
        check("mantener pulsado repite (≥ 3 pasos de 0,2°, sin ráfaga perdida)", moved >= 0.55, f"{moved:.2f}°")
        pg.click("#calCenter"); idle(pg)

        # ---- láser
        pg.click("#calLaser"); pg.wait_for_function("document.querySelector('#calLaser')?.textContent.includes('ENCENDIDO')", timeout=4000)
        check("láser encendido con cuenta atrás de 2:00", "2:00" in pg.inner_text("#calLaser") or "1:59" in pg.inner_text("#calLaser"), pg.inner_text("#calLaser"))
        check("el módulo simulado tiene el láser encendido", pg.evaluate("window.__sonar.transport.laserOn") is True)

        # ---- esquinas
        names = {1: (1, 1), 2: (20, 1), 3: (20, 20), 4: (1, 20)}
        check("CALCULAR deshabilitado sin esquinas", pg.is_disabled("#calFit"))
        total = 0
        for n, (x, y) in names.items():
            total += drive(pg, truth(pg, x, y))
            pg.click(f"#corner-{n}"); pg.wait_for_function(f"document.querySelector('#cmark-{n}')?.textContent==='✓'", timeout=4000)
            if n == 1:
                pg.locator("#calib").screenshot(path=out / "cal-02-esquina-1.png")
        check(f"4 esquinas registradas solo con la cruceta ({total} toques)", all(pg.inner_text(f"#cmark-{n}") == "✓" for n in names))
        check("CALCULAR habilitado con las 4 esquinas", not pg.is_disabled("#calFit"))
        check("GUARDAR deshabilitado hasta calcular", pg.is_disabled("#calSave"))
        total = drive(pg, truth(pg, 11, 11))
        pg.click("#corner-5"); pg.wait_for_function("document.querySelector('#cmark-5')?.textContent==='✓'", timeout=4000)
        check("punto de control (11,11) registrado", True, f"{total} toques")
        pg.locator("#calib").screenshot(path=out / "cal-03-esquinas.png")

        # ---- calcular
        pg.click("#calFit"); pg.wait_for_function("document.querySelector('#calFitRes')?.textContent.includes('error del control')", timeout=5000)
        res = pg.inner_text("#calFitRes")
        err = float(res.split(":")[-1].replace("°", "").strip())
        check("CALCULAR muestra el error del control (< 0,3°)", err < 0.3, res)
        check("mapa calculado", "calculado" in pg.inner_text("#calMap") and "fábrica" not in pg.inner_text("#calMap"), pg.inner_text("#calMap"))
        check("GUARDAR habilitado tras calcular", not pg.is_disabled("#calSave"))
        pg.locator("#calib").screenshot(path=out / "cal-04-calculado.png")

        # ---- verificar tocando celdas: el láser cae en la casilla
        pg.evaluate("document.querySelector('#calBoard').scrollIntoView({block:'center'})")  # la barra de pestañas tapa el borde inferior
        pg.wait_for_timeout(200)
        bb = pg.locator("#calBoard").bounding_box()
        cw = bb["width"] / 20
        worst = 0.0
        for (x, y) in ((14, 6), (3, 17), (20, 20), (1, 1)):
            pg.mouse.click(bb["x"] + (x - 0.5) * cw, bb["y"] + (20 - y + 0.5) * cw)   # y = 1 es la fila de abajo
            try:
                pg.wait_for_function(f"window.__sonar.calib.verified.value && window.__sonar.calib.verified.value.x=={x} && window.__sonar.calib.verified.value.y=={y}", timeout=6000)
            except Exception:
                print("DEBUG", pg.evaluate("JSON.stringify({m: window.__sonar.calib.msg.value, v: window.__sonar.calib.verified.value, w: window.__sonar.calib.working.value, l: window.__sonar.calib.laserOn.value, ang: [window.__sonar.transport.pan, window.__sonar.transport.tilt]})"), bb)
                raise
            idle(pg)
            px, py = pointing(pg)
            worst = max(worst, math.hypot(px - x, py - y))
            sel = pg.evaluate("[...document.querySelectorAll('#calBoard .c')].findIndex(e=>e.classList.contains('sel'))")
            if sel != (20 - y) * 20 + (x - 1):
                worst = 99
        check("verificar: el láser cae en la celda tocada (error < 0,3 celdas) y se marca en el tablero", worst < 0.3, f"peor {worst:.3f} celdas")
        pg.mouse.click(bb["x"] + 13.5 * cw, bb["y"] + (20 - 6 + 0.5) * cw)
        pg.wait_for_function("window.__sonar.calib.verified.value?.x===14", timeout=6000); idle(pg)
        pg.locator("#calib").screenshot(path=out / "cal-05-verificar.png")

        # ---- guardar
        pg.click("#calSave"); pg.wait_for_function("document.querySelector('#calibMsg')?.textContent.includes('guardado')", timeout=4000)
        check("GUARDAR persiste el mapa en el módulo", pg.evaluate("!!window.__sonar.transport.saved.fit"), pg.inner_text("#calibMsg"))
        pg.locator("#calib").screenshot(path=out / "cal-06-guardado.png")

        # ---- STOP apaga el láser
        check("láser aún encendido antes del STOP", "ENCENDIDO" in pg.inner_text("#calLaser"))
        pg.click("#calStop"); pg.wait_for_function("document.querySelector('#calLaser')?.textContent.includes('ENCENDER')", timeout=4000)
        check("STOP apaga el láser (app y módulo)", pg.evaluate("window.__sonar.transport.laserOn") is False)

        # ---- disparar desde Batalla sigue funcionando con el mapa
        pg.click("#tab-batalla"); pg.wait_for_selector("#bFire")
        pg.click("#val-x"); pg.get_by_role("button", name="9", exact=True).click()
        pg.click("#val-y"); pg.get_by_role("button", name="9", exact=True).click()
        pg.click("#bFire"); pg.wait_for_selector("#vYes", timeout=5000)
        px, py = pointing(pg)
        check("un DISPARAR normal cae en la celda con el mapa calibrado", math.hypot(px - 9, py - 9) < 0.3, f"({px:.2f},{py:.2f})")
        pg.click("#vNo"); pg.wait_for_timeout(1800)

        # ---- reiniciar el mapa
        pg.click("#tab-enlace"); pg.wait_for_selector("#calReset")
        pg.click("#calReset"); pg.wait_for_function("document.querySelector('#calibMsg')?.textContent.includes('Mapa borrado')", timeout=5000)
        check("REINICIAR MAPA borra las esquinas y vuelve a fábrica", all(pg.inner_text(f"#cmark-{n}") in ("·", "○") for n in range(1, 6)) and "fábrica" in pg.inner_text("#calMap"))
        check("GUARDAR vuelve a estar deshabilitado", pg.is_disabled("#calSave"))
        pg.locator("#calib").screenshot(path=out / "cal-07-reiniciado.png")

        check("sin scroll horizontal tras el flujo", pg.evaluate("document.documentElement.scrollWidth") <= 375)
        check("sin errores de consola", not ERRORS, "; ".join(ERRORS)[:300])
        br.close()
    bad = [r for r in RES if not r[1]]
    print(f"\n{len(RES) - len(bad)}/{len(RES)} comprobaciones OK")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
