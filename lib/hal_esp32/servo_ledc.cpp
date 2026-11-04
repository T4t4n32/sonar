// hal::Servo sobre LEDC. 50 Hz, 16 bits: periodo 20000 us = 65536 cuentas.
#include <math.h>
#include "config.h"
#include "hal_esp32.h"

namespace {

constexpr uint32_t kFreqHz = 50;
constexpr uint8_t kResBits = 16;
constexpr double kPeriodUs = 1000000.0 / kFreqHz;          // 20000
constexpr double kCounts = 65536.0;                         // 2^kResBits

// Ángulo de servo (0..180) → cuentas de LEDC.
uint32_t dutyForDeg(float deg) {
  if (!(deg >= 0.0f)) deg = 0.0f;                           // también atrapa NaN
  if (deg > 180.0f) deg = 180.0f;
  const double us = cfg::SERVO_MIN_US + (double)(cfg::SERVO_MAX_US - cfg::SERVO_MIN_US) * deg / 180.0;
  double duty = us * kCounts / kPeriodUs + 0.5;
  if (duty > kCounts - 1) duty = kCounts - 1;
  return (uint32_t)duty;
}

}  // namespace

namespace hal_esp32 {

LedcServo::LedcServo(int pin, int channel) : pin_(pin), channel_(channel) {
  // Sin PWM, el pin queda en LOW (no flotante) hasta el primer attach().
  digitalWrite(pin_, LOW);
  pinMode(pin_, OUTPUT);
}

void LedcServo::applyDuty() {
  const uint32_t duty = dutyForDeg(lastDeg_);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin_, duty);
#else
  ledcWrite(channel_, duty);
#endif
}

void LedcServo::attach() {
  if (attached_) return;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  // core 3.x: la API es por pin (el canal se asigna solo). Rama sin probar en este proyecto.
  if (!configured_) configured_ = ledcAttach(pin_, kFreqHz, kResBits);
  if (!configured_) return;
  applyDuty();
#else
  // core 2.x: canal + temporizador explícitos. ledcSetup devuelve 0 si falla.
  if (!configured_) configured_ = ledcSetup(channel_, kFreqHz, kResBits) != 0;
  if (!configured_) return;
  ledcWrite(channel_, dutyForDeg(lastDeg_));   // el primer pulso ya sale con el ángulo correcto
  ledcAttachPin(pin_, channel_);
#endif
  attached_ = true;
}

void LedcServo::detach() {
  if (!attached_) {                            // ya libre: solo asegura el nivel bajo
    digitalWrite(pin_, LOW);
    return;
  }
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin_, 0);
  ledcDetach(pin_);
  configured_ = false;                         // en 3.x ledcDetach libera el canal
#else
  ledcWrite(channel_, 0);
  ledcDetachPin(pin_);
#endif
  digitalWrite(pin_, LOW);
  pinMode(pin_, OUTPUT);
  attached_ = false;
}

void LedcServo::writeDeg(float servoDeg) {
  if (isnan(servoDeg)) return;
  if (servoDeg < 0.0f) servoDeg = 0.0f;
  if (servoDeg > 180.0f) servoDeg = 180.0f;
  lastDeg_ = servoDeg;
  if (attached_) applyDuty();
}

}  // namespace hal_esp32
