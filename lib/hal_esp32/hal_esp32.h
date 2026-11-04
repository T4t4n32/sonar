#pragma once
// Implementaciones reales (ESP32 clásico + Arduino-ESP32) de las interfaces de lib/core/hal.h.
// Pensado para el core Arduino-ESP32 2.0.x (API de LEDC por canal); hay una rama para 3.x (API por pin) sin probar.
#include <Arduino.h>
#include <functional>
#include "hal.h"

namespace hal_esp32 {

// Servo por LEDC: 50 Hz, 16 bits, pulso cfg::SERVO_MIN_US..SERVO_MAX_US para 0..180°.
// Desconectado (detach) el pin queda en LOW sin emitir PWM, así el servo no recibe pulsos.
// attach() emite el último ángulo escrito (90° la primera vez) para que el primer pulso ya sea válido.
class LedcServo : public hal::Servo {
 public:
  // `channel` LEDC (0..15). Dos servos deben usar canales de pares distintos (0/1 comparten temporizador).
  LedcServo(int pin, int channel);
  void attach() override;
  void detach() override;
  void writeDeg(float servoDeg) override;

 private:
  int pin_;
  int channel_;
  float lastDeg_ = 90.0f;
  bool configured_ = false;
  bool attached_ = false;
  void applyDuty();
};

// Láser (vía transistor, activo en alto). El constructor deja el pin en LOW de inmediato: declara este objeto
// como global y primero de todos para que el láser quede apagado antes de setup().
class LaserPin : public hal::Laser {
 public:
  explicit LaserPin(int pin);
  void set(bool on) override;
  bool isOn() const override;   // lee el registro de salida del GPIO: refleja el pin real, no una copia

 private:
  int pin_;
};

// Zumbador ACTIVO por GPIO: suena a su frecuencia propia (se ignora `hz`). Bloquea `ms` esperando con el reloj,
// de modo que el gancho de inactividad sigue leyendo líneas (STOP) mientras suena.
class ActiveBuzzer : public hal::Buzzer {
 public:
  ActiveBuzzer(int pin, hal::Clock& clock);
  void beep(uint16_t hz, uint16_t ms) override;

 private:
  int pin_;
  hal::Clock& clock_;
};

// LED (activo en alto).
class LedPin : public hal::Indicator {
 public:
  explicit LedPin(int pin);
  void set(bool on) override;

 private:
  int pin_;
};

// Reloj de Arduino con gancho de inactividad: mientras delayMs() espera, llama al gancho cada ~2 ms.
// Así main puede seguir leyendo BT/USB (STOP / ERR BUSY) aunque Controller::handleLine esté bloqueado.
class ArduinoClock : public hal::Clock {
 public:
  void setIdleHook(std::function<void()> hook) { hook_ = std::move(hook); }
  uint32_t ms() override;
  void delayMs(uint32_t ms) override;

 private:
  std::function<void()> hook_;
  bool inHook_ = false;
};

// Calibración en NVS (Preferences): namespace "duelo", clave "cal", blob = core::calSerialize.
class NvsCalStore : public hal::CalStore {
 public:
  bool load(core::Calibration& out) override;
  bool save(const core::Calibration& c) override;
  void erase() override;
};

}  // namespace hal_esp32
