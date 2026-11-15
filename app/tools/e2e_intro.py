# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Prueba e2e del splash y el tutorial animado de SONAR (375×812, sin hardware).

Requiere `npx vite preview --port 4173` (o --url). Capturas en registro/2026-11-15-app/intro-*.png.
    uv run --script tools/e2e_intro.py
Usa `?introSpeed=N` (acelera el tiempo N veces) para recorrer las 16 escenas en pocos segundos.
"""
from __future__ import annotations

import argparse
import sys
import time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
RES: list[tuple[str, bool, str]] = []
ERRORS: list[str] = []
# duración (ms) de cada escena, igual que guion.ts
DUR = {"flota": 8000, "bluetooth": 6000, "test": 6000, "coordenada": 6000, "laser": 5000, "ledio": 4500, "noledio": 4500,
       "ubicar": 6000, "victoria": 5000, "enlace": 6000, "enlace-test": 6000, "batalla": 7000, "veredicto": 6000,
       "ubicar-ui": 6000, "flota-ui": 6000, "partida": 6500}


def check(nombre: str, ok: bool, detalle: str = "") -> None:
    RES.append((nombre, bool(ok), detalle))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""), flush=True)


def scene(pg) -> str:
    return pg.get_attribute("#intro", "data-scene") or ""


def goto_scene(pg, sid: str) -> None:
    """Va a la escena `sid` con Siguiente/Atrás (la reproducción sigue sola, así que se recalcula cada vez)."""
    order = list(DUR)
    for _ in range(40):
        cur = scene(pg)
        if cur == sid:
            return
        if cur not in order:
            pg.wait_for_timeout(40); continue
        btn = "#introNext" if order.index(cur) < order.index(sid) else "#introPrev"
        if btn == "#introNext" and not pg.locator("#introNext").count():
            raise AssertionError(f"sin Siguiente buscando {sid}; escena actual {cur}")
        pg.click(btn)
        pg.wait_for_timeout(60)
    raise AssertionError(f"no llegó a la escena {sid}")


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        import glob, os
        cands = sorted(glob.glob(os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), "chromium_headless_shell-*", "*", "chrome-headless-shell.exe")))
        if not cands:
            raise
        return p.chromium.launch(executable_path=cands[-1])


def newpage(br, **kw):
    ctx = br.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, color_scheme="dark", **kw)
    pg = ctx.new_page()
    pg.on("console", lambda m: ERRORS.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: ERRORS.append(f"pageerror: {e}"))
    return ctx, pg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:4173/")
    ap.add_argument("--out", default=str(REPO / "registro" / "2026-11-15-app"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = launch(p)

        # ---------- 1. splash + Acto 1 a velocidad real (x2.5 solo para las capturas) ----------
        ctx, pg = newpage(br)
        pg.goto(a.url, wait_until="commit")
        pg.wait_for_selector("#splash", state="attached", timeout=4000)
        check("splash presente en el primer pintado", True)
        pg.wait_for_timeout(700)
        pg.screenshot(path=out / "intro-01-splash.png")
        pg.wait_for_selector("#intro", timeout=8000)
        check("el splash se retira solo", pg.locator("#splash").count() == 0)
        check("arranca el Acto 1 en «La flota»", scene(pg) == "flota" and "ACTO 1" in pg.inner_text(".ibrand b"), scene(pg))
        check("16 puntos de progreso (9 + 7)", pg.locator(".dots i").count() == 16, str(pg.locator(".dots i").count()))
        check("«Saltar» visible", pg.is_visible("#introSkip"))
        check("subtítulo en español", "20×20" in pg.inner_text(".cap"), pg.inner_text(".cap"))

        # pausa por toque largo y reanudar con el botón
        st = pg.locator(".stagei").bounding_box()
        cx, cy = st["x"] + st["width"] / 2, st["y"] + st["height"] / 2
        pg.mouse.move(cx, cy); pg.mouse.down(); pg.wait_for_timeout(750); pg.mouse.up()
        pg.wait_for_timeout(100)
        check("toque largo pausa (EN PAUSA)", pg.is_visible(".pbadge") and "paused" in (pg.get_attribute("#intro", "class") or ""))
        pg.click("#introPause"); pg.wait_for_timeout(100)
        check("botón Continuar reanuda", not pg.is_visible(".pbadge"))
        # deslizar a la izquierda = siguiente; derecha = anterior
        pg.mouse.move(cx + 90, cy); pg.mouse.down(); pg.mouse.move(cx - 90, cy, steps=6); pg.mouse.up(); pg.wait_for_timeout(150)
        check("deslizar izquierda -> siguiente escena", scene(pg) == "bluetooth", scene(pg))
        pg.mouse.move(cx - 90, cy); pg.mouse.down(); pg.mouse.move(cx + 90, cy, steps=6); pg.mouse.up(); pg.wait_for_timeout(150)
        check("deslizar derecha -> escena anterior", scene(pg) == "flota", scene(pg))
        pg.click("#introNext"); pg.wait_for_timeout(100)
        check("Siguiente avanza", scene(pg) == "bluetooth")
        pg.click("#introPrev"); pg.wait_for_timeout(100)
        check("Atrás retrocede", scene(pg) == "flota")
        pg.goto(a.url + "?introSpeed=2.5")  # reinicio solo para acelerar las capturas (introSeen aún sin marcar)
        pg.wait_for_selector("#intro", timeout=8000)

        shots = [("flota", .92, "02-flota"), ("bluetooth", .8, "03-bluetooth"), ("coordenada", .85, "04-coordenada"), ("laser", .8, "05-laser"),
                 ("ledio", .78, "06-explosion"), ("noledio", .85, "07-gota"), ("ubicar", .85, "08-ubicar"), ("victoria", .9, "09-victoria"),
                 ("enlace", .85, "10-ui-enlace"), ("batalla", .9, "11-ui-batalla"), ("veredicto", .45, "12-ui-pausa"), ("flota-ui", .8, "13-ui-flota")]
        for sid, frac, name in shots:
            goto_scene(pg, sid)
            pg.wait_for_timeout(int(DUR[sid] * frac / 2.5))
            pg.click("#introPause"); pg.wait_for_timeout(120)
            pg.screenshot(path=out / f"intro-{name}.png")
            pg.click("#introPause"); pg.wait_for_timeout(50)
        ctx.close()

        # ---------- 2. recorrido completo acelerado x20 + «Empezar» + no repite ----------
        ctx, pg = newpage(br)
        pg.goto(a.url + "?introSpeed=20")
        pg.wait_for_selector("#intro", timeout=8000)
        seen: list[str] = []
        t0 = time.time()
        while time.time() - t0 < 20:
            s = scene(pg)
            if s and (not seen or seen[-1] != s):
                seen.append(s)
            if pg.locator("#introGo").count():
                break
            pg.wait_for_timeout(30)
        check("recorre las 16 escenas encadenadas", len(seen) >= 14 and "ledio" in seen and "noledio" in seen and "victoria" in seen and seen[-1] == "partida", ",".join(seen))
        check("pasa del Acto 1 al Acto 2 solo", "enlace" in seen and seen.index("enlace") > seen.index("victoria"))
        pg.wait_for_selector("#introGo", timeout=5000)
        check("al final aparece «Empezar»", "Empezar" in pg.inner_text("#introGo"))
        pg.click("#introGo"); pg.wait_for_timeout(200)
        check("«Empezar» cierra el tutorial", pg.locator("#intro").count() == 0 and pg.is_visible("#tab-batalla"))
        check("introSeen marcado", pg.evaluate("localStorage.getItem('sonar.v1.introSeen')") == "1")
        pg.reload(); pg.wait_for_selector("#tab-batalla")
        pg.wait_for_timeout(1500)
        check("al recargar NO vuelve el tutorial", pg.locator("#intro").count() == 0)
        check("el splash sí se muestra y se retira en cada arranque", pg.locator("#splash").count() == 0)

        # ---------- 3. «Ver tutorial» en Partida ----------
        pg.click("#tab-partida"); pg.wait_for_selector("#bTutorial")
        pg.get_by_role("button", name="Acto 2", exact=True).click()
        pg.click("#bTutorial"); pg.wait_for_selector("#intro")
        check("«Ver tutorial» (Acto 2) abre en «Enlace»", scene(pg) == "enlace" and "ACTO 2" in pg.inner_text(".ibrand b"), scene(pg))
        pg.click("#introSkip"); pg.wait_for_timeout(200)
        check("«Saltar» cierra y vuelve a Partida", pg.locator("#intro").count() == 0 and pg.is_visible("#bTutorial"))
        pg.get_by_role("button", name="Acto 1", exact=True).click()
        pg.click("#bTutorial"); pg.wait_for_selector("#intro")
        check("«Ver tutorial» (Acto 1) abre en «La flota»", scene(pg) == "flota")
        check("Acto 1 solo: 9 puntos", pg.locator(".dots i").count() == 9)
        pg.click("#introSkip")
        pg.get_by_role("button", name="Todo", exact=True).click()
        pg.click("#bTutorial"); pg.wait_for_selector("#intro")
        check("«Ver tutorial» (Todo) abre en «La flota» con 16 puntos", scene(pg) == "flota" and pg.locator(".dots i").count() == 16)
        pg.click("#introSkip")
        pg.screenshot(path=out / "intro-14-partida-ver-tutorial.png")
        ctx.close()

        # ---------- 4. sin scroll horizontal a 360/375/412 ----------
        for w in (360, 375, 412):
            ctx, pg = newpage(br)
            pg.set_viewport_size({"width": w, "height": 780})
            pg.goto(a.url + "?introSpeed=1")
            pg.wait_for_selector("#intro", timeout=8000)
            bad = []
            for sid in ("flota", "bluetooth", "coordenada", "enlace", "batalla", "flota-ui", "partida"):
                goto_scene(pg, sid); pg.wait_for_timeout(150)
                sw = pg.evaluate("document.documentElement.scrollWidth"); bw = pg.evaluate("document.body.scrollWidth")
                if max(sw, bw) > w:
                    bad.append(f"{sid}:{max(sw, bw)}")
                ov = pg.evaluate("() => { const r = document.querySelector('#intro').getBoundingClientRect(); return [r.width, [...document.querySelectorAll('#intro *')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && (b.right > innerWidth + 1 || b.left < -1) && !e.closest('svg') }).length] }")
                if ov[1]:
                    bad.append(f"{sid}:desborda{ov[1]}")
            check(f"sin scroll/desborde horizontal a {w}px", not bad, ",".join(bad))
            ctx.close()

        # ---------- 5. movimiento reducido ----------
        ctx, pg = newpage(br, reduced_motion="reduce")
        pg.goto(a.url + "?introSpeed=4")
        pg.wait_for_selector("#intro", timeout=8000)
        goto_scene(pg, "ledio"); pg.wait_for_timeout(300)
        anim = pg.evaluate("[...document.querySelectorAll('#intro .scene .an')].filter(e => getComputedStyle(e).animationName !== 'none').length")
        check("reduced-motion: escenas sin animaciones de movimiento", anim == 0, str(anim))
        check("reduced-motion: los subtítulos siguen avanzando", pg.inner_text(".cap").strip() != "")
        pg.screenshot(path=out / "intro-15-reduced-motion.png")
        ctx.close()

        br.close()
    errs = [e for e in ERRORS if "favicon" not in e]
    check("sin errores de consola", not errs, "; ".join(errs[:3]))
    fails = [r for r in RES if not r[1]]
    print(f"\n{len(RES) - len(fails)}/{len(RES)} comprobaciones OK")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
