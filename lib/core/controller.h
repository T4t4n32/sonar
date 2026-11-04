#pragma once
// Orquestador de un módulo: línea de texto → acción → respuestas. PURO C++ (sin Arduino). Contrato compartido.
//
// COMPORTAMIENTO OBLIGATORIO (las pruebas nativas lo verifican con HAL falsos):
//  1. begin(): láser APAGADO lo primero; carga la calibración del CalStore (o defaultCalibration()); servos SIN activar (detach).
//  2. handleLine(): parseLine(); si hay error de sintaxis responde errorText(); si está ocupado responde "ERR BUSY".
//  3. FIRE (x,y): aimAtCell(); si !ok → "ERR LIMIT". Secuencia: láser OFF → attach servos → toServo() → por eje, si approach()
//     pide waypoint, ir primero al waypoint → ir al ángulo final con rampa (pasos ≤ cfg::MAX_STEP_DEG cada cfg::STEP_MS) →
//     delayMs(cfg::SETTLE_MS) → comprobar interlock (no hay STOP pendiente) → láser ON → buzzer.beep(cfg::BEEP_HZ, cfg::BEEP_MS) →
//     delayMs(cfg::LASER_ON_MS) → láser OFF → responder fireOkText(x,y). Los servos quedan activos (reteniendo).
//     INVARIANTE DE SEGURIDAD: el láser solo está encendido entre el interlock y el fin del tiempo de permanencia; NUNCA mientras se mueve un servo.
//  4. STOP (o requestStop()): láser OFF de inmediato; si había un disparo, este responde "ERR STOP". STOP responde "OK STOP".
//  5. TEST: "TEST START"; para cada celda de cfg::TEST_CELLS: disparar, responder "OK (x,y)", delayMs(cfg::TEST_GAP_MS); al final "TEST DONE".
//     Si algo falla: "TEST ABORT" seguido de la línea de error.
//  6. PING → "PONG " DEVICE_NAME " " FW_VERSION.
//  7. CAL SHOW → "CAL x y h panTrim tiltTrim" (con 2 decimales); CAL SET → valida (h 50..400, x -200..400, y -300..400, trims -10..10)
//     y responde "OK CAL" o "ERR RANGE"; CAL SAVE → store.save → "OK SAVE" o "ERR STORE"; CAL RESET → defaults + store.erase → "OK RESET".
//  8. MARK HIT → LED encendido cfg::LED_HIT_MS (bloqueante con clock) → "OK MARK"; MARK MISS → "OK MARK" sin encender el LED.
#include <functional>
#include <string>
#include "hal.h"
#include "protocol.h"

namespace core {

class Controller {
 public:
  using Reply = std::function<void(const std::string&)>;

  Controller(hal::Servo& pan, hal::Servo& tilt, hal::Laser& laser, hal::Buzzer& buzzer,
             hal::Indicator& led, hal::Clock& clock, hal::CalStore& store);

  void begin();
  void handleLine(const std::string& line, const Reply& out);   // una línea completa; bloquea mientras dispara
  void requestStop();                                            // seguro desde otra tarea: aborta y apaga el láser en cuanto pueda
  bool busy() const;
  const Calibration& calibration() const;

 private:
  // la implementación es libre (controller.cpp)
  hal::Servo& pan_;
  hal::Servo& tilt_;
  hal::Laser& laser_;
  hal::Buzzer& buzzer_;
  hal::Indicator& led_;
  hal::Clock& clock_;
  hal::CalStore& store_;
  Calibration cal_;
  volatile bool stop_ = false;
  volatile bool busy_ = false;
  float panNowDeg_ = 90.0f;
  float tiltNowDeg_ = 90.0f;
  bool servosAttached_ = false;

  bool fire(Cell c, std::string& errLine);
  void moveAxis(hal::Servo& s, float& nowDeg, float targetDeg);
};

}  // namespace core
