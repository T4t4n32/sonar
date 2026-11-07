#!/usr/bin/env python3
"""
Copia ../web/index.html a app/www/index.html SIN modificarlo.
Úsalo antes de 'npx cap sync android' para que el APK lleve la web actual.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT.parent / "web" / "index.html"
DST_DIR = ROOT / "www"
DST = DST_DIR / "index.html"

def main():
    if not SRC.exists():
        raise SystemExit(f"❌ No existe el origen: {SRC}")
    DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DST)
    print(f"✅ Copiado {SRC} → {DST} ({DST.stat().st_size} bytes)")

if __name__ == "__main__":
    main()