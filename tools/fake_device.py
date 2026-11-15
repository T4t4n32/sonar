#!/usr/bin/env python3
"""Módulo SIMULADO de SONAR (solo biblioteca estándar).

Implementa docs/03-firmware-y-app/PROTOCOLO.md en dos transportes:
  * HTTP: GET /         -> web/index.html
          GET /cmd?l=.. -> respuesta en texto plano, una línea por respuesta
  * TCP:  (opcional, --tcp PUERTO) líneas crudas terminadas en salto de línea

Tiempos: cada duración real (rampa de servos, asentamiento, láser 1,5 s, hueco
del TEST 1,5 s, LED 2 s) se divide entre --speed. Por defecto --speed 5, es
decir cinco veces más rápido que el real. A velocidad 1 el movimiento típico
dura ~1 s, como en el hardware.

Uso:
  python tools/fake_device.py                        # http://127.0.0.1:8080/
  python tools/fake_device.py --port 8080 --tcp 5000 --speed 1
  python tools/fake_device.py --host 0.0.0.0         # accesible desde el celular
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import socketserver
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import parse_qs, urlsplit

REPO = Path(__file__).resolve().parent.parent

# ---- Constantes: espejo de include/config.h y docs/03-firmware-y-app/PROTOCOLO.md
DEVICE_NAME = "DUELO-FAKE"
FW_VERSION = "0.1.0"
GRID_N = 20
CELL_MM = 10.0
STATION_X_MM = 100.0
STATION_Y_MM = -65.0
TILT_H_MM = 180.0
PAN_LIMIT_DEG = 57.0
TILT_MIN_DEG = 30.0
TILT_MAX_DEG = 72.0
PAN_CENTER_SERVO_DEG = 90.0
TILT_HORIZ_SERVO_DEG = 90.0
PAN_SIGN = 1.0
TILT_SIGN = 1.0
MAX_STEP_DEG = 2.0
STEP_MS = 20
OVERSHOOT_DEG = 2.0
SETTLE_MS = 300
LASER_ON_MS = 1500
TEST_GAP_MS = 1500
LED_HIT_MS = 2000
BEEP_HZ = 1000
BEEP_MS = 150
TEST_CELLS = [(1, 1), (20, 1), (20, 20), (1, 20), (11, 11)]
MAX_LINE = 64
# Rangos de CAL SET: x, y, h, panTrim, tiltTrim (mm y grados)
CAL_RANGES = [(-200.0, 400.0), (-300.0, 400.0), (50.0, 400.0), (-10.0, 10.0), (-10.0, 10.0)]
_READ_LIMIT = 256

ERR_TEXT = {
    "EMPTY": "ERR EMPTY",
    "TOOLONG": "ERR TOOLONG",
    "FORMAT": "ERR FORMAT",
    "RANGE": "ERR RANGE",
    "UNKNOWN": "ERR UNKNOWN",
}

# ---------------------------------------------------------------- protocolo
_FIRE_RE = re.compile(r"\(\s*([^\s,()]*)\s*,\s*([^\s,()]*)\s*\)")
_INT_RE = re.compile(r"[+-]?\d+")
_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)")


@dataclass
class Parsed:
    kind: str = ""       # FIRE TEST STOP PING HELLO MODE ARM MARK_HIT MARK_MISS CAL_SHOW CAL_SET CAL_SAVE CAL_RESET
    x: int = 0
    y: int = 0
    vals: tuple = ()
    err: str = ""        # clave de ERR_TEXT cuando la línea no es válida


def parse_line(raw: str) -> Parsed:
    """Analiza una línea del protocolo. Tolerante con espacios, \\r\\n y mayúsculas."""
    text = raw.rstrip("\r\n")
    s = text.strip()
    if not s:
        return Parsed(err="EMPTY")
    if len(text) > MAX_LINE:
        return Parsed(err="TOOLONG")
    if s.startswith("(") or "," in s:  # "(x,y)": los paréntesis son obligatorios
        m = _FIRE_RE.fullmatch(s)
        if not m or not _INT_RE.fullmatch(m.group(1)) or not _INT_RE.fullmatch(m.group(2)):
            return Parsed(err="FORMAT")
        x, y = int(m.group(1)), int(m.group(2))
        if not (1 <= x <= GRID_N and 1 <= y <= GRID_N):
            return Parsed(err="RANGE")
        return Parsed(kind="FIRE", x=x, y=y)
    words = s.split()
    head, args = words[0].upper(), words[1:]
    if head in ("TEST", "STOP", "PING"):
        return Parsed(kind=head) if not args else Parsed(err="FORMAT")
    if head in ("HELLO", "ARM"):  # protocolo v2 (docs/03-firmware-y-app/PROTOCOLO.md)
        return Parsed(kind=head) if not args else Parsed(err="FORMAT")
    if head == "MODE":
        if not args:
            return Parsed(kind="MODE")
        if args[0].upper() not in ("BT", "WIFI"):
            return Parsed(err="UNKNOWN")
        return Parsed(kind="MODE", vals=(args[0].upper(),)) if len(args) == 1 else Parsed(err="FORMAT")
    if head == "MARK":
        if len(args) == 1 and args[0].upper() in ("HIT", "MISS"):
            return Parsed(kind="MARK_" + args[0].upper())
        return Parsed(err="FORMAT")
    if head == "CAL":
        if not args:
            return Parsed(err="FORMAT")
        sub, rest = args[0].upper(), args[1:]
        if sub in ("SHOW", "SAVE", "RESET"):
            return Parsed(kind="CAL_" + sub) if not rest else Parsed(err="FORMAT")
        if sub == "SET":
            if len(rest) != 5 or not all(_NUM_RE.fullmatch(v) for v in rest):
                return Parsed(err="FORMAT")
            return Parsed(kind="CAL_SET", vals=tuple(float(v) for v in rest))
        return Parsed(err="UNKNOWN")
    return Parsed(err="UNKNOWN")


# ---------------------------------------------------------------- geometría
@dataclass
class Cal:
    x: float = STATION_X_MM
    y: float = STATION_Y_MM
    h: float = TILT_H_MM
    pan_trim: float = 0.0
    tilt_trim: float = 0.0


def aim_mm(x_mm: float, y_mm: float, cal: Cal) -> Optional[tuple[float, float]]:
    """(pan, tilt) en grados para un punto en mm, o None si excede los límites.

    pan = atan2(dx, dy) (0 = al frente, + = derecha); tilt = atan2(h, hypot(dx, dy)) (bajo la horizontal).
    """
    dx = x_mm - cal.x
    dy = y_mm - cal.y
    pan = math.degrees(math.atan2(dx, dy))
    tilt = math.degrees(math.atan2(cal.h, math.hypot(dx, dy)))
    if abs(pan) > PAN_LIMIT_DEG or not (TILT_MIN_DEG <= tilt <= TILT_MAX_DEG):
        return None
    return pan, tilt


def aim_cell(x: int, y: int, cal: Cal) -> Optional[tuple[float, float]]:
    if not (1 <= x <= GRID_N and 1 <= y <= GRID_N):
        return None
    return aim_mm((x - 0.5) * CELL_MM, (y - 0.5) * CELL_MM, cal)


def _clamp(deg: float) -> float:
    return min(180.0, max(0.0, deg))


def to_servo(pan: float, tilt: float, cal: Cal) -> tuple[float, float]:
    p = PAN_CENTER_SERVO_DEG + PAN_SIGN * pan + cal.pan_trim
    t = TILT_HORIZ_SERVO_DEG + TILT_SIGN * tilt + cal.tilt_trim
    return _clamp(p), _clamp(t)


def _ceil_steps(delta_deg: float) -> int:
    return math.ceil(round(abs(delta_deg) / MAX_STEP_DEG, 9))


def _axis_steps(now: float, target: float) -> int:
    """Pasos de la rampa de un eje, con el waypoint de aproximación si el destino está por debajo."""
    steps = 0
    if target < now:  # aproximarse siempre desde el mismo lado (holgura de engranes)
        waypoint = target - OVERSHOOT_DEG
        steps += _ceil_steps(now - waypoint)
        now = waypoint
    return steps + _ceil_steps(target - now)


# ---------------------------------------------------------------- módulo
def _stderr_log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def default_nvs_path() -> Path:
    return Path(tempfile.gettempdir()) / "duelo_fake_nvs.json"


LONG_KINDS = ("FIRE", "TEST", "MARK_HIT")  # órdenes que ocupan el módulo mientras duran


class Device:
    """Lógica del módulo. Una orden larga a la vez.

    _lock protege _busy y el evento de parada. Las órdenes rápidas (PING, CAL, MARK MISS)
    se ejecutan bajo _lock y no ocupan el módulo, así que nunca hacen fallar a una orden larga
    que llega al mismo tiempo. Si hay una orden larga en curso, responden ERR BUSY.
    El estado físico (calibración, servos, láser) solo se toca bajo _lock o con el módulo ocupado.
    STOP solo fija el evento de parada: se atiende aunque haya una orden en curso.
    """

    def __init__(self, speed: float = 5.0, nvs_path: Optional[Path] = None,
                 log: Optional[Callable[[str], None]] = None):
        if speed <= 0:
            raise ValueError("--speed debe ser mayor que 0")
        self.speed = float(speed)
        self.nvs_path = Path(nvs_path) if nvs_path else default_nvs_path()
        self._log_fn = log or _stderr_log
        self._lock = threading.Lock()
        self._busy = False
        self._stop = threading.Event()
        self.cal = self._load_nvs()
        self.servo = (PAN_CENTER_SERVO_DEG, TILT_HORIZ_SERVO_DEG)
        self.laser_on = False
        self.led_on = False

    def log(self, msg: str) -> None:
        self._log_fn(msg)

    # -- candado de ocupación
    def _begin(self) -> Optional[threading.Event]:
        with self._lock:
            if self._busy:
                return None
            self._busy = True
            self._stop = threading.Event()
            return self._stop

    def _end(self) -> None:
        with self._lock:
            self._busy = False

    def request_stop(self) -> None:
        with self._lock:
            self._stop.set()

    # -- entrada de líneas
    def handle_line(self, raw: str, reply: Callable[[str], None]) -> None:
        """Procesa una línea y llama a reply() por cada línea de respuesta, en orden."""

        def out(text: str) -> None:
            self.log(f"  > {text}")
            reply(text)

        self.log(f"< {raw.strip()!r}")
        p = parse_line(raw)
        if p.err:
            out(ERR_TEXT[p.err])
            return
        if p.kind == "STOP":  # se atiende aunque el módulo esté ocupado
            self.log("STOP: láser OFF y aborto de la orden en curso")
            self.request_stop()
            out("OK STOP")
            return
        if p.kind in LONG_KINDS:
            stop = self._begin()
            if stop is None:
                out("ERR BUSY")
                return
            try:
                self._run_long(p, stop, out)
            finally:
                self._end()
            return
        with self._lock:  # orden rápida: una sola respuesta, calculada bajo el candado
            reply_text = "ERR BUSY" if self._busy else self._quick(p)
        out(reply_text)

    def _run_long(self, p: Parsed, stop: threading.Event, out: Callable[[str], None]) -> None:
        if p.kind == "FIRE":
            err = self._fire(p.x, p.y, stop)
            out(err or f"OK ({p.x},{p.y})")
        elif p.kind == "TEST":
            self._test(stop, out)
        elif p.kind == "MARK_HIT":
            self._led_hit()
            out("OK MARK")

    def _quick(self, p: Parsed) -> str:
        if p.kind == "MARK_MISS":
            return "OK MARK"
        if p.kind == "PING":
            return f"PONG {DEVICE_NAME} {FW_VERSION}"
        if p.kind == "HELLO":  # el simulador se anuncia como Wi-Fi con envío en vivo (capacidades: sim)
            return f"HELLO SONAR 2 {FW_VERSION} {DEVICE_NAME} WIFI sim"
        if p.kind == "MODE":  # no reinicia nada: solo lo acepta, para probar las páginas
            return f"OK MODE {p.vals[0]}" if p.vals else "MODE WIFI"
        if p.kind == "ARM":
            return "ARM NOTREQ"
        if p.kind == "CAL_SHOW":
            c = self.cal
            return f"CAL {c.x:.2f} {c.y:.2f} {c.h:.2f} {c.pan_trim:.2f} {c.tilt_trim:.2f}"
        if p.kind == "CAL_SET":
            vals = [v + 0.0 for v in p.vals]  # +0.0 quita el -0
            if all(lo <= v <= hi for v, (lo, hi) in zip(vals, CAL_RANGES)):
                self.cal = Cal(*vals)
                return "OK CAL"
            return "ERR RANGE"
        if p.kind == "CAL_SAVE":
            return "OK SAVE" if self._save_nvs() else "ERR STORE"
        if p.kind == "CAL_RESET":
            self.cal = Cal()
            self._erase_nvs()
            return "OK RESET"
        return "ERR UNKNOWN"

    # -- tiempos simulados
    def _wait(self, stop: threading.Event, real_ms: float) -> bool:
        """Espera real_ms (de hardware) escalados por --speed. True si llegó un STOP."""
        return stop.wait(max(0.0, real_ms) / 1000.0 / self.speed)

    def _set_laser(self, on: bool) -> None:
        self.laser_on = on
        self.log("LASER ON" if on else "LASER OFF")

    # -- disparo
    def _fire(self, x: int, y: int, stop: threading.Event) -> Optional[str]:
        """Secuencia de disparo. Devuelve None si todo va bien, o la línea de error."""
        aim = aim_cell(x, y, self.cal)
        if aim is None:
            self.log(f"celda ({x},{y}) fuera de los límites de pan/tilt")
            return "ERR LIMIT"
        target = to_servo(aim[0], aim[1], self.cal)
        steps = _axis_steps(self.servo[0], target[0]) + _axis_steps(self.servo[1], target[1])
        move_ms = steps * STEP_MS
        self.log(f"mover servos a pan {target[0]:.1f} / tilt {target[1]:.1f} ({move_ms / 1000:.2f} s reales)")
        if self._wait(stop, move_ms):          # el láser nunca se enciende mientras se mueve
            return "ERR STOP"
        self.servo = target
        if self._wait(stop, SETTLE_MS):
            return "ERR STOP"
        if stop.is_set():                       # interlock: no se enciende con un STOP pendiente
            return "ERR STOP"
        self._set_laser(True)
        self.log(f"zumbador {BEEP_HZ} Hz {BEEP_MS} ms")
        try:
            interrupted = self._wait(stop, LASER_ON_MS)
        finally:
            self._set_laser(False)
        return "ERR STOP" if interrupted else None

    def _test(self, stop: threading.Event, out: Callable[[str], None]) -> None:
        out("TEST START")
        for x, y in TEST_CELLS:
            err = self._fire(x, y, stop)
            if err:
                out("TEST ABORT")
                out(err)
                return
            out(f"OK ({x},{y})")
            if self._wait(stop, TEST_GAP_MS):
                out("TEST ABORT")
                out("ERR STOP")
                return
        out("TEST DONE")

    def _led_hit(self) -> None:
        self.led_on = True
        self.log(f"LED ON {LED_HIT_MS / 1000:.1f} s reales")
        time.sleep(LED_HIT_MS / 1000.0 / self.speed)
        self.led_on = False

    # -- NVS simulada (un JSON en el directorio temporal, o --nvs)
    def _load_nvs(self) -> Cal:
        try:
            d = json.loads(self.nvs_path.read_text(encoding="utf-8"))
            cal = Cal(float(d["x"]), float(d["y"]), float(d["h"]), float(d["pan"]), float(d["tilt"]))
            self.log(f"calibración cargada de {self.nvs_path}")
            return cal
        except FileNotFoundError:
            return Cal()
        except (OSError, ValueError, KeyError, TypeError) as e:
            self.log(f"NVS ilegible ({e}): se usan los valores por defecto")
            return Cal()

    def _save_nvs(self) -> bool:
        c = self.cal
        data = {"x": c.x, "y": c.y, "h": c.h, "pan": c.pan_trim, "tilt": c.tilt_trim}
        tmp = self.nvs_path.with_name(self.nvs_path.name + ".tmp")
        try:
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self.nvs_path)
            self.log(f"calibración guardada en {self.nvs_path}")
            return True
        except OSError as e:
            self.log(f"error al guardar la NVS: {e}")
            return False

    def _erase_nvs(self) -> None:
        try:
            self.nvs_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            self.log(f"no se pudo borrar la NVS: {e}")


# ---------------------------------------------------------------- transportes
def make_http_handler(dev: Device, web_file: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DUELO-FAKE/0.1"

        def log_message(self, fmt, *args):  # el registro lo lleva Device
            pass

        def _send(self, code: int, ctype: str, body: bytes) -> None:
            try:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except OSError:  # el cliente se fue; la orden ya se ejecutó
                pass

        def do_GET(self) -> None:
            url = urlsplit(self.path)
            if url.path in ("/", "/index.html"):
                try:
                    body = web_file.read_bytes()
                except OSError:
                    self._send(500, "text/plain; charset=utf-8", f"falta {web_file}\n".encode("utf-8"))
                    return
                self._send(200, "text/html; charset=utf-8", body)
                return
            if url.path == "/cmd":
                line = parse_qs(url.query, keep_blank_values=True).get("l", [""])[0]
                lines: list[str] = []
                dev.handle_line(line, lines.append)  # bloquea hasta la última línea de respuesta
                body = "".join(s + "\n" for s in lines).encode("utf-8")
                self._send(200, "text/plain; charset=utf-8", body)
                return
            self._send(404, "text/plain; charset=utf-8", b"no encontrado\n")

    return Handler


def make_tcp_handler(dev: Device):
    class TcpHandler(socketserver.StreamRequestHandler):
        timeout = 900  # segundos sin datos antes de cerrar la conexión

        def handle(self) -> None:
            dead = False

            def reply(text: str) -> None:
                nonlocal dead
                if dead:
                    return
                try:
                    self.wfile.write((text + "\n").encode("utf-8"))
                    self.wfile.flush()
                except OSError:
                    dead = True  # la orden sigue hasta el final, como en el hardware

            while True:
                try:
                    raw = self.rfile.readline(_READ_LIMIT)
                except OSError:
                    break
                if not raw:
                    break
                if len(raw) >= _READ_LIMIT and not raw.endswith(b"\n"):
                    # Línea demasiado larga: se responde ERR TOOLONG y se descarta hasta el fin de línea.
                    while True:
                        try:
                            rest = self.rfile.readline(_READ_LIMIT)
                        except OSError:
                            return
                        if not rest or rest.endswith(b"\n"):
                            break
                dev.handle_line(raw.decode("utf-8", "replace"), reply)

    return TcpHandler


class _HttpServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"  # en Windows, SO_REUSEADDR permitiría robar el puerto


class _TcpServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Módulo simulado DUELO (HTTP y, opcional, TCP).")
    ap.add_argument("--host", default="127.0.0.1",
                    help="interfaz de escucha (0.0.0.0 para acceder desde el celular en la red)")
    ap.add_argument("--port", type=int, default=8080, help="puerto HTTP (por defecto 8080)")
    ap.add_argument("--tcp", type=int, metavar="PUERTO",
                    help="servidor TCP de líneas crudas en ese puerto")
    ap.add_argument("--speed", type=float, default=5.0,
                    help="velocidad relativa al hardware real (por defecto 5.0)")
    ap.add_argument("--nvs", type=Path, metavar="ARCHIVO",
                    help="archivo que simula la NVS (por defecto, en el directorio temporal)")
    ap.add_argument("--web", type=Path, metavar="ARCHIVO",
                    help="interfaz a servir en / (por defecto web/index.html del repositorio)")
    args = ap.parse_args(argv)
    _utf8_streams()

    web_file = args.web or (REPO / "web" / "index.html")
    try:
        dev = Device(speed=args.speed, nvs_path=args.nvs)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    try:
        httpd = _HttpServer((args.host, args.port), make_http_handler(dev, web_file))
        tcpd = _TcpServer((args.host, args.tcp), make_tcp_handler(dev)) if args.tcp is not None else None
    except OSError as e:
        print(f"error: no se pudo abrir el puerto: {e}", file=sys.stderr)
        return 2

    print(f"{DEVICE_NAME} {FW_VERSION} simulado · velocidad x{args.speed:g}", flush=True)
    print(f"  HTTP  http://{args.host}:{args.port}/   interfaz: {web_file}", flush=True)
    if tcpd is not None:
        print(f"  TCP   {args.host}:{args.tcp}   (líneas crudas)", flush=True)
    print("  Ctrl+C para salir", flush=True)

    if tcpd is not None:
        threading.Thread(target=tcpd.serve_forever, name="tcp", daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        if tcpd is not None:
            tcpd.shutdown()
            tcpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
