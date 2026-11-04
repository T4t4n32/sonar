#!/usr/bin/env python3
"""Celular de pruebas por línea de comandos para el módulo duelo-laser.

Transportes (elige uno):
  --tcp HOST:PUERTO          líneas crudas (fake_device.py --tcp, o el módulo por TCP)
  --http http://HOST:PUERTO  GET /cmd?l=...  (fake_device.py, o el módulo en modo mantenimiento)
  --serial COM5              puerto serie a 115200 (requiere pyserial)

Órdenes:
  fire X Y      dispara (X,Y)
  test          rutina TEST (5 posiciones)
  ping          PING
  raw "LINEA"   envía la línea tal cual
  selftest      batería de pruebas del protocolo; sale con 1 si algo falla

Códigos de salida: 0 correcto · 1 respuesta de error (o selftest con FAIL) · 2 no se pudo conectar.

Ejemplos:
  python tools/sim_phone.py --http http://127.0.0.1:8080 fire 10 10
  python tools/sim_phone.py --tcp 127.0.0.1:5000 test
  python tools/sim_phone.py --http http://127.0.0.1:8080 selftest
"""
from __future__ import annotations

import argparse
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
CONFIG_H = REPO / "include" / "config.h"
FALLBACK_TEST_CELLS = [(1, 1), (20, 1), (20, 20), (1, 20), (11, 11)]
CAL_RX = r"CAL -?\d+\.\d{2} -?\d+\.\d{2} -?\d+\.\d{2} -?\d+\.\d{2} -?\d+\.\d{2}"


def load_test_cells() -> tuple[list[tuple[int, int]], str]:
    """Lee cfg::TEST_CELLS de include/config.h para que el selftest siga al firmware."""
    try:
        text = CONFIG_H.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_TEST_CELLS, "integrada (no se encontró include/config.h)"
    m = re.search(r"TEST_CELLS\s*\[\s*5\s*\]\s*\[\s*2\s*\]\s*=\s*\{(.*?)\}\s*;", text, re.S)
    pairs = re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(1)) if m else []
    if len(pairs) != 5:
        return FALLBACK_TEST_CELLS, "integrada (no se pudo leer cfg::TEST_CELLS)"
    return [(int(a), int(b)) for a, b in pairs], "include/config.h"


def read_response(readline: Callable[[], str]) -> list[str]:
    """Lee la respuesta de una orden: una línea, salvo la rutina TEST (hasta TEST DONE o TEST ABORT + error)."""
    first = readline()
    out = [first]
    if first == "TEST START":
        while True:
            nxt = readline()
            out.append(nxt)
            if nxt == "TEST DONE":
                break
            if nxt == "TEST ABORT":
                out.append(readline())
                break
    return out


class TcpTransport:
    def __init__(self, host: str, port: int, timeout: float):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.rf = self.sock.makefile("rb")

    def send(self, line: str) -> list[str]:
        self.sock.sendall(line.encode("utf-8") + b"\n")
        return read_response(self._readline)

    def _readline(self) -> str:
        raw = self.rf.readline()
        if not raw:
            raise ConnectionError("el módulo cerró la conexión")
        return raw.decode("utf-8", "replace").rstrip("\r\n")

    def close(self) -> None:
        for closer in (self.rf.close, self.sock.close):
            try:
                closer()
            except OSError:
                pass


class HttpTransport:
    def __init__(self, base: str, timeout: float):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def send(self, line: str) -> list[str]:
        url = f"{self.base}/cmd?l={quote(line, safe='')}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                body = r.read()
        except urllib.error.HTTPError as e:  # el módulo responde ERR en texto aunque el código sea de error
            body = e.read()
        return body.decode("utf-8", "replace").splitlines()

    def close(self) -> None:
        pass


class SerialTransport:
    def __init__(self, port: str, baud: int, timeout: float):
        try:
            import serial  # pyserial (opcional)
        except ImportError:
            raise SystemExit("falta pyserial para --serial: pip install pyserial (ver tools/requirements.txt)")
        self.ser = serial.Serial(port, baud, timeout=0.5)
        self.timeout = timeout

    def send(self, line: str) -> list[str]:
        self.ser.reset_input_buffer()
        self.ser.write(line.encode("utf-8") + b"\n")
        return read_response(self._readline)

    def _readline(self) -> str:
        t0 = time.monotonic()
        buf = b""
        while True:
            buf += self.ser.readline()
            if buf.endswith(b"\n"):
                return buf.decode("utf-8", "replace").rstrip("\r\n")
            if time.monotonic() - t0 > self.timeout:
                raise TimeoutError("sin respuesta del módulo")

    def close(self) -> None:
        self.ser.close()


