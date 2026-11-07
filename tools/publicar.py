# /// script
# requires-python = ">=3.10"
# ///
"""Publica el repositorio SONAR (lo pasa de privado a público) cuando toca y solo si es seguro.

Pensado para correr programado el 2026-11-24 (día de la entrega). Guardas, en orden:
  1. Fecha y hora: no antes del 2026-11-24 17:00 hora local (después de la entrega). `--ahora` salta SOLO esta guarda (uso manual).
  2. `gh` autenticado y el repositorio existe.
  3. `tools/preflight_publicar.py` sin hallazgos ALTA (árbol de trabajo + historial completo).
  4. Árbol de trabajo limpio respecto de origin/main (lo que se publica es lo que está subido).
Si alguna falla, NO publica y deja el motivo en registro/publicacion-<fecha>.md. Con `--dry-run` no cambia nada.

    uv run --script tools/publicar.py --dry-run
    uv run --script tools/publicar.py --ahora        # manual, con las demás guardas
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLUG = "T4t4n32/sonar"
NO_ANTES_DE = datetime.datetime(2026, 11, 24, 17, 0)
DESCRIPCION = "SONAR · Batalla Naval: ESP32 + torreta pan-tilt con láser, control por Bluetooth y Wi-Fi, firmware, interfaz web y simulador."
TEMAS = ["esp32", "platformio", "arduino", "bluetooth", "mecatronica", "laser", "capacitor"]


def sh(*cmd: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ahora", action="store_true", help="salta solo la guarda de fecha y hora")
    a = ap.parse_args()
    ahora = datetime.datetime.now()
    log = REPO / "registro" / f"publicacion-{ahora:%Y-%m-%d}.md"
    notas: list[str] = [f"# Publicación — {ahora:%Y-%m-%d %H:%M}", ""]

    def abortar(motivo: str) -> int:
        notas.append(f"**NO SE PUBLICÓ.** {motivo}")
        log.parent.mkdir(exist_ok=True)
        log.write_text("\n".join(notas) + "\n", encoding="utf-8")
        print("NO SE PUBLICÓ:", motivo)
        return 1

    if not a.ahora and ahora < NO_ANTES_DE:
        return abortar(f"todavía no es la hora (no antes de {NO_ANTES_DE:%Y-%m-%d %H:%M}).")
    notas.append(f"- Fecha/hora: OK ({'manual' if a.ahora else 'programada'})")

    v = sh("gh", "repo", "view", SLUG, "--json", "visibility,isPrivate")
    if v.returncode != 0:
        return abortar("gh no está autenticado o el repositorio no existe: " + v.stderr.strip()[:200])
    estado = json.loads(v.stdout)
    notas.append(f"- Repositorio {SLUG}: {estado['visibility']}")
    if not estado["isPrivate"]:
        return abortar("el repositorio ya es público; no hay nada que hacer.")

    pf = sh(sys.executable, "tools/preflight_publicar.py", "--json")
    try:
        hallazgos = json.loads(pf.stdout)
    except json.JSONDecodeError:
        return abortar("el preflight no devolvió JSON válido.")
    alta = [h for h in hallazgos if h["severity"] == "ALTA"]
    notas.append(f"- Preflight: {len(alta)} ALTA · {sum(h['severity'] == 'MEDIA' for h in hallazgos)} MEDIA · {sum(h['severity'] == 'BAJA' for h in hallazgos)} BAJA")
    if alta:
        return abortar(f"el preflight encontró {len(alta)} hallazgo(s) ALTA; revisa `python tools/preflight_publicar.py`.")

    sh("git", "fetch", "origin")
    sucio = sh("git", "status", "--porcelain").stdout.strip()
    adelantado = sh("git", "rev-list", "--count", "origin/main..HEAD").stdout.strip()
    if sucio or adelantado not in ("0", ""):
        return abortar("hay cambios sin subir o sin confirmar (git status / commits locales): lo publicado no coincidiría con lo trabajado.")
    notas.append("- Árbol limpio y sincronizado con origin/main: OK")

    if a.dry_run:
        notas.append("**DRY-RUN:** todas las guardas pasaron; no se cambió nada.")
        log.parent.mkdir(exist_ok=True)
        log.write_text("\n".join(notas) + "\n", encoding="utf-8")
        print("DRY-RUN OK: se publicaría ahora.")
        return 0

    r = sh("gh", "repo", "edit", SLUG, "--visibility", "public", "--accept-visibility-change-consequences",
           "--description", DESCRIPCION, *sum((["--add-topic", t] for t in TEMAS), []))
    if r.returncode != 0:
        return abortar("gh repo edit falló: " + r.stderr.strip()[:300])
    notas.append(f"**PUBLICADO** → https://github.com/{SLUG}")
    log.parent.mkdir(exist_ok=True)
    log.write_text("\n".join(notas) + "\n", encoding="utf-8")
    print("PUBLICADO:", f"https://github.com/{SLUG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
