// Mapa de apuntado por esquinas. PURO C++ (sin Arduino). Contrato: gridmap.h.
#include "gridmap.h"

#include <cmath>
#include <string.h>

#include "config.h"

namespace core {

namespace {

constexpr double kDeg2Rad = 0.017453292519943295;
constexpr double kRad2Deg = 57.295779513082320876798154814105;
constexpr double kCenterCell = 10.5;   // centro de la matriz 20×20 en coordenadas de celda
constexpr double kHalfSpan = 9.5;      // media distancia entre la celda 1 y la 20: normaliza a [-1, 1]

constexpr int kCells[GRID_PTS][2] = {{1, 1}, {20, 1}, {20, 20}, {1, 20}, {11, 11}};

double norm(int cell) { return (static_cast<double>(cell) - kCenterCell) / kHalfSpan; }

// Ángulos de servo -> dirección en coordenadas gnomónicas (u, v). false si el rayo es paralelo al plano de referencia.
bool uvOf(double panServo, double tiltServo, double& u, double& v) {
  const double th = (panServo - cfg::PAN_CENTER_SERVO_DEG) * kDeg2Rad;
  const double ph = (tiltServo - cfg::TILT_HORIZ_SERVO_DEG) * kDeg2Rad;
  const double c = std::cos(th);
  if (!(std::fabs(c) > 1e-6) || !(std::fabs(std::cos(ph)) > 1e-6)) return false;
  u = std::tan(th);
  v = std::tan(ph) / c;
  return std::isfinite(u) && std::isfinite(v);
}

// Resuelve A·x = b (8×8) por eliminación gaussiana con pivote parcial. false si es (casi) singular.
bool solve8(double a[8][9], double x[8]) {
  for (int col = 0; col < 8; ++col) {
    int piv = col;
    for (int r = col + 1; r < 8; ++r) {
      if (std::fabs(a[r][col]) > std::fabs(a[piv][col])) piv = r;
    }
    if (!(std::fabs(a[piv][col]) > 1e-10)) return false;
    if (piv != col) {
      for (int k = 0; k < 9; ++k) { const double t = a[col][k]; a[col][k] = a[piv][k]; a[piv][k] = t; }
    }
    for (int r = col + 1; r < 8; ++r) {
      const double f = a[r][col] / a[col][col];
      for (int k = col; k < 9; ++k) a[r][k] -= f * a[col][k];
    }
  }
  for (int r = 7; r >= 0; --r) {
    double s = a[r][8];
    for (int k = r + 1; k < 8; ++k) s -= a[r][k] * x[k];
    x[r] = s / a[r][r];
    if (!std::isfinite(x[r])) return false;
  }
  return true;
}

// Evalúa la homografía en la celda (x,y) -> (u,v).
bool applyH(const double h[8], double x, double y, double& u, double& v) {
  const double xn = (x - kCenterCell) / kHalfSpan, yn = (y - kCenterCell) / kHalfSpan;
  const double w = h[6] * xn + h[7] * yn + 1.0;
  if (!(w > 1e-6)) return false;
  u = (h[0] * xn + h[1] * yn + h[2]) / w;
  v = (h[3] * xn + h[4] * yn + h[5]) / w;
  return std::isfinite(u) && std::isfinite(v);
}

bool aimFromH(const double h[8], double x, double y, double& panServo, double& tiltServo) {
  double u, v;
  if (!applyH(h, x, y, u, v)) return false;
  const double th = std::atan(u);
  const double ph = std::atan(v * std::cos(th));
  panServo = cfg::PAN_CENTER_SERVO_DEG + th * kRad2Deg;
  tiltServo = cfg::TILT_HORIZ_SERVO_DEG + ph * kRad2Deg;
  return std::isfinite(panServo) && std::isfinite(tiltServo);
}

// ---- serialización (misma convención que geometry.cpp: float little-endian, CRC16-CCITT-FALSE)
uint16_t crc16(const unsigned char* data, unsigned n) {
  uint16_t crc = 0xFFFF;
  for (unsigned i = 0; i < n; ++i) {
    crc = static_cast<uint16_t>(crc ^ (static_cast<uint16_t>(data[i]) << 8));
    for (int b = 0; b < 8; ++b) crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021) : static_cast<uint16_t>(crc << 1);
  }
  return crc;
}
void putF32(unsigned char* p, float v) {
  uint32_t u;
  memcpy(&u, &v, sizeof u);
  p[0] = static_cast<unsigned char>(u & 0xFF);
  p[1] = static_cast<unsigned char>((u >> 8) & 0xFF);
  p[2] = static_cast<unsigned char>((u >> 16) & 0xFF);
  p[3] = static_cast<unsigned char>((u >> 24) & 0xFF);
}
float getF32(const unsigned char* p) {
  const uint32_t u = static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) | (static_cast<uint32_t>(p[2]) << 16) |
                     (static_cast<uint32_t>(p[3]) << 24);
  float v;
  memcpy(&v, &u, sizeof v);
  return v;
}
constexpr unsigned char kMagic0 = 'G', kMagic1 = 'M', kVersion = 1;
constexpr unsigned kDataOffset = 4;                       // 'G','M', versión, banderas
constexpr unsigned kCrcOffset = kDataOffset + 10 * 4;     // 44
static_assert(kCrcOffset + 2 == GRID_BLOB_SIZE, "el blob del mapa debe medir 46 bytes");

}  // namespace

