// Geometría de apuntado y serialización de la calibración. PURO C++ (sin Arduino).
// Contrato: geometry.h. Marco y ecuaciones documentados allí.
#include "geometry.h"

#include <cmath>
#include <string.h>

#include "config.h"

namespace core {

namespace {

constexpr double kRadToDeg = 57.295779513082320876798154814105;

static_assert(sizeof(float) == 4, "calSerialize asume float de 32 bits");

// Recorta a 0..180. Un valor no finito (no debería ocurrir) cae al punto medio, nunca a un extremo.
float clampServoDeg(float v) {
  if (!std::isfinite(v)) return 90.0f;
  if (v < 0.0f) return 0.0f;
  if (v > 180.0f) return 180.0f;
  return v;
}

// CRC16-CCITT-FALSE: poly 0x1021, init 0xFFFF, sin reflejo, sin xorout. Valor de control "123456789" -> 0x29B1.
uint16_t crc16Ccitt(const unsigned char* data, unsigned n) {
  uint16_t crc = 0xFFFF;
  for (unsigned i = 0; i < n; ++i) {
    crc = static_cast<uint16_t>(crc ^ (static_cast<uint16_t>(data[i]) << 8));
    for (int b = 0; b < 8; ++b) {
      crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021) : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

// float <-> 4 bytes little-endian, independiente del endianness del anfitrión.
void putF32(unsigned char* p, float v) {
  uint32_t u;
  memcpy(&u, &v, sizeof u);
  p[0] = static_cast<unsigned char>(u & 0xFF);
  p[1] = static_cast<unsigned char>((u >> 8) & 0xFF);
  p[2] = static_cast<unsigned char>((u >> 16) & 0xFF);
  p[3] = static_cast<unsigned char>((u >> 24) & 0xFF);
}

float getF32(const unsigned char* p) {
  const uint32_t u = static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
                     (static_cast<uint32_t>(p[2]) << 16) | (static_cast<uint32_t>(p[3]) << 24);
  float v;
  memcpy(&v, &u, sizeof v);
  return v;
}

constexpr unsigned char kMagic0 = 'D';
constexpr unsigned char kMagic1 = 'L';
constexpr unsigned char kVersion = 1;
constexpr unsigned kHeaderSize = 3;                      // 'D','L', versión
constexpr unsigned kPayloadSize = 5 * 4;                 // 5 floats
constexpr unsigned kCrcOffset = kHeaderSize + kPayloadSize;   // 23: el CRC cubre los 23 bytes anteriores

static_assert(kCrcOffset + 2 == CAL_BLOB_SIZE, "el tamaño del blob debe ser 25 bytes");

}  // namespace

bool cellInRange(int x, int y) {
  return x >= 1 && x <= cfg::GRID_N && y >= 1 && y <= cfg::GRID_N;
}

Station defaultStation() {
  return Station{cfg::STATION_X_MM, cfg::STATION_Y_MM, cfg::TILT_H_MM};
}

Aim aimAtMm(float xMm, float yMm, const Station& s) {
  Aim a;
  a.ok = false;
  a.panDeg = 0.0f;
  a.tiltDeg = 0.0f;

  // Se calcula en double: la precisión de float en atan2 sobra, pero evita sorpresas en los bordes de los límites.
  const double dx = static_cast<double>(xMm) - static_cast<double>(s.xMm);
  const double dy = static_cast<double>(yMm) - static_cast<double>(s.yMm);
  const double h = static_cast<double>(s.hMm);
  if (!std::isfinite(dx) || !std::isfinite(dy) || !std::isfinite(h)) return a;   // entrada inválida: ok=false, ángulos 0

  a.panDeg = static_cast<float>(std::atan2(dx, dy) * kRadToDeg);
  a.tiltDeg = static_cast<float>(std::atan2(h, std::hypot(dx, dy)) * kRadToDeg);
  // Los ángulos calculados se devuelven aunque excedan los límites (diagnóstico); ok indica si son seguros.
  a.ok = std::fabs(a.panDeg) <= cfg::PAN_LIMIT_DEG && a.tiltDeg >= cfg::TILT_MIN_DEG && a.tiltDeg <= cfg::TILT_MAX_DEG;
  return a;
}

Aim aimAtCell(Cell c, const Station& s) {
  if (!cellInRange(c.x, c.y)) {
    Aim bad;
    bad.ok = false;
    bad.panDeg = 0.0f;
    bad.tiltDeg = 0.0f;
    return bad;
  }
  // Centro de la celda i: (i - 0.5) * CELL_MM.
  const float xMm = (static_cast<float>(c.x) - 0.5f) * cfg::CELL_MM;
  const float yMm = (static_cast<float>(c.y) - 0.5f) * cfg::CELL_MM;
  return aimAtMm(xMm, yMm, s);
}

Calibration defaultCalibration() {
  Calibration c;
  c.station = defaultStation();
  c.panTrimDeg = 0.0f;
  c.tiltTrimDeg = 0.0f;
  return c;
}

ServoCmd toServo(const Aim& a, const Calibration& c) {
  ServoCmd r;
  r.panServoDeg = clampServoDeg(cfg::PAN_CENTER_SERVO_DEG + cfg::PAN_SIGN * a.panDeg + c.panTrimDeg);
  r.tiltServoDeg = clampServoDeg(cfg::TILT_HORIZ_SERVO_DEG + cfg::TILT_SIGN * a.tiltDeg + c.tiltTrimDeg);
  return r;
}

Approach approach(float currentDeg, float targetDeg, float overshootDeg) {
  Approach ap;
  if (targetDeg < currentDeg) {
    ap.needsWaypoint = true;
    ap.waypointDeg = targetDeg - overshootDeg;
  } else {
    ap.needsWaypoint = false;
    ap.waypointDeg = targetDeg;   // sin waypoint: se deja el destino para que el campo nunca quede sin definir
  }
  return ap;
}

unsigned calSerialize(const Calibration& c, unsigned char* out, unsigned cap) {
  if (out == nullptr || cap < CAL_BLOB_SIZE) return 0;
  out[0] = kMagic0;
  out[1] = kMagic1;
  out[2] = kVersion;
  putF32(out + 3, c.station.xMm);
  putF32(out + 7, c.station.yMm);
  putF32(out + 11, c.station.hMm);
  putF32(out + 15, c.panTrimDeg);
  putF32(out + 19, c.tiltTrimDeg);
  const uint16_t crc = crc16Ccitt(out, kCrcOffset);
  out[kCrcOffset] = static_cast<unsigned char>(crc & 0xFF);          // little-endian
  out[kCrcOffset + 1] = static_cast<unsigned char>((crc >> 8) & 0xFF);
  return CAL_BLOB_SIZE;
}

bool calDeserialize(const unsigned char* in, unsigned n, Calibration& out) {
  if (in == nullptr || n != CAL_BLOB_SIZE) return false;
  if (in[0] != kMagic0 || in[1] != kMagic1) return false;
  if (in[2] != kVersion) return false;
  const uint16_t stored = static_cast<uint16_t>(in[kCrcOffset] | (static_cast<uint16_t>(in[kCrcOffset + 1]) << 8));
  if (crc16Ccitt(in, kCrcOffset) != stored) return false;

  Calibration c;
  c.station.xMm = getF32(in + 3);
  c.station.yMm = getF32(in + 7);
  c.station.hMm = getF32(in + 11);
  c.panTrimDeg = getF32(in + 15);
  c.tiltTrimDeg = getF32(in + 19);
  out = c;   // `out` solo se toca si todo es válido
  return true;
}

}  // namespace core