def build_factory(args) -> tuple[Callable[[], object], str, bool]:
    """Devuelve (crear_transporte, descripción, admite_segunda_conexión)."""
    if args.tcp:
        host, _, port = args.tcp.rpartition(":")
        if not host or not port.isdigit():
            raise SystemExit("--tcp espera HOST:PUERTO, p. ej. 127.0.0.1:5000")
        p = int(port)
        return (lambda: TcpTransport(host, p, args.timeout)), f"tcp {host}:{p}", True
    if args.http:
        return (lambda: HttpTransport(args.http, args.timeout)), f"http {args.http}", True
    return (lambda: SerialTransport(args.serial, args.baud, args.timeout)), f"serie {args.serial}", False


# ---------------------------------------------------------------- selftest
def _exact(expected: list[str]) -> Callable[[list[str]], bool]:
    return lambda got: got == expected


def _pattern(rx: str) -> Callable[[list[str]], bool]:
    return lambda got: len(got) == 1 and re.fullmatch(rx, got[0]) is not None


def _safe_send(factory, tx_holder: list, line: str) -> list[str]:
    """Envía sin dejar que una excepción corte la batería; si falla, rehace la conexión."""
    try:
        return tx_holder[0].send(line)
    except Exception as e:  # noqa: BLE001 - se reporta como FAIL
        tx_holder[0].close()
        tx_holder[0] = factory()
        return [f"<excepción: {e}>"]


def _busy_checks(factory, cells: list[tuple[int, int]]) -> list[tuple[str, str, str]]:
    """Con el módulo ocupado en un TEST: PING -> ERR BUSY, STOP -> OK STOP, el TEST se aborta con ERR STOP."""
    rows: list[tuple[str, str, str]] = []
    t_test = factory()
    t_ctl = factory()
    box: dict[str, list[str]] = {}

    def run_test() -> None:
        try:
            box["lines"] = t_test.send("TEST")
        except Exception as e:  # noqa: BLE001
            box["lines"] = [f"<excepción: {e}>"]

    th = threading.Thread(target=run_test, daemon=True)
    th.start()
    seen: Optional[list[str]] = None
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and th.is_alive():
        try:
            r = t_ctl.send("PING")
        except Exception as e:  # noqa: BLE001
            r = [f"<excepción: {e}>"]
        if r == ["ERR BUSY"]:
            seen = r
            break
        time.sleep(0.05)
    rows.append(("PING con el módulo ocupado (TEST en curso)",
                 "PASS" if seen else "FAIL",
                 "ERR BUSY" if seen else "nunca se vio ocupado (ni ERR BUSY)"))
    if seen:
        try:
            stop_r = t_ctl.send("STOP")
        except Exception as e:  # noqa: BLE001
            stop_r = [f"<excepción: {e}>"]
        rows.append(("STOP con el módulo ocupado",
                     "PASS" if stop_r == ["OK STOP"] else "FAIL",
                     " | ".join(stop_r)))
    th.join(60)
    lines = box.get("lines", [])
    ok = bool(seen) and lines[:1] == ["TEST START"] and lines[-2:] == ["TEST ABORT", "ERR STOP"]
    rows.append(("TEST interrumpido por STOP (ABORT + ERR STOP)",
                 "PASS" if ok else "FAIL",
                 " | ".join(lines)))
    for t in (t_test, t_ctl):
        t.close()
    return rows


