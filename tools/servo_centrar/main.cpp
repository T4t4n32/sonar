// SONAR — firmware de CENTRADO de servos (herramienta de montaje, NO es el firmware de juego).
// Sin láser, sin Bluetooth: solo los dos servos por USB serie (115200).
//   pio run -e servo_centrar -t upload   y luego   pio device monitor -e servo_centrar
//
// Al arrancar los servos quedan LIBRES (sin señal). Nada se mueve hasta que mandes una orden.
// 90° = centro: el rayo al frente (pan) y horizontal (tilt), igual que config.h.
//
//   c        centra los dos a 90° (rampa lenta)
//   p        selecciona PAN            t   selecciona TILT
//   + / -    mueve el seleccionado 1°  (++ / -- : 5°)
//   p 95     pan al ángulo de servo 95 t 85   tilt a 85
//   u 1500   pulso directo en µs al seleccionado (600..2400)
//   e        recorre el rango de trabajo (pan ±57°, tilt 30..72°) para ver si algo roza; cualquier tecla lo aborta
//   x        suelta los dos servos (sin señal): se pueden mover a mano
//   i        estado        ?  ayuda
#include <Arduino.h>
#include "config.h"

namespace {

constexpr float kMinDeg = 15.0f;    // tope de seguridad de esta herramienta
constexpr float kMaxDeg = 165.0f;
constexpr uint32_t kStepMs = 15;    // 1° cada 15 ms: ~66°/s, suave para la fuente

struct Servo {
  const char* name;
  int pin;
  int channel;
  float deg;
  bool on;
};

Servo g_pan{"PAN", cfg::pins::PAN, 0, 90.0f, false};
Servo g_tilt{"TILT", cfg::pins::TILT, 2, 90.0f, false};
Servo* g_sel = &g_pan;

uint32_t dutyForUs(float us) { return (uint32_t)(us * 65536.0f / 20000.0f + 0.5f); }
float usForDeg(float d) { return cfg::SERVO_MIN_US + (cfg::SERVO_MAX_US - cfg::SERVO_MIN_US) * d / 180.0f; }

void writeUs(Servo& s, float us) {
  if (!s.on) {
    ledcSetup(s.channel, 50, 16);
    ledcWrite(s.channel, dutyForUs(us));
    ledcAttachPin(s.pin, s.channel);
    s.on = true;
  } else {
    ledcWrite(s.channel, dutyForUs(us));
  }
}

void release(Servo& s) {
  if (s.on) {
    ledcWrite(s.channel, 0);
    ledcDetachPin(s.pin);
    s.on = false;
  }
  pinMode(s.pin, OUTPUT);
  digitalWrite(s.pin, LOW);
}

bool abortRequested() {
  if (Serial.available()) {
    while (Serial.available()) Serial.read();
    return true;
  }
  return false;
}

// Mueve despacio al ángulo de servo `target`. Devuelve false si se abortó.
bool moveTo(Servo& s, float target, bool abortable = false) {
  if (target < kMinDeg) target = kMinDeg;
  if (target > kMaxDeg) target = kMaxDeg;
  if (!s.on) writeUs(s, usForDeg(s.deg));   // primer pulso en el ángulo recordado
  while (fabsf(s.deg - target) > 0.001f) {
    const float d = target - s.deg;
    s.deg += (fabsf(d) < 1.0f) ? d : (d > 0 ? 1.0f : -1.0f);
    writeUs(s, usForDeg(s.deg));
    delay(kStepMs);
    if (abortable && abortRequested()) return false;
  }
  return true;
}

void status() {
  Serial.printf("%s%s: %.1f deg  (%.0f us)%s\n", g_sel == &g_pan ? "> " : "  ", g_pan.name, g_pan.deg,
                usForDeg(g_pan.deg), g_pan.on ? "" : "  [libre]");
  Serial.printf("%s%s: %.1f deg  (%.0f us)%s\n", g_sel == &g_tilt ? "> " : "  ", g_tilt.name, g_tilt.deg,
                usForDeg(g_tilt.deg), g_tilt.on ? "" : "  [libre]");
}

void help() {
  Serial.println("c centrar | p/t elegir pan/tilt | + - (++ --) mover | p 95 / t 85 angulo | u 1500 pulso us");
  Serial.println("e recorrer rango | x soltar | i estado | ? ayuda   (angulo de servo; 90 = centro)");
}

void sweep() {
  Serial.println("Recorrido de prueba (cualquier tecla aborta). Mira y escucha: si algo roza o zumba, abortar.");
  const float p0 = cfg::PAN_CENTER_SERVO_DEG, t0 = cfg::TILT_HORIZ_SERVO_DEG;
  const float tMid = t0 + cfg::TILT_SIGN * 51.0f;
  if (!moveTo(g_pan, p0, true) || !moveTo(g_tilt, tMid, true)) goto abortado;
  if (!moveTo(g_pan, p0 - cfg::PAN_SIGN * cfg::PAN_LIMIT_DEG, true)) goto abortado;
  if (!moveTo(g_pan, p0 + cfg::PAN_SIGN * cfg::PAN_LIMIT_DEG, true)) goto abortado;
  if (!moveTo(g_pan, p0, true)) goto abortado;
  if (!moveTo(g_tilt, t0 + cfg::TILT_SIGN * cfg::TILT_MIN_DEG, true)) goto abortado;
  if (!moveTo(g_tilt, t0 + cfg::TILT_SIGN * cfg::TILT_MAX_DEG, true)) goto abortado;
  if (!moveTo(g_tilt, tMid, true)) goto abortado;
  Serial.println("Recorrido terminado.");
  status();
  return;
abortado:
  Serial.println("Abortado.");
  status();
}

void handle(String line) {
  line.trim();
  if (!line.length()) return;
  const char c0 = line[0];
  float v = 0;
  if (line == "c") {
    moveTo(g_pan, 90.0f);
    moveTo(g_tilt, 90.0f);
    Serial.println("Centrado a 90 deg.");
    status();
  } else if (line == "+" || line == "-" || line == "++" || line == "--") {
    const float step = (line.length() == 2 ? 5.0f : 1.0f) * (c0 == '+' ? 1.0f : -1.0f);
    moveTo(*g_sel, g_sel->deg + step);
    status();
  } else if (c0 == 'p' || c0 == 't') {
    Servo& s = (c0 == 'p') ? g_pan : g_tilt;
    g_sel = &s;
    if (sscanf(line.c_str() + 1, "%f", &v) == 1) moveTo(s, v);
    status();
  } else if (c0 == 'u' && sscanf(line.c_str() + 1, "%f", &v) == 1) {
    if (v < 600 || v > 2400) {
      Serial.println("Fuera de 600..2400 us.");
    } else {
      g_sel->deg = constrain((v - cfg::SERVO_MIN_US) * 180.0f / (cfg::SERVO_MAX_US - cfg::SERVO_MIN_US), 0.0f, 180.0f);
      writeUs(*g_sel, v);
      Serial.printf("%s a %.0f us (%.1f deg)\n", g_sel->name, v, g_sel->deg);
    }
  } else if (line == "e") {
    sweep();
  } else if (line == "x") {
    release(g_pan);
    release(g_tilt);
    Serial.println("Servos libres (sin senal).");
  } else if (line == "i") {
    status();
  } else {
    help();
  }
}

}  // namespace

void setup() {
  digitalWrite(cfg::pins::LASER, LOW);   // láser siempre apagado (aquí no se usa)
  pinMode(cfg::pins::LASER, OUTPUT);
  release(g_pan);
  release(g_tilt);
  Serial.begin(115200);
  delay(300);
  Serial.println("\nSONAR centrado de servos. Servos LIBRES hasta que mandes una orden.");
  help();
}

void loop() {
  static String buf;
  while (Serial.available()) {
    const char ch = (char)Serial.read();
    if (ch == '\n' || ch == '\r') {
      handle(buf);
      buf = "";
    } else if (buf.length() < 40) {
      buf += ch;
    }
  }
}
