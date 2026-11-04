// hal::Buzzer y hal::Indicator: salidas digitales simples.
#include "hal_esp32.h"

namespace hal_esp32 {

ActiveBuzzer::ActiveBuzzer(int pin, hal::Clock& clock) : pin_(pin), clock_(clock) {
  digitalWrite(pin_, LOW);
  pinMode(pin_, OUTPUT);
}

void ActiveBuzzer::beep(uint16_t /*hz*/, uint16_t ms) {
  digitalWrite(pin_, HIGH);
  clock_.delayMs(ms);          // espera "con gancho": se siguen atendiendo STOP / ERR BUSY
  digitalWrite(pin_, LOW);
}

LedPin::LedPin(int pin) : pin_(pin) {
  digitalWrite(pin_, LOW);
  pinMode(pin_, OUTPUT);
}

void LedPin::set(bool on) {
  digitalWrite(pin_, on ? HIGH : LOW);
}

}  // namespace hal_esp32