def run_selftest(factory, label: str, parallel: bool) -> int:
    cells, cells_src = load_test_cells()
    expected_test = ["TEST START"] + [f"OK ({x},{y})" for x, y in cells] + ["TEST DONE"]
    cases: list[tuple[str, Callable[[list[str]], bool], str]] = [
        ("PING", _pattern(r"PONG \S+ \d+\.\d+\.\d+"), "PONG <nombre> <versión>"),
        ("(10,10)", _exact(["OK (10,10)"]), "OK (10,10)"),
        ("(0,5)", _exact(["ERR RANGE"]), "ERR RANGE"),
        ("(21,1)", _exact(["ERR RANGE"]), "ERR RANGE"),
        ("(a,b)", _exact(["ERR FORMAT"]), "ERR FORMAT"),
        ("HOLA", _exact(["ERR UNKNOWN"]), "ERR UNKNOWN"),
        ("", _exact(["ERR EMPTY"]), "ERR EMPTY"),
        ("CAL SHOW", _pattern(CAL_RX), "CAL x y h panTrim tiltTrim"),
        ("CAL SET 110 -60 170 1.5 -1", _exact(["OK CAL"]), "OK CAL"),
        ("CAL SHOW", _exact(["CAL 110.00 -60.00 170.00 1.50 -1.00"]), "valores recién fijados"),
        ("CAL SET 999 0 0 0 0", _exact(["ERR RANGE"]), "ERR RANGE"),
        ("CAL RESET", _exact(["OK RESET"]), "OK RESET"),
        ("CAL SHOW", _exact(["CAL 100.00 -65.00 180.00 0.00 0.00"]), "valores por defecto"),
        ("MARK MISS", _exact(["OK MARK"]), "OK MARK"),
        ("MARK HIT", _exact(["OK MARK"]), "OK MARK"),
        ("STOP", _exact(["OK STOP"]), "OK STOP"),
        ("TEST", _exact(expected_test), "TEST START, OK en cada celda, TEST DONE"),
    ]

    print(f"Transporte: {label} · TEST_CELLS: {cells_src} {cells}")
    holder = [factory()]
    rows: list[tuple[str, str, str]] = []
    try:
        for sent, pred, desc in cases:
            got = _safe_send(factory, holder, sent)
            ok = pred(got)
            detail = " | ".join(got)
            if not ok:
                detail = f"esperado: {desc} · recibido: {detail}"
            rows.append((f'"{sent}"', "PASS" if ok else "FAIL", detail))
        if parallel:
            rows.extend(_busy_checks(factory, cells))
        else:
            rows.append(("TEST interrumpido por STOP", "SKIP", "serie: no admite una segunda conexión"))
    finally:
        holder[0].close()

    w = max(len(r[0]) for r in rows)
    print()
    print(f"{'#':>2}  {'Enviado':<{w}}  {'Estado':<6}  Recibido / detalle")
    for i, (name, state, detail) in enumerate(rows, 1):
        print(f"{i:>2}  {name:<{w}}  {state:<6}  {detail}")
    n_pass = sum(1 for r in rows if r[1] == "PASS")
    n_fail = sum(1 for r in rows if r[1] == "FAIL")
    n_skip = sum(1 for r in rows if r[1] == "SKIP")
    print()
    print(f"Resultado: {n_pass} PASS, {n_fail} FAIL, {n_skip} SKIP")
    return 1 if n_fail else 0


# ---------------------------------------------------------------- CLI
def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Celular de pruebas para el módulo duelo-laser.")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--tcp", metavar="HOST:PUERTO", help="transporte TCP de líneas crudas")
    grp.add_argument("--http", metavar="URL", help="transporte HTTP, p. ej. http://127.0.0.1:8080")
    grp.add_argument("--serial", metavar="PUERTO", help="puerto serie, p. ej. COM5 (requiere pyserial)")
    ap.add_argument("--baud", type=int, default=115200, help="velocidad del puerto serie")
    ap.add_argument("--timeout", type=float, default=60.0, help="segundos máximos por orden")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="ORDEN")
    f = sub.add_parser("fire", help="dispara (X,Y)")
    f.add_argument("x", type=int)
    f.add_argument("y", type=int)
    sub.add_parser("test", help="rutina TEST de 5 posiciones")
    sub.add_parser("ping", help="PING")
    r = sub.add_parser("raw", help="envía una línea tal cual")
    r.add_argument("linea")
    sub.add_parser("selftest", help="batería de pruebas del protocolo")
    args = ap.parse_args(argv)
    _utf8_streams()

    label = args.tcp or args.http or args.serial
    try:
        factory, label, parallel = build_factory(args)
        if args.cmd == "selftest":
            return run_selftest(factory, label, parallel)
        if args.cmd == "fire":
            line = f"({args.x},{args.y})"
        elif args.cmd == "raw":
            line = args.linea
        else:
            line = args.cmd.upper()  # TEST | PING
        tx = factory()
        try:
            lines = tx.send(line)
        finally:
            tx.close()
    except (OSError, TimeoutError, ConnectionError) as e:
        print(f"error de conexión con {label}: {e}", file=sys.stderr)
        return 2

    for text in lines:
        print(text)
    bad = any(t.startswith("ERR") or t.startswith("TEST ABORT") for t in lines)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
