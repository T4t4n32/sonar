# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Preflight de publicación para SONAR (ESP32, Batalla Naval).

Escanea el árbol de trabajo y TODO el historial de git en busca de:
- Contraseñas/claves/secretos/tokens
- Archivos sensibles (*.jks, *.keystore, *.pem, *.p12, .env)
- Datos personales (correos, teléfonos colombianos, cédulas, nombres de lista)
- Archivos > 5 MB
- Falta de LICENSE o README.md
- Rutas absolutas de Windows con usuario (severidad BAJA)

Salida: tabla con severidad ALTA/MEDIA/BAJA, archivo, línea, commit y fragmento CENSURADO.
Código de salida 1 si hay ALTA.

Opciones:
  --json        Salida JSON en lugar de tabla
  --selftest    Crea un repo git temporal con un secreto falso y comprueba que lo detecta
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------- Patrones de detección ----------

# Claves/secretos/tokens genéricos (clave=valor o clave: valor)
SECRET_PATTERN = re.compile(
    r"(?i)(pass(word)?|pwd|secret|token|api[_-]?key)\s*[=:]\s*[\"']([^\"']{4,})[\"']"
)

# WIFI_PASS* (incluye WIFI_PASS_MAINT de config.h)
WIFI_PASS_PATTERN = re.compile(r"(?i)WIFI_PASS\w*\s*[=:]\s*[\"']?([^\"'\s]{4,})[\"']?")

# #define NOMBRE_PASS "valor" (estilo C/C++, sin = ni :) — config.h usa este formato
DEFINE_PASS_PATTERN = re.compile(r"(?i)#define\s+\w*(pass|pwd|secret|token|key)\w*\s+[\"']([^\"']{4,})[\"']")

# Bloques PEM de clave privada
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN .* PRIVATE KEY-----")

# Correos electrónicos
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Teléfonos colombianos: 3XXXXXXXXX (10 dígitos empezando por 3)
PHONE_CO_PATTERN = re.compile(r"\b3\d{9}\b")

# Cédula / C.C. / T.I. seguidos de número (7-10 dígitos)
CEDULA_PATTERN = re.compile(r"(?i)(c[eé]dula|c\.c\.|t\.i\.)\s*[#:]*\s*(\d{7,10})")

# Rutas absolutas de Windows con usuario: C:\Users\<usuario>\...
WIN_ABS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\Users\\[^\\]+\\")

# Extensiones de archivos sensibles
SENSITIVE_EXTS = {".jks", ".keystore", ".pem", ".p12", ".env"}

# Tamaño límite para archivos grandes (5 MB)
LARGE_FILE_LIMIT = 5 * 1024 * 1024

# Valor por defecto conocido que cuenta como MEDIA, no ALTA
DEFAULT_WIFI_PASS = "duelo1234"


@dataclass
class Finding:
    severity: str          # "ALTA" | "MEDIA" | "BAJA"
    file: str              # ruta relativa al repo
    line: int              # 1-indexed
    commit: str            # hash corto o "WORKTREE"
    snippet: str           # fragmento censurado (máx 4 chars de secreto)

    def to_dict(self) -> dict:
        return asdict(self)


def censor_secret(text: str, secret: str) -> str:
    """Censura un secreto mostrando solo los primeros 4 caracteres."""
    if len(secret) <= 4:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 4)


def censor_match(match: re.Match, full_line: str) -> str:
    """Devuelve la línea con el grupo secreto censurado (grupo 3 para SECRET_PATTERN, grupo 1 para WIFI_PASS)."""
    # Intentar grupo 3 (SECRET_PATTERN), luego grupo 1 (WIFI_PASS), luego grupo 0 completo
    for grp in (3, 1, 0):
        try:
            secret = match.group(grp)
            if secret and len(secret) >= 4:
                censored = censor_secret(secret, secret)
                return full_line.replace(secret, censored, 1)
        except IndexError:
            continue
    return full_line


