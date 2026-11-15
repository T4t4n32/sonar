#!/usr/bin/env python3
"""Compila el APK debug de SONAR de punta a punta.

  build web (tsc + vite) -> npx cap sync android -> gradlew assembleDebug -> dist-apk/SONAR-<versión>-debug.apk

Uso:  python tools/build_apk.py [--skip-typecheck] [--no-web] [--install]
  --skip-typecheck  solo `vite build` (sin tsc), útil si otro módulo está a medias
  --no-web          no reconstruye la web (usa app/www tal cual)
  --install         al final, `adb install -r` en el celular conectado (pide confirmación del usuario: no es default)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
JBR = Path(os.environ.get("SONAR_JAVA_HOME", r"C:\Program Files\Android\Android Studio\jbr"))
SDK = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")
NPM = "npm.cmd" if os.name == "nt" else "npm"
NPX = "npx.cmd" if os.name == "nt" else "npx"


def run(cmd, cwd=APP, env=None):
    print(f"\n$ {' '.join(map(str, cmd))}   (en {cwd})", flush=True)
    r = subprocess.run(list(map(str, cmd)), cwd=cwd, env=env)
    if r.returncode != 0:
        sys.exit(f"FALLÓ ({r.returncode}): {' '.join(map(str, cmd))}")


def latest_build_tool(name: str) -> Path | None:
    bt = SDK / "build-tools"
    if not bt.is_dir():
        return None
    for d in sorted(bt.iterdir(), key=lambda p: [int(x) if x.isdigit() else 0 for x in p.name.replace("-", ".").split(".")], reverse=True):
        for ext in (".exe", ".bat", ""):
            f = d / (name + ext)
            if f.is_file():
                return f
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-typecheck", action="store_true")
    ap.add_argument("--no-web", action="store_true")
    ap.add_argument("--install", action="store_true")
    a = ap.parse_args()

    if not (JBR / "bin" / ("java.exe" if os.name == "nt" else "java")).exists():
        sys.exit(f"No encuentro el JDK en {JBR}. Define SONAR_JAVA_HOME (JBR de Android Studio; el java del PATH 1.8 no sirve).")
    if not SDK.is_dir():
        sys.exit(f"No encuentro el Android SDK en {SDK}. Define ANDROID_HOME.")
    env = dict(os.environ, JAVA_HOME=str(JBR), ANDROID_HOME=str(SDK), ANDROID_SDK_ROOT=str(SDK))
    env["PATH"] = str(JBR / "bin") + os.pathsep + env["PATH"]

    version = json.loads((APP / "package.json").read_text(encoding="utf-8"))["version"]

    if not a.no_web:
        run([NPX, "vite", "build"] if a.skip_typecheck else [NPM, "run", "build"], env=env)
    run([NPX, "cap", "sync", "android"], env=env)
    gradlew = str(APP / "android" / ("gradlew.bat" if os.name == "nt" else "gradlew"))
    run([gradlew, "assembleDebug"], cwd=APP / "android", env=env)

    src = APP / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if not src.is_file():
        sys.exit(f"Gradle terminó pero no existe {src}")
    dist = APP / "dist-apk"
    dist.mkdir(exist_ok=True)
    dst = dist / f"SONAR-{version}-debug.apk"
    shutil.copy2(src, dst)
    print(f"\nAPK listo: {dst}  ({dst.stat().st_size / 1024 / 1024:.2f} MB)")

    aapt2 = latest_build_tool("aapt2")
    if aapt2:
        out = subprocess.run([str(aapt2), "dump", "badging", str(dst)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        keys = ("package:", "sdkVersion", "targetSdkVersion", "uses-permission", "uses-feature", "application-label:", "launchable-activity", "supports-screens")
        print("\n-- aapt2 dump badging (resumen) --")
        for ln in out.splitlines():
            if ln.startswith(keys) or "screenOrientation" in ln:
                print(ln)
    if a.install:
        adb = SDK / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
        run([adb, "install", "-r", dst])
    else:
        print(f'\nInstalar: adb install -r "{dst}"')


if __name__ == "__main__":
    main()
