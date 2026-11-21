// Orquestador de un módulo: línea de texto -> acción -> respuestas. PURO C++ (sin Arduino).
// El comportamiento obligatorio está en el comentario de controller.h; las pruebas nativas lo verifican con HAL falsos.
#include "controller.h"

#include <stdio.h>

#include <cmath>

#include "config.h"
#include "geometry.h"
#include "protocol.h"

namespace core {

namespace {

// Marca el controlador como ocupado mientras dura una orden (también si la salida lanza una excepción).
struct BusyGuard {
  volatile bool& flag;
  explicit BusyGuard(volatile bool& f) : flag(f) { flag = true; }
  ~BusyGuard() { flag = false; }
  BusyGuard(const BusyGuard&) = delete;
  BusyGuard& operator=(const BusyGuard&) = delete;
};

float clampServo(float v) {
  if (v < 0.0f) return 0.0f;
  if (v > 180.0f) return 180.0f;
  return v;
}

// Rampa de `now` a `target`: pasos de a lo sumo cfg::MAX_STEP_DEG, uno cada cfg::STEP_MS. Se detiene si hay STOP.
// `now` siempre refleja la última posición realmente ordenada al servo.
void rampTo(hal::Servo& s, float& now, float target, hal::Clock& clock, const volatile bool& stop) {
  for (;;) {
    if (stop) return;
    const float diff = target - now;
    if (!(std::fabs(diff) > 0.0f)) return;   // llegó (o `target` no es un número): nada que hacer
    if (std::fabs(diff) <= cfg::MAX_STEP_DEG) {
      now = target;
    } else {
      now += (diff > 0.0f) ? cfg::MAX_STEP_DEG : -cfg::MAX_STEP_DEG;
    }
    s.writeDeg(now);
    clock.delayMs(cfg::STEP_MS);
  }
}

// "%.2f" sin el "-0.00" de los valores negativos diminutos.
std::string fmt2(float v) {
  char buf[32];
  snprintf(buf, sizeof buf, "%.2f", static_cast<double>(v));
  std::string s(buf);
  if (s == "-0.00") s = "0.00";
  return s;
}

// Rangos aceptados por CAL SET (y por la calibración cargada de NVS): x -200..400, y -300..400, h 50..400, trims -10..10 (un trim mayor deja casi horizontal el rayo y podría sacarlo del tablero).
// Las comparaciones fallan con NaN, así que un NaN nunca se acepta.
bool calValuesValid(const float c[5]) {
  return c[0] >= -200.0f && c[0] <= 400.0f &&
         c[1] >= -300.0f && c[1] <= 400.0f &&
         c[2] >= 50.0f && c[2] <= 400.0f &&
         c[3] >= -10.0f && c[3] <= 10.0f &&
         c[4] >= -10.0f && c[4] <= 10.0f;
}

bool calibrationValid(const Calibration& c) {
  const float v[5] = {c.station.xMm, c.station.yMm, c.station.hMm, c.panTrimDeg, c.tiltTrimDeg};
  return calValuesValid(v);
}

bool servoSafe(float pan, float tilt) {
  return pan >= cfg::SERVO_SAFE_MIN && pan <= cfg::SERVO_SAFE_MAX && tilt >= cfg::SERVO_SAFE_MIN && tilt <= cfg::SERVO_SAFE_MAX;
}

}  // namespace

Controller::Controller(hal::Servo& pan, hal::Servo& tilt, hal::Laser& laser, hal::Buzzer& buzzer,
                       hal::Indicator& led, hal::Clock& clock, hal::CalStore& store)
    : pan_(pan), tilt_(tilt), laser_(laser), buzzer_(buzzer), led_(led), clock_(clock), store_(store),
      cal_(defaultCalibration()) {}

void Controller::begin() {
  laser_.set(false);   // lo primero, antes de tocar cualquier otra cosa

  Calibration loaded = defaultCalibration();
  if (store_.load(loaded) && calibrationValid(loaded)) {
    cal_ = loaded;
  } else {
    cal_ = defaultCalibration();
  }

  grid_ = GridCal();
  if (gridStore_) {
    GridCal g;
    if (gridStore_->load(g)) grid_ = g;
  }
  aimLaserOn_ = false;

  pan_.detach();       // servos libres hasta el primer disparo
  tilt_.detach();
  servosAttached_ = false;
  panNowDeg_ = cfg::PAN_CENTER_SERVO_DEG;
  tiltNowDeg_ = cfg::TILT_HORIZ_SERVO_DEG;
  stop_ = false;
  busy_ = false;
}

void Controller::requestStop() {
  stop_ = true;
  aimLaserOn_ = false;
  laser_.set(false);   // apagado inmediato (un GPIO); el disparo en curso lo notará y responderá ERR STOP
}

void Controller::tick() {
  if (aimLaserOn_ && !busy_ && static_cast<uint32_t>(clock_.ms() - aimLaserSince_) >= cfg::AIM_LASER_MAX_MS) {
    laser_.set(false);   // LASER ON se olvida encendido: se apaga solo
    aimLaserOn_ = false;
  }
}

void Controller::attachServos() {
  if (servosAttached_) return;
  pan_.attach();
  tilt_.attach();
  servosAttached_ = true;
  pan_.writeDeg(panNowDeg_);     // PWM definido desde el primer instante: el servo no salta a un valor arbitrario
  tilt_.writeDeg(tiltNowDeg_);
}

bool Controller::targetFor(Cell c, ServoCmd& out) const {
  if (grid_.valid) {
    float p, t;
    if (!gridAim(grid_, c.x, c.y, p, t) || !servoSafe(p, t)) return false;
    out.panServoDeg = p;
    out.tiltServoDeg = t;
    return true;
  }
  const Aim aim = aimAtCell(c, cal_.station);
  if (!aim.ok) return false;
  out = toServo(aim, cal_);
  return true;
}

bool Controller::busy() const { return busy_; }

const Calibration& Controller::calibration() const { return cal_; }

void Controller::moveAxis(hal::Servo& s, float& nowDeg, float targetDeg) {
  // Siempre se llega al destino subiendo el ángulo (elimina la holgura de los engranes).
  const Approach ap = approach(nowDeg, targetDeg, cfg::OVERSHOOT_DEG);
  if (ap.needsWaypoint) rampTo(s, nowDeg, clampServo(ap.waypointDeg), clock_, stop_);
  rampTo(s, nowDeg, targetDeg, clock_, stop_);
}

bool Controller::fire(Cell c, std::string& errLine) {
  ServoCmd target;
  if (!targetFor(c, target)) {
    errLine = "ERR LIMIT";
    return false;
  }

  // Cada salida por STOP apaga el láser; se centraliza para que ninguna ruta lo olvide.
  auto stopped = [this, &errLine]() {
    laser_.set(false);
    errLine = "ERR STOP";
    return false;
  };

  aimLaserOn_ = false;             // un disparo manda sobre el láser de apuntado
  laser_.set(false);
  if (stop_) return stopped();

  attachServos();

  moveAxis(pan_, panNowDeg_, target.panServoDeg);
  moveAxis(tilt_, tiltNowDeg_, target.tiltServoDeg);
  if (stop_) return stopped();

  clock_.delayMs(cfg::SETTLE_MS);
  if (stop_) return stopped();   // interlock: sin STOP pendiente

  laser_.set(true);
  if (stop_) return stopped();   // un STOP entre el interlock y el encendido no deja el láser encendido

  buzzer_.beep(cfg::BEEP_HZ, cfg::BEEP_MS);
  if (stop_) return stopped();

  clock_.delayMs(cfg::LASER_ON_MS);
  laser_.set(false);
  if (stop_) {
    errLine = "ERR STOP";
    return false;
  }
  return true;
}

bool Controller::disarmed() const { return link_.armedSeconds && link_.armedSeconds() <= 0; }

void Controller::handleLine(const std::string& line, const Reply& out) {
  auto say = [&out](const std::string& s) {
    if (out) out(s);
  };

  const ParseResult pr = parseLine(line);
  if (pr.err != ParseError::None) {
    say(errorText(pr.err));
    return;
  }

  // STOP se atiende siempre, incluso con un disparo en curso (llega desde otra tarea).
  if (pr.cmd.type == CmdType::Stop) {
    requestStop();
    say("OK STOP");
    return;
  }

  if (busy_) {
    say("ERR BUSY");
    return;
  }

  stop_ = false;   // un STOP anterior (sin disparo en curso) no debe abortar la orden nueva
  BusyGuard guard(busy_);

  switch (pr.cmd.type) {
    case CmdType::Fire: {
      if (disarmed()) {
        say("ERR DISARMED");
        break;
      }
      std::string err;
      if (fire(Cell{pr.cmd.x, pr.cmd.y}, err)) {
        say(fireOkText(pr.cmd.x, pr.cmd.y));
      } else {
        say(err);
      }
      break;
    }

    case CmdType::Test: {
      if (disarmed()) {
        say("ERR DISARMED");
        break;
      }
      say("TEST START");
      bool aborted = false;
      for (const auto& tc : cfg::TEST_CELLS) {
        std::string err;
        if (!fire(Cell{tc[0], tc[1]}, err)) {
          say("TEST ABORT");
          say(err);
          aborted = true;
          break;
        }
        say(fireOkText(tc[0], tc[1]));
        clock_.delayMs(cfg::TEST_GAP_MS);
        if (stop_) {
          say("TEST ABORT");
          say("ERR STOP");
          aborted = true;
          break;
        }
      }
      if (!aborted) say("TEST DONE");
      break;
    }

    case CmdType::Stop:   // ya tratado arriba
      break;

    case CmdType::Ping:
      say(std::string("PONG ") + DEVICE_NAME + " " + FW_VERSION);
      break;

    case CmdType::CalShow:
      say("CAL " + fmt2(cal_.station.xMm) + " " + fmt2(cal_.station.yMm) + " " + fmt2(cal_.station.hMm) + " " +
          fmt2(cal_.panTrimDeg) + " " + fmt2(cal_.tiltTrimDeg));
      break;

    case CmdType::CalSet:
      if (!calValuesValid(pr.cmd.cal)) {
        say("ERR RANGE");
      } else {
        cal_.station.xMm = pr.cmd.cal[0];
        cal_.station.yMm = pr.cmd.cal[1];
        cal_.station.hMm = pr.cmd.cal[2];
        cal_.panTrimDeg = pr.cmd.cal[3];
        cal_.tiltTrimDeg = pr.cmd.cal[4];
        say("OK CAL");
      }
      break;

    case CmdType::CalSave: {
      bool ok = store_.save(cal_);
      if (gridStore_) {
        bool any = false;
        for (int i = 0; i < GRID_PTS; ++i) any = any || grid_.has[i];
        if (any) {
          ok = gridStore_->save(grid_) && ok;
        } else {
          gridStore_->erase();
        }
      }
      say(ok ? "OK SAVE" : "ERR STORE");
      break;
    }

    case CmdType::CalReset:
      cal_ = defaultCalibration();
      store_.erase();
      grid_ = GridCal();
      if (gridStore_) gridStore_->erase();
      say("OK RESET");
      break;

    // ---- Protocolo v3: calibración por esquinas
    case CmdType::Pt:
      say("PT " + fmt2(panNowDeg_) + " " + fmt2(tiltNowDeg_));
      break;

    case CmdType::Jog:
    case CmdType::Goto: {
      if (disarmed()) {
        say("ERR DISARMED");
        break;
      }
      const bool rel = pr.cmd.type == CmdType::Jog;
      const float p = rel ? panNowDeg_ + pr.cmd.a : pr.cmd.a;
      const float t = rel ? tiltNowDeg_ + pr.cmd.b : pr.cmd.b;
      if (!servoSafe(p, t)) {
        say("ERR LIMIT");
        break;
      }
      attachServos();
      moveAxis(pan_, panNowDeg_, p);
      moveAxis(tilt_, tiltNowDeg_, t);
      if (stop_) {
        say("ERR STOP");
      } else {
        say("OK JOG " + fmt2(panNowDeg_) + " " + fmt2(tiltNowDeg_));
      }
      break;
    }

    case CmdType::LaserOn:
      if (disarmed()) {
        say("ERR DISARMED");
        break;
      }
      laser_.set(true);
      aimLaserOn_ = true;
      aimLaserSince_ = clock_.ms();
      say("OK LASER ON");
      break;

    case CmdType::LaserOff:
      laser_.set(false);
      aimLaserOn_ = false;
      say("OK LASER OFF");
      break;

    case CmdType::LaserQuery:
      say(aimLaserOn_ ? "LASER ON" : "LASER OFF");
      break;

    case CmdType::Corner: {
      const int i = pr.cmd.x - 1;
      grid_.has[i] = true;
      grid_.pan[i] = panNowDeg_;
      grid_.tilt[i] = tiltNowDeg_;
      if (i < 4) grid_.valid = false;   // cambiar una esquina invalida el mapa hasta el próximo CAL FIT
      say("OK CORNER " + std::to_string(pr.cmd.x) + " " + fmt2(panNowDeg_) + " " + fmt2(tiltNowDeg_));
      break;
    }

    case CmdType::Corners: {
      std::string bits;
      for (int i = 0; i < GRID_PTS; ++i) bits += grid_.has[i] ? '1' : '0';
      say("CORNERS " + bits + " " + (grid_.valid ? "1" : "0"));
      break;
    }

    case CmdType::CalFit: {
      if (!gridHasCorners(grid_)) {
        say("ERR NODATA");
        break;
      }
      float err = -1.0f;
      if (!gridFit(grid_, err)) {
        say("ERR FIT");
      } else {
        say(err < 0.0f ? std::string("OK FIT -") : "OK FIT " + fmt2(err));
      }
      break;
    }

    case CmdType::CalMap:
      say(grid_.valid ? "MAP GRID" : "MAP GEO");
      break;

    case CmdType::Aim: {
      if (disarmed()) {
        say("ERR DISARMED");
        break;
      }
      ServoCmd target;
      if (!targetFor(Cell{pr.cmd.x, pr.cmd.y}, target) || !servoSafe(target.panServoDeg, target.tiltServoDeg)) {
        say("ERR LIMIT");
        break;
      }
      attachServos();
      moveAxis(pan_, panNowDeg_, target.panServoDeg);
      moveAxis(tilt_, tiltNowDeg_, target.tiltServoDeg);
      say(stop_ ? "ERR STOP" : "OK AIM " + std::to_string(pr.cmd.x) + " " + std::to_string(pr.cmd.y));
      break;
    }

    case CmdType::MarkHit:
      led_.set(true);
      clock_.delayMs(cfg::LED_HIT_MS);
      led_.set(false);
      say("OK MARK");
      break;

    case CmdType::MarkMiss:
      say("OK MARK");
      break;

    case CmdType::Hello:
      say(std::string("HELLO SONAR 2 ") + FW_VERSION + " " + DEVICE_NAME + " " + link_.mode + " " + link_.caps);
      break;

    case CmdType::Mode:
      if (pr.cmd.mode == 0) {
        say("MODE " + link_.mode);
      } else if (!link_.requestMode) {
        say("ERR UNKNOWN");
      } else {
        say(link_.requestMode(pr.cmd.mode) ? std::string("OK MODE ") + (pr.cmd.mode == 1 ? "BT" : "WIFI") : "ERR STORE");
      }
      break;

    case CmdType::Arm:
      if (!link_.armedSeconds) {
        say("ARM NOTREQ");
      } else {
        const int left = link_.armedSeconds();
        say(left > 0 ? "ARM ON " + std::to_string(left) : std::string("ARM OFF"));
      }
      break;
  }
}

}  // namespace core
