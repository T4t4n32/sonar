#pragma once
// HAL falsos para las pruebas nativas. TODOS registran sus eventos, en orden, en un único `Log`:
// escrituras de servo (con el estado del láser en ese instante), cambios del láser, esperas, pitidos, LED,
// accesos al almacén de calibración y las respuestas del controlador.
//
// `Log::hook` se invoca justo después de registrar cada evento (no se reentra a sí mismo): sirve para simular
// que "algo ocurre durante" una espera, p. ej. un STOP que llega desde otra tarea.
#include <stdint.h>

#include <functional>
#include <string>
#include <vector>

#include "controller.h"
#include "hal.h"

namespace fakes {

enum class Ev {
  ServoAttach, ServoDetach, ServoWrite,
  LaserSet, Delay, Beep, LedSet,
  StoreLoad, StoreSave, StoreErase,
  Reply
};

struct Event {
  Ev kind = Ev::Delay;
  int servo = -1;          // 0 = pan, 1 = tilt (eventos de servo)
  float deg = 0.0f;        // ServoWrite
  bool on = false;         // LaserSet / LedSet: valor escrito
  bool laserOn = false;    // estado del láser en el instante del evento (en LaserSet, el estado NUEVO)
  uint32_t ms = 0;         // Delay / Beep
  uint16_t hz = 0;         // Beep
  uint32_t t = 0;          // reloj falso (ms) al registrar el evento
  std::string text;        // Reply
};

struct Log {
  std::vector<Event> events;
  bool laserOn = false;
  bool ledOn = false;
  uint32_t nowMs = 0;
  std::function<void(const Event&)> hook;
  bool inHook = false;

  void add(Event e) {
    e.laserOn = laserOn;
    e.t = nowMs;
    events.push_back(e);
    if (hook && !inHook) {
      inHook = true;
      const Event copy = e;   // el hook puede provocar más eventos: no se pasa una referencia al vector
      hook(copy);
      inHook = false;
    }
  }
};

class FakeServo : public hal::Servo {
 public:
  FakeServo(Log& log, int id) : log_(log), id_(id) {}

  void attach() override {
    attached = true;
    ++attaches;
    Event e;
    e.kind = Ev::ServoAttach;
    e.servo = id_;
    log_.add(e);
  }
  void detach() override {
    attached = false;
    ++detaches;
    Event e;
    e.kind = Ev::ServoDetach;
    e.servo = id_;
    log_.add(e);
  }
  void writeDeg(float servoDeg) override {
    if (!attached) ++writesWhileDetached;
    if (!(servoDeg >= 0.0f && servoDeg <= 180.0f)) ++writesOutOfRange;
    lastDeg = servoDeg;
    Event e;
    e.kind = Ev::ServoWrite;
    e.servo = id_;
    e.deg = servoDeg;
    log_.add(e);
  }

  bool attached = false;
  int attaches = 0;
  int detaches = 0;
  int writesWhileDetached = 0;   // escrituras con el servo sin activar: deben ser 0
  int writesOutOfRange = 0;      // escrituras fuera de 0..180 (o NaN): deben ser 0
  float lastDeg = -1.0f;

 private:
  Log& log_;
  int id_;
};

class FakeLaser : public hal::Laser {
 public:
  explicit FakeLaser(Log& log) : log_(log) {}   // inicia APAGADO (log.laserOn == false)

  void set(bool on) override {
    log_.laserOn = on;
    Event e;
    e.kind = Ev::LaserSet;
    e.on = on;
    log_.add(e);
  }
  bool isOn() const override { return log_.laserOn; }

 private:
  Log& log_;
};

class FakeBuzzer : public hal::Buzzer {
 public:
  explicit FakeBuzzer(Log& log) : log_(log) {}

  void beep(uint16_t hz, uint16_t ms) override {
    Event e;
    e.kind = Ev::Beep;
    e.hz = hz;
    e.ms = ms;
    log_.add(e);
    log_.nowMs += ms;   // el pitido bloquea ms
  }

 private:
  Log& log_;
};

class FakeLed : public hal::Indicator {
 public:
  explicit FakeLed(Log& log) : log_(log) {}

  void set(bool on) override {
    log_.ledOn = on;
    Event e;
    e.kind = Ev::LedSet;
    e.on = on;
    log_.add(e);
  }

 private:
  Log& log_;
};

class FakeClock : public hal::Clock {
 public:
  explicit FakeClock(Log& log) : log_(log) {}

  uint32_t ms() override { return log_.nowMs; }
  void delayMs(uint32_t ms) override {
    Event e;
    e.kind = Ev::Delay;
    e.ms = ms;
    log_.add(e);        // se registra al INICIO de la espera (y es ahí donde corre el hook)
    log_.nowMs += ms;
  }

 private:
  Log& log_;
};

class FakeStore : public hal::CalStore {
 public:
  explicit FakeStore(Log& log) : log_(log) {}

  bool load(core::Calibration& out) override {
    ++loads;
    note(Ev::StoreLoad);
    if (!hasData) return false;
    out = data;
    return true;
  }
  bool save(const core::Calibration& c) override {
    ++saves;
    note(Ev::StoreSave);
    if (!saveOk) return false;
    data = c;
    hasData = true;
    return true;
  }
  void erase() override {
    ++erases;
    note(Ev::StoreErase);
    hasData = false;
  }

  bool hasData = false;
  core::Calibration data = core::defaultCalibration();
  bool saveOk = true;
  int loads = 0;
  int saves = 0;
  int erases = 0;

 private:
  void note(Ev k) {
    Event e;
    e.kind = k;
    log_.add(e);
  }
  Log& log_;
};

// Un módulo completo: HAL falsos + Controller, todos sobre el mismo registro.
struct Rig {
  Log log;
  FakeServo pan{log, 0};
  FakeServo tilt{log, 1};
  FakeLaser laser{log};
  FakeBuzzer buzzer{log};
  FakeLed led{log};
  FakeClock clock{log};
  FakeStore store{log};
  core::Controller ctrl{pan, tilt, laser, buzzer, led, clock, store};

  Rig() = default;
  Rig(const Rig&) = delete;
  Rig& operator=(const Rig&) = delete;

  // Envía una línea al controlador. Cada respuesta se devuelve (en orden) y además queda en el registro como
  // evento Reply, para poder comprobar su posición relativa a los eventos de hardware.
  std::vector<std::string> send(const std::string& line) {
    std::vector<std::string> replies;
    ctrl.handleLine(line, [this, &replies](const std::string& r) {
      replies.push_back(r);
      Event e;
      e.kind = Ev::Reply;
      e.text = r;
      log.add(e);
    });
    return replies;
  }
};

}  // namespace fakes
