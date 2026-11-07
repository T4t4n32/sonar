# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Prueba de punta a punta de la web SONAR contra el módulo simulado (sin hardware).

Levanta `fake_device.py`, abre `web/index.html` en Chromium (celular 375×812 y escritorio 1280×800), recorre cada estado,
mide y guarda capturas + resumen en `registro/<fecha>/`. Sale con código 1 si algo falla.

    uv run --script tools/e2e_web.py                 # registro/<hoy>/
    uv run --script tools/e2e_web.py --out registro/prueba
(la primera vez: `uvx playwright install chromium`, solo si no hay navegador instalado)
"""
from __future__ import annotations

import argparse
import datetime
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
RES: list[tuple[str, bool, str]] = []
ERRORS: list[str] = []


def check(nombre: str, ok: bool, detalle: str = "") -> None:
    RES.append((nombre, bool(ok), detalle))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""), flush=True)


def libre() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def celda(page, x: int, y: int) -> tuple[float, float]:
    b = page.locator("#bw").bounding_box()
    return b["x"] + (x - .5) / 20 * b["width"], b["y"] + (y - .5) / 20 * b["height"]


def tocar(page, x: int, y: int, touch: bool) -> None:
    px, py = celda(page, x, y)
    (page.touchscreen.tap if touch else page.mouse.click)(px, py)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    out = (a.out or REPO / "registro" / datetime.date.today().isoformat())
    out = out if out.is_absolute() else REPO / out
    out.mkdir(parents=True, exist_ok=True)
    port = libre()
    srv = subprocess.Popen([sys.executable, str(REPO / "tools" / "fake_device.py"), "--port", str(port), "--speed", "2"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO)
    url = f"http://127.0.0.1:{port}/"
    try:
        for _ in range(50):
            try: socket.create_connection(("127.0.0.1", port), 0.2).close(); break
            except OSError: time.sleep(0.1)
        size = (REPO / "web" / "index.html").stat().st_size
        check("peso del archivo ≤ 60 KB (va embebido en el ESP32)", size <= 60 * 1024, f"{size / 1024:.1f} KB")
        with sync_playwright() as p:
            br = p.chromium.launch()
            # ---------------- celular ----------------
            ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, has_touch=True, is_mobile=True, color_scheme="dark")
            pg = ctx.new_page()
            pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
            pg.goto(url); pg.wait_for_selector("#pill.on", timeout=8000)
            check("conecta con el módulo y muestra su nombre", "DUELO-FAKE" in pg.inner_text("#ptxt"), pg.inner_text("#ptxt"))
            check("DISPARAR empieza deshabilitado sin objetivo", pg.is_disabled("#bFire"))
            pg.screenshot(path=out / "movil-01-inicio.png")
            tocar(pg, 13, 7, True); pg.wait_for_timeout(450)
            check("1 toque fija el objetivo (13,7)", "(13, 7)" in pg.inner_text("#coord"), pg.inner_text("#coord").split("\n")[0])
            fb = pg.locator("#bFire").bounding_box()
            check("DISPARAR visible sin desplazar (dock fijo)", fb is not None and fb["y"] + fb["height"] <= 812, f"y={fb['y']:.0f}")
            pg.screenshot(path=out / "movil-02-objetivo.png")
            pg.tap("#bFire"); pg.wait_for_timeout(350)
            check("el rayo se dibuja durante el disparo", "on" in (pg.get_attribute("#beam", "class") or ""))
            pg.screenshot(path=out / "movil-03-disparando.png")
            pg.wait_for_selector("#shot.ok", timeout=15000); pg.wait_for_timeout(250)
            check("disparo completado: 2 toques en total (celda + DISPARAR)", True)
            check("la celda queda marcada como disparada", pg.locator(".c.shot").count() == 1)
            check("TOCADO/AGUA se habilitan tras el disparo", not pg.is_disabled("#bHit") and not pg.is_disabled("#bMiss"))
            pg.screenshot(path=out / "movil-04-disparo-completado.png")
            pg.tap("#bHit"); pg.wait_for_selector("#shot:has-text('Tocado')", timeout=8000); pg.wait_for_timeout(300)
            check("marcar TOCADO cambia la celda", pg.locator(".c.hit").count() == 1)
            pg.screenshot(path=out / "movil-05-tocado.png")
            # TEST
            pg.evaluate("document.getElementById('bTest').scrollIntoView({block:'center'})")
            pg.tap("#bTest"); pg.wait_for_timeout(500)
            check("TEST: los 5 objetivos pulsan «en curso»", pg.locator(".step.run").count() == 5)
            pg.screenshot(path=out / "movil-06-test-en-curso.png")
            pg.wait_for_function("document.getElementById('tmsg').textContent.includes('superada')", timeout=60000)
            check("TEST: 5 de 5 posiciones confirmadas", pg.locator(".step.ok").count() == 5)
            pg.screenshot(path=out / "movil-07-test-5de5.png")
            # calibración
            pg.evaluate("document.querySelector('#cal summary').scrollIntoView()"); pg.click("#cal summary")
            pg.fill("#k3", "50"); pg.click("#bCalSet")
            check("calibración: valor fuera de rango se rechaza en la página", "bad" in (pg.get_attribute("#k3", "class") or ""))
            pg.fill("#k3", "1.5"); pg.click("#bCalSet"); pg.wait_for_timeout(500)
            pg.click("#bCalShow"); pg.wait_for_timeout(500)
            check("calibración: APLICAR y LEER devuelven el valor", pg.input_value("#k3") in ("1.50", "1.5"), pg.input_value("#k3"))
            pg.screenshot(path=out / "movil-08-calibracion.png")
            pg.click("#logbox summary")
            with pg.expect_download() as d:
                pg.click("#bExport")
            d.value.save_as(out / "bitacora-ejemplo.txt")
            check("la bitácora se descarga como .txt", (out / "bitacora-ejemplo.txt").stat().st_size > 50)
            pg.screenshot(path=out / "movil-09-bitacora.png", full_page=True)
            # desbordes
            for w in (320, 375, 414, 768):
                pg.set_viewport_size({"width": w, "height": 800}); pg.wait_for_timeout(150)
                ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                check(f"sin desplazamiento horizontal a {w} px", ov <= 1, f"{ov}px")
            pg.set_viewport_size({"width": 375, "height": 812})
            # tema claro
            pg.click("#bTheme"); pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(250)
            check("existe tema claro (Carta náutica) y se activa con el botón", pg.evaluate("document.documentElement.dataset.theme") == "light")
            pg.screenshot(path=out / "movil-10-tema-claro.png")
            ctx.close()
            # ---------------- sin enlace ----------------
            ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, has_touch=True, is_mobile=True, color_scheme="dark")
            pg = ctx.new_page(); pg.route("**/cmd*", lambda r: r.abort())
            pg.goto(url); pg.wait_for_selector("#pill.off", timeout=8000); pg.wait_for_timeout(300)
            check("sin enlace: muestra instrucciones y reintentar", pg.is_visible("#veil") and "DUELO-A-MANT" in pg.inner_text("#veil"))
            check("sin enlace: DISPARAR deshabilitado", pg.is_disabled("#bFire"))
            pg.screenshot(path=out / "movil-11-sin-enlace.png")
            ctx.close()
            # ---------------- modo simulado (sin módulo) ----------------
            ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, has_touch=True, is_mobile=True, color_scheme="dark")
            pg = ctx.new_page(); pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
            pg.route("**/cmd*", lambda r: r.abort())  # demuestra que no usa el módulo
            pg.goto(url + "?demo=1"); pg.wait_for_selector("#pill.on", timeout=8000)
            check("modo simulado: insignia visible y sin red", "Simulado" in pg.inner_text("#ptxt") and "SIMULADO" in pg.inner_text("#bDemo").upper())
            tocar(pg, 5, 15, True); pg.tap("#bFire"); pg.wait_for_selector("#shot.ok", timeout=15000)
            check("modo simulado: dispara y responde OK", pg.locator(".c.shot").count() == 1)
            pg.screenshot(path=out / "movil-12-simulado.png")
            ctx.close()
            # ---------------- escritorio + teclado ----------------
            ctx = br.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1, color_scheme="dark")
            pg = ctx.new_page(); pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
            pg.goto(url); pg.wait_for_selector("#pill.on", timeout=8000)
            pg.focus("#bw")
            for k in ("ArrowRight", "ArrowDown", "ArrowDown"):
                pg.keyboard.press(k)
            check("teclado: flechas mueven el objetivo", "(11, 13)" in pg.inner_text("#coord"), pg.inner_text("#coord").split("\n")[0])
            pg.keyboard.press("Enter"); pg.wait_for_selector("#shot.ok", timeout=15000)
            check("teclado: Intro dispara", pg.locator(".c.shot").count() == 1)
            tocar(pg, 18, 4, False); pg.mouse.move(*celda(pg, 18, 4)); pg.wait_for_timeout(450)
            pg.screenshot(path=out / "escritorio-01.png")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
            check("teclado: Esc envía STOP", "STOP" in (pg.text_content("#log") or ""))
            pg.click("#bTheme"); pg.wait_for_timeout(250); pg.screenshot(path=out / "escritorio-02-claro.png")
            names = pg.evaluate("[...document.querySelectorAll('button')].filter(b=>!(b.textContent||'').trim() && !b.getAttribute('aria-label')).length")
            check("todos los botones tienen nombre accesible", names == 0, f"{names} sin nombre")
            ctx.close(); br.close()
        check("consola sin errores ni avisos", not ERRORS, "; ".join(ERRORS[:3]))
    finally:
        srv.terminate()
    ok = all(r[1] for r in RES)
    md = ["# Registro de pruebas — web SONAR", "", f"Fecha: {datetime.datetime.now():%Y-%m-%d %H:%M} · `tools/e2e_web.py` contra `tools/fake_device.py` (simulado, **sin hardware**).", "",
          f"**Resultado: {sum(r[1] for r in RES)}/{len(RES)} pruebas correctas.**", "", "| prueba | estado | detalle |", "|---|---|---|"]
    md += [f"| {n} | {'PASS' if k else '**FAIL**'} | {d} |" for n, k, d in RES]
    md += ["", "## Capturas", ""] + [f"- `{f.name}`" for f in sorted(out.glob("*.png"))]
    (out / "RESUMEN.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n{'TODO OK' if ok else 'HAY FALLOS'} — {sum(r[1] for r in RES)}/{len(RES)} · registro en {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