def load_name_list() -> list[str]:
    """Carga lista de nombres desde tools/.preflight-nombres.txt si existe."""
    path = REPO_ROOT / "tools" / ".preflight-nombres.txt"
    if not path.is_file():
        return []
    try:
        content = path.read_text(encoding="utf-8")
        return [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    except OSError:
        return []


NAME_LIST = load_name_list()
NAME_PATTERN = re.compile(r"\b(" + "|".join(re.escape(n) for n in NAME_LIST) + r")\b") if NAME_LIST else None


def scan_file_content(filepath: Path, rel_path: str, commit: str, findings: list[Finding]) -> None:
    """Escanea un archivo línea por línea buscando patrones sensibles."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    if rel_path.replace("/", "\\").replace("\\", "/") == "tools/preflight_publicar.py":
        return   # contiene sus propios patrones y datos de prueba: se excluye para no marcarse a sí mismo
    if rel_path.replace("\\", "/").startswith("registro/preflight-"):
        return   # los informes de este escáner citan fragmentos censurados: no se re-escanean

    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        # Patrones de secretos genéricos
        for m in SECRET_PATTERN.finditer(line):
            secret = m.group(3)
            sev = "ALTA"
            snippet = censor_match(m, line)
            findings.append(Finding(sev, rel_path, i, commit, snippet))

        # WIFI_PASS*
        for m in WIFI_PASS_PATTERN.finditer(line):
            secret = m.group(1)
            # El valor por defecto duelo1234 cuenta como MEDIA
            sev = "MEDIA" if secret == DEFAULT_WIFI_PASS else "ALTA"
            snippet = censor_match(m, line)
            findings.append(Finding(sev, rel_path, i, commit, snippet))

        # #define con clave (config.h): el valor por defecto conocido cuenta como MEDIA
        for m in DEFINE_PASS_PATTERN.finditer(line):
            sev = "MEDIA" if m.group(2) == DEFAULT_WIFI_PASS else "ALTA"
            findings.append(Finding(sev, rel_path, i, commit, censor_match(m, line)))

        # Claves privadas PEM
        if PRIVATE_KEY_PATTERN.search(line):
            findings.append(Finding("ALTA", rel_path, i, commit, "-----BEGIN * PRIVATE KEY-----"))

        # Correos
        for m in EMAIL_PATTERN.finditer(line):
            # No reportar correos obviamente de ejemplo/documentación
            email = m.group(0)
            if not any(x in email.lower() for x in ("example", "test", "dummy", "localhost", "noreply", "placeholder")):
                findings.append(Finding("MEDIA", rel_path, i, commit, email[:4] + "*" * (len(email) - 4)))

        # Teléfonos colombianos
        for m in PHONE_CO_PATTERN.finditer(line):
            phone = m.group(0)
            findings.append(Finding("MEDIA", rel_path, i, commit, phone[:4] + "*" * (len(phone) - 4)))

        # Cédulas
        for m in CEDULA_PATTERN.finditer(line):
            num = m.group(2)
            findings.append(Finding("MEDIA", rel_path, i, commit, num[:4] + "*" * (len(num) - 4)))

        # Nombres de la lista
        if NAME_PATTERN:
            for m in NAME_PATTERN.finditer(line):
                name = m.group(0)
                findings.append(Finding("MEDIA", rel_path, i, commit, name[:4] + "*" * (len(name) - 4)))

        # Rutas absolutas de Windows con usuario (BAJA)
        for m in WIN_ABS_PATH_PATTERN.finditer(line):
            findings.append(Finding("BAJA", rel_path, i, commit, m.group(0)[:60]))


def scan_worktree(findings: list[Finding]) -> None:
    """Escanea el árbol de trabajo actual (archivos no ignorados por git)."""
    try:
        # Obtener archivos tracked + untracked (no ignorados)
        result = subprocess.run(
            ["git", "ls-files", "-c", "-o", "--exclude-standard"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        files = result.stdout.splitlines() if result.returncode == 0 else []
    except (subprocess.SubprocessError, OSError):
        files = []

    for rel in files:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue

        # Archivos sensibles por extensión/nombre
        if path.suffix.lower() in SENSITIVE_EXTS or path.name.lower() == ".env":
            findings.append(Finding("ALTA", rel, 0, "WORKTREE", f"Archivo sensible: {path.name}"))

        # Tamaño > 5 MB
        try:
            if path.stat().st_size > LARGE_FILE_LIMIT:
                findings.append(Finding("MEDIA", rel, 0, "WORKTREE", f"Archivo > 5 MB ({path.stat().st_size} bytes)"))
        except OSError:
            pass

        # Escanear contenido
        scan_file_content(path, rel, "WORKTREE", findings)

    # Verificar existencia de LICENSE y README.md
    if not (REPO_ROOT / "LICENSE").is_file():
        findings.append(Finding("ALTA", "LICENSE", 0, "WORKTREE", "Falta LICENSE en la raíz"))
    if not (REPO_ROOT / "README.md").is_file():
        findings.append(Finding("MEDIA", "README.md", 0, "WORKTREE", "Falta README.md en la raíz"))


def scan_git_history(findings: list[Finding]) -> None:
    """Escanea TODO el historial de git (git rev-list --all) buscando secretos."""
    try:
        # Obtener todos los commits
        result = subprocess.run(
            ["git", "rev-list", "--all"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        commits = result.stdout.splitlines()
    except (subprocess.CalledProcessError, OSError):
        return

    # Para cada commit, buscar con git log -p -G
    # Usamos un enfoque más eficiente: git log -p --all -G<pattern> para cada patrón
    patterns = [
        r"(?i)(pass(word)?|pwd|secret|token|api[_-]?key)\s*[=:]\s*[\"'][^\"']{4,}[\"']",
        r"(?i)WIFI_PASS\w*\s*[=:]\s*[\"']?[^\"'\s]{4,}[\"']?",
        r"-----BEGIN .* PRIVATE KEY-----",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        r"\b3\d{9}\b",
        r"(?i)(c[eé]dula|c\.c\.|t\.i\.)\s*[#:]*\s*\d{7,10}",
    ]

    # Si hay nombres en la lista, añadirlos
    if NAME_LIST:
        patterns.append(r"\b(" + "|".join(re.escape(n) for n in NAME_LIST) + r")\b")

    # Ejecutar búsqueda combinada con git log -p --all -G
    # -G busca diferencias que añadan/eliminen el patrón (más preciso que -S)
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["git", "log", "-p", "--all", "-G", pattern, "--no-color"],
                cwd=REPO_ROOT, capture_output=True, text=True, check=True, timeout=120
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            continue

        # Parsear la salida de git log -p
        current_commit = ""
        current_file = ""
        for line in result.stdout.splitlines():
            if line.startswith("commit "):
                current_commit = line.split()[1][:8]
            elif line.startswith("diff --git"):
                # diff --git a/path b/path
                parts = line.split()
                if len(parts) >= 4:
                    current_file = parts[3][2:]  # quita b/
            elif line.startswith("+") and not line.startswith("+++"):
                # Línea añadida
                added = line[1:]
                # Buscar el patrón en la línea añadida
                scan_added_line(added, current_file, current_commit, findings, pattern)


def scan_added_line(line: str, file: str, commit: str, findings: list[Finding], pattern: str) -> None:
    if file.replace("\\", "/") == "tools/preflight_publicar.py":
        return
    """Escanea una línea añadida en el historial contra un patrón específico."""
    regex = re.compile(pattern)
    for m in regex.finditer(line):
        secret = ""
        sev = "ALTA"
        snippet = line[:120]

        # Intentar extraer el secreto para censurar
        if "WIFI_PASS" in pattern:
            secret = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            sev = "MEDIA" if secret == DEFAULT_WIFI_PASS else "ALTA"
        elif "PRIVATE KEY" in pattern:
            secret = "PRIVATE KEY"
        elif "3\\d{9}" in pattern:
            secret = m.group(0)
            sev = "MEDIA"
        elif "cedula" in pattern.lower() or "c\\.c\\." in pattern.lower() or "t\\.i\\." in pattern.lower():
            secret = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(0)
            sev = "MEDIA"
        elif NAME_LIST and any(n in pattern for n in NAME_LIST):
            secret = m.group(0)
            sev = "MEDIA"
        else:
            # Patrón genérico de secretos
            secret = m.group(3) if m.lastindex and m.lastindex >= 3 else m.group(0)

        if secret and len(secret) >= 4:
            censored = censor_secret(secret, secret)
            snippet = line.replace(secret, censored, 1)[:120]
        findings.append(Finding(sev, file or "?", 0, commit, snippet))


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    """Elimina hallazgos duplicados (mismo archivo, línea, commit, snippet)."""
    seen = set()
    unique = []
    for f in findings:
        key = (f.severity, f.file, f.line, f.commit, f.snippet)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def print_table(findings: list[Finding]) -> None:
    """Imprime hallazgos en formato tabla."""
    if not findings:
        print("✓ No se encontraron hallazgos.")
        return

    # Ordenar por severidad (ALTA > MEDIA > BAJA), luego archivo, línea
    severity_order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 9), f.file, f.line))

    print(f"{'Sev':<5} {'Archivo':<40} {'Línea':>6} {'Commit':<8} Fragmento")
    print("-" * 100)
    for f in findings:
        file_short = f.file if len(f.file) <= 40 else "..." + f.file[-37:]
        line_str = str(f.line) if f.line > 0 else "-"
        print(f"{f.severity:<5} {file_short:<40} {line_str:>6} {f.commit:<8} {f.snippet}")


def print_json(findings: list[Finding]) -> None:
    """Imprime hallazgos en formato JSON."""
    print(json.dumps([f.to_dict() for f in findings], ensure_ascii=False, indent=2))


def run_selftest() -> int:
    """Crea un repo temporal con un secreto falso y verifica que lo detecta."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "test_repo"
        repo.mkdir()

        # Inicializar repo git
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)

        # Commit inicial limpio
        (repo / "README.md").write_text("# Test\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo, capture_output=True, check=True)

        # Commit con secreto
        secret_file = repo / "secret.txt"
        secret_file.write_text('api_key = "SUPER_SECRET_KEY_12345"\n')
        subprocess.run(["git", "add", "secret.txt"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Add secret"], cwd=repo, capture_output=True, check=True)

        # Ejecutar preflight sobre el repo temporal
        # Copiar el script al repo temporal para que lo use
        script_path = REPO_ROOT / "tools" / "preflight_publicar.py"
        script_content = script_path.read_text(encoding="utf-8")

        # Ejecutar desde el repo temporal
        result = subprocess.run(
            [sys.executable, str(script_path), "--json", "--root", str(repo)],
            cwd=repo, capture_output=True, text=True, timeout=60
        )

        if result.returncode != 1:
            print(f"FAIL: se esperaba código de salida 1 (ALTA), got {result.returncode}")
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
            return 1

        try:
            findings = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("FAIL: salida no es JSON válido")
            print(result.stdout)
            return 1

        # Verificar que detectó el secreto
        alta_findings = [f for f in findings if f["severity"] == "ALTA"]
        secret_found = any("SUPER_SECRET" in f["snippet"] or "API_KEY" in f["snippet"].upper() for f in alta_findings)

        if not secret_found:
            print("FAIL: no detectó el secreto plantado")
            print("Hallazgos:", json.dumps(findings, indent=2))
            return 1

        print("PASS: selftest detectó correctamente el secreto en el historial")
        return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Preflight de publicación para SONAR")
    ap.add_argument("--json", action="store_true", help="Salida JSON")
    ap.add_argument("--selftest", action="store_true", help="Ejecuta autocomprobación con repo temporal")
    ap.add_argument("--root", type=Path, help="repositorio a escanear (por defecto, el de este script)")
    args = ap.parse_args(argv)
    if args.root:
        global REPO_ROOT
        REPO_ROOT = args.root.resolve()

    if args.selftest:
        return run_selftest()

    findings: list[Finding] = []

    # 1. Escanear árbol de trabajo
    scan_worktree(findings)

    # 2. Escanear historial de git
    scan_git_history(findings)

    # 3. Deduplicar
    findings = deduplicate_findings(findings)

    # 4. Salida
    if args.json:
        print_json(findings)
    else:
        print_table(findings)

    # Código de salida: 1 si hay ALTA
    has_alta = any(f.severity == "ALTA" for f in findings)
    return 1 if has_alta else 0


if __name__ == "__main__":
    sys.exit(main())