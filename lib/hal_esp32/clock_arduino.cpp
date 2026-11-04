// hal::Clock con gancho de inactividad.
#include "hal_esp32.h"

namespace {
constexpr uint32_t kSliceMs = 2;   // cada cuánto se llama al gancho mientras se espera
}

namespace hal_esp32 {

uint32_t ArduinoClock::ms() {
  return millis();
}

void ArduinoClock::delayMs(uint32_t waitMs) {
  const uint32_t start = millis();
  for (;;) {
    const uint32_t elapsed = millis() - start;     // aritmética sin signo: correcta al desbordar millis()
    if (elapsed >= waitMs) break;
    if (hook_ && !inHook_) {
      inHook_ = true;                              // el gancho no puede reentrar en sí mismo
      hook_();
      inHook_ = false;
    }
    const uint32_t left = waitMs - (millis() - start);
    if ((int32_t)left <= 0) break;                 // el gancho tardó más que la espera
    delay(left < kSliceMs ? left : kSliceMs);      // cede la CPU a FreeRTOS (BT / Wi-Fi)
  }
}

}  // namespace hal_esp32
