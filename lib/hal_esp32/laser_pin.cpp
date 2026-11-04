// hal::Laser sobre un GPIO. Activo en alto (GPIO → 1 kΩ → base de 2N2222A; 10 kΩ de la base a GND).
#include "hal_esp32.h"
#include "soc/gpio_reg.h"
#include "soc/soc.h"

namespace hal_esp32 {

LaserPin::LaserPin(int pin) : pin_(pin) {
  // Primero el nivel en el registro de salida, luego el modo: el pin nunca llega a ponerse en HIGH.
  digitalWrite(pin_, LOW);
  pinMode(pin_, OUTPUT);
  digitalWrite(pin_, LOW);
}

void LaserPin::set(bool on) {
  digitalWrite(pin_, on ? HIGH : LOW);
}

bool LaserPin::isOn() const {
  // digitalRead() no sirve en un pin configurado solo como salida (su entrada está deshabilitada):
  // se lee el registro de salida (GPIO0..31).
  return ((REG_READ(GPIO_OUT_REG) >> pin_) & 1u) != 0;
}

}  // namespace hal_esp32
