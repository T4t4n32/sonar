#pragma once
// Interfaces de hardware (HAL). PURO C++: la implementación real vive en lib/hal_esp32 y las falsas, en test/. Contrato compartido.
#include <stdint.h>
#include "geometry.h"

namespace hal {

struct Servo {
  virtual ~Servo() {}
  virtual void attach() = 0;                    // empieza a emitir PWM
  virtual void detach() = 0;                    // deja de emitir PWM (servo libre)
  virtual void writeDeg(float servoDeg) = 0;    // 0..180
};

struct Laser {
  virtual ~Laser() {}
  virtual void set(bool on) = 0;
  virtual bool isOn() const = 0;                // DEBE iniciar APAGADO
};

struct Buzzer {
  virtual ~Buzzer() {}
  virtual void beep(uint16_t hz, uint16_t ms) = 0;   // puede bloquear ms
};

struct Indicator {
  virtual ~Indicator() {}
  virtual void set(bool on) = 0;
};

struct Clock {
  virtual ~Clock() {}
  virtual uint32_t ms() = 0;
  virtual void delayMs(uint32_t ms) = 0;
};

struct CalStore {
  virtual ~CalStore() {}
  virtual bool load(core::Calibration& out) = 0;          // false si no hay datos válidos
  virtual bool save(const core::Calibration& c) = 0;
  virtual void erase() = 0;
};

}  // namespace hal