void gridPointCell(int n, int& x, int& y) {
  if (n < 0 || n >= GRID_PTS) n = 0;
  x = kCells[n][0];
  y = kCells[n][1];
}

bool gridHasCorners(const GridCal& g) { return g.has[0] && g.has[1] && g.has[2] && g.has[3]; }

bool gridFit(GridCal& g, float& checkErrDeg) {
  checkErrDeg = -1.0f;
  g.valid = false;
  if (!gridHasCorners(g)) return false;

  double a[8][9];
  for (int i = 0; i < 4; ++i) {
    double u, v;
    if (!uvOf(g.pan[i], g.tilt[i], u, v)) return false;
    const double x = norm(kCells[i][0]), y = norm(kCells[i][1]);
    // h11 x + h12 y + h13 - u x h31 - u y h32 = u   y   h21 x + h22 y + h23 - v x h31 - v y h32 = v
    const double r1[9] = {x, y, 1, 0, 0, 0, -u * x, -u * y, u};
    const double r2[9] = {0, 0, 0, x, y, 1, -v * x, -v * y, v};
    for (int k = 0; k < 9; ++k) { a[2 * i][k] = r1[k]; a[2 * i + 1][k] = r2[k]; }
  }
  double h[8];
  if (!solve8(a, h)) return false;
  for (int k = 0; k < 8; ++k) g.h[k] = h[k];

  // Las 4 esquinas deben caer dentro del rango de la homografía (w > 0) y repetir los ángulos medidos.
  for (int i = 0; i < 4; ++i) {
    double p, t;
    if (!aimFromH(g.h, kCells[i][0], kCells[i][1], p, t)) return false;
    if (std::fabs(p - g.pan[i]) > 0.5 || std::fabs(t - g.tilt[i]) > 0.5) return false;
  }
  g.valid = true;

  if (g.has[4]) {
    double p, t;
    if (aimFromH(g.h, kCells[4][0], kCells[4][1], p, t)) {
      checkErrDeg = static_cast<float>(std::fmax(std::fabs(p - g.pan[4]), std::fabs(t - g.tilt[4])));
    } else {
      checkErrDeg = 999.0f;
    }
  }
  return true;
}

bool gridAim(const GridCal& g, int x, int y, float& panServo, float& tiltServo) {
  if (!g.valid || x < 1 || x > cfg::GRID_N || y < 1 || y > cfg::GRID_N) return false;
  double p, t;
  if (!aimFromH(g.h, x, y, p, t)) return false;
  panServo = static_cast<float>(p);
  tiltServo = static_cast<float>(t);
  return true;
}

unsigned gridSerialize(const GridCal& g, unsigned char* out, unsigned cap) {
  if (out == nullptr || cap < GRID_BLOB_SIZE) return 0;
  out[0] = kMagic0;
  out[1] = kMagic1;
  out[2] = kVersion;
  unsigned char flags = 0;
  for (int i = 0; i < GRID_PTS; ++i) {
    if (g.has[i]) flags = static_cast<unsigned char>(flags | (1u << i));
  }
  if (g.valid) flags = static_cast<unsigned char>(flags | (1u << 5));
  out[3] = flags;
  for (int i = 0; i < GRID_PTS; ++i) {
    putF32(out + kDataOffset + 4 * i, g.pan[i]);
    putF32(out + kDataOffset + 4 * (GRID_PTS + i), g.tilt[i]);
  }
  const uint16_t crc = crc16(out, kCrcOffset);
  out[kCrcOffset] = static_cast<unsigned char>(crc & 0xFF);
  out[kCrcOffset + 1] = static_cast<unsigned char>((crc >> 8) & 0xFF);
  return GRID_BLOB_SIZE;
}

bool gridDeserialize(const unsigned char* in, unsigned n, GridCal& out) {
  if (in == nullptr || n != GRID_BLOB_SIZE) return false;
  if (in[0] != kMagic0 || in[1] != kMagic1 || in[2] != kVersion) return false;
  const uint16_t stored = static_cast<uint16_t>(in[kCrcOffset] | (static_cast<uint16_t>(in[kCrcOffset + 1]) << 8));
  if (crc16(in, kCrcOffset) != stored) return false;

  GridCal g;
  const unsigned char flags = in[3];
  for (int i = 0; i < GRID_PTS; ++i) {
    g.has[i] = (flags >> i) & 1u;
    g.pan[i] = getF32(in + kDataOffset + 4 * i);
    g.tilt[i] = getF32(in + kDataOffset + 4 * (GRID_PTS + i));
    if (g.has[i] && !(g.pan[i] >= 0.0f && g.pan[i] <= 180.0f && g.tilt[i] >= 0.0f && g.tilt[i] <= 180.0f)) return false;
  }
  if ((flags >> 5) & 1u) {
    float err;
    if (!gridFit(g, err)) return false;   // se recalcula: un blob "válido" que ya no ajusta se rechaza
  }
  out = g;
  return true;
}

}  // namespace core
