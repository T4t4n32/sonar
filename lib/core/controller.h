#pragma once
// Orquestador de un módulo: línea de texto → acción → respuestas. PURO C++ (sin Arduino). Contrato compartido.
//
// COMPORTAMIENTO OBLIGATORIO (las pruebas nativas lo verifican con HAL falsos):
//  1. begin(): láser APAGADO lo primero; carga la calibración del CalStore (o defaultCalibration()); servos SIN activar (detach).
//  2. handleLine(): parseLine(); si hay error de sintaxis responde errorText(); si está ocupado responde "ERR BUSY".
//  3. FIRE (x,y): aimAtCell(); si !ok → "ERR LIMIT". Secuencia: láser OFF → attach servos → toServo() → movimiento SINCRONIZADO
//     de los dos ejes con perfil suave (pasos ≤ cfg::MAX_STEP_DEG cada cfg::STEP_MS); el eje que va a bajar pasa antes por un
//     waypoint (destino − cfg::OVERSHOOT_DEG) y remata subiendo despacio (≤ cfg::CREEP_STEP_DEG por paso) →
//     delayMs(cfg::SETTLE_MS) → comprobar interlock (no hay STOP pendiente) → láser ON → buzzer.beep(cfg::BEEP_HZ, cfg::BEEP_MS) →
//     delayMs(cfg::LASER_ON_MS) → láser OFF → responder fireOkText(x,y). Los servos quedan activos (reteniendo).
//     INVARIANTE DE SEGURIDAD: el láser solo está encendido entre el interlock y el fin del tiempo de permanencia; NUNCA mientras se mueve un servo.
//  4. STOP (o requestStop()): láser OFF de inmediato; si había un disparo, este responde "ERR STOP". STOP responde "OK STOP".
//  5. TEST: "TEST START"; para cada celda de cfg::TEST_CELLS: disparar, responder "OK (x,y)", delayMs(cfg::TEST_GAP_MS); al final "TEST DONE".
//     Si algo falla: "TEST ABORT" seguido de la línea de error.
//  6. PING → "PONG " DEVICE_NAME " " FW_VERSION.
//  7. CAL SHOW → "CAL x y h panTrim tiltTrim" (con 2 decimales); CAL SET → valida (h 50..400, x -200..400, y -300..400, trims -10..10)
//     y responde "OK CAL" o "ERR RANGE"; CAL SAVE → store.save → "OK SAVE" o "ERR STORE"; CAL RESET → defaults + store.erase → "OK RESET".
//  9. Protocolo v2 (opcional; sin configurar, el comportamiento es el v1): HELLO → "HELLO SONAR 2 <fw> <nombre> <modo> <caps>";
//     MODE → "MODE <modo>"; MODE BT|WIFI → "OK MODE <modo>" (o "ERR UNKNOWN" sin manejador, "ERR STORE" si lo rechaza);
//     ARM → "ARM NOTREQ" | "ARM OFF" | "ARM ON <s>" (el armado es SOLO físico: ninguna orden lo activa); con armado exigido,
//     FIRE y TEST responden "ERR DISARMED" sin mover nada. STOP, PING, HELLO, CAL y MARK nunca se bloquean.
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

  // Protocolo v2: lo rellena el firmware según el modo y los transportes activos.
  struct Link {
    std::string mode = "BT";                 // modo de arranque: "BT" o "WIFI"
    std::string caps = "-";                  // capacidades separadas por comas, sin espacios (p. ej. "ws,stream")
    std::function<bool(int)> requestMode;    // 1 = BT, 2 = WIFI; true si lo acepta (el firmware reinicia tras responder)
    std::function<std::string()> info;       // diagnóstico de la plataforma ("up=12 rst=POWERON heap=200000"); vacío = "-"
    std::function<int()> armedSeconds;       // segundos de armado que quedan (0 = desarmado); vacío = no se exige armado
  };
  void setLink(const Link& l) { link_ = l; }

  // Mapa de apuntado por esquinas (opcional; llamar ANTES de begin()). Sin almacén, el mapa solo vive en RAM.
  void setGridStore(hal::GridStore* s) { gridStore_ = s; }

  void begin();
  void tick();                                                   // llamar desde el bucle principal: apaga el láser de apuntado vencido
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
  Link link_;
  volatile bool stop_ = false;
  volatile bool busy_ = false;
  float panNowDeg_ = 90.0f;
  float tiltNowDeg_ = 90.0f;
  bool servosAttached_ = false;
  hal::GridStore* gridStore_ = nullptr;
  GridCal grid_;                                // mapa por esquinas (valid = se usa en vez de la geometría)
  volatile bool aimLaserOn_ = false;            // láser encendido a propósito por LASER ON (calibración)
  uint32_t aimLaserSince_ = 0;

  bool disarmed() const;                        // armado exigido y vencido
  bool targetFor(Cell c, ServoCmd& out) const;  // ángulos de servo de una celda (mapa por esquinas si lo hay; si no, geometría)
  void attachServos();
  bool fire(Cell c, std::string& errLine);
  void moveTo(float panDeg, float tiltDeg);     // movimiento sincronizado y suave de los dos ejes (ver controller.cpp)
};

}  // namespace core
